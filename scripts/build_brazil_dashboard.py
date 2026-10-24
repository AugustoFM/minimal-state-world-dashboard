"""Write dashboard/brazil_data.js from the committed Monte Carlo and D4 outputs.

Run from the repo root, then open dashboard/brazil.html. Reuses the indicator
labels, decimal precision and D2-gate parsing already reviewed in
scripts/report_brazil_results.py rather than redefining them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.report_brazil_results import (  # noqa: E402
    DECIMALS,
    HEADLINE_INDICATORS,
    LABELS,
    parse_backtest,
    validate_summary,
)

SUMMARY_PATH = ROOT / "outputs/runs/summary_percentiles.csv"
METADATA_PATH = ROOT / "outputs/runs/run_metadata.json"
BACKTEST_PATH = ROOT / "outputs/backtest.md"
SCENARIOS_PATH = ROOT / "config/scenarios.yaml"
D4_PATH = ROOT / "data/brazil/debt_level_diagnostics.csv"
OUTPUT_PATH = ROOT / "dashboard/brazil_data.js"

# A deliberately small subset of HEADLINE_INDICATORS for the dashboard's charted
# metrics (the others remain in outputs/results_brazil.md); keeps the page
# legible rather than exposing all 24 at once.
CHART_INDICATORS = (
    "gdp_level_vs_s0_pct",
    "gdp_level_vs_s0_pct_with_feedback",
    "debt_gdp_vs_s0_pp",
    "debt_gdp_with_feedback_vs_s0_pp",
    "unemployment_change_pp",
    "gini_change_vs_s0_points",
    "poverty_218_change_vs_s0_pp",
    "poverty_759_change_vs_s0_pp",
    "infant_mortality_difference_vs_s0",
    "life_expectancy_difference_vs_s0_years",
)
# S1 is a reference (cost of offsetting ageing without any size change), not part
# of the R/E grid the dashboard compares; keep it out of the default chart list
# but still selectable.
SCENARIO_ORDER = ["R_max", "R_amb", "R_mod", "S1", "E_mod", "E_amb", "E_mod_tax", "E_amb_tax"]


def _round(value: object) -> object:
    if isinstance(value, float):
        if pd.isna(value):
            return None
        return round(value, 6)
    return value


def build() -> dict:
    import yaml

    summary = pd.read_csv(SUMMARY_PATH)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    backtest_text = BACKTEST_PATH.read_text(encoding="utf-8")
    scenarios_config = yaml.safe_load(SCENARIOS_PATH.read_text(encoding="utf-8"))
    validate_summary(summary, metadata)
    diagnostics = parse_backtest(backtest_text)

    chart_rows = summary.loc[summary["indicator"].isin(CHART_INDICATORS)].copy()
    results = [
        {
            "variant": row.variant, "persistence": row.persistence, "scenario": row.scenario,
            "horizon": int(row.horizon), "year": int(row.year), "indicator": row.indicator,
            "p10": _round(row.p10), "p50": _round(row.p50), "p90": _round(row.p90),
            "status": row.status,
        }
        for row in chart_rows.itertuples(index=False)
    ]

    scenarios = {}
    for code, definition in scenarios_config["scenarios"].items():
        if code not in set(summary["scenario"]):
            continue
        scenarios[code] = {
            "description": definition.get("description", definition.get("name", "")),
            "by_year": definition.get("by_year"),
            "direction": definition.get("direction"),
            "financing": definition.get("financing"),
        }

    indicators = {
        name: {"label": LABELS.get(name, name), "decimals": DECIMALS.get(name, 2)}
        for name in CHART_INDICATORS
    }

    d4 = None
    if D4_PATH.exists():
        draws = pd.read_csv(D4_PATH)
        sampled = draws.loc[draws["draw"] > 0]
        value_columns = [
            "debt_gdp_s0", "debt_gdp_s0_sfa_brazil", "debt_gdp_s0_sfa_emerging",
            "debt_gdp_frf_emerging", "debt_gdp_frf_brazil_robustness", "debt_gdp_premium_nonlinear",
            "stabilising_primary_balance_pp", "fiscal_gap_pp", "primary_balance_gdp_actual",
        ]
        by_horizon = {}
        for horizon, group in sampled.groupby("horizon"):
            entry = {}
            for column in value_columns:
                entry[column] = {
                    "p10": _round(float(group[column].quantile(0.10))),
                    "p50": _round(float(group[column].quantile(0.50))),
                    "p90": _round(float(group[column].quantile(0.90))),
                }
            for threshold in (90.0, 100.0, 120.0):
                entry[f"p_breach_{int(threshold)}_no_sfa"] = _round(float((group["debt_gdp_s0"] > threshold).mean()))
                entry[f"p_breach_{int(threshold)}_sfa_brazil"] = _round(float((group["debt_gdp_s0_sfa_brazil"] > threshold).mean()))
                entry[f"p_breach_{int(threshold)}_sfa_emerging"] = _round(float((group["debt_gdp_s0_sfa_emerging"] > threshold).mean()))
            by_horizon[int(horizon)] = entry
        d4 = {"n_draws": int(draws["draw"].max()) + 1, "by_horizon": by_horizon}

    return {
        "meta": {
            "seed": metadata.get("seed"), "n_draws": metadata.get("n_draws"),
            "created_utc": metadata.get("created_utc"), "inputs_commit": metadata.get("inputs_commit"),
        },
        "d2": diagnostics,
        "scenario_order": [code for code in SCENARIO_ORDER if code in scenarios],
        "scenarios": scenarios,
        "indicators": indicators,
        "results": results,
        "d4": d4,
    }


def main() -> None:
    data = build()
    OUTPUT_PATH.write_text("window.BRAZIL_DATA=" + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(data['results'])} result rows, {len(data['scenarios'])} scenarios -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
