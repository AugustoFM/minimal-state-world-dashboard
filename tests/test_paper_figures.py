from __future__ import annotations

from pathlib import Path

import pytest

from src import paper_figures


def test_load_horizon_percentiles_returns_one_row_per_scenario_horizon() -> None:
    data = paper_figures.load_horizon_percentiles("debt_gdp_vs_s0_pp")
    assert len(data) == len(paper_figures.SCENARIOS) * len(paper_figures.HORIZONS)
    assert set(data["scenario"]) == set(paper_figures.SCENARIOS)
    assert set(data["horizon"]) == set(paper_figures.HORIZONS)


def test_loaded_debt_percentiles_match_the_headline_table() -> None:
    # Spot-check against tab:headline's own published 10-year cells.
    data = paper_figures.load_horizon_percentiles("debt_gdp_vs_s0_pp")
    row = data.loc[data["scenario"].eq("R_amb") & data["horizon"].eq(10)].iloc[0]
    assert row["p50"] == pytest.approx(-23.3, abs=0.1)
    assert row["p10"] == pytest.approx(-24.7, abs=0.1)
    assert row["p90"] == pytest.approx(-21.4, abs=0.1)


def test_unknown_indicator_raises_rather_than_silently_returning_partial_rows() -> None:
    with pytest.raises(ValueError):
        paper_figures.load_horizon_percentiles("not_a_real_indicator")


def test_build_scenario_grid_and_backtest_figure_write_nonempty_pdfs(tmp_path: Path) -> None:
    debt_path = tmp_path / "debt_fan.pdf"
    gini_path = tmp_path / "gini_fan.pdf"
    backtest_path = tmp_path / "backtest_fit.pdf"
    paper_figures.build_scenario_grid("debt_gdp_vs_s0_pp", "Debt/GDP vs. S0 (pp)", debt_path)
    paper_figures.build_scenario_grid("gini_change_vs_s0_points", "Gini vs. S0 (points)", gini_path)
    paper_figures.build_backtest_figure(backtest_path)
    for path in (debt_path, gini_path, backtest_path):
        assert path.exists()
        assert path.stat().st_size > 1000


def test_scenario_labels_have_no_latex_escapes() -> None:
    # Matplotlib's default (non-usetex) text renderer shows a literal backslash for "\_" rather
    # than interpreting it as LaTeX, so these labels must use plain underscores.
    for label in paper_figures.SCENARIO_LABELS.values():
        assert "\\" not in label
