from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import debt_level_diagnostics as dld
from src.macro import debt_step


def _synthetic_s0(debt_path: dict[int, float], pb_path: dict[int, float], adj_path: dict[int, float] | None = None) -> pd.DataFrame:
    years = sorted(debt_path)
    adj_path = adj_path or {}
    return pd.DataFrame({
        "year": years,
        "scenario": "S0",
        "debt_gdp": [debt_path[y] for y in years],
        "primary_balance_gdp": [pb_path[y] for y in years],
        "debt_adjustment_pp": [adj_path.get(y, 0.0) for y in years],
    })


def test_implied_r_minus_g_matches_debt_step_identity() -> None:
    # Build a path with a known, constant (1+i)/(1+g) - 1 = 0.05 and primary deficit -2.0 pp/yr.
    debt = {2025: 70.0}
    pb_pct = -2.0
    for year in range(2026, 2031):
        prior = debt[year - 1] / 100.0
        debt[year] = debt_step(prior, 0.0, 0.0, 0.0) * 0  # placeholder, overwritten below
    # debt_step(d_prev, i, g, pb) returns d_prev*(1+i)/(1+g) - pb, with i, g, pb fractions.
    debt = {2025: 0.70}
    for year in range(2026, 2031):
        debt[year] = debt_step(debt[year - 1], 0.05, 0.0, pb_pct / 100.0)
    frame = _synthetic_s0({y: v * 100.0 for y, v in debt.items()}, {y: pb_pct for y in debt})
    r_minus_g = dld.implied_r_minus_g(frame)
    assert np.isnan(r_minus_g.loc[2025])
    for year in range(2026, 2031):
        assert r_minus_g.loc[year] == pytest.approx(0.05, abs=1e-9)


def test_stabilising_primary_balance_is_debt_times_r_minus_g() -> None:
    prior = pd.Series({2026: 80.0, 2027: 90.0})
    r_minus_g = pd.Series({2026: 0.05, 2027: -0.02})
    stabilising = dld.stabilising_primary_balance_pp(prior, r_minus_g)
    assert stabilising.loc[2026] == pytest.approx(4.0)
    assert stabilising.loc[2027] == pytest.approx(-1.8)


def test_fiscal_reaction_debt_path_zero_rho_reproduces_the_input_identity() -> None:
    debt = {2025: 0.70}
    for year in range(2026, 2036):
        debt[year] = debt_step(debt[year - 1], 0.08, 0.03, -0.02)
    frame = _synthetic_s0({y: v * 100.0 for y, v in debt.items()}, {y: -2.0 for y in debt})
    reconstructed = dld.fiscal_reaction_debt_path(frame, rho=0.0, base_year=2025)
    for year in debt:
        assert reconstructed.loc[year] == pytest.approx(debt[year] * 100.0, abs=1e-6)


def test_fiscal_reaction_debt_path_positive_rho_lowers_debt_vs_plain_identity() -> None:
    debt = {2025: 0.70}
    for year in range(2026, 2036):
        debt[year] = debt_step(debt[year - 1], 0.08, 0.02, -0.03)
    frame = _synthetic_s0({y: v * 100.0 for y, v in debt.items()}, {y: -3.0 for y in debt})
    positive = dld.fiscal_reaction_debt_path(frame, rho=0.0334, base_year=2025)
    negative = dld.fiscal_reaction_debt_path(frame, rho=-0.037, base_year=2025)
    plain = debt[2035] * 100.0
    # A positive reaction (primary balance improves as debt rises) must leave debt
    # lower than the no-reaction identity; Brazil's own (negative) estimate must
    # leave it higher, per docs/debt_models_review.md's finding.
    assert positive.loc[2035] < plain
    assert negative.loc[2035] > plain


def test_nonlinear_premium_debt_path_matches_plain_identity_below_threshold() -> None:
    debt = {2025: 0.50}
    for year in range(2026, 2031):
        debt[year] = debt_step(debt[year - 1], 0.06, 0.03, -0.01)
    frame = _synthetic_s0({y: v * 100.0 for y, v in debt.items()}, {y: -1.0 for y in debt})
    # Threshold far above every debt value in this path: premium is always zero.
    path = dld.nonlinear_premium_debt_path(frame, base_year=2025, threshold_pct_gdp=500.0, bp_per_pp_squared=0.12)
    for year in debt:
        assert path.loc[year] == pytest.approx(debt[year] * 100.0, abs=1e-6)


