from __future__ import annotations

import math
import subprocess
import sys

import pandas as pd
import pytest

from src import backtest
from src.macro import debt_step, growth_accounting_backcast, read_pwt_brazil_growth


def test_debt_backtest_zero_residual_reproduces_textbook_recursion() -> None:
    rows = [{
        "year": 2020,
        "observed_debt_gdp": 60.0,
        "primary_balance_gdp": 0.0,
        "implicit_interest_pct": float("nan"),
        "nominal_gdp_growth_pct": float("nan"),
    }]
    debt = 0.60
    for year, interest, growth, primary in [
        (2021, 5.0, 3.0, 1.0),
        (2022, 7.0, 4.0, -0.5),
    ]:
        debt = debt * (1 + interest / 100) / (1 + growth / 100) - primary / 100
        rows.append({
            "year": year, "observed_debt_gdp": debt * 100,
            "primary_balance_gdp": primary, "implicit_interest_pct": interest,
            "nominal_gdp_growth_pct": growth,
        })
    result = backtest.debt_backtest(pd.DataFrame(rows))
    assert result["residual_pp"].abs().max() < 1e-12


def test_growth_all_pwt_inputs_reproduces_c2_backcast_error() -> None:
    pwt = read_pwt_brazil_growth(backtest.DEFAULT_PATHS["pwt"])
    result = backtest.growth_backtest_pwt(pwt, 2000, 2019)
    error = (result["predicted_growth_pct"] - result["pwt_observed_growth_pct"]).mean()
    expected = growth_accounting_backcast(pwt)["average_error_pp"]
    assert error == pytest.approx(expected, abs=1e-12)
    assert error == pytest.approx(0.1172, abs=0.00005)


def test_result_rows_are_unique_and_complete() -> None:
    results, _, _ = backtest.run_backtests()
    assert not results.duplicated(["test", "year"]).any()
    expected = {
        "debt_engine": 15,
        "debt_engine_one_step": 14,
        "growth_block": 14,
        "multiplier_total": 15,
        "multiplier_categories": 15,
        "inflation_pass_through": 20,
    }
    assert results.groupby("test")["year"].size().to_dict() == expected
    assert results[["observed_value", "predicted_value", "residual"]].notna().all().all()


def test_cli_runs_offline() -> None:
    # Use an explicit workspace-local target: the host's default pytest temp
    # root can be unreadable under the Windows ACL used by this repository.
    results = backtest.ROOT / "outputs/backtest_test_results.csv"
    report = backtest.ROOT / "outputs/backtest_test_report.md"
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "src.backtest", "--results", str(results), "--report", str(report)],
            cwd=backtest.ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert completed.returncode == 0, completed.stderr
        assert results.exists() and report.exists()
        assert "Overall proposed gate" in report.read_text(encoding="utf-8")
    finally:
        results.unlink(missing_ok=True)
        report.unlink(missing_ok=True)


def test_one_step_debt_reanchors_on_observed_lag() -> None:
    inputs = pd.DataFrame({
        "year": [2000, 2001, 2002],
        "observed_debt_gdp": [50.0, 60.0, 55.0],
        "primary_balance_gdp": [0.0, 1.0, 2.0],
        "implicit_interest_pct": [math.nan, 10.0, 8.0],
        "nominal_gdp_growth_pct": [math.nan, 5.0, 6.0],
    })
    out = backtest.debt_one_step(inputs)
    assert out["year"].tolist() == [2001, 2002]
    assert out.loc[1, "predicted_debt_gdp"] == pytest.approx(debt_step(0.60, 0.08, 0.06, 0.02) * 100)
