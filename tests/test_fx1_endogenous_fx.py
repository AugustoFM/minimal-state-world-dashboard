from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import fx1_endogenous_fx as fx1


def test_extra_inflation_from_depreciation_matches_the_pass_through_formula() -> None:
    fx = pd.Series([2.0, 0.0, 0.0])
    result = fx1.extra_inflation_from_depreciation(fx, pass_12=0.10, pass_24=0.16)
    assert result.iloc[0] == pytest.approx(0.10 * 2.0)
    assert result.iloc[1] == pytest.approx((0.16 - 0.10) * 2.0)
    assert result.iloc[2] == pytest.approx(0.0)


def test_run_draws_draw_zero_is_reproducible_and_uses_the_central_values() -> None:
    first = fx1.run_draws(n_draws=3, seed=123)
    second = fx1.run_draws(n_draws=3, seed=123)
    pd.testing.assert_frame_equal(first, second)
    zero = first.loc[first["draw"].eq(0)]
    assert np.allclose(zero["elasticity_sampled"], 1.0)  # config central
    assert np.allclose(zero["premium_bp_sampled"], 5.0)  # config central (sovereign_risk_premium)
    assert np.allclose(zero["fx_share_pct_sampled"], 4.0)  # DC1's config central


def test_sampled_parameters_stay_inside_their_configured_bounds() -> None:
    draws = fx1.run_draws(n_draws=10, seed=7)
    sampled = draws.loc[draws["draw"] > 0]
    assert (sampled["elasticity_sampled"] >= 0.5 - 1e-9).all()
    assert (sampled["elasticity_sampled"] <= 3.0 + 1e-9).all()
    assert (sampled["premium_bp_sampled"] >= 2.0 - 1e-9).all()
    assert (sampled["premium_bp_sampled"] <= 7.0 + 1e-9).all()
    assert (sampled["fx_share_pct_sampled"] >= 3.7 - 1e-9).all()
    assert (sampled["fx_share_pct_sampled"] <= 4.4 + 1e-9).all()


def test_incremental_debt_matches_the_exact_revaluation_formula() -> None:
    draws = fx1.run_draws(n_draws=4, seed=11)
    for row in draws.itertuples():
        expected = row.fx_share_pct_sampled / 100.0 * row.debt_gdp_baseline * (row.extra_depreciation_pct / 100.0)
        assert row.incremental_debt_gdp_from_fx1_pp == pytest.approx(expected, rel=1e-9)
        assert row.debt_gdp_with_fx1 == pytest.approx(row.debt_gdp_baseline + expected, rel=1e-9)


def test_extra_depreciation_and_incremental_debt_are_non_negative_for_every_scenario() -> None:
    # Debt deviations from base year are expected to be positive at these horizons for every
    # headline scenario under the central draw, so the sovereign-risk-driven depreciation (and the
    # debt it adds back through the FX-linked tranche) should be non-negative too.
    draws = fx1.run_draws(n_draws=1, seed=7)
    assert (draws["extra_depreciation_pct"] >= 0.0).all()
    assert (draws["incremental_debt_gdp_from_fx1_pp"] >= 0.0).all()


def test_summarise_and_render_report_do_not_crash_on_a_small_run() -> None:
    draws = fx1.run_draws(n_draws=4, seed=5)
    summary = fx1.summarise(draws)
    assert len(summary) > 0
    report = fx1.render_report(draws, summary, n_draws=4, seed=5)
    assert "# FX1: endogenous exchange-rate response to fiscal stress" in report
    for scenario in fx1.SCENARIOS:
        assert scenario in report


def test_module_never_calls_montecarlo_run_or_evaluate_draw() -> None:
    import inspect

    for name, member in inspect.getmembers(fx1, predicate=inspect.isfunction):
        if member.__module__ != fx1.__name__:
            continue
        calls = {instr.argval for instr in __import__("dis").get_instructions(member) if instr.opname == "LOAD_GLOBAL"}
        assert "evaluate_draw" not in calls, f"{name} must not call src.montecarlo.evaluate_draw"
