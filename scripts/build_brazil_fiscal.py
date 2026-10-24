"""Build annual Brazil general-government expenditure from Tesouro workbook."""
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/brazil/demonstrativos-governo-geral.xlsx"
OUT = ROOT / "data/brazil/fiscal.csv"


def build() -> pd.DataFrame:
    amount = pd.read_excel(RAW, sheet_name="1.2", header=None)
    share = pd.read_excel(RAW, sheet_name="1.2.a", header=None)
    # Both sheets have quarter labels in row 3 and the consolidated general-
    # government series in row 17. Values are quarterly R$ millions and share
    # fractions respectively. Primary expenditure excludes interest (row 22).
    labels = amount.iloc[3, 2:].tolist()
    data = []
    for col, label in enumerate(labels, start=2):
        if not isinstance(label, str) or "-" not in label:
            continue
        year = int(label[:4])
        total = pd.to_numeric(amount.iloc[17, col], errors="coerce")
        interest = pd.to_numeric(amount.iloc[22, col], errors="coerce")
        total_pct = pd.to_numeric(share.iloc[17, col], errors="coerce") * 100
        interest_pct = pd.to_numeric(share.iloc[22, col], errors="coerce") * 100
        data.append({
            "year": year,
            "quarter": {"I": 1, "II": 2, "III": 3, "IV": 4}[label.split("-")[-1]],
            "total_spending_r_millions": total,
            "primary_spending_r_millions": total - interest,
            "total_spending_pct_gdp": total_pct,
            "primary_spending_pct_gdp": total_pct - interest_pct,
            "source": "Tesouro Nacional, Estatísticas Fiscais do Governo Geral, table 1.2",
            "definition": "General government consolidated expenditure (GFSM 2014); primary = total expenditure less interest",
            "mandatory_spending_r_millions": pd.NA,
            "discretionary_spending_r_millions": pd.NA,
        })
    quarterly = pd.DataFrame(data)
    annual = quarterly.groupby("year", as_index=False).agg(
        quarters_observed=("quarter", "count"),
        total_spending_r_millions=("total_spending_r_millions", "sum"),
        primary_spending_r_millions=("primary_spending_r_millions", "sum"),
        # Published quarterly percentages are rolling 12-month ratios, so the
        # annual observation is the Q4 value rather than the sum of quarters.
        total_spending_pct_gdp=("total_spending_pct_gdp", "last"),
        primary_spending_pct_gdp=("primary_spending_pct_gdp", "last"),
    )
    annual["source"] = "Tesouro Nacional, Estatísticas Fiscais do Governo Geral, tables 1.2 and 1.2.a"
    annual["definition"] = "GFSM 2014 general-government consolidated expenditure; amounts sum observed quarter flows; percent-of-GDP is Q4 rolling-12-month ratio (last observed quarter for incomplete years); primary excludes interest"
    annual["mandatory_spending_r_millions"] = pd.NA
    annual["discretionary_spending_r_millions"] = pd.NA
    OUT.parent.mkdir(parents=True, exist_ok=True)
    annual.to_csv(OUT, index=False)
    return annual


if __name__ == "__main__":
    result = build()
    print(f"Wrote {len(result)} annual observations to {OUT}")
