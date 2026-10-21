from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import external_v2 as c7


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data() -> pd.DataFrame:
    return c7.load_prepare_data()


@pytest.fixture(scope="module")
def models(data) -> dict:
    return c7.estimate_channels("all", data)


def test_ols_reproduces_numpy_lstsq() -> None:
    x = np.column_stack([np.ones(6), np.arange(6.0), np.array([0.0, 1.0, 0.0, 1.0, 0.0, 1.0])])
    y = np.array([1.0, 2.1, 1.7, 3.4, 3.0, 4.8])
    expected = np.linalg.lstsq(x, y, rcond=None)[0]
    actual = c7.ols_newey_west(y, x, lag=1)
    np.testing.assert_allclose(actual["beta"], expected, rtol=1e-13, atol=1e-13)


def test_newey_west_matches_hand_computation() -> None:
    # Hand calculation for y=[1,2,1.5,3,2.5], X=[1,t], Bartlett lag 1:
    # beta=[1.2,.4], residuals=[-.2,.4,-.5,.6,-.3],
    # covariance=[[.0184,-.0084],[-.0084,.0052]].
    x = np.column_stack([np.ones(5), np.arange(5.0)])
    y = np.array([1.0, 2.0, 1.5, 3.0, 2.5])
    actual = c7.ols_newey_west(y, x, lag=1)
    np.testing.assert_allclose(actual["covariance"], [[0.0184, -0.0084], [-0.0084, 0.0052]], atol=1e-14)
    np.testing.assert_allclose(actual["se"], np.sqrt([0.0184, 0.0052]), atol=1e-14)


def test_no_test_observation_enters_any_fit(models) -> None:
    for name, model in models.items():
        fit_start, fit_end = model["fit_window"]
        test_start, test_end = model["test_window"]
        years = set(model["estimation_years"])
        assert years
        assert min(years) >= fit_start and max(years) <= fit_end
        assert years.isdisjoint(range(test_start, test_end + 1)), name
    assert models["B3_debt_rate"]["estimation_years"] == list(range(2012, 2018))


def test_zero_path_has_zero_effects(models) -> None:
    path = pd.DataFrame({
        "dlnP": np.zeros(5), "dUS": np.zeros(5), "world_gdp_growth_pct": np.zeros(5),
    })
    effects = c7.effects_from_path(path, models)
    np.testing.assert_array_equal(effects.to_numpy(), np.zeros((5, 6)))


def test_one_off_price_shock_has_coefficient_implied_signs(models) -> None:
    path = pd.DataFrame({
        "dlnP": [10.0, 0.0, 0.0], "dUS": [0.0, 0.0, 0.0],
        "world_gdp_growth_pct": [0.0, 0.0, 0.0],
    })
    effects = c7.effects_from_path(path, models)
    expected = {
        "gdp_level_pct": np.sign(models["A_output"]["coefficients"]["dlnP"]),
        "embi_change_bp": np.sign(models["B1_spread"]["coefficients"]["dlnP"]),
        "investment_rate_change_pp": np.sign(models["C_investment"]["coefficients"]["dlnP"]),
        "revenue_change_pp_gdp": np.sign(models["D_revenue"]["coefficients"]["lnP"]),
    }
    for column, sign in expected.items():
        assert np.sign(effects.loc[0, column]) == sign
    expected_real = np.sign(effects.loc[0, "embi_change_bp"] * models["B2_real_rate"]["coefficients"]["dEMBI_per_100"])
    assert np.sign(effects.loc[0, "real_rate_change_pp"]) == expected_real
    expected_debt = np.sign(effects.loc[0, "real_rate_change_pp"] * models["B3_debt_rate"]["coefficients"]["dr"])
    assert np.sign(effects.loc[0, "debt_rate_change_pp"]) == expected_debt


def test_outputs_are_deterministic(data) -> None:
    first = c7.run()
    second = c7.run()
    pd.testing.assert_frame_equal(first[0], second[0])
    pd.testing.assert_frame_equal(first[1], second[1])
    assert first[2:] == second[2:]
    history = c7.historical_changes_v2()
    assert list(history.index) == list(range(2000, 2025))
    assert list(history.columns) == ["dlnP", "dUS", "world_gdp_growth_pct"]


def test_cli_runs_offline_and_writes_owned_outputs() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "src.external_v2"], cwd=ROOT,
        check=True, capture_output=True, text=True, timeout=60,
    )
    assert "Wrote 42 coefficient rows" in completed.stdout
    for relative in (
        "config/c7_proposed.yaml", "data/brazil/c7_estimates.csv", "data/brazil/c7_backtest.csv",
        "outputs/c7_backtest.md", "docs/c7_external_v2.md",
    ):
        assert (ROOT / relative).is_file()
