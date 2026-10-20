"""Extract selected columns from an IBGE fixed-width microdata file.

Column positions come from the official SAS reading program shipped with the
survey (e.g. data/raw/brazil/layouts/pnadc_2025_visita1_input.txt), so no
position is hand-typed. The text file is streamed straight from the official
zip in chunks; only the requested columns are kept, and the output goes to the
git-ignored data/processed/brazil/microdata/ directory. Feed that export to
scripts/load_brazil_microdata.py with a reviewed mapping.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

import pandas as pd


# Matches SAS INPUT lines such as "@0058 V1032   15.   /* Peso */" or "@0006 UF   $2.".
SAS_FIELD = re.compile(r"^@(\d+)\s+(\w+)\s+(\$?)(\d+)\.")


def parse_sas_layout(path: Path) -> pd.DataFrame:
    """Return name, start (0-based), width and is_text for every INPUT field."""
    rows = []
    for line in path.read_text(encoding="latin-1").splitlines():
        match = SAS_FIELD.match(line.strip())
        if match:
            start, name, text, width = match.groups()
            rows.append({
                "name": name,
                "start": int(start) - 1,
                "width": int(width),
                "is_text": text == "$",
            })
    layout = pd.DataFrame(rows)
    if layout.empty or layout["name"].duplicated().any():
        raise ValueError(f"Could not parse a unique field list from {path}")
    return layout


def read_columns(
    zip_path: Path, layout: pd.DataFrame, columns: list[str], chunksize: int = 200_000
) -> pd.DataFrame:
    missing = sorted(set(columns) - set(layout["name"]))
    if missing:
        raise ValueError(f"Columns not in layout: {missing}")
    selected = layout.set_index("name").loc[columns]
    colspecs = [(int(s), int(s + w)) for s, w in zip(selected["start"], selected["width"])]
    # Keep everything as text first so codes keep leading zeros; numeric fields
    # are converted afterwards, with blanks becoming missing rather than zero.
    dtypes = {name: str for name in columns}
    with zipfile.ZipFile(zip_path) as archive:
        members = [m for m in archive.namelist() if m.lower().endswith(".txt")]
        if len(members) != 1:
            raise ValueError(f"Expected one .txt member in {zip_path}, found {members}")
        with archive.open(members[0]) as handle:
            chunks = pd.read_fwf(
                handle, colspecs=colspecs, names=columns, dtype=dtypes,
                header=None, chunksize=chunksize, encoding="latin-1",
            )
            frame = pd.concat(chunks, ignore_index=True)
    for name in columns:
        if not selected.loc[name, "is_text"]:
            frame[name] = pd.to_numeric(frame[name].str.strip(), errors="coerce")
    return frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path, help="Official IBGE microdata zip")
    parser.add_argument("layout", type=Path, help="Official SAS reading program (INPUT statement)")
    parser.add_argument("output", type=Path, help="CSV output under data/processed/brazil/microdata/")
    parser.add_argument("columns", nargs="*", help="Source variable names to keep")
    parser.add_argument("--mapping", type=Path, help="Approved mapping JSON; keeps exactly its source columns")
    args = parser.parse_args()
    columns = list(args.columns)
    if args.mapping:
        mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
        columns += [c for c in [*mapping["columns"], *mapping.get("household_key_columns", [])] if c not in columns]
    if not columns:
        parser.error("give column names or --mapping")
    if "processed/brazil/microdata" not in args.output.as_posix():
        raise ValueError("Microdata extracts must be written under data/processed/brazil/microdata/ (git-ignored)")
    frame = read_columns(args.zip, parse_sas_layout(args.layout), columns)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    print(f"Wrote {len(frame)} rows x {len(columns)} columns to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
