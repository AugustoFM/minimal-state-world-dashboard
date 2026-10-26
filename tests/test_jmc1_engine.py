from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import external, jmc1_engine as jmc1
from src.cyc1_state_dependent_multiplier import classify_recession_years
from src.macro import run_corner
from src.montecarlo import central_draw, inputs_for_draw, load_context, parameters_for_draw


def _central_corner():
    context = load_context(variants=["default"])
    params = context["parameters"]
    draw = central_draw(params, context["inputs"])
    annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
    draw_parameters = parameters_for_draw(params, draw)
    draw_inputs = inputs_for_draw(context["inputs"], draw)
    corner = run_corner(
        annual, context["population"], context["variant_configs"]["default"],
        draw_parameters, draw_inputs, "central", "transitory",
    )
    changes = external.historical_changes()
    steps = max(context["target_years"]) - context["base_year"]
    rng = np.random.default_rng(1)
    bootstrapped = external.bootstrap_path(rng, changes, steps)
    effects = external.gdp_and_inflation_effects(bootstrapped, params)
    corner = external.apply_external(corner, effects, draw_inputs)
    return corner, draw_inputs


def test_zero_coefficients_reproduce_apply_external_exactly() -> None:
    corner, draw_inputs = _central_corner()
    s0 = corner.loc[corner["scenario"].eq("S0")].sort_values("year").set_index("year")
    effective_level_s0 = s0["real_gdp"] * (1.0 + s0["external_gdp_level_pct"] / 100.0)
    recession_years = classify_recession_years(effective_level_s0)

    result = jmc1._joint_debt_path(
        corner, draw_inputs, "central", recession_years,
        ratio=1.0, inflation_target_pct=3.0, phi_pi=0.0, phi_y=0.0,
        elasticity=0.0, premium_bp=5.0, fx_share_pct=4.0,
        inequality_log_effect=None,
    )
    assert np.allclose(
        result["debt_gdp_joint"].to_numpy(), corner["debt_gdp_with_external"].to_numpy(), atol=1e-9,
    )


def test_zero_elasticity_and_zero_premium_also_reproduce_exactly() -> None:
    corner, draw_inputs = _central_corner()
    s0 = corner.loc[corner["scenario"].eq("S0")].sort_values("year").set_index("year")
    effective_level_s0 = s0["real_gdp"] * (1.0 + s0["external_gdp_level_pct"] / 100.0)
    recession_years = classify_recession_years(effective_level_s0)

    result = jmc1._joint_debt_path(
        corner, draw_inputs, "central", recession_years,
        ratio=1.0, inflation_target_pct=3.0, phi_pi=0.0, phi_y=0.0,
        elasticity=0.0, premium_bp=0.0, fx_share_pct=4.0,
        inequality_log_effect=None,
    )
    assert np.allclose(
        result["debt_gdp_joint"].to_numpy(), corner["debt_gdp_with_external"].to_numpy(), atol=1e-9,
    )


def test_nonzero_taylor_rule_moves_debt_in_the_expected_direction() -> None:
    # An expansion (positive output gap) with a positive phi_y should raise the rate and the
    # resulting debt/GDP relative to the zero-coefficient path, for a scenario with a genuinely
    # positive gap (E_amb).
    corner, draw_inputs = _central_corner()
    s0 = corner.loc[corner["scenario"].eq("S0")].sort_values("year").set_index("year")
    effective_level_s0 = s0["real_gdp"] * (1.0 + s0["external_gdp_level_pct"] / 100.0)
    recession_years = classify_recession_years(effective_level_s0)
    common = dict(
        frame=corner, draw_inputs=draw_inputs, variant="central", recession_years=recession_years,
        ratio=1.0, inflation_target_pct=3.0, elasticity=0.0, premium_bp=0.0, fx_share_pct=4.0,
        inequality_log_effect=None,
    )
    off = jmc1._joint_debt_path(**common, phi_pi=0.0, phi_y=0.0)
    on = jmc1._joint_debt_path(**common, phi_pi=0.3, phi_y=0.3)
    e_amb_off = off.loc[corner["scenario"].eq("E_amb")]["debt_gdp_joint"]
    e_amb_on = on.loc[corner["scenario"].eq("E_amb")]["debt_gdp_joint"]
    assert (e_amb_on.to_numpy()[1:] >= e_amb_off.to_numpy()[1:] - 1e-9).all()


def test_run_draws_draw_zero_is_reproducible_with_the_inequality_loop_off() -> None:
    first = jmc1.run_draws(n_draws=3, seed=123, close_inequality_loop=False)
    second = jmc1.run_draws(n_draws=3, seed=123, close_inequality_loop=False)
    pd.testing.assert_frame_equal(first, second)
    zero = first.loc[first["draw"].eq(0)]
    assert np.allclose(zero["ratio_sampled"], 1.5)  # CYC1 config central
    assert np.allclose(zero["elasticity_sampled"], 1.0)  # FX1 config central
    assert np.allclose(zero["premium_bp_sampled"], 5.0)  # sovereign_risk_premium config central
    assert np.allclose(zero["fx_share_pct_sampled"], 4.0)  # DC1 config central


def test_sampled_parameters_stay_inside_their_configured_bounds() -> None:
    draws = jmc1.run_draws(n_draws=8, seed=7, close_inequality_loop=False)
    sampled = draws.loc[draws["draw"] > 0]
    assert (sampled["ratio_sampled"] >= 1.0 - 1e-9).all() and (sampled["ratio_sampled"] <= 2.5 + 1e-9).all()
    assert (sampled["elasticity_sampled"] >= 0.5 - 1e-9).all() and (sampled["elasticity_sampled"] <= 3.0 + 1e-9).all()
    assert (sampled["fx_share_pct_sampled"] >= 3.7 - 1e-9).all() and (sampled["fx_share_pct_sampled"] <= 4.4 + 1e-9).all()


def test_closing_the_inequality_loop_runs_and_produces_finite_results() -> None:
    draws = jmc1.run_draws(n_draws=1, seed=5, close_inequality_loop=True)
    assert len(draws) > 0
    assert np.isfinite(draws["debt_gdp_joint_vs_s0_pp"]).all()
    assert np.isfinite(draws["incremental_debt_gdp_from_joint_pp"]).all()


def test_summarise_and_render_report_do_not_crash_on_a_small_run() -> None:
    draws = jmc1.run_draws(n_draws=4, seed=5, close_inequality_loop=False)
    summary = jmc1.summarise(draws)
    assert len(summary) > 0
    report = jmc1.render_report(draws, summary, n_draws=4, seed=5)
    assert "# JMC1: a jointly-integrated Monte Carlo" in report
    for scenario in jmc1.SCENARIOS:
        assert scenario in report


def test_module_never_calls_montecarlo_run_or_evaluate_draw() -> None:
    import dis
    import inspect

    for name, member in inspect.getmembers(jmc1, predicate=inspect.isfunction):
        if member.__module__ != jmc1.__name__:
            continue
        calls = {instr.argval for instr in dis.get_instructions(member) if instr.opname == "LOAD_GLOBAL"}
        assert "evaluate_draw" not in calls, f"{name} must not call src.montecarlo.evaluate_draw"
