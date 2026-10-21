"""Synthetic tests for the fixed I1 interest-rate protocol."""

import numpy as np
import pandas as pd

from src.rates import (
    align_focus_horizon,
    estimate_pass_through,
    fisher_real_rate,
    ols_newey_west,
    select_focus_month_end,
)


def test_fisher_real_rate():
    assert np.isclose(fisher_real_rate(10.0, 5.0), 100 * (1.10 / 1.05 - 1))
    values = fisher_real_rate(np.array([10.0, 0.0]), np.array([5.0, 0.0]))
    assert np.allclose(values, [100 * (1.10 / 1.05 - 1), 0.0])


def test_focus_month_end_picks_last_survey_for_each_reference_year():
    raw = pd.DataFrame({
        "Data": ["2024-01-05", "2024-01-26", "2024-01-19", "2024-02-02"],
        "DataReferencia": [2025, 2025, 2026, 2025],
        "Mediana": [8.0, 8.5, 7.0, 8.2],
    })
    result = select_focus_month_end(raw)
    january_2025 = result[(result.month == pd.Timestamp("2024-01-01")) &
                          (result.reference_year == 2025)].iloc[0]
    assert january_2025["survey_date"] == pd.Timestamp("2024-01-26")
    assert january_2025["median"] == 8.5
    assert len(result) == 3


def test_horizon_alignment_uses_calendar_year_not_row_shift():
    frame = pd.DataFrame({
        "month": pd.to_datetime(["2023-12-01", "2024-01-01", "2024-01-01"]),
        "reference_year": [2026, 2026, 2027],
        "survey_date": pd.to_datetime(["2023-12-29", "2024-01-31", "2024-01-31"]),
        "median": [9.0, 99.0, 8.0],
    })
    result = align_focus_horizon(frame, 3)
    assert result.to_dict() == {pd.Timestamp("2023-12-01"): 9.0,
                                pd.Timestamp("2024-01-01"): 8.0}


def test_newey_west_recovers_simulated_slope_and_positive_se():
    rng = np.random.default_rng(20261021)
    n = 2000
    x = rng.normal(size=n)
    innovations = rng.normal(scale=0.25, size=n)
    error = np.empty(n)
    error[0] = innovations[0]
    for index in range(1, n):
        error[index] = 0.65 * error[index - 1] + innovations[index]
    y = 1.2 + 2.5 * x + error
    result = ols_newey_west(y, np.column_stack([np.ones(n), x]), lag=6)
    assert np.allclose(result["beta"], [1.2, 2.5], atol=0.04)
    assert np.all(np.asarray(result["se"]) > 0)
    assert np.allclose(result["covariance"], np.asarray(result["covariance"]).T)


def test_pass_through_recovers_current_lagged_and_long_run():
    rng = np.random.default_rng(7)
    years = np.arange(1980, 2026)
    selic = rng.normal(10.0, 2.0, len(years))
    implicit = np.full(len(years), np.nan)
    implicit[1:] = 2.0 + 0.3 * selic[1:] + 0.5 * selic[:-1]
    frame = pd.DataFrame({"selic_annual_avg_pct": selic,
                          "implicit_nominal_rate_pct": implicit}, index=years)
    result = estimate_pass_through(frame)
    assert np.isclose(result["current"], 0.3, atol=1e-10)
    assert np.isclose(result["lagged"], 0.5, atol=1e-10)
    assert np.isclose(result["long_run"], 0.8, atol=1e-10)
    assert np.isclose(result["year1_share"], 0.375, atol=1e-10)
