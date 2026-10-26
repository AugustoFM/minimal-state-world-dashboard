from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from src import pcy1_fiscal_timing as pcy1


def test_load_series_negates_the_borrowing_requirement(tmp_path: Path) -> None:
    # backtest_observed.csv's primary_result_pct_gdp is a borrowing requirement
    # ("negative = surplus"); load_series must flip it into a conventional,
    # surplus-positive primary_balance_pct_gdp.
    csv_path = tmp_path / "observed.csv"
    csv_path.write_text(
        "year,indicator,value,label,series_code,source\n"
        "2019,gdp_growth_pct,1.221,,,\n"
        "2019,primary_result_pct_gdp,0.84,,,\n"
        "2020,gdp_growth_pct,-3.277,,,\n"
        "2020,primary_result_pct_gdp,9.24,,,\n",
        encoding="utf-8",
    )
    frame = pcy1.load_series(csv_path)
    assert frame.loc[2019, "primary_balance_pct_gdp"] == pytest.approx(-0.84)
    assert frame.loc[2020, "primary_balance_pct_gdp"] == pytest.approx(-9.24)
    assert "primary_result_pct_gdp" not in frame.columns


def test_compute_gap_and_impulse_matches_hand_computation() -> None:
    frame = pd.DataFrame(
        {"gdp_growth_pct": [2.0, 2.0, 2.0, 5.0, 2.0], "primary_balance_pct_gdp": [1.0, 1.0, 1.0, 1.0, -1.0]},
        index=[2000, 2001, 2002, 2003, 2004],
    )
    out = pcy1.compute_gap_and_impulse(frame, trend_window_years=3)
    # Trend at 2002 is the mean of 2000-2002 (2.0); at 2003 the mean of 2001-2003 (3.0).
    assert out.loc[2002, "trend_growth_pct"] == pytest.approx(2.0)
    assert out.loc[2003, "trend_growth_pct"] == pytest.approx(3.0)
    assert out.loc[2003, "output_gap_proxy_pp"] == pytest.approx(5.0 - 3.0)
    # Balance falls from 1.0 (2003) to -1.0 (2004): fiscal_impulse_pp = -(-1.0 - 1.0) = +2.0 (expansionary).
    assert out.loc[2004, "fiscal_impulse_pp"] == pytest.approx(2.0)
    # No trend for the first trend_window_years-1 rows.
    assert math.isnan(out.loc[2000, "trend_growth_pct"])
    assert math.isnan(out.loc[2001, "trend_growth_pct"])


@pytest.mark.parametrize(
    "gap,impulse,expected",
    [
        (1.0, 1.0, "procyclical_expansionary"),
        (-1.0, -1.0, "procyclical_contractionary"),
        (1.0, -1.0, "countercyclical"),
        (-1.0, 1.0, "countercyclical"),
        (0.0, 0.05, "broadly_neutral"),
        (0.0, -0.05, "broadly_neutral"),
        (float("nan"), 1.0, "not_classified"),
        (1.0, float("nan"), "not_classified"),
    ],
)
def test_classify_year(gap: float, impulse: float, expected: str) -> None:
    assert pcy1.classify_year(gap, impulse) == expected


def test_classify_year_respects_the_neutral_threshold() -> None:
    # Exactly at the threshold is still "inside" (strict <), so it classifies normally.
    assert pcy1.classify_year(1.0, 0.1) == "procyclical_expansionary"
    assert pcy1.classify_year(1.0, 0.099) == "broadly_neutral"


def test_render_report_runs_on_the_real_repository_data() -> None:
    frame = pcy1.classify(pcy1.compute_gap_and_impulse(pcy1.load_series()))
    report = pcy1.render_report(frame)
    assert "# PCY1: historical fiscal-timing (procyclicality) diagnostic" in report
    assert "2011" in report and "2014" in report
    # Every classified row's label appears somewhere in the per-year table.
    for label in frame["classification"].unique():
        assert label in report
