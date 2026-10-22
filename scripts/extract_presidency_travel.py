"""Extract Presidency-related travel and payment-card records from Portal da Transparencia bulk files.

The yearly travel zips (viagens, 2014+) and monthly payment-card zips (CPGF, 2013+) are ~2 GB in total, so they
are not archived in the repo. This script keeps only the rows needed for task TR and writes compact extracts to
data/raw/brazil/travel/. Traveller names and CPFs are dropped. Source zip SHA-256 hashes go to a manifest.

Rules (fixed before looking at totals):
- travel: organ superior code 20000 (Presidencia da Republica) -> category "presidency"; organ superior 52000
  (Defesa) with a motive mentioning the President ("PRESIDEN") -> category "defence_presidential_support";
  any other organ whose motive mentions a presidential trip ("COMITIVA PRESIDENCIAL", "VIAGEM PRESIDENCIAL",
  "ACOMPANHAR O PRESIDENTE", "MISSAO PRESIDENCIAL", "COMITIVA DO PRESIDENTE") -> "other_organs_presidential".
  International when any destination's suffix after "/" is not a two-letter Brazilian state code.
- payment card: organ superior code 20000 only (all transactions, including those published as protected).

Usage: python scripts/extract_presidency_travel.py <folder with viagens_YYYY.zip and cpgf/YYYYMM.zip>
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

OUT = Path("data/raw/brazil/travel")
UFS = {"AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
       "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"}
PRESIDENTIAL = re.compile(r"COMITIVA PRESIDENCIAL|VIAGEM PRESIDENCIAL|ACOMPANHAR O (?:SR\.? )?PRESIDENTE|"
                          r"MISSAO PRESIDENCIAL|COMITIVA DO (?:SR\.? )?PRESIDENTE")
TRAVEL_COLS = {
    "Identificador do processo de viagem": "trip_id", "Situação": "status", "Código do órgão superior": "organ_code",
    "Nome do órgão superior": "organ", "Nome órgão solicitante": "requesting_unit", "Cargo": "position",
    "Período - Data de início": "start", "Período - Data de fim": "end", "Destinos": "destinations",
    "Motivo": "motive", "Valor diárias": "per_diem_brl", "Valor passagens": "tickets_brl",
    "Valor devolução": "refund_brl", "Valor outros gastos": "other_brl",
}


def _plain(text: str) -> str:
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().upper()


def _international(destinations: str) -> bool:
    for part in str(destinations).split(","):
        if "/" in part:
            suffix = part.rsplit("/", 1)[1].strip()
            if suffix and suffix.upper() not in UFS and suffix.lower() != "sem informação":
                return True
    return False


def _money(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
                         errors="coerce").fillna(0.0)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def travel(folder: Path) -> tuple[pd.DataFrame, list[dict]]:
    frames, manifest = [], []
    for path in sorted(folder.glob("viagens_*.zip")):
        manifest.append({"file": path.name, "bytes": path.stat().st_size, "sha256": _sha(path)})
        with zipfile.ZipFile(path) as archive:
            name = next((n for n in archive.namelist() if n.endswith("_Viagem.csv")), None)
            if name is None:
                continue
            with archive.open(name) as raw:
                reader = pd.read_csv(io.TextIOWrapper(raw, encoding="latin1"), sep=";", quotechar='"', dtype=str,
                                     usecols=list(TRAVEL_COLS), chunksize=200_000)
                for chunk in reader:
                    chunk = chunk.rename(columns=TRAVEL_COLS)
                    motive = chunk["motive"].fillna("").map(_plain)
                    presidency = chunk["organ_code"].eq("20000")
                    defence = chunk["organ_code"].eq("52000") & motive.str.contains("PRESIDEN")
                    other = ~presidency & ~defence & motive.str.contains(PRESIDENTIAL)
                    keep = chunk.loc[presidency | defence | other].copy()
                    if keep.empty:
                        continue
                    keep["category"] = "other_organs_presidential"
                    keep.loc[presidency[keep.index], "category"] = "presidency"
                    keep.loc[defence[keep.index], "category"] = "defence_presidential_support"
                    for column in ("per_diem_brl", "tickets_brl", "refund_brl", "other_brl"):
                        keep[column] = _money(keep[column])
                    keep["international"] = keep["destinations"].map(_international)
                    keep["source_file"] = path.name
                    frames.append(keep)
    return pd.concat(frames, ignore_index=True), manifest


def card(folder: Path) -> tuple[pd.DataFrame, list[dict]]:
    frames, manifest = [], []
    for path in sorted((folder / "cpgf").glob("*.zip")):
        manifest.append({"file": f"cpgf/{path.name}", "bytes": path.stat().st_size, "sha256": _sha(path)})
        try:
            archive = zipfile.ZipFile(path)
        except zipfile.BadZipFile:
            continue
        with archive:
            for name in archive.namelist():
                with archive.open(name) as raw:
                    frame = pd.read_csv(io.TextIOWrapper(raw, encoding="latin1"), sep=";", quotechar='"', dtype=str)
                frame = frame.loc[frame["CÓDIGO ÓRGÃO SUPERIOR"].eq("20000")]
                frame = frame.drop(columns=[c for c in ("CPF PORTADOR", "NOME PORTADOR") if c in frame])
                frame["VALOR TRANSAÇÃO"] = _money(frame["VALOR TRANSAÇÃO"])
                frame["source_file"] = f"cpgf/{path.name}"
                frames.append(frame)
    return pd.concat(frames, ignore_index=True), manifest


def main(argv: list[str]) -> int:
    folder = Path(argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    trips, manifest_t = travel(folder)
    trips.to_csv(OUT / "presidency_travel_2014_2026.csv.gz", index=False, compression="gzip")
    cards, manifest_c = card(folder)
    cards.to_csv(OUT / "presidency_cpgf_2013_2026.csv.gz", index=False, compression="gzip")
    with (OUT / "portal_transparencia_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_t + manifest_c)
    print(f"travel rows {len(trips)}; card rows {len(cards)}")
    print(trips.groupby(["category", "international"])[["per_diem_brl", "tickets_brl", "other_brl"]].sum().round(0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
