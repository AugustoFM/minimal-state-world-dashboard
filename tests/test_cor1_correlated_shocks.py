from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import cor1_correlated_shocks as cor1


def test_load_joint_historical_deviations_is_demeaned() -> None:
    deviations = cor1.load_joint_historical_deviations()
    assert len(deviations) > 0
    for column in deviations.columns:
        assert deviations[column].mean() == pytest.approx(0.0, abs=1e-9)


def test_block_bootstrap_joint_returns_requested_length_and_only_observed_values() -> None:
    deviations = cor1.load_joint_historical_deviations()
    rng = np.random.default_rng(3)
    boot = cor1.block_bootstrap_joint(rng, deviations, steps=17)
    assert len(boot) == 17
    for column in deviations.columns:
        assert set(boot[column].round(9)).issubset(set(deviations[column].round(9)))


def test_block_bootstrap_joint_rejects_blocks_longer_than_the_sample() -> None:
    deviations = cor1.load_joint_historical_deviations().iloc[:2]
    with pytest.raises(ValueError):
        cor1.block_bootstrap_joint(np.random.default_rng(0), deviations, steps=5)


def test_zero_shocks_reproduce_the_published_corner_exactly() -> None:
    # draw 0 (the central draw) uses an all-zero shock frame; the resulting debt_gdp_correlated
    # path must exactly reproduce debt_gdp_with_external, the critical regression every diagnostic
    # this session carries.
    draws = cor1.run_draws(n_draws=1, seed=20261026)
    assert np.allclose(
        draws["debt_gdp_baseline_vs_s0_pp"].to_numpy(), draws["debt_gdp_correlated_vs_s0_pp"].to_numpy(), atol=1e-6,
    )


def test_run_draws_draw_zero_is_reproducible() -> None:
    first = cor1.run_draws(n_draws=3, seed=123)
    second = cor1.run_draws(n_draws=3, seed=123)
    pd.testing.assert_frame_equal(first, second)


def test_sampled_draws_generally_differ_from_the_published_baseline() -> None:
    draws = cor1.run_draws(n_draws=6, seed=5)
    sampled = draws.loc[(draws["draw"] > 0) & draws["scenario"].ne("S0")]
    assert (sampled["debt_gdp_baseline_vs_s0_pp"] != sampled["debt_gdp_correlated_vs_s0_pp"]).any()


def test_summarise_and_render_report_do_not_crash_on_a_small_run() -> None:
    draws = cor1.run_draws(n_draws=4, seed=5)
    summary = cor1.summarise(draws)
    assert len(summary) > 0
    report = cor1.render_report(draws, summary, n_draws=4, seed=5)
    assert "# COR1: jointly-correlated macro-fiscal shock diagnostic" in report
    for scenario in cor1.SCENARIOS:
        assert scenario in report


def test_module_never_calls_montecarlo_run_or_evaluate_draw() -> None:
    import dis
    import inspect

    for name, member in inspect.getmembers(cor1, predicate=inspect.isfunction):
        if member.__module__ != cor1.__name__:
            continue
        calls = {instr.argval for instr in dis.get_instructions(member) if instr.opname == "LOAD_GLOBAL"}
        assert "evaluate_draw" not in calls, f"{name} must not call src.montecarlo.evaluate_draw"
