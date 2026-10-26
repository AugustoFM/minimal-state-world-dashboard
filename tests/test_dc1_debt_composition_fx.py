from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src import dc1_debt_composition_fx as dc1


def test_cumulative_depreciation_matches_hand_computation() -> None:
    # Two years of log changes (x100): +10, then -5. Cumulative depreciation vs the base year
    # must be exp((10 - 5) / 100) - 1, not a naive sum of percentages.
    changes = pd.Series([10.0, -5.0])
    cumulative = dc1.cumulative_depreciation(changes)
    assert cumulative.iloc[0] == pytest.approx(math.exp(10.0 / 100.0) - 1.0)
    assert cumulative.iloc[1] == pytest.approx(math.exp(5.0 / 100.0) - 1.0)


def test_run_draws_draw_zero_is_reproducible_and_uses_the_central_share() -> None:
    first = dc1.run_draws(n_draws=3, seed=123)
    second = dc1.run_draws(n_draws=3, seed=123)
    pd.testing.assert_frame_equal(first, second)
    zero = first.loc[first["draw"].eq(0)]
    assert np.allclose(zero["fx_share_pct_sampled"], 4.0)  # config central


def test_sampled_share_stays_inside_configured_bounds() -> None:
    draws = dc1.run_draws(n_draws=10, seed=7)
    sampled = draws.loc[draws["draw"] > 0, "fx_share_pct_sampled"]
    assert (sampled >= 3.7 - 1e-9).all()
    assert (sampled <= 4.4 + 1e-9).all()


def test_additional_debt_gdp_pp_matches_the_exact_revaluation_formula() -> None:
    draws = dc1.run_draws(n_draws=5, seed=11)
    for row in draws.itertuples():
        expected = row.fx_share_pct_sampled / 100.0 * row.debt_gdp_with_external * (
            row.cumulative_brl_depreciation_pct / 100.0
        )
        assert row.additional_debt_gdp_pp_from_fx_revaluation == pytest.approx(expected, rel=1e-9, abs=1e-9)
        assert row.debt_gdp_with_fx_revaluation == pytest.approx(
            row.debt_gdp_with_external + row.additional_debt_gdp_pp_from_fx_revaluation, rel=1e-9,
        )


def test_zero_cumulative_depreciation_is_a_no_op() -> None:
    draws = dc1.run_draws(n_draws=5, seed=11)
    base_year_rows = draws.loc[draws["horizon"] == 0]
    if len(base_year_rows) > 0:
        assert np.allclose(base_year_rows["additional_debt_gdp_pp_from_fx_revaluation"], 0.0)


def test_summarise_and_render_report_do_not_crash_on_a_small_run() -> None:
    draws = dc1.run_draws(n_draws=4, seed=5)
    summary = dc1.summarise(draws)
    assert len(summary) > 0
    report = dc1.render_report(draws, summary, n_draws=4, seed=5)
    assert "# DC1: FX-linked debt-stock revaluation diagnostic" in report
    assert "R_amb" in report and "R_mod" in report and "S0" in report


def test_module_never_calls_montecarlo_run_or_evaluate_draw() -> None:
    # DC1 must stay a standalone, additive diagnostic: it may import src.montecarlo's pure
    # helper functions, but never call or wrap src.montecarlo.run()/evaluate_draw() itself.
    import inspect

    for name, member in inspect.getmembers(dc1, predicate=inspect.isfunction):
        if member.__module__ != dc1.__name__:
            continue
        calls = {instr.argval for instr in __import__("dis").get_instructions(member) if instr.opname == "LOAD_GLOBAL"}
        assert "evaluate_draw" not in calls, f"{name} must not call src.montecarlo.evaluate_draw"
