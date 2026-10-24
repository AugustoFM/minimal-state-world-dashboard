"""Reshape the official IBGE Brazil population projection to long CSV."""
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/brazil/ibge_projecoes_2024_tab1_idade_simples.xlsx"
OUT = ROOT / "data/brazil/population.csv"


def build() -> pd.DataFrame:
    raw = pd.read_excel(RAW, sheet_name=0, header=5)
    raw.columns = [str(c).split(".")[0] for c in raw.columns]
    year_cols = [c for c in raw.columns if c.isdigit() and 2000 <= int(c) <= 2070]
    brazil = raw.loc[raw["SIGLA"].eq("BR"), ["IDADE", "SEXO", "SIGLA", "LOCAL", *year_cols]].copy()
    result = brazil.melt(
        id_vars=["IDADE", "SEXO", "SIGLA", "LOCAL"],
        value_vars=year_cols,
        var_name="year",
        value_name="population",
    ).rename(columns={"IDADE": "age", "SEXO": "sex", "SIGLA": "iso3", "LOCAL": "location"})
    result["year"] = result["year"].astype(int)
    result["population"] = pd.to_numeric(result["population"], errors="coerce")
    result["source"] = "IBGE Population Projections, 2024 revision, table 1 (single age and sex)"
    result = result.dropna(subset=["population"]).sort_values(["year", "sex", "age"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT, index=False)
    return result


if __name__ == "__main__":
    result = build()
    print(f"Wrote {len(result)} observations ({result.year.min()}–{result.year.max()}) to {OUT}")
