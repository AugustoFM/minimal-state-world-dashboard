from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src import cyc1_state_dependent_multiplier as cyc1


def test_classify_recession_years_flags_a_below_trend_year() -> None:
    # Steady 2% growth for 5 years (trend fully warmed up), then a sharp drop: the drop year
    # must classify as below its own trailing mean, the steady years must not.
    level = pd.Series([100.0, 102.0, 104.04, 106.1208, 108.243216, 106.08])
    recession = cyc1.classify_recession_years(level, trend_window_years=5)
    assert recession.iloc[5]  # the drop year
    assert not recession.iloc[4]  # last steady-growth year, trend == growth


def test_run_draws_draw_zero_is_reproducible_and_uses_the_central_ratio() -> None:
    first = cyc1.run_draws(n_draws=3, seed=123)
    second = cyc1.run_draws(n_draws=3, seed=123)
    pd.testing.assert_frame_equal(first, second)
    zero = first.loc[first["draw"].eq(0)]
    assert np.allclose(zero["ratio_sampled"], 1.5)  # config central


def test_sampled_ratio_stays_inside_configured_bounds() -> None:
    draws = cyc1.run_draws(n_draws=10, seed=7)
    sampled = draws.loc[draws["draw"] > 0, "ratio_sampled"]
    assert (sampled >= 1.0 - 1e-9).all()
    assert (sampled <= 2.5 + 1e-9).all()


def test_state_dependent_effect_only_differs_from_fixed_in_recession_years() -> None:
    draws = cyc1.run_draws(n_draws=5, seed=11)
    for row in draws.itertuples():
        fixed, state_dep = row.gdp_level_vs_s0_pct_fixed_multiplier, row.gdp_level_vs_s0_pct_state_dependent
        if row.ratio_sampled == pytest.approx(1.0):
            # A ratio of exactly 1.0 is a no-op regardless of regime.
            assert state_dep == pytest.approx(fixed)
        elif not math.isclose(fixed, state_dep, rel_tol=1e-9, abs_tol=1e-12):
            # Wherever the two differ, it must be exactly the sampled ratio's rescaling.
            assert state_dep == pytest.approx(fixed * row.ratio_sampled, rel=1e-6)


def test_summarise_and_render_report_do_not_crash_on_a_small_run() -> None:
    draws = cyc1.run_draws(n_draws=4, seed=5)
    summary = cyc1.summarise(draws)
    assert len(summary) > 0
    assert (summary["mean_recession_years_to_horizon"] >= 0).all()
    report = cyc1.render_report(draws, summary, n_draws=4, seed=5)
    assert "# CYC1: state-dependent (cyclical) fiscal-multiplier diagnostic" in report
    assert "R_amb" in report and "R_mod" in report


def test_module_never_calls_montecarlo_run_or_evaluate_draw() -> None:
    # CYC1 must stay a standalone, additive diagnostic: it may import src.montecarlo's pure
    # helper functions, but never call or wrap src.montecarlo.run()/evaluate_draw() itself.
    import inspect

    for name, member in inspect.getmembers(cyc1, predicate=inspect.isfunction):
        if member.__module__ != cyc1.__name__:
            continue
        calls = {instr.argval for instr in __import__("dis").get_instructions(member) if instr.opname == "LOAD_GLOBAL"}
        assert "evaluate_draw" not in calls, f"{name} must not call src.montecarlo.evaluate_draw"
