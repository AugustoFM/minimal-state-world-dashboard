"""Build the F1 fiscal-target delivery dataset from archived LDO annexes.

Run from the repository root with ``python scripts/build_fiscal_delivery.py``.
Fiscal amounts below are transcribed from the archived official annexes.  The
script validates every stored quote against text extracted from its source.
"""

from __future__ import annotations

import csv
import json
import math
import re
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/brazil/fiscal_delivery"
GDP_FILE = ROOT / "data/raw/brazil/macro/ibge_sidra_1846_gdp_current_1996_2025.json"
BCB_FILE = ROOT / "data/brazil/backtest_observed.csv"
CSV_FILE = ROOT / "data/brazil/fiscal_delivery.csv"
DOC_FILE = ROOT / "docs/f1_fiscal_delivery.md"
CONFIG_FILE = ROOT / "config/f1_proposed.yaml"

COLUMNS = [
    "evaluated_year", "concept", "original_target_brl_bn",
    "original_target_pct_gdp", "final_target_brl_bn",
    "final_target_pct_gdp", "n_revisions", "revision_laws",
    "deductions_used_brl_bn", "outturn_brl_bn", "outturn_pct_gdp",
    "miss_vs_original_pp_gdp", "miss_vs_final_pp_gdp", "government",
    "special_event", "source_file", "source_quote", "extraction_method",
]

FILES = {
    1999: "ldo2001_avaliacao_metas_ano_anterior.pdf",
    2000: "ldo2002_avaliacao_metas_ano_anterior.pdf",
    2002: "ldo2004_avaliacao_metas_ano_anterior.pdf",
    2008: "ldo2010_avaliacao_metas_ano_anterior.pdf",
    2010: "ldo2012_avaliacao_metas_ano_anterior.pdf",
    2011: "ldo2013_avaliacao_metas_ano_anterior.pdf",
    2012: "ldo2014_avaliacao_metas_ano_anterior.pdf",
    2014: "ldo2016_avaliacao_metas_ano_anterior.pdf",
    2015: "ldo2017_avaliacao_metas_ano_anterior.pdf",
    2016: "ldo2018_avaliacao_metas_ano_anterior.pdf",
    2017: "ldo2019_avaliacao_metas_ano_anterior.docx",
    2018: "ldo2020_avaliacao_metas_ano_anterior.pdf",
    2019: "ldo2021_avaliacao_metas_ano_anterior.pdf",
    2020: "ldo2022_avaliacao_metas_ano_anterior.pdf",
    2021: "ldo2023_avaliacao_metas_ano_anterior.pdf",
    2022: "ldo2024_avaliacao_metas_ano_anterior.pdf",
    2023: "ldo2025_avaliacao_metas_ano_anterior.pdf",
    2024: "ldo2026_avaliacao_metas_ano_anterior.pdf",
    2025: "ldo2027_avaliacao_metas_ano_anterior.pdf",
}


def normalize_text(text: str) -> str:
    """Match the stable whitespace-normalised representation used by quotes."""
    return re.sub(r"\s+", " ", text).strip()


def extract_text(path: Path) -> str:
    """Extract PDF text with pypdf or DOCX text directly from Word XML."""
    if path.suffix.lower() == ".pdf":
        raw = " ".join(page.extract_text() or "" for page in PdfReader(path).pages)
    elif path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
        tag = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        raw = " ".join(
            "".join(node.text or "" for node in paragraph.iter(tag + "t"))
            for paragraph in root.iter(tag + "p")
        )
    else:  # pragma: no cover - guarded by the fixed source inventory
        raise ValueError(f"Unsupported source type: {path}")
    return normalize_text(raw)


def government_for_year(year: int) -> str:
    if 1999 <= year <= 2002:
        return "FHC II (PSDB)"
    if 2003 <= year <= 2010:
        return "Lula I-II (PT)"
    if 2011 <= year <= 2015:
        return "Dilma (PT)"
    if year == 2016:
        return "2016 transition"
    if 2017 <= year <= 2018:
        return "Temer (MDB)"
    if 2019 <= year <= 2022:
        return "Bolsonaro (PSL/PL)"
    if 2023 <= year <= 2025:
        return "Lula III (PT)"
    raise ValueError(year)


def event_for_year(year: int) -> str:
    return {
        1999: "devaluation",
        2008: "global crisis",
        2020: "pandemic; fiscal targets suspended under state of calamity",
    }.get(year, "")


