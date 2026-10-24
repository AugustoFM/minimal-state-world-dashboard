"""Tidy the Receita Federal 'Distribuição da Renda por Centis' workbook (A3).

Source: centis-br-ac2024.xlsx (IRPF declarations, calendar year 2024), one
sheet per ranking concept (Tables I-XI; see metadados-centis-ac2024.pdf).
Each sheet has 120 rows that OVERLAP: rows 1-100 are centiles of declarants
(row 100 = whole top 1%), rows 101-110 split row 100 into tenths, and rows
111-120 split row 110 (top 0.1%) into tenths. The output gives every row its
population bounds (p_low, p_high, in % of declarants) and a `partition` flag
marking a non-overlapping set (rows 1-99, 101-109, 111-120) that sums to the
total. Values are kept exactly as published (R$, calendar year 2024). Output is
wide: one row per table x centile row, one column per published field (fields
absent from a table are empty).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/brazil/tax/centis-br-ac2024.xlsx"
OUTPUT = ROOT / "data/brazil/micro/tax_centiles_2024.csv"
SHEET_TABLE = {
    "BRI": "I", "BRII": "II", "BRIII": "III", "BRIV": "IV", "BRV": "V", "BRVI": "VI",
    "BRVII": "VII", "BRVIII": "VIII", "BRIX": "IX", "BRX": "X", "BRXI": "XI",
}
HEADER_ROWS = (4, 5)   # parent and child header labels
FIRST_DATA_ROW = 7
LABEL_COLUMN = 1


def row_bounds(row: int) -> tuple[float, float, bool]:
    """Population bounds (% of declarants) and partition membership of a row."""
    if 1 <= row <= 100:
        return row - 1.0, float(row), row != 100
    if 101 <= row <= 110:
        return 99 + (row - 101) / 10, 99 + (row - 100) / 10, row != 110
    if 111 <= row <= 120:
        return 99.9 + (row - 111) / 100, 99.9 + (row - 110) / 100, True
    raise ValueError(f"Unexpected row number {row}")


def column_names(sheet: pd.DataFrame) -> dict[int, str]:
    names: dict[int, str] = {}
    parent = ""
    for col in range(LABEL_COLUMN + 1, sheet.shape[1]):
        top = sheet.iat[HEADER_ROWS[0], col]
        child = sheet.iat[HEADER_ROWS[1], col]
        if pd.notna(top):
            parent = " ".join(str(top).split())
        label = " ".join(str(child).split()) if pd.notna(child) else parent
        if label and label != "nan":
            names[col] = f"{parent} | {label}" if pd.notna(child) and parent and parent != label else label
    return names


def tidy_sheet(sheet: pd.DataFrame, table: str) -> pd.DataFrame:
    concept = " ".join(str(sheet.iat[3, LABEL_COLUMN]).split())
    names = column_names(sheet)
    body = sheet.iloc[FIRST_DATA_ROW:]
    body = body.loc[pd.to_numeric(body[LABEL_COLUMN], errors="coerce").notna()]
    if len(body) != 120:
        raise ValueError(f"Table {table}: expected 120 rows, found {len(body)}")
    records = []
    for _, line in body.iterrows():
        row = int(line[LABEL_COLUMN])
        p_low, p_high, partition = row_bounds(row)
        for col, field in names.items():
            value = pd.to_numeric(line[col], errors="coerce")
            if pd.isna(value):
                continue
            records.append({
                "table": table, "ranking_concept": concept, "row": row,
                "p_low": p_low, "p_high": p_high, "partition": partition,
                "field": field, "value": float(value),
            })
    return pd.DataFrame.from_records(records)


def build() -> pd.DataFrame:
    sheets = pd.read_excel(RAW, sheet_name=None, header=None)
    missing = set(SHEET_TABLE) - set(sheets)
    if missing:
        raise ValueError(f"Workbook lacks sheets {sorted(missing)}")
    tidy = pd.concat(
        [tidy_sheet(sheets[name], table) for name, table in SHEET_TABLE.items()],
        ignore_index=True,
    )
    keys = ["table", "ranking_concept", "row", "p_low", "p_high", "partition"]
    fields = list(dict.fromkeys(tidy["field"]))
    wide = tidy.pivot_table(index=keys, columns="field", values="value", aggfunc="first", sort=False)
    wide = wide.reindex(columns=fields).reset_index()
    wide.insert(0, "calendar_year", 2024)
    return wide


def main() -> int:
    tidy = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_csv(OUTPUT, index=False, float_format="%.2f")
    print(f"Wrote {len(tidy)} rows to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
