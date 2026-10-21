from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts import report_brazil_results as report


ROOT = Path(__file__).resolve().parents[1]


def test_report_builds_offline_and_has_correct_gate() -> None:
    built = report.build_report()
    assert "Internal review - not for publication: D2 gate FAIL" in built
    assert built == (ROOT / "outputs/results_brazil.md").read_text(encoding="utf-8")


def test_formatted_cell_matches_csv_rounding() -> None:
    summary = pd.read_csv(ROOT / "outputs/runs/summary_percentiles.csv")
    row = summary[
        summary["variant"].eq("default")
        & summary["persistence"].eq("persistent")
        & summary["scenario"].eq("R_mod")
        & summary["horizon"].eq(20)
        & summary["indicator"].eq("gdp_level_vs_s0_pct")
    ].iloc[0]
    expected = f"{row.p50:.2f} [{row.p10:.2f}, {row.p90:.2f}]"
    assert expected in report.build_report()


def test_s0_excluded_from_difference_tables_and_all_scenarios_defined() -> None:
    built = report.build_report()
    headline = built.split("## Headline results", 1)[1].split("## Debt/GDP levels", 1)[0]
    assert "| S0 |" not in headline

    summary = pd.read_csv(ROOT / "outputs/runs/summary_percentiles.csv")
    scenario_section = built.split("## Scenarios", 1)[1].split("## Headline results", 1)[0]
    for scenario in summary["scenario"].unique():
        assert f"| {scenario} |" in scenario_section


def test_build_is_deterministic() -> None:
    assert report.build_report() == report.build_report()
