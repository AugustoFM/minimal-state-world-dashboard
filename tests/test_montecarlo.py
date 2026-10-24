from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import montecarlo as mc

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def context() -> dict:
    return mc.load_context(variants=["default", "pension_only", "efficiency_only",
                                     "investment_also_cut_stress", "compensating_transfers"])


@pytest.fixture(scope="module")
def central(context) -> pd.DataFrame:
    draw = mc.central_draw(context["parameters"], context["inputs"])
    return mc.evaluate_draw(draw, context)


def test_central_draw_reproduces_published_c2_central(central) -> None:
    published = pd.read_csv(ROOT / "data/brazil/macro.csv")
    published = published.loc[published["variant"].eq("central")]
    default = central.loc[central["variant"].eq("default")]
    checked = 0
    for indicator in ("gdp_level_vs_s0_pct", "gdp_per_capita", "debt_gdp", "unemployment_change_pp", "primary_balance_gdp"):
        merged = default.merge(
            published.loc[published["indicator"].eq(indicator)],
            on=["year", "scenario", "persistence"], validate="one_to_one",
        )
        assert len(merged) == len(default)
        np.testing.assert_allclose(merged[indicator], merged["value"], rtol=1e-9, atol=1e-6)
        checked += len(merged)
    assert checked > 0


def test_central_draw_reproduces_published_c4_central(central) -> None:
    published = pd.read_csv(ROOT / "data/brazil/social.csv")
    published = published.loc[published["variant"].eq("central") & published["value"].notna()]
    default = central.loc[central["variant"].eq("default") & central["persistence"].eq("transitory")]
    for indicator in ("real_public_health_spending_pc_change_vs_s0_pct", "infant_mortality_difference_vs_s0",
                      "life_expectancy_difference_vs_s0_years", "hdi_health_index_difference_vs_s0"):
        merged = default.merge(
            published.loc[published["indicator"].eq(indicator)], on=["year", "scenario"], validate="one_to_one",
        )
        assert len(merged) == len(default)
        np.testing.assert_allclose(merged[indicator], merged["value"], rtol=1e-9, atol=1e-9)


def test_s0_differences_are_zero_in_every_draw(central) -> None:
    s0 = central.loc[central["scenario"].eq("S0")]
    for column in ("gdp_level_vs_s0_pct", "gdp_per_capita_vs_s0_pct", "debt_gdp_vs_s0_pp",
                   "infant_mortality_difference_vs_s0", "life_expectancy_difference_vs_s0_years"):
        assert np.allclose(s0[column], 0.0)


def test_variant_shares_follow_definitions(context) -> None:
    configs = context["variant_configs"]
    for name, config in configs.items():
        assert sum(config["package_shares"].values()) == pytest.approx(1.0)
    assert configs["pension_only"]["package_shares"] == {"pension_and_indexation": 1.0}
    comp = configs["compensating_transfers"]["package_shares"]
    assert comp["means_tested_transfers"] == pytest.approx(-0.1)
    assert comp["pension_and_indexation"] == pytest.approx(0.44)
    assert "public_investment" not in configs["investment_also_cut_stress"]["protected"]
    assert configs["default"]["protected"] == context["scenarios"]["protected"]


def test_programme_instrument_paths_are_used_only_in_instrument_mode(context) -> None:
    scenarios = {"scenarios": {"P": {
        "revenue_by_instrument_by_year": {
            "top_income": {1: 0.1, 5: 0.5},
            "tax_expenditures": {1: 0.1, 5: 0.5},
        }
    }}}
    assert mc.scenario_revenue_by_instrument(scenarios, "P", 3) == pytest.approx(
        {"top_income": 0.3, "tax_expenditures": 0.3}
    )
    assert mc.scenario_revenue_by_instrument(scenarios, "S0", 3) is None
    assert context["tax_incidence"] == "instrument"


def test_pension_only_has_no_health_effect(central) -> None:
    pension = central.loc[central["variant"].eq("pension_only") & central["scenario"].isin(["R_mod", "R_amb"])]
    # Health spending per capita still moves with GDP, but no cut lands on health services.
    efficiency = central.loc[central["variant"].eq("efficiency_only") & central["scenario"].isin(["R_mod", "R_amb"])]
    assert (pension["real_public_health_spending_pc_change_vs_s0_pct"].abs()
            < efficiency["real_public_health_spending_pc_change_vs_s0_pct"].abs().to_numpy()).all()


