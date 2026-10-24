"""Validate the canonical PNAD Contínua extract against published IBGE aggregates.

Reads the git-ignored canonical export produced by load_brazil_microdata.py and
writes only weighted aggregates (no records) to data/brazil/micro/, so the
result can be versioned. Targets: IBGE SIDRA table 7435 (Gini of household
per-capita income) and the IBGE 2025 population projection (A2).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/processed/brazil/microdata/pnadc_2025_visita1_canonical.csv"
SIDRA_GINI = ROOT / "data/raw/brazil/micro_validation/ibge_sidra_7435_gini.json"
POPULATION = ROOT / "data/brazil/population.csv"
OUTPUT = ROOT / "data/brazil/micro/validation_pnadc_2025.csv"
GINI_VARIABLE = "10681"  # SIDRA 7435: Gini of household per-capita income
GINI_TOLERANCE = 0.005   # published coefficient of variation is ~0.6%, i.e. SE ~0.003
POPULATION_TOLERANCE = 0.01


def weighted_gini(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    cumulative_income = np.cumsum(values * weights)
    previous = cumulative_income - values * weights
    return float(
        1 - np.sum(weights * (cumulative_income + previous)) / (weights.sum() * cumulative_income[-1])
    )


def published_gini(year: int) -> float:
    rows = json.loads(SIDRA_GINI.read_text(encoding="utf-8"))[1:]
    match = [r for r in rows if r["D2C"] == GINI_VARIABLE and r["D3C"] == str(year)]
    if len(match) != 1:
        raise ValueError(f"SIDRA 7435 has no single Gini value for {year}")
    return float(match[0]["V"])


def projected_population(year: int) -> float:
    population = pd.read_csv(POPULATION)
    both = population.loc[population["sex"].eq("Ambos") & population["year"].eq(year)]
    return float(both["population"].sum())


def validate(data: pd.DataFrame) -> pd.DataFrame:
    year = int(data["year"].iloc[0])
    income = data.dropna(subset=["household_income_per_capita_brl"])
    gini = weighted_gini(
        income["household_income_per_capita_brl"].to_numpy(float),
        income["survey_weight"].to_numpy(float),
    )
    target_gini = published_gini(year)
    population = float(data["survey_weight"].sum())
    target_population = projected_population(year)
    rows = [
        {
            "check": "gini_household_income_per_capita",
            "computed": gini,
            "published": target_gini,
            "difference": gini - target_gini,
            "tolerance": GINI_TOLERANCE,
            "source": "IBGE SIDRA 7435, variable 10681",
        },
        {
            "check": "weighted_population_relative",
            "computed": population,
            "published": target_population,
            "difference": population / target_population - 1,
            "tolerance": POPULATION_TOLERANCE,
            "source": "IBGE projections 2024 revision (data/brazil/population.csv)",
        },
    ]
    for column in (
        "retirement_pension_income_brl", "bolsa_familia_income_brl", "bpc_income_brl",
        "unemployment_insurance_income_brl",
    ):
        rows.append({
            "check": f"annualised_total_{column}",
            "computed": float((data[column].fillna(0) * data["survey_weight"]).sum() * 12),
            "published": np.nan,
            "difference": np.nan,
            "tolerance": np.nan,
            "source": "context only: survey totals understate administrative totals",
        })
    result = pd.DataFrame(rows)
    result.insert(0, "year", year)
    result["passed"] = [
        abs(d) <= t if pd.notna(t) else pd.NA for d, t in zip(result["difference"], result["tolerance"])
    ]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=CANONICAL)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = validate(pd.read_csv(args.input, low_memory=False))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False, float_format="%.6f")
    print(result.to_string(index=False))
    failed = result["passed"].eq(False).sum()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
