"""Synthetic identity and estimator tests for :mod:`src.debt_panel`."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.debt_panel import (
    brazil_primary_balance_comparison,
    decompose_panel,
    decomposition_row,
    detect_episodes,
    estimate_frf,
    find_local_peaks,
    restricted_distribution,
    stabilisation_comparison,
)


def test_decomposition_closes_observed_debt_change() -> None:
    result = decomposition_row(
        debt=72.0,
        lagged_debt=65.0,
        primary_balance=-1.5,
        interest=4.0,
        real_growth=3.0,
        inflation=4.0,
    )
    contributions = sum(result[name] for name in (
        "primary_deficit_contribution",
        "interest_contribution",
        "real_growth_contribution",
        "inflation_contribution",
        "sfa",
    ))
    assert np.isclose(contributions, result["delta_d"])


def test_r_minus_g_formula_and_low_debt_guard() -> None:
    result = decomposition_row(52.0, 50.0, 0.0, 3.0, 2.0, 4.0)
    gamma = 1.02 * 1.04 - 1.0
    nominal_rate = 3.0 * (1.0 + gamma) / 50.0
    expected = (nominal_rate - gamma) / (1.0 + gamma) * 100.0
    assert np.isclose(result["effective_nominal_rate_pct"], nominal_rate * 100.0)
    assert np.isclose(result["r_minus_g_pct"], expected)
    assert np.isnan(decomposition_row(5.0, 4.99, 0.0, 0.2, 2.0, 2.0)["r_minus_g_pct"])


def _episode_panel() -> pd.DataFrame:
    debt = [40, 42, 45, 50, 60, 70, 80, 75, 65, 55, 50, 48, 49, 50, 52, 55, 60, 70, 82, 90, 95]
    years = list(range(2000, 2000 + len(debt)))
    return pd.DataFrame({
        "iso3": "BRA", "group": "emerging", "year": years, "d": debt,
        "pb": 0.0, "ie": 2.0, "real_growth": 2.0, "deflator_inflation": 3.0,
    })


def test_peak_and_episode_detection() -> None:
    panel = _episode_panel()
    peaks = find_local_peaks(panel, radius=5)
    assert peaks[["peak_year", "peak_debt"]].to_records(index=False).tolist() == [(2006, 80.0)]
    decomposition = decompose_panel(panel)
    episodes = detect_episodes(panel, decomposition)
    reductions = episodes[episodes["episode_type"] == "reduction"]
    increases = episodes[episodes["episode_type"] == "increase"]
    assert ((reductions["start_year"] == 2006) & (reductions["end_debt"] <= 50)).any()
    assert (increases["debt_change"] >= 30).all()


def test_frf_recovers_known_rho() -> None:
    rng = np.random.default_rng(7301)
    rho, phi, beta = 0.045, 0.35, 0.4
    rows = []
    countries = [f"C{i:02d}" for i in range(30)]
    for country_number, iso in enumerate(countries):
        primary, fixed_effect = 0.0, (country_number - 15) / 20.0
        for year in range(1900, 2025):
            debt = 55.0 + rng.normal(0, 18)
            gap = rng.normal(0, 0.025)
            if year == 1900:
                primary = fixed_effect + rng.normal(0, 0.2)
            else:
                primary = fixed_effect + rho * previous_debt + beta * gap + phi * primary + rng.normal(0, 0.12)
            rows.append({"iso3": iso, "year": year, "d": debt, "pb": primary, "output_gap": gap})
            previous_debt = debt
    panel = pd.DataFrame(rows)
    model = estimate_frf(panel, countries)
    coefficients = dict(zip(model["names"], model["beta"]))
    assert abs(coefficients["debt_lag"] - rho) < 0.004
    assert abs(coefficients["pb_lag"] - phi) < 0.04


def test_restricted_distribution_excludes_high_inflation_and_respects_periods() -> None:
    decomposition = pd.DataFrame({
        "iso3": ["BRA", "BRA", "MEX", "USA"],
        "group": ["emerging", "emerging", "emerging", "advanced"],
        "year": [1999, 2000, 2010, 2010],
        "deflator_inflation": [5.0, 15.0, 4.0, 2.0],
        "r_minus_g_pct": [1.0, 99.0, 3.0, 2.0],
    })
    result = restricted_distribution(decomposition, "r_minus_g_pct")
    emerging_2000 = result[(result["sample"] == "emerging") & (result["period"] == "2000-2024")].iloc[0]
    brazil_full = result[(result["sample"] == "Brazil") & (result["period"] == "1975-2024")].iloc[0]
    assert emerging_2000["n"] == 1
    assert emerging_2000["mean"] == 3.0
    assert brazil_full["n"] == 1
    assert brazil_full["mean"] == 1.0


def test_brazil_primary_balance_sign_aligned_comparison() -> None:
    panel = pd.DataFrame({
        "iso3": ["BRA", "BRA", "MEX"], "year": [2001, 2002, 2002],
        "pb": [2.0, -1.0, 0.0],
    })
    official = pd.DataFrame({"year": [2001, 2002], "official_pb": [1.5, -0.5]})
    result = brazil_primary_balance_comparison(panel, official)
    assert result["fpp_minus_official_gap"].tolist() == [0.5, -0.5]


def test_stabilisation_comparison_uses_decimal_response_threshold() -> None:
    estimates = pd.DataFrame({
        "specification": ["primary", "primary"],
        "sample": ["emerging", "brazil"],
        "term": ["long_run_debt_response", "long_run_debt_response"],
        "estimate": [0.06, 0.01],
    })
    decomposition = pd.DataFrame({
        "iso3": ["BRA", "MEX"], "group": ["emerging", "emerging"],
        "year": [2010, 2010], "deflator_inflation": [5.0, 5.0],
        "r_minus_g_pct": [4.0, 2.0],
    })
    result = stabilisation_comparison(estimates, decomposition)
    s0 = result[result["benchmark"] == "S0 central 2045"].set_index("sample")
    assert np.isclose(s0.loc["emerging", "response_needed"], .049 / 1.005)
    assert s0.loc["emerging", "stabilises"] == "yes"
    assert s0.loc["brazil", "stabilises"] == "no"