def test_nonlinear_premium_is_capped() -> None:
    # Force a very large excess above the threshold so the uncapped quadratic
    # premium would be enormous; the applied premium must never exceed the cap.
    debt = {2025: 0.70}
    for year in range(2026, 2046):
        debt[year] = debt_step(debt[year - 1], 0.08, 0.0, -0.05)  # no growth, large deficit: debt explodes
    frame = _synthetic_s0({y: v * 100.0 for y, v in debt.items()}, {y: -5.0 for y in debt})
    r_minus_g = dld.implied_r_minus_g(frame)
    path = dld.nonlinear_premium_debt_path(frame, base_year=2025, threshold_pct_gdp=100.0, bp_per_pp_squared=0.12)
    years = sorted(debt)
    for year in years[1:]:
        prior = path.loc[year - 1]
        # pb is -5.0 (a deficit); the recursion computes debt[year] = prior*ratio - pb,
        # i.e. prior*ratio + 5.0, so ratio = (debt[year] - 5.0) / prior.
        implied_ratio = (path.loc[year] - 5.0) / prior
        premium = (implied_ratio - 1.0 - float(r_minus_g.loc[year])) * 10_000.0
        assert premium <= dld.PREMIUM_CAP_BP + 1e-6


def test_sfa_source_path_brazil_matches_existing_bootstrap_mechanism() -> None:
    from src import external
    d3 = dld._yaml(dld.DEFAULT_PATHS["d3"])
    rng_a = np.random.default_rng(12345)
    rng_b = np.random.default_rng(12345)
    direct = external.bootstrap_path(rng_a, external.historical_sfa_changes(), 20)
    expected = {int(step): float(value) for step, value in zip(direct["step"], direct["sfa_pp"])}
    via_module = dld.sfa_source_path(rng_b, 20, "brazil", d3)
    assert via_module == expected


def test_sfa_source_path_emerging_stays_within_a_wide_band_of_the_panel_moments() -> None:
    d3 = dld._yaml(dld.DEFAULT_PATHS["d3"])
    rng = np.random.default_rng(999)
    path = dld.sfa_source_path(rng, 2000, "emerging", d3)
    values = np.array(list(path.values()))
    moments = d3["stock_flow_adjustment_pp"]["emerging"]
    assert values.min() >= float(moments["p10"]) - 1e-9
    assert values.max() <= float(moments["p90"]) + 1e-9


def test_sfa_source_path_rejects_unknown_source() -> None:
    d3 = dld._yaml(dld.DEFAULT_PATHS["d3"])
    with pytest.raises(ValueError):
        dld.sfa_source_path(np.random.default_rng(0), 5, "nonsense", d3)


def test_stream_index_does_not_collide_with_existing_montecarlo_streams() -> None:
    # src.montecarlo.run() uses independent RNG streams [seed, 1] through [seed, 9]
    # (external, programmes, C7, corruption, privatisation, education, firm
    # distress, W3, SFA). This module must use a different index so it can never
    # perturb any existing Monte Carlo output, even run with the same seed.
    existing_indices = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    assert dld.STREAM_INDEX not in existing_indices


def test_run_s0_draws_draw_zero_is_reproducible_and_central() -> None:
    first = dld.run_s0_draws(n_draws=2, seed=20261020)
    second = dld.run_s0_draws(n_draws=2, seed=20261020)
    pd.testing.assert_frame_equal(first, second)
    draw_zero = first.loc[first["draw"].eq(0)]
    # The central draw is deterministic: re-running with a different seed must
    # not change its values (only the sampled draws, draw > 0, depend on the seed).
    other_seed = dld.run_s0_draws(n_draws=2, seed=999)
    other_zero = other_seed.loc[other_seed["draw"].eq(0)]
    pd.testing.assert_series_equal(
        draw_zero["debt_gdp_s0"].reset_index(drop=True),
        other_zero["debt_gdp_s0"].reset_index(drop=True),
    )
