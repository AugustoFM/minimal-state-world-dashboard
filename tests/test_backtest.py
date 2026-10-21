from __future__ import annotations

import math
import subprocess
import sys

import numpy as np
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
        "debt_engine_zero_sfa_oos": 8,
        "debt_engine_with_sfa_oos": 8,
        "growth_block": 14,
        "multiplier_total": 15,
        "multiplier_categories": 15,
        "inflation_pass_through": 20,
        "c7_channel_a_oos": 10,
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
        text = report.read_text(encoding="utf-8")
        assert "Tier 1 - differences vs S0" in text
        assert "Tier 2 - debt/GDP levels" in text
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


@pytest.mark.parametrize(
    ("one_step_mae", "growth_mean", "c7_rmse", "naive_rmse", "sfa_final", "tier1", "tier2"),
    [
        (2.0, 0.4, 3.0, 4.0, 4.0, "PASS", "PASS"),
        (2.6, 0.4, 3.0, 4.0, 4.0, "FAIL", "PASS"),
        (2.0, -0.6, 3.0, 4.0, 4.0, "FAIL", "PASS"),
        (2.0, 0.4, 4.0, 4.0, 4.0, "FAIL", "PASS"),
        (2.0, 0.4, 3.0, 4.0, 5.1, "PASS", "FAIL"),
    ],
)
def test_two_tier_gate_logic(
    one_step_mae: float,
    growth_mean: float,
    c7_rmse: float,
    naive_rmse: float,
    sfa_final: float,
    tier1: str,
    tier2: str,
) -> None:
    stats = pd.DataFrame([
        {"test": "debt_engine_one_step", "mae": one_step_mae},
        {"test": "growth_block", "mean_error": growth_mean},
        {"test": "c7_channel_a_oos", "rmse": c7_rmse, "naive_rmse": naive_rmse},
        {"test": "debt_engine_with_sfa_oos", "final_error": sfa_final},
    ])
    verdicts = backtest.gate_verdicts(stats, backtest._yaml(backtest.DEFAULT_PATHS["d2"]))
    assert verdicts == {"tier_1_differences_vs_s0": tier1, "tier_2_levels": tier2}


def test_sfa_estimation_stops_at_2017_and_zero_mean_reproduces_zero_sfa() -> None:
    sfas = [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 7.0]
    observed = [50.0]
    for sfa in sfas:
        observed.append(observed[-1] + sfa)
    inputs = pd.DataFrame({
        "year": list(range(2010, 2019)),
        "observed_debt_gdp": observed,
        "primary_balance_gdp": 0.0,
        "implicit_interest_pct": [math.nan] + [0.0] * 8,
        "nominal_gdp_growth_pct": [math.nan] + [0.0] * 8,
    })
    recursion, summary = backtest.sfa_out_of_sample(inputs)
    assert summary["estimation_years"] == list(range(2011, 2018))
    assert summary["mean_2011_2017"] == pytest.approx(0.0)
    assert summary["values_by_year"][2018] == pytest.approx(7.0)
    assert recursion["with_sfa_debt_gdp"].tolist() == pytest.approx(recursion["zero_sfa_debt_gdp"].tolist())


def test_period_table_windows_and_values_trace_to_inputs() -> None:
    wide = backtest.observed_wide(backtest.DEFAULT_PATHS["observed"])
    parameters = backtest._yaml(backtest.DEFAULT_PATHS["parameters"])
    table = backtest.period_diagnostic(
        wide,
        backtest.DEFAULT_PATHS["fiscal"],
        backtest.DEFAULT_PATHS["workbook"],
        backtest.DEFAULT_PATHS["external_observed"],
        backtest.DEFAULT_PATHS["c7_estimates"],
        parameters,
    )
    assert len(table) == len(backtest.PERIOD_WINDOWS) == 6
    regular = table.loc[~table["separately_flagged"]].sort_values("start_year")
    assert (regular["start_year"].iloc[1:].to_numpy() > regular["end_year"].iloc[:-1].to_numpy()).all()
    flagged = table.loc[table["separately_flagged"]].iloc[0]
    assert (flagged.start_year, flagged.end_year) == (2023, 2025)

    fiscal = pd.read_csv(backtest.DEFAULT_PATHS["fiscal"]).set_index("year")["primary_spending_pct_gdp"]
    revenue = backtest.read_general_government_revenue(backtest.DEFAULT_PATHS["workbook"])
    external = pd.read_csv(backtest.DEFAULT_PATHS["external_observed"]).pivot(index="year", columns="indicator", values="value")
    for row in regular.itertuples(index=False):
        years = range(row.start_year, row.end_year + 1)
        assert row.average_real_gdp_growth_pct == pytest.approx(wide.loc[list(years), "gdp_growth_pct"].mean())
        base = row.start_year - 1  # changes run from the inherited level
        assert row.primary_spending_change_pp == pytest.approx(fiscal.loc[row.end_year] - fiscal.loc[base])
        assert row.revenue_change_pp == pytest.approx(revenue.loc[row.end_year] - revenue.loc[base])
        primary = -wide["primary_result_pct_gdp"]
        debt = wide["gross_general_government_debt_pct_gdp"]
        assert row.primary_balance_change_pp == pytest.approx(primary.loc[row.end_year] - primary.loc[base])
        assert row.gross_debt_change_pp == pytest.approx(debt.loc[row.end_year] - debt.loc[base])
        price = external["commodity_export_price_index"]
        expected_price = (np.log(price.loc[row.end_year]) - np.log(price.loc[base])) * 100.0
        assert row.commodity_price_log_change_pct == pytest.approx(expected_price)
        assert row.model_residual_pp == pytest.approx(row.model_implied_growth_pct - row.average_real_gdp_growth_pct)

    assert flagged.average_real_gdp_growth_pct == pytest.approx(
        (wide.loc[2023, "gdp_growth_pct"] + wide.loc[2024, "gdp_growth_pct"] + backtest.IBGE_2025_GROWTH) / 3.0
    )
    assert flagged.primary_spending_change_pp == pytest.approx(fiscal.loc[2025] - fiscal.loc[2022])
    assert flagged.revenue_change_pp == pytest.approx(revenue.loc[2025] - revenue.loc[2022])
    assert math.isnan(flagged.gross_debt_change_pp)
    assert math.isnan(flagged.model_implied_growth_pct)
    assert "hand-entered" in flagged.growth_source