# Values are R$ billion and percentage points of GDP.  Positive means surplus;
# negative means deficit.  A None is an evidenced absence, not an estimate.
# Short quotes are exact substrings of whitespace-normalised extracted text.
MANUAL: dict[int, dict[str, dict[str, object]]] = {
    1999: {
        "consolidated public sector": dict(o=None, op=None, f=None, fp=None, d=None, u=None, up=None, n=0, laws="",
            q="Neste programa estabeleceram-se metas de superávit primário do setor público consolidado para o período 1999-2001 muito superiores aos resultados observados entre 1995 e 1998"),
        "central government": dict(o=16.2, op=None, f=16.2, fp=None, d=None, u=21.5, up=2.13, n=0, laws="",
            q="O resultado obtido, de R$ 21,5 bilhões, superou largamente a meta original, contribuindo decisivamente para a estabilização da dívida líquida como proporção do PIB."),
    },
    2000: {
        "consolidated public sector": dict(o=None, op=None, f=None, fp=None, d=None, u=None, up=None, n=0, laws="", q="A meta conjunta estabelecida pela Medida Provisória em questão fixou o superávit do Governo Central e das Empresas Estatais Federais em, no mínimo, R$ 30,5 bilhões."),
        "central government": dict(o=28.5, op=2.65, f=None, fp=None, d=None, u=None, up=None, n=1, laws="MP 2.030-30, 20 June 2000", q="À época, tal meta implicava um superávit de R$ 28,5 bilhões, com base nas estimativas disponíveis para o PIB de 2000."),
    },
    2002: {
        "consolidated public sector": dict(o=None, op=None, f=None, fp=None, d=None, u=None, up=None, n=0, laws="", q="Ao final de 2002, o Governo Federal apresentou resultado primário superavitário de R$ 38,2 bilhões (2,90% do PIB)"),
        "central government": dict(o=26.4, op=2.0, f=29.2, fp=2.24, d=None, u=31.9, up=2.42, n=1, laws="MP 2.211, 29 August 2001", q="Ao final de 2002, o Governo Federal apresentou resultado primário superavitário de R$ 38,2 bilhões (2,90% do PIB), sendo R$ 31,9 bilhões (2,42% do PIB) referentes aos Orçamentos Fiscal e da Seguridade Social"),
    },
    2008: {
        "consolidated public sector": dict(o=None, op=3.80, f=None, fp=3.80, d=None, u=118.0, up=4.07, n=0, laws="", q="Encerrado o exercício de 2008, apurou-se superá vit primário do Setor Público consolidado de R$ 118,0 bilhões, equivalente a 4,07% do PIB estimado do período"),
        "central government": dict(o=None, op=2.20, f=None, fp=2.20, d=None, u=71.3, up=2.46, n=0, laws="", q="No que tange ao Governo Federal, o superá vit primário apurado distribuiu-se entre o Governo Central e as empresas estatais federais nos montantes de R$ 71,3 b ilhões (2,46% do PIB) e R$ 14,0 bilhões (0,48% do PIB), respectivamente."),
    },
    2010: {
        "consolidated public sector": dict(o=None, op=3.30, f=None, fp=3.10, d=22.1, u=101.7, up=None, n=1, laws="Law 12.377, 30 December 2010", q="Além disso, destaca-se que o resultado pr imário atingido pelo Governo Federal em 2010 contribuiu com 76,79% do superávit global do setor público consolidado não-financeiro, que perfez, no período, R$ 101,7 bilhões."),
        "central government": dict(o=72.6, op=2.15, f=76.3, fp=2.15, d=22.1, u=78.7233, up=2.22, n=2, laws="Law 12.182, 29 December 2009; Law 12.377, 30 December 2010", q="Dessa forma, as novas metas de resultado primário do Governo Central e das Empresas Estatais Federais foram definidas em R$ 76,3 bilhões (2,15% do PIB) e resultado nulo (0,00% do PIB), respectivamente."),
    },
    2011: {
        "consolidated public sector": dict(o=117.9, op=None, f=127.9, fp=None, d=0.0, u=128.7205, up=None, n=1, laws="Decrees 7.575/2011 and 7.622/2011 (additional effort)", q="Cabe acrescentar que o valor a maior do resultado pri mário realizado pelo Governo Federal (R$ 1,9 bilhão) foi suficiente para garantir o cumprimento da meta de resultado primário do setor público consolidado (R$ 127,9 bilhões)"),
        "central government": dict(o=81.8, op=None, f=91.8, fp=None, d=0.0, u=93.0355, up=None, n=1, laws="Decrees 7.575/2011 and 7.622/2011 (additional effort)", q="O superávit primário do Governo Central superou em R$ 1,3 bilhão sua meta prevista, enquanto o resultado das Empresas Estatais Federais ficou acima do previsto em R$ 579,1 milhões."),
    },
    2012: {
        "consolidated public sector": dict(o=139.8, op=None, f=139.8, fp=None, d=39.3, u=None, up=None, n=0, laws="", q="A meta de superávit primário para o setor público consolidado não financeiro, estabelec ida na LDO-2012, foi fixada em R$ 139,8 bilhões para 2012"),
        "central government": dict(o=97.0, op=None, f=97.0, fp=None, d=39.3, u=86.086, up=None, n=0, laws="", q="Ao final do ano, as despesas no âmbito do PAC atingiram o montante de R$ 39,3 bilhões, o que resultou num valor de meta de superávit primário do Governo Federal para fins de cumprimento do dispositivo legal de R$ 57,7 bilhões."),
    },
    2014: {
        "consolidated public sector": dict(o=None, op=None, f=None, fp=None, d=None, u=None, up=None, n=0, laws="", q="A meta de superávit primário para o Governo Central (Tesouro Nacional, Previdência Social e Banco Central), estabelecida na Lei nº 12.919, de 24 de dezembro de 2013"),
        "central government": dict(o=116.072, op=None, f=116.072, fp=None, d=161.741, u=-20.4717, up=None, n=1, laws="Law 13.053, 15 December 2014", q="Ao final de 2014, as despesas do PAC atingiram R$ 57,7 bilhões, enquanto as desonerações tributárias, divulgadas pela RFB, chegaram a R$ 104,0 bilhões, totalizando uma possiblidade total de abatimento de R$ 161,7 bilhões"),
    },
    2015: {
        "consolidated public sector": dict(o=66.3, op=None, f=-48.9, fp=-0.85, d=66.9, u=-111.2, up=None, n=1, laws="Law 13.199, 3 December 2015", q="Assim, o resultado prim ário do Setor Público consolidado não financeiro foi de déficit de R$ 111,2 bilhões, inferior ao valor máximo previsto na LDO (déficit de R$ 115,8 bilhões)."),
        "central government": dict(o=55.3, op=None, f=-51.8244, fp=None, d=66.858, u=-116.6556, up=None, n=1, laws="Law 13.199, 3 December 2015", q="Meta Resultado Primário Fixada na LDO 116.072, 0 -51.824,4 24.000,0 II. Meta Resultado Primário Ajustada PAC/Desonerações -45.669,0 -118.682,4 III. Resultado Primário Obtido -22.479,3 -118.384,3"),
    },
    2016: {
        "consolidated public sector": dict(o=30.6, op=None, f=-163.9, fp=None, d=0.0, u=-155.8, up=None, n=1, laws="Law 13.291, 25 May 2016", q="Assim, o resultado de 2016 para o Setor Público ficou em déficit de R$ 155,8 bilhões, inferior ao máximo previsto na LDO-2016 (déficit de R$ 163,9 bilhões)."),
        "central government": dict(o=24.0, op=None, f=-170.496, fp=None, d=0.0, u=-159.473, up=None, n=1, laws="Law 13.291, 25 May 2016", q="Meta Resultado Primário Fixada na LDO -51.824,4 -170.496,0 -139.000,0 II. Meta Resultado Primário Ajustada PAC/Desonerações -118.682,4 -170.496,0 -139.000,0 III. Resultado Primário Obtido -118.384,3 -160.309,0 -139.000,0 Fiscal e Seguridade Social -116.655,6 -159.473,0"),
    },
    2017: {
        "consolidated public sector": dict(o=-143.1, op=None, f=-163.1, fp=None, d=0.0, u=-110.6, up=None, n=1, laws="Law 13.480, 13 September 2017", q="Assim, o resultado de 2017 para o Setor Público ficou em déficit de R$ 110,6 bilhões, inferior ao máximo previsto na LDO-2017 (déficit de R$ 163,1 bilhões)."),
        "central government": dict(o=-139.0, op=None, f=-159.0, fp=None, d=0.0, u=-118.4, up=None, n=1, laws="Law 13.480, 13 September 2017", q="Finalizado o exercício de 2017, verificou-se que o Governo Federal atingiu déficit primário de R$ 119,4 bilhões, composto de déficits do Governo Central de R$ 118,4 bilhões e déficit das Empresas Estatais Federais de R$ 952 milhões"),
    },
    2018: {
        "consolidated public sector": dict(o=-131.3, op=None, f=-161.3, fp=None, d=0.0, u=-108.3, up=None, n=1, laws="Law 13.480, 13 September 2017", q="Assim, o resultado de 2018 para o Setor Público ficou em déficit de R$ 1 08,3 bilhões, inferior ao previsto na LDO- 2018 (déficit de R$ 161,3 bilhões)."),
        "central government": dict(o=-129.0, op=None, f=-159.0, fp=-2.23, d=0.0, u=-116.167, up=-1.70, n=1, laws="Law 13.480, 13 September 2017", q="IV. Resultado Primário Governo Central (I – II + III)3 -159.000 -2,23 -116.167 -1,70 V. Resultado Primário Empresas Estatais Federais -3.500 -0,05 3.466 0,05"),
    },
    2019: {
        "consolidated public sector": dict(o=-132.0, op=None, f=-132.0, fp=None, d=0.0, u=-61.9, up=None, n=0, laws="", q="Assim, o resultado de 2019 para o Setor Público ficou em déficit de R$ 61,9 bilhões, inferior ao previsto na LDO - 2019 (déficit de R$ 132,0 bilhões)."),
        "central government": dict(o=-139.0, op=-1.84, f=-139.0, fp=-1.84, d=0.0, u=-88.899, up=-1.23, n=0, laws="", q="III. Resultado Primário Governo Central (I - II)2 -139.000 -1,84 -88.899 -1,23 IV. Resultado Primário Empresas Estatais Federais -3.500 -0,05 10.292 0,14"),
    },
    2020: {
        "consolidated public sector": dict(o=-118.9, op=None, f=-158.710, fp=-1.51, d=0.0, u=-702.950, up=-9.44, n=1, laws="Law 13.983, 3 April 2020", q="E - Resultado Primário: Setor Público Não Financeiro (C + D) -158.710 -1,51 -702.950 -9,44 Anexo IV – Tabela 3"),
        "central government": dict(o=-124.1, op=None, f=-124.1, fp=-1.58, d=0.0, u=-745.266, up=-10.01, n=0, laws="", q="A - Resultado Primário: Governo Central (I - II + III) 1 -124.100 -1,58 -745.266 -10,01 I."),
    },
    2021: {
        "consolidated public sector": dict(o=-250.888, op=-3.74, f=-250.888, fp=-3.74, d=84.5, u=64.727, up=0.75, n=0, laws="", q="E - Resultado Primário: Setor Público Não Financeiro (C + D) -250.888 -3,74 64.727 0,75 Anexo IV – Tabela 3"),
        "central government": dict(o=-247.118, op=-3.16, f=-247.118, fp=-3.16, d=84.5, u=-35.872, up=-0.41, n=0, laws="", q="A - Resultado Primário: Governo Central (I - II + III) -247.118 -3,16 - 35.872 - 0,41 I."),
    },
    2022: {
        "consolidated public sector": dict(o=-177.491, op=-2.00, f=-177.491, fp=-2.00, d=40.5, u=125.994, up=1.27, n=0, laws="", q="E - Resultado Primário: Setor Público Não Financeiro (C + D) -177.491 -2,00 125.994 1,27 Anexo IV – Tabela 3"),
        "central government": dict(o=-170.474, op=-1.92, f=-170.474, fp=-1.92, d=40.5, u=54.947, up=0.55, n=0, laws="", q="A - Resultado Primário: Governo Central (I - II + III) -170.474 -1,92 54.947 0,55 I."),
    },
    2023: {
        "consolidated public sector": dict(o=-69.009, op=-0.66, f=-69.009, fp=-0.66, d=241.3, u=-249.124, up=-2.29, n=0, laws="", q="E - Resultado Primário: Setor Público Não Financeiro (C + D) -69.009 -0,66 -249.124 -2,29 Anexo IV – Tabela 3"),
        "central government": dict(o=-65.906, op=-0.63, f=-65.906, fp=-0.63, d=241.3, u=-264.533, up=-2.44, n=0, laws="", q="A - Resultado Primário: Governo Central (I - II + III) -65.906 -0,63 -264.533 -2,44 I."),
    },
    2024: {
        "consolidated public sector": dict(o=-13.312, op=-0.12, f=-13.312, fp=-0.12, d=36.6, u=-47.090, up=-0.40, n=0, laws="", q="E - Resultado Primário: Setor Público Não Financeiro (C + D) -13.312 -0,12 -47.090 -0,40 Anexo IV – Tabela 3"),
        "central government": dict(o=0.0, op=0.0, f=0.0, fp=0.0, d=36.6, u=-45.364, up=-0.38, n=0, laws="", q="A - Resultado Primário: Governo Central (I - II + III) 0 0 -45.364 -0,38 I."),
    },
    2025: {
        "consolidated public sector": dict(o=-5.215, op=None, f=-5.215, fp=None, d=48.6, u=-54.761, up=-0.43, n=0, laws="", q="E - Resultado Primário: Setor Público Não Financeiro (C + D)\\2 -36.281,8 -0,29 -54.761 -0,43 Anexo IV – Tabela 3"),
        "central government": dict(o=0.0, op=0.0, f=0.0, fp=0.0, d=48.6, u=-58.687, up=-0.46, n=0, laws="", q="A - Resultado Primário: Governo Central (I - II + III)\\1 -29.067 -0,23 -58.687 -0,46 I."),
    },
}


