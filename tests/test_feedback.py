import math

import pandas as pd
import pytest

from src.feedback import (
    MissingFeedbackInput,
    apply_feedback,
    public_capital_log_output_effect,
    pwt_schooling_phi,
)


def population(start=2025, end=2050):
    return pd.DataFrame(
        [
            {"year": year, "age": age, "population": 1_000.0, "iso3": "BR", "sex": "Ambos"}
            for year in range(start, end + 1)
            for age in range(0, 91)
        ]
    )


def corner(end=2045, reform_spending=-1.0, reform_primary=0.0, reform_debt=50.0):
    rows = []
    for scenario in ("S0", "R_mod"):
        for year in range(2025, end + 1):
            gap = 0.0 if scenario == "S0" or year == 2025 else reform_spending
            rows.append(
                {
                    "year": year,
                    "scenario": scenario,
                    "spending_pct_gdp": 40.0 + gap,
                    "gdp_level_vs_s0_pct": 0.0,
                    "real_gdp": 100.0,
                    "gdp_per_capita": 10.0,
                    "primary_balance_gdp": 0.0 if scenario == "S0" else reform_primary,
                    "debt_gdp": 50.0 if scenario == "S0" else reform_debt,
                }
            )
    return pd.DataFrame(rows)


def kwargs(**updates):
    values = dict(
        base_adult_schooling_years=8.425371752,
        schooling_elasticity=0.0,
        return_up_to_4=0.134,
        return_4_to_8=0.101,
        return_above_8=0.068,
        capital_share=0.422,
        education_share_gdp=5.1,
        health_share_gdp=5.0,
        efficiency_package_share=0.0,
        service_cut_fraction=0.0,
        life_expectancy_change=None,
        health_output_pct_per_year=0.0,
        public_investment_package_share=0.0,
        public_capital_elasticity=0.0,
        initial_public_capital_gdp=0.5,
        public_capital_depreciation=0.05,
        sovereign_risk_bp_per_debt_pp=0.0,
        base_real_interest_rate_pct=0.0,
        inflation_pct=0.0,
        initial_debt_gdp=50.0,
        gini_change=None,
        inequality_growth_pp_per_gini=0.0,
    )
    values.update(updates)
    return values


def test_all_zero_channels_reproduce_corner_exactly():
    source = corner(reform_spending=-1.0, reform_debt=50.0)
    reform = source["scenario"].eq("R_mod")
    source.loc[reform, "gdp_level_vs_s0_pct"] = -0.4013
    source.loc[reform, "gdp_per_capita"] = 9.95987
    result = apply_feedback(source, population(), **kwargs())
    pd.testing.assert_series_equal(
        result["gdp_level_vs_s0_pct_with_feedback"], source["gdp_level_vs_s0_pct"],
        check_names=False,
    )
    pd.testing.assert_series_equal(
        result["gdp_per_capita_with_feedback"], source["gdp_per_capita"], check_names=False,
    )
    pd.testing.assert_series_equal(
        result["debt_gdp_with_feedback"], source["debt_gdp"], check_names=False,
    )


def test_s0_has_zero_feedback_in_every_channel():
    source = corner()
    le = {(row.year, row.scenario): 2.0 for row in source.itertuples()}
    result = apply_feedback(
        source, population(),
        **kwargs(
            schooling_elasticity=0.35, efficiency_package_share=0.2,
            service_cut_fraction=1.0, life_expectancy_change=le,
            health_output_pct_per_year=4.0, public_investment_package_share=0.2,
            public_capital_elasticity=0.1, sovereign_risk_bp_per_debt_pp=5.0,
        ),
    )
    s0 = result.loc[result["scenario"].eq("S0")]
    for channel in ("human_capital", "health", "public_capital", "sovereign_risk_premium", "inequality"):
        assert (s0[f"{channel}_contribution_pct"].abs() < 1e-12).all()
        assert (s0[f"{channel}_debt_contribution_pp"].abs() < 1e-12).all()


