from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import iy1_interest_income_distribution as iy1


def test_capital_income_shares_are_well_formed() -> None:
    shares = iy1.capital_income_shares()
    assert 0.0 < shares["top_1_share_pct"] <= shares["top_10_share_pct"] <= 100.0


def test_cumulative_extra_inflation_matches_hand_computation() -> None:
    effects = pd.DataFrame({"step": [1, 2, 3], "external_extra_inflation_pp": [10.0, -5.0, 0.0]})
    cumulative = iy1._cumulative_extra_inflation(effects, base_year=2025, years=[2026, 2027, 2028])
    assert cumulative[2025] == 0.0
    assert cumulative[2026] == pytest.approx(10.0)
    assert cumulative[2027] == pytest.approx((1.10 * 0.95 - 1.0) * 100.0)
    assert cumulative[2028] == pytest.approx((1.10 * 0.95 * 1.00 - 1.0) * 100.0)


def test_run_draws_draw_zero_is_reproducible() -> None:
    first = iy1.run_draws(n_draws=2, seed=123)
    second = iy1.run_draws(n_draws=2, seed=123)
    pd.testing.assert_frame_equal(first, second)


def test_expansion_scenarios_with_positive_debt_service_increase_gini_via_iy1() -> None:
    # The reviewer's claim under test: a debt-financed expansion that raises government interest
    # expense should make IY1's windfall channel push the Gini up, not down, since interest income
    # concentrates at the top. Where interest expense does rise (the common case for these two
    # debt-financed expansion scenarios), the Gini change from switching IY1 on should be positive.
    draws = iy1.run_draws(n_draws=3, seed=11)
    rising_interest = draws.loc[draws["delta_interest_pp_gdp"] > 0.01]
    assert len(rising_interest) > 0
    assert (rising_interest["gini_change_from_iy1_points"] > 0).mean() > 0.9


def test_summarise_and_render_report_do_not_crash_on_a_small_run() -> None:
    draws = iy1.run_draws(n_draws=3, seed=5)
    summary = iy1.summarise(draws)
    assert len(summary) > 0
    shares = iy1.capital_income_shares()
    report = iy1.render_report(draws, summary, shares, n_draws=3, seed=5)
    assert "# IY1: interest-income and inflation-tax distribution diagnostic" in report
    assert "E_mod" in report and "E_amb" in report


def test_module_never_calls_montecarlo_run_or_evaluate_draw() -> None:
    import inspect

    for name, member in inspect.getmembers(iy1, predicate=inspect.isfunction):
        if member.__module__ != iy1.__name__:
            continue
        calls = {instr.argval for instr in __import__("dis").get_instructions(member) if instr.opname == "LOAD_GLOBAL"}
        assert "evaluate_draw" not in calls, f"{name} must not call src.montecarlo.evaluate_draw"