def test_sampling_is_reproducible_and_percentiles_ordered(context) -> None:
    small = dict(context)
    small["variant_configs"] = {"default": context["variant_configs"]["default"]}
    first, draws_a, _ = mc.run(6, seed=7, context=small)
    second, draws_b, _ = mc.run(6, seed=7, context=small)
    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(draws_a, draws_b)
    summary = mc.summarise(first, 6)
    modelled = summary.loc[summary["status"].str.startswith("modelled")]
    assert (modelled["p10"] <= modelled["p50"] + 1e-12).all()
    assert (modelled["p50"] <= modelled["p90"] + 1e-12).all()
    gaps = summary.loc[summary["status"].str.startswith("not_modelled")]
    # C3 is now modelled; remaining gaps are its S1 rows (no package allocation) and any listed in NOT_MODELLED.
    assert set(gaps["indicator"]) <= set(mc.NOT_MODELLED) | set(mc.MICRO_OUTPUTS)
    assert gaps[["p10", "p50", "p90"]].isna().all().all()


def test_sfa_uses_a_dedicated_stream_and_only_perturbs_debt(context) -> None:
    small = dict(context)
    small["variant_configs"] = {"default": context["variant_configs"]["default"]}
    with_sfa, draws_with, _ = mc.run(4, seed=11, context=small)
    without = dict(small)
    without.pop("sfa_changes")
    without_sfa, draws_without, _ = mc.run(4, seed=11, context=without)
    assert "sfa_cumulative_pp" in draws_with.columns
    assert "sfa_cumulative_pp" not in draws_without.columns
    assert draws_with["sfa_cumulative_pp"].abs().gt(0).any()
    # Every other stream (parameters, external C6/C7, education, firm coefficients) is untouched:
    # turning the new [seed, 9] stream on or off does not perturb them.
    unrelated = [
        c for c in draws_with.columns
        if c not in {"sfa_debt_adjustment_by_year", "sfa_cumulative_pp"} and c in draws_without.columns
    ]
    pd.testing.assert_frame_equal(draws_with[unrelated], draws_without[unrelated])
    # Debt differs (directly, and through the risk-premium feedback it drives); GDP-side
    # indicators that do not route through debt stay untouched.
    assert not with_sfa["debt_gdp"].equals(without_sfa["debt_gdp"])
    pd.testing.assert_series_equal(with_sfa["gdp_level_vs_s0_pct"], without_sfa["gdp_level_vs_s0_pct"])


def test_central_draw_has_no_sfa_noise(context) -> None:
    # central_draw/evaluate_draw (used for the published macro.csv/social.csv and for
    # reference_paths' boom/neutral/bust diagnostic) never sets this key, so it is
    # unaffected by SFA regardless of what load_context() provides.
    draw = mc.central_draw(context["parameters"], context["inputs"])
    assert "sfa_debt_adjustment_by_year" not in draw


def test_samples_stay_inside_configured_ranges(context) -> None:
    rng = np.random.default_rng(1)
    params, inputs = context["parameters"], context["inputs"]
    for _ in range(200):
        draw = mc.sample_draw(rng, params, inputs)
        acc = params["fiscal_multipliers_brazil"]["accumulated"]
        for category in mc.MULTIPLIER_CATEGORIES:
            assert acc[category]["low"] <= draw[f"multiplier_{category}"] <= acc[category]["high"]
        for name in mc.MACRO_RANGED:
            entry = inputs["macro"][name]
            assert entry["low"] <= draw[name] <= entry["high"]
        assert (draw["profile_year"], draw["pension_gdp_per_worker_weight"]) in context["grid"]


def test_degenerate_triangular_returns_central() -> None:
    assert mc.triangular(np.random.default_rng(0), 2.0, 2.0, 2.0) == 2.0
    with pytest.raises(ValueError):
        mc.triangular(np.random.default_rng(0), 3.0, 1.0, 2.0)


