from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import dis1_disaster_shock as dis1


def test_primary_balance_path_conserves_shape_and_phases_out() -> None:
    events = np.array([False, True, False, False, False])
    hits = np.array([1.0])
    path = dis1.primary_balance_path(events, hits, years=5, decay_years=2)
    assert path[0] == pytest.approx(0.0)
    assert path[1] == pytest.approx(1.0)
    assert path[2] == pytest.approx(0.5)
    assert path[3] == pytest.approx(0.0)
    assert path[4] == pytest.approx(0.0)


def test_sample_primary_balance_hits_rejects_invalid_bounds() -> None:
    rng = np.random.default_rng(1)
    with pytest.raises(ValueError):
        dis1.sample_primary_balance_hits(rng, 3, low=0.5, mode=0.1, high=0.2)


def test_no_events_leaves_debt_gdp_unchanged() -> None:
    # When the sampled probability is driven to zero, no event can fire, and the diagnostic
    # must reproduce the external-adjusted baseline exactly.
    events = dis1.sample_events(np.random.default_rng(0), years=20, probability=0.0)
    assert not events.any()
    path = dis1.level_path(events, np.array([]), years=20, build_up_years=1, half_life_years=2.0)
    assert np.allclose(path, 0.0)
    balance = dis1.primary_balance_path(events, np.array([]), years=20, decay_years=2)
    assert np.allclose(balance, 0.0)


def test_run_draws_draw_zero_is_reproducible_and_uses_the_central_values() -> None:
    first = dis1.run_draws(n_draws=3, seed=123)
    second = dis1.run_draws(n_draws=3, seed=123)
    pd.testing.assert_frame_equal(first, second)
    zero = first.loc[first["draw"].eq(0)]
    expected_probability = 0.5 * (dis1.EVENT_PROBABILITY_CFG["low"] + dis1.EVENT_PROBABILITY_CFG["high"])
    assert np.allclose(zero["probability_sampled"], expected_probability)


def test_sampled_probabilities_stay_inside_their_configured_bounds() -> None:
    draws = dis1.run_draws(n_draws=10, seed=7)
    sampled = draws.loc[draws["draw"] > 0]
    assert (sampled["probability_sampled"] >= dis1.EVENT_PROBABILITY_CFG["low"] - 1e-9).all()
    assert (sampled["probability_sampled"] <= dis1.EVENT_PROBABILITY_CFG["high"] + 1e-9).all()


def test_additional_debt_is_zero_whenever_no_shock_hit_that_year() -> None:
    draws = dis1.run_draws(n_draws=6, seed=5)
    no_shock = draws.loc[(draws["extra_gdp_level_pct"] == 0.0) & (draws["extra_primary_balance_cost_pp"] == 0.0)]
    assert (no_shock["additional_debt_gdp_pp_from_disaster"] == 0.0).all()
    assert np.allclose(no_shock["debt_gdp_with_disaster"], no_shock["debt_gdp_baseline"])


def test_summarise_and_render_report_do_not_crash_on_a_small_run() -> None:
    draws = dis1.run_draws(n_draws=4, seed=5)
    summary = dis1.summarise(draws)
    assert len(summary) > 0
    report = dis1.render_report(draws, summary, n_draws=4, seed=5)
    assert "# DIS1: climate/natural-disaster tail-shock diagnostic" in report
    for scenario in dis1.SCENARIOS:
        assert scenario in report


def test_module_never_calls_montecarlo_run_or_evaluate_draw() -> None:
    import dis
    import inspect

    for name, member in inspect.getmembers(dis1, predicate=inspect.isfunction):
        if member.__module__ != dis1.__name__:
            continue
        calls = {instr.argval for instr in dis.get_instructions(member) if instr.opname == "LOAD_GLOBAL"}
        assert "evaluate_draw" not in calls, f"{name} must not call src.montecarlo.evaluate_draw"
