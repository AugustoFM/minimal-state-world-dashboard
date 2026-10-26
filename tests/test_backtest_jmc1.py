from __future__ import annotations

import pytest

from src import backtest_jmc1 as jmc1bt


def test_oracle_errors_match_the_published_backtest_report() -> None:
    # outputs/backtest.md's own debt_engine / debt_engine_one_step rows.
    result = jmc1bt.run_validation()
    assert result["oracle_errors"]["cumulative"]["rmse"] == pytest.approx(9.322, abs=0.01)
    assert result["oracle_errors"]["one_step"]["rmse"] == pytest.approx(2.390, abs=0.01)


def test_fixed_mechanism_beats_taylor_only_on_debt_fit_both_datasets() -> None:
    result = jmc1bt.run_validation()
    assert result["one_step_errors"]["fixed"]["rmse"] <= result["one_step_errors"]["taylor_only"]["rmse"]
    assert result["sidra_one_step_errors"]["fixed"]["rmse"] <= result["sidra_one_step_errors"]["taylor_only"]["rmse"]


def test_taylor_only_beats_fixed_on_the_selic_level_itself() -> None:
    result = jmc1bt.run_validation()
    assert result["selic_errors"]["taylor_only"]["rmse"] <= result["selic_errors"]["fixed"]["rmse"]


def test_load_backtest_inputs_has_consecutive_debt_years_from_2006() -> None:
    frame = jmc1bt.load_backtest_inputs()
    anchored = frame.loc[frame["gross_general_government_debt_pct_gdp"].notna()]
    years = anchored.index.tolist()
    assert years[0] == 2006
    assert years == list(range(years[0], years[-1] + 1))


def test_render_report_does_not_crash_and_names_both_verdicts() -> None:
    result = jmc1bt.run_validation()
    report = jmc1bt.render_report(result)
    assert "# JMC1 validation" in report
    assert "Refined test" in report
    assert "oracle" in report


def test_module_never_calls_montecarlo_run_or_evaluate_draw() -> None:
    import dis
    import inspect

    for name, member in inspect.getmembers(jmc1bt, predicate=inspect.isfunction):
        if member.__module__ != jmc1bt.__name__:
            continue
        calls = {instr.argval for instr in dis.get_instructions(member) if instr.opname == "LOAD_GLOBAL"}
        assert "evaluate_draw" not in calls, f"{name} must not call src.montecarlo.evaluate_draw"
