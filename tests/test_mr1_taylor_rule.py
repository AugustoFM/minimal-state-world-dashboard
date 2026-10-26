from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import external
from src import mr1_taylor_rule as mr1
from src.macro import macro_input, run_corner
from src.montecarlo import central_draw, inputs_for_draw, load_context, parameters_for_draw


def _central_corner():
    context = load_context(variants=["default"])
    params = context["parameters"]
    draw = central_draw(params, context["inputs"])
    annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
    draw_parameters = parameters_for_draw(params, draw)
    draw_inputs = inputs_for_draw(context["inputs"], draw)
    corner = run_corner(
        annual, context["population"], context["variant_configs"]["default"], draw_parameters, draw_inputs,
        "central", "transitory",
    )
    changes = external.historical_changes()
    steps = max(context["target_years"]) - context["base_year"]
    bootstrapped = external.bootstrap_path(np.random.default_rng([1, 2, 3]), changes, steps)
    effects = external.gdp_and_inflation_effects(bootstrapped, params)
    corner = external.apply_external(corner, effects, draw_inputs)
    return corner, draw_inputs


def test_taylor_real_rate_reduces_to_base_rate_when_coefficients_are_zero() -> None:
    assert mr1.taylor_real_rate(5.0, 7.0, 2.0, 3.0, 0.0, 0.0) == pytest.approx(5.0)


def test_taylor_real_rate_responds_positively_to_both_gaps() -> None:
    base = mr1.taylor_real_rate(5.0, 3.0, 0.0, 3.0, 0.5, 0.5)
    higher_inflation = mr1.taylor_real_rate(5.0, 5.0, 0.0, 3.0, 0.5, 0.5)
    higher_output_gap = mr1.taylor_real_rate(5.0, 3.0, 2.0, 3.0, 0.5, 0.5)
    assert higher_inflation > base
    assert higher_output_gap > base


def test_rerun_debt_with_zero_coefficients_exactly_reproduces_the_baseline_debt_path() -> None:
    corner, draw_inputs = _central_corner()
    inflation_target = macro_input(draw_inputs, "gdp_deflator_growth", "central")
    taylor_zero = mr1._rerun_debt_with_rate_rule(corner, draw_inputs, "central", inflation_target, 0.0, 0.0)
    np.testing.assert_allclose(taylor_zero.to_numpy(), corner["debt_gdp_with_external"].to_numpy(), atol=1e-9)


def test_run_draws_draw_zero_is_reproducible_and_uses_the_central_discount() -> None:
    first = mr1.run_draws(n_draws=3, seed=123)
    second = mr1.run_draws(n_draws=3, seed=123)
    pd.testing.assert_frame_equal(first, second)
    zero = first.loc[first["draw"].eq(0)]
    assert np.allclose(zero["phi_pi_sampled"], 0.5 * 0.6)  # config central discount


def test_sampled_discount_stays_inside_configured_bounds() -> None:
    draws = mr1.run_draws(n_draws=10, seed=7)
    phi = draws.loc[draws["draw"] > 0, "phi_pi_sampled"]
    assert (phi >= 0.5 * 0.3 - 1e-9).all()
    assert (phi <= 0.5 * 1.0 + 1e-9).all()


def test_expansions_raise_the_rate_and_contractions_cut_it_vs_s0() -> None:
    # At the short horizon the output-gap term dominates the (common-across-scenarios) inflation
    # term, so the sign of the rate differential should match the sign of the scenario's own effect:
    # expansions (E_mod, E_amb) raise the Selic vs S0, contractions (R_mod, R_amb) cut it.
    draws = mr1.run_draws(n_draws=5, seed=11)
    short_horizon = draws.loc[draws["horizon"] == 5]
    for scenario in ("E_mod", "E_amb"):
        assert (short_horizon.loc[short_horizon["scenario"].eq(scenario), "real_rate_differential_vs_s0_pp"] > 0).all()
    for scenario in ("R_mod", "R_amb"):
        assert (short_horizon.loc[short_horizon["scenario"].eq(scenario), "real_rate_differential_vs_s0_pp"] < 0).all()


def test_summarise_and_render_report_do_not_crash_on_a_small_run() -> None:
    draws = mr1.run_draws(n_draws=4, seed=5)
    summary = mr1.summarise(draws)
    assert len(summary) > 0
    report = mr1.render_report(draws, summary, n_draws=4, seed=5)
    assert "# MR1: Taylor-rule monetary-reaction-function diagnostic" in report
    for scenario in mr1.SCENARIOS:
        assert scenario in report


def test_module_never_calls_montecarlo_run_or_evaluate_draw() -> None:
    import inspect

    for name, member in inspect.getmembers(mr1, predicate=inspect.isfunction):
        if member.__module__ != mr1.__name__:
            continue
        calls = {instr.argval for instr in __import__("dis").get_instructions(member) if instr.opname == "LOAD_GLOBAL"}
        assert "evaluate_draw" not in calls, f"{name} must not call src.montecarlo.evaluate_draw"