def annual_gdp() -> dict[int, float]:
    records = json.loads(GDP_FILE.read_text(encoding="utf-8-sig"))
    totals: defaultdict[int, float] = defaultdict(float)
    counts: defaultdict[int, int] = defaultdict(int)
    for item in records[1:]:
        if item.get("D4N") != "PIB a preços de mercado" or item.get("D2N") != "Valores a preços correntes":
            continue
        year = int(item["D3C"][:4])
        totals[year] += float(item["V"]) / 1_000.0  # R$ million -> billion
        counts[year] += 1
    bad = {year: count for year, count in counts.items() if count != 4}
    if bad:
        raise ValueError(f"GDP years without exactly four quarters: {bad}")
    return dict(totals)


def _round(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(value, digits)


def build_rows() -> list[dict[str, object]]:
    gdps = annual_gdp()
    texts = {year: extract_text(RAW / name) for year, name in FILES.items()}
    rows: list[dict[str, object]] = []
    for year in sorted(MANUAL):
        for concept in ("consolidated public sector", "central government"):
            item = MANUAL[year][concept]
            quote = str(item["q"])
            if len(quote) > 400:
                raise ValueError(f"Quote exceeds 400 characters: {year} {concept}")
            if quote not in texts[year]:
                raise ValueError(f"Quote not found in extracted text: {year} {concept}: {quote!r}")
            op = item["op"]
            fp = item["fp"]
            up = item["up"]
            derived: list[str] = []
            if item["o"] is not None and op is None:
                op = float(item["o"]) / gdps[year] * 100
                derived.append("original %")
            if item["f"] is not None and fp is None:
                fp = float(item["f"]) / gdps[year] * 100
                derived.append("final %")
            if item["u"] is not None and up is None:
                up = float(item["u"]) / gdps[year] * 100
                derived.append("outturn %")
            row = {
                "evaluated_year": year,
                "concept": concept,
                "original_target_brl_bn": item["o"],
                "original_target_pct_gdp": _round(op),
                "final_target_brl_bn": item["f"],
                "final_target_pct_gdp": _round(fp),
                "n_revisions": item["n"],
                "revision_laws": item["laws"],
                "deductions_used_brl_bn": item["d"],
                "outturn_brl_bn": item["u"],
                "outturn_pct_gdp": _round(up),
                "miss_vs_original_pp_gdp": _round(None if op is None or up is None else float(up) - float(op)),
                "miss_vs_final_pp_gdp": _round(None if fp is None or up is None else float(up) - float(fp)),
                "government": government_for_year(year),
                "special_event": event_for_year(year),
                "source_file": FILES[year],
                "source_quote": quote,
                "extraction_method": "manual",
                "_derived": ", ".join(derived),
            }
            rows.append(row)
    return rows


def bcb_values() -> dict[int, float]:
    with BCB_FILE.open(encoding="utf-8-sig", newline="") as handle:
        return {
            int(row["year"]): -float(row["value"])
            for row in csv.DictReader(handle)
            if row["indicator"] == "primary_result_pct_gdp"
        }


def cross_check(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    bcb = bcb_values()
    checks = []
    for row in rows:
        if row["concept"] != "consolidated public sector" or row["outturn_pct_gdp"] is None:
            continue
        year = int(row["evaluated_year"])
        if year not in bcb:
            continue
        annex = float(row["outturn_pct_gdp"])
        diff = annex - bcb[year]
        if year == 2008:
            note = "Annex includes the R$14.2bn FFIE/Fundo Soberano capitalisation; BCB SGS 5793 uses the current below-the-line series."
        elif abs(diff) > 0.2:
            note = "Flag: difference exceeds 0.2 pp; likely historical-GDP vintage and/or annex-versus-current-series methodology."
        elif year == 2020:
            note = "Annex percentage uses its contemporary GDP estimate; SGS is the current vintage."
        else:
            note = "Within 0.2 pp; small differences reflect rounding and GDP vintages."
        checks.append({"year": year, "annex": annex, "bcb": bcb[year], "difference": round(diff, 4), "note": note})
    return checks


def summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    result = []
    for concept in ("consolidated public sector", "central government"):
        subset = [r for r in rows if r["concept"] == concept and r["miss_vs_original_pp_gdp"] is not None and r["miss_vs_final_pp_gdp"] is not None]
        groups = [(name, [r for r in subset if r["government"] == name]) for name in dict.fromkeys(r["government"] for r in subset)]
        groups.append(("Pooled", subset))
        for name, group in groups:
            if not group:
                continue
            original = [float(r["miss_vs_original_pp_gdp"]) for r in group]
            final = [float(r["miss_vs_final_pp_gdp"]) for r in group]
            result.append({
                "concept": concept, "government": name, "n": len(group),
                "mean_original": statistics.fmean(original), "median_original": statistics.median(original),
                "mean_final": statistics.fmean(final), "median_final": statistics.median(final),
            })
    return result


def fmt(value: object, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def write_csv(rows: list[dict[str, object]]) -> None:
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CSV_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_docs(rows: list[dict[str, object]], checks: list[dict[str, object]], stats: list[dict[str, object]]) -> None:
    lines = [
        "# F1 fiscal delivery: LDO targets versus outturns",
        "",
        "## Method and conventions",
        "",
        "The builder extracts whitespace-normalised text from the archived official LDO/PLDO annexes with `pypdf`; the 2019 DOCX is read directly from `word/document.xml`. The fiscal figures are hand-transcribed because layouts and concepts vary, and every stored quote is checked as an exact substring of the extracted source text. Blank cells mean that the annex does not report the requested concept—not zero. Government Federal (central government plus federal state-owned enterprises) is not silently relabelled as central government.",
        "",
        "**Sign convention:** surplus is positive and deficit is negative for targets and outturns. A miss is `outturn − target`, in percentage points of GDP; a negative miss therefore means a result below the target. Original/final targets are kept before permitted deductions, which are reported separately. The 2024–25 zero central target is likewise kept separate from its tolerance band and exclusions.",
        "",
        "Percentages marked † were not printed by the annex and are derived from its R$ amount using annual nominal GDP: the sum of the four quarterly values in offline SIDRA table 1846. Published annex percentages are retained even when a later GDP vintage differs. The annexes are the source of the main series; BCB SGS 5793 is only a cross-check.",
        "",
        "## Per-year results",
        "",
        "R$ values are billions; GDP values and misses are percentage points.",
        "",
        "| Year | Concept | Original R$ / % GDP | Final R$ / % GDP | Deductions R$ | Outturn R$ / % GDP | Miss original | Miss final | Government |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        derived = set(str(row["_derived"]).split(", "))
        def cell(amount_key: str, pct_key: str, derived_name: str) -> str:
            mark = "†" if derived_name in derived else ""
            return f"{fmt(row[amount_key])} / {fmt(row[pct_key])}{mark}"
        lines.append(
            f"| {row['evaluated_year']} | {row['concept']} | {cell('original_target_brl_bn', 'original_target_pct_gdp', 'original %')} | "
            f"{cell('final_target_brl_bn', 'final_target_pct_gdp', 'final %')} | {fmt(row['deductions_used_brl_bn'])} | "
            f"{cell('outturn_brl_bn', 'outturn_pct_gdp', 'outturn %')} | {fmt(row['miss_vs_original_pp_gdp'])} | "
            f"{fmt(row['miss_vs_final_pp_gdp'])} | {row['government']} |"
        )
    lines += [
        "",
        "Missing evaluated years (no archived annex): **2001, 2003–2007, 2009, 2013**. The archived 1999, 2000, 2002, 2012 and 2014 annexes also leave some consolidated cells unavailable under the requested definition.",
        "",
        "Special events are retained: 1999 devaluation; 2008 global crisis; and 2020 pandemic, when the state of calamity suspended the requirement to attain fiscal targets.",
        "",
        "## Summaries",
        "",
        "Only rows with both an outturn and the relevant target enter each statistic. Pandemic year 2020 remains included. Numbers are pp of GDP.",
        "",
        "| Concept | Government period | n | Mean miss vs original | Median | Mean miss vs final | Median |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in stats:
        lines.append(f"| {item['concept']} | {item['government']} | {item['n']} | {item['mean_original']:.2f} | {item['median_original']:.2f} | {item['mean_final']:.2f} | {item['median_final']:.2f} |")
    lines += [
        "",
        "## BCB consolidated-sector cross-check",
        "",
        "BCB SGS 5793 is stored with negative values for surpluses, so it is sign-flipped before comparison. Difference is `annex − sign-flipped BCB`, in pp of GDP.",
        "",
        "| Year | Annex | BCB (sign-flipped) | Difference | Note |",
        "|---:|---:|---:|---:|---|",
    ]
    for check in checks:
        lines.append(f"| {check['year']} | {check['annex']:.2f} | {check['bcb']:.2f} | {check['difference']:+.2f} | {check['note']} |")
    lines += [
        "",
        "## Neutrality and attribution",
        "",
        "The same statistics and inclusion rules are applied to every government period; this document uses no ranking language. Calendar-year attribution is descriptive, not causal: budgets and LDOs are often prepared in the prior year, economic shocks cross administrations, and 2016 is explicitly labelled a transition year (Dilma until 12 May; Temer thereafter). Bolsonaro's party label notes election by PSL and PL affiliation from 2021. Missing annex years are not filled or interpolated, so government-period sample sizes differ.",
        "",
        "The proposed pooled empirical distribution is isolated in `config/f1_proposed.yaml`; it is not a model parameter until lead-developer review.",
        "",
    ]
    DOC_FILE.parent.mkdir(parents=True, exist_ok=True)
    DOC_FILE.write_text("\n".join(lines), encoding="utf-8")


def write_proposal(rows: list[dict[str, object]]) -> None:
    consolidated = [r for r in rows if r["concept"] == "consolidated public sector" and r["miss_vs_original_pp_gdp"] is not None and r["miss_vs_final_pp_gdp"] is not None]
    original = sorted(float(r["miss_vs_original_pp_gdp"]) for r in consolidated)
    final = sorted(float(r["miss_vs_final_pp_gdp"]) for r in consolidated)
    def nearest(values: list[float], p: float) -> float:
        return values[round((len(values) - 1) * p)]
    text = f"""# Proposed only; do not consume as a model parameter before review.
fiscal_delivery:
  status: proposed
  concept: consolidated_public_sector
  sign_convention: surplus_positive_deficit_negative
  miss_definition: outturn_pct_gdp_minus_target_pct_gdp
  includes_pandemic_2020: true
  n: {len(consolidated)}
  miss_vs_original_pp_gdp:
    p10: {nearest(original, 0.10):.4f}
    p50: {statistics.median(original):.4f}
    p90: {nearest(original, 0.90):.4f}
  miss_vs_final_pp_gdp:
    p10: {nearest(final, 0.10):.4f}
    p50: {statistics.median(final):.4f}
    p90: {nearest(final, 0.90):.4f}
  source: data/brazil/fiscal_delivery.csv
  note: Empirical archived-year distribution; missing years are not filled or interpolated.
"""
    CONFIG_FILE.write_text(text, encoding="utf-8")


def main() -> None:
    rows = build_rows()
    checks = cross_check(rows)
    stats = summaries(rows)
    write_csv(rows)
    write_docs(rows, checks, stats)
    write_proposal(rows)
    print(f"Wrote {len(rows)} rows to {CSV_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