def test_schooling_cohort_replacement_and_piecewise_phi():
    assert pwt_schooling_phi(9, 0.134, 0.101, 0.068) - pwt_schooling_phi(8, 0.134, 0.101, 0.068) == pytest.approx(0.068)
    result = apply_feedback(
        corner(), population(),
        **kwargs(
            schooling_elasticity=0.35, efficiency_package_share=1.0,
            service_cut_fraction=1.0,
        ),
    )
    reform = result.loc[result["scenario"].eq("R_mod")].set_index("year")
    assert reform.loc[2025, "adult_mean_schooling_change_years"] == 0
    assert reform.loc[2032, "adult_mean_schooling_change_years"] == 0
    assert reform.loc[2035, "adult_mean_schooling_change_years"] < 0
    assert reform.loc[2045, "adult_mean_schooling_change_years"] < reform.loc[2035, "adult_mean_schooling_change_years"]


def test_health_channel_is_linear_and_zero_at_zero_change():
    source = corner(end=2027)
    le = {(row.year, row.scenario): (0.0 if row.year == 2025 else row.year - 2025) for row in source.itertuples()}
    result = apply_feedback(
        source, population(end=2027),
        **kwargs(life_expectancy_change=le, health_output_pct_per_year=2.0),
    )
    reform = result.loc[result["scenario"].eq("R_mod")].set_index("year")
    assert reform.loc[2025, "health_contribution_pct"] == pytest.approx(0.0)
    assert reform.loc[2026, "health_contribution_pct"] == pytest.approx(2.0)
    assert reform.loc[2027, "health_contribution_pct"] == pytest.approx(4.0)


def test_public_capital_full_depreciation_uses_current_investment_gap():
    source = corner(end=2026)
    gap = pd.Series(0.0, index=source.index)
    reform_idx = source.index[(source["scenario"].eq("R_mod")) & source["year"].eq(2026)][0]
    gap.loc[reform_idx] = -1.0
    effect, status = public_capital_log_output_effect(
        source, gap,
        initial_public_capital_gdp=0.5,
        public_capital_depreciation=1.0,
        public_capital_elasticity=0.1,
    )
    assert status == "modelled"
    # With delta=1, inferred S0 investment is K/GDP=0.5 and the current gap is -0.01.
    assert effect.loc[reform_idx] == pytest.approx(0.1 * math.log((0.5 - 0.01) / 0.5))


def test_risk_premium_amplifies_a_positive_debt_deviation_and_zero_is_unchanged():
    source = corner(end=2030, reform_primary=-2.0, reform_debt=50.0)
    zero = apply_feedback(source, population(end=2030), **kwargs())
    risk = apply_feedback(
        source, population(end=2030),
        **kwargs(sovereign_risk_bp_per_debt_pp=7.0),
    )
    assert zero["debt_gdp_with_feedback"].equals(source["debt_gdp"])
    z = zero.loc[zero["scenario"].eq("R_mod") & zero["year"].eq(2030), "debt_gdp_with_feedback"].iloc[0]
    r = risk.loc[risk["scenario"].eq("R_mod") & risk["year"].eq(2030), "debt_gdp_with_feedback"].iloc[0]
    assert r > z


def test_feedback_constant_rate_offset_matches_raising_the_scalar():
    source = corner(end=2030, reform_primary=-2.0, reform_debt=50.0)
    offset = apply_feedback(
        source, population(end=2030),
        **kwargs(sovereign_risk_bp_per_debt_pp=5.0, real_rate_path_offset_pp={2026: 1.0}),
    )
    scalar = apply_feedback(
        source, population(end=2030),
        **kwargs(sovereign_risk_bp_per_debt_pp=5.0, base_real_interest_rate_pct=1.0),
    )
    pd.testing.assert_series_equal(
        offset["debt_gdp_with_feedback"], scalar["debt_gdp_with_feedback"], check_names=False
    )