def test_uniform_leakage_cancels_out_of_comparisons(context) -> None:
    draw = mc.central_draw(context["parameters"], context["inputs"])
    low = mc.evaluate_draw({**draw, "leakage_share": 0.0}, context)
    high = mc.evaluate_draw({**draw, "leakage_share": 0.3}, context)
    for column in ("real_public_health_spending_pc_change_vs_s0_pct", "infant_mortality_difference_vs_s0",
                   "life_expectancy_difference_vs_s0_years", "debt_gdp_vs_s0_pp"):
        np.testing.assert_allclose(low[column], high[column], atol=1e-10)
    # The sensitivity is zero without leakage and favourable (lower IMR) when leakage exists.
    np.testing.assert_allclose(
        low["infant_mortality_difference_vs_s0_leakage_halved"], low["infant_mortality_difference_vs_s0"], atol=1e-10
    )
    s0 = high.loc[high["scenario"].eq("S0")]
    assert (s0["infant_mortality_difference_vs_s0_leakage_halved"] < 0).all()


def test_feedback_columns_present_and_s0_has_no_supply_feedback(central) -> None:
    s0 = central.loc[central["scenario"].eq("S0")]
    for column in ("human_capital_contribution_pct", "health_contribution_pct", "public_capital_contribution_pct"):
        assert np.allclose(s0[column], 0.0, atol=1e-10)
    assert np.allclose(s0["gdp_level_vs_s0_pct_with_feedback"], 0.0, atol=1e-10)
    # Investment stress cuts public capital, so its public-capital contribution is negative for cuts.
    stress = central.loc[central["variant"].eq("investment_also_cut_stress") & central["scenario"].eq("R_amb")
                         & central["horizon"].eq(20)]
    assert (stress["public_capital_contribution_pct"] < 0).all()


def test_ed_and_bk_channels_are_zero_for_s0_and_bk_is_linear(central) -> None:
    s0 = central.loc[central["scenario"].eq("S0")]
    for column in (
        "education_capacity_contribution_pct", "innovation_capacity_contribution_pct",
        "firm_npl_change_vs_s0_pp", "firm_exit_rate_change_vs_s0_pp",
        "employer_share_change_pp", "youth_homicide_rate_change_per_100k",
    ):
        assert np.allclose(s0[column], 0.0, atol=1e-12)
    source = pd.DataFrame({
        "year": [2025, 2026, 2025, 2026],
        "scenario": ["S0", "S0", "R", "R"],
        "sovereign_risk_premium_pp": [0.0, 0.2, 0.0, 0.7],
    })
    result = mc.firm_distress_for_draw(source, {
        "firm_npl_rate_coefficient": 0.46, "firm_exit_rate_coefficient": 0.713,
    })
    row = result.loc[result["scenario"].eq("R") & result["year"].eq(2026)].iloc[0]
    assert row["firm_npl_change_vs_s0_pp"] == pytest.approx(0.46 * 0.5)
    assert row["firm_exit_rate_change_vs_s0_pp"] == pytest.approx(0.713 * 0.5)


MICRO_FILE = ROOT / "data/processed/brazil/microdata/pnadc_2025_c3_input.csv"


@pytest.mark.skipif(not MICRO_FILE.exists(), reason="git-ignored PNAD microdata not present")
def test_distribution_outputs_for_default_variant(central) -> None:
    default = central.loc[central["variant"].eq("default") & central["persistence"].eq("transitory")]
    s0 = default.loc[default["scenario"].eq("S0")]
    assert np.allclose(s0["gini_change_vs_s0_points"], 0.0)
    r_amb = default.loc[default["scenario"].eq("R_amb") & default["horizon"].eq(10)]
    assert (r_amb["gini_change_vs_s0_points"] > 0).all()          # consolidation raises inequality (Ball et al. direction)
    assert (r_amb["poverty_759_change_vs_s0_pp"] > 0).all()
    other = central.loc[central["variant"].eq("pension_only")]
    assert np.allclose(s0[list(mc.MICRO_OUTPUTS)], 0.0)
    assert other[list(mc.MICRO_OUTPUTS)].isna().all().all()
    assert {unit for name, unit in mc.MICRO_OUTPUTS.items() if "poverty_smoothed" in name} == {"pp"}
    assert {unit for name, unit in mc.MICRO_OUTPUTS.items() if "poverty_gap_" in name and "gap_sq" not in name} == {
        "pp_of_line"
    }