def test_equal_small_cut_and_increase_are_opposite_to_first_order():
    cut = corner(end=2035, reform_spending=-0.001)
    increase = corner(end=2035, reform_spending=0.001)
    settings = kwargs(
        schooling_elasticity=0.35, efficiency_package_share=1.0,
        service_cut_fraction=1.0, public_investment_package_share=1.0,
        public_capital_elasticity=0.1, public_capital_depreciation=0.1,
    )
    cut_result = apply_feedback(cut, population(end=2035), **settings)
    increase_result = apply_feedback(increase, population(end=2035), **settings)
    for channel in ("human_capital", "public_capital"):
        c = cut_result.loc[cut_result["scenario"].eq("R_mod") & cut_result["year"].eq(2035), f"{channel}_contribution_pct"].iloc[0]
        i = increase_result.loc[increase_result["scenario"].eq("R_mod") & increase_result["year"].eq(2035), f"{channel}_contribution_pct"].iloc[0]
        assert c == pytest.approx(-i, rel=2e-3, abs=1e-10)
    cut_le = {(row.year, row.scenario): (-0.001 if row.scenario == "R_mod" else 0.0) for row in cut.itertuples()}
    increase_le = {(row.year, row.scenario): (0.001 if row.scenario == "R_mod" else 0.0) for row in increase.itertuples()}
    cut_health = apply_feedback(cut, population(end=2035), **kwargs(life_expectancy_change=cut_le, health_output_pct_per_year=4.0))
    increase_health = apply_feedback(increase, population(end=2035), **kwargs(life_expectancy_change=increase_le, health_output_pct_per_year=4.0))
    c = cut_health.loc[cut_health["scenario"].eq("R_mod") & cut_health["year"].eq(2035), "health_contribution_pct"].iloc[0]
    i = increase_health.loc[increase_health["scenario"].eq("R_mod") & increase_health["year"].eq(2035), "health_contribution_pct"].iloc[0]
    assert c == pytest.approx(-i, rel=1e-10)


def test_missing_public_capital_inputs_raise_unless_allowed():
    with pytest.raises(MissingFeedbackInput, match="IMF ICSD"):
        apply_feedback(
            corner(end=2026), population(end=2026),
            **kwargs(initial_public_capital_gdp=None, public_capital_depreciation=None),
        )
    result = apply_feedback(
        corner(end=2026), population(end=2026),
        **kwargs(initial_public_capital_gdp=None, public_capital_depreciation=None),
        allow_missing=True,
    )
    assert (result["public_capital_contribution_pct"] == 0).all()
    assert result["public_capital_status"].str.startswith("skipped").all()


def test_risk_premium_is_relative_to_base_debt_and_applies_to_s0():
    source = corner(end=2035)
    source.loc[source["scenario"].eq("S0"), "primary_balance_gdp"] = -5.0  # S0 debt rises
    no_premium = apply_feedback(source, population(end=2035), **kwargs())
    premium = apply_feedback(source, population(end=2035), **kwargs(sovereign_risk_bp_per_debt_pp=5.0))
    s0_final = lambda r: r.loc[r["scenario"].eq("S0") & r["year"].eq(2035), "debt_gdp_with_feedback"].item()
    assert s0_final(premium) > s0_final(no_premium)
    s0 = premium.loc[premium["scenario"].eq("S0")]
    assert (s0["sovereign_risk_premium_debt_contribution_pp"] >= -1e-12).all()


def test_risk_premium_deviation_cap_binds():
    source = corner(end=2045)
    source.loc[source["scenario"].eq("S0"), "primary_balance_gdp"] = -10.0  # debt far above base
    capped = apply_feedback(source, population(end=2045), **kwargs(sovereign_risk_bp_per_debt_pp=5.0, risk_premium_cap_pp=20.0))
    uncapped = apply_feedback(source, population(end=2045), **kwargs(sovereign_risk_bp_per_debt_pp=5.0, risk_premium_cap_pp=None))
    final = lambda r: r.loc[r["scenario"].eq("S0") & r["year"].eq(2045), "debt_gdp_with_feedback"].item()
    assert final(capped) < final(uncapped)
