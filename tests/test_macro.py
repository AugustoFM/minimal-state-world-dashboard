from __future__ import annotations

import copy

import pandas as pd
import pytest

from src.macro import (
    MissingMacroInput,
    build_spending_paths,
    debt_step,
    growth_accounting_backcast,
    load_macro_inputs,
    multiplier_by_package,
    multiplier_level_effect,
    pwt_implied_investment_rates,
    project_macro,
    nominal_rate_from_real,
    real_rate_from_nominal,
    read_pwt_brazil_growth,
    read_general_government_fiscal_workbook,
    real_interest_rate_for_year,
    run_corner,
    validate_capital_price_basis,
)
from src.baseline import project_baseline, read_yaml


def _scenarios(pace_mod=0.2, pace_amb=0.4):
    return {
        "horizons_years": [1, 2, 3],
        "scenarios": {
            "S0": {},
            "S1": {},
            "R_mod": {
                "pace_pp_gdp_per_year_below_S0": pace_mod,
                "by_year": {1: pace_mod, 2: 2 * pace_mod, 3: 3 * pace_mod},
            },
            "R_amb": {
                "pace_pp_gdp_per_year_below_S0": pace_amb,
                "by_year": {1: pace_amb, 2: 2 * pace_amb, 3: 3 * pace_amb},
            },
        },
        "package_shares": {
            "pension_and_indexation": 0.4,
            "subsidies_and_tax_expenditures": 0.25,
            "efficiency_health_education_admin": 0.2,
            "other_current": 0.15,
        },
        "protected": ["public_investment", "means_tested_transfers"],
    }


def _parameters(multiplier=1.0):
    estimates = {
        name: {
            "horizon_months": 24,
            "low": multiplier,
            "central": multiplier,
            "high": multiplier,
        }
        for name in ("social_benefits", "subsidies", "other_expenditures", "public_investment")
    }
    return {
        "fiscal_multipliers_brazil": {"accumulated": estimates},
        "macro_modelling_choices": {
            "package_to_multiplier_category": {
                "pension_and_indexation": "social_benefits",
                "subsidies_and_tax_expenditures": "subsidies",
                "efficiency_health_education_admin": "efficiency",
                "other_current": "other_expenditures",
                "public_investment": "public_investment",
                "means_tested_transfers": "social_benefits",
            },
            "efficiency_output_effect": {
                "low": multiplier,
                "central": multiplier,
                "high": multiplier,
            },
            "personnel_multiplier": {"rule": "use other_expenditures"},
        },
    }


def _baseline():
    rows = []
    for year in range(2025, 2029):
        for variant in ("low", "central", "high"):
            for scenario, value in (("S0", 40 + year - 2025), ("S1", 40)):
                rows.append(
                    {
                        "year": year,
                        "scenario": scenario,
                        "variant": variant,
                        "category": "total",
                        "spending_pct_gdp": value,
                    }
                )
    return pd.DataFrame(rows)


def _population():
    rows = []
    for year in range(2024, 2029):
        rows.extend(
            [
                {"year": year, "age": 10, "population": 20, "iso3": "BR", "sex": "Ambos"},
                {"year": year, "age": 30, "population": 60, "iso3": "BR", "sex": "Ambos"},
                {"year": year, "age": 70, "population": 20, "iso3": "BR", "sex": "Ambos"},
            ]
        )
    return pd.DataFrame(rows)


def _inputs():
    values = {
        "initial_debt_gdp": 70,
        "effective_nominal_interest_rate": 5,
        "effective_real_interest_rate": 2,
        "revenue_gdp": 35,
        "gdp_deflator_growth": 3,
        "tfp_growth": 1,
        "human_capital_growth": 1,
        "capital_share": 0.3,
        "investment_rate": 18,
        "capital_output_ratio": 3,
        "depreciation_rate": 5,
        "okun_coefficient": 0.2,
        "base_real_gdp": 1000,
        "base_gdp_per_capita": 10_000,
    }
    macro = {
        name: {"low": value, "central": value, "high": value}
        for name, value in values.items()
    }
    macro["initial_debt_gdp"]["year"] = 2025
    macro["base_real_gdp"]["year"] = 2025
    macro["base_gdp_per_capita"]["year"] = 2025
    basis = "test_constant_price_basis"
    macro["investment_rate"]["price_basis_id"] = basis
    macro["capital_output_ratio"]["price_basis_id"] = basis
    return {"macro": macro}


def test_zero_spending_change_gives_zero_effect_and_reform_equals_s0():
    scenarios = _scenarios(0, 0)
    baseline = _baseline()
    baseline.loc[baseline["scenario"].eq("S1"), "spending_pct_gdp"] = baseline.loc[
        baseline["scenario"].eq("S0"), "spending_pct_gdp"
    ].to_numpy()
    result = project_macro(
        baseline, _population(), scenarios, _parameters(), _inputs(), [1, 2, 3]
    )
    gdp = result[result["indicator"].eq("gdp_level_vs_s0_pct")]
    assert (gdp["value"] == 0).all()
    debt = result[result["indicator"].eq("debt_gdp")]
    pivot = debt.pivot_table(
        index=["year", "variant", "persistence"], columns="scenario", values="value"
    )
    assert (pivot["R_mod"] - pivot["S0"]).abs().max() < 1e-10
    assert (pivot["R_amb"] - pivot["S0"]).abs().max() < 1e-10


def test_cut_with_zero_multipliers_lowers_debt():
    result = run_corner(
        _baseline(), _population(), _scenarios(), _parameters(0), _inputs(), "central", "persistent"
    )
    final = result[result["year"].eq(2028)].set_index("scenario")
    assert final.loc["R_mod", "debt_gdp"] < final.loc["S0", "debt_gdp"]
    assert final.loc["R_amb", "debt_gdp"] < final.loc["R_mod", "debt_gdp"]


def test_persistent_loss_at_least_transitory_for_sustained_cut():
    _, gaps = build_spending_paths(_baseline(), _scenarios(), "central")
    multipliers = multiplier_by_package(_parameters(1), "central")
    transitory = multiplier_level_effect(gaps, multipliers, "transitory")
    persistent = multiplier_level_effect(gaps, multipliers, "persistent")
    joined = transitory.merge(persistent, on=["year", "scenario"], suffixes=("_t", "_p"))
    reform = joined[joined["scenario"].eq("R_mod")]
    difference = (
        reform["gdp_level_vs_s0_pct_p"].abs()
        - reform["gdp_level_vs_s0_pct_t"].abs()
    )
    assert (difference >= -1e-12).all()


def test_by_year_reduction_off_pace_line_is_authoritative():
    scenarios = _scenarios()
    scenarios["scenarios"]["R_mod"]["by_year"] = {1: 0.3, 3: 1.1}
    totals, _ = build_spending_paths(_baseline(), scenarios, "central")
    reform = totals.loc[totals["scenario"].eq("R_mod")].set_index("year")
    assert reform.loc[2026, "gap_below_s0_pp"] == pytest.approx(0.3)
    assert reform.loc[2027, "gap_below_s0_pp"] == pytest.approx(0.7)
    assert reform.loc[2028, "gap_below_s0_pp"] == pytest.approx(1.1)


def test_optional_r_max_by_year_path_is_included():
    scenarios = _scenarios()
    scenarios["scenarios"]["R_max"] = {"by_year": {1: 0.5, 3: 1.8}}
    totals, _ = build_spending_paths(_baseline(), scenarios, "central")
    maximum = totals.loc[totals["scenario"].eq("R_max")].set_index("year")
    assert maximum.loc[2027, "gap_below_s0_pp"] == pytest.approx(1.15)


def test_debt_identity_holds_year_by_year():
    debt = 0.70
    for growth, primary_balance in ((0.04, -0.02), (0.06, 0.01), (0.03, 0.00)):
        expected = debt * 1.05 / (1 + growth) - primary_balance
        debt = debt_step(debt, 0.05, growth, primary_balance)
        assert debt == pytest.approx(expected)


def test_real_rate_conversion_round_trips():
    for nominal, inflation in ((10.6923, 13.0), (11.1931, 8.6), (13.0654, 5.73)):
        real = real_rate_from_nominal(nominal, inflation)
        assert nominal_rate_from_real(real, inflation) == pytest.approx(nominal)


def test_zero_real_rate_zero_real_growth_zero_primary_keeps_debt_ratio_constant():
    inflation = 0.037
    nominal_rate = nominal_rate_from_real(0.0, inflation * 100) / 100
    nominal_growth = (1 + 0.0) * (1 + inflation) - 1
    assert debt_step(0.70, nominal_rate, nominal_growth, 0.0) == pytest.approx(0.70)


def test_workbook_primary_balance_reproduces_reported_row_33():
    fiscal = read_general_government_fiscal_workbook(
        "data/raw/brazil/demonstrativos-governo-geral.xlsx", 2025
    )
    assert fiscal["primary_revenue_gdp"] == pytest.approx(38.9699449448)
    assert fiscal["primary_spending_gdp"] == pytest.approx(39.7620150669)
    assert abs(
        fiscal["calculated_primary_balance_gdp"]
        - fiscal["reported_primary_balance_gdp"]
    ) < 0.05


def test_sgs_json_supplies_exact_2025_debt_anchor():
    inputs = load_macro_inputs("config/parameters.yaml")
    assert inputs["derived"]["gross_debt_gdp_history"][2025] == pytest.approx(78.64)
    assert inputs["macro"]["initial_debt_gdp"]["central"] == pytest.approx(78.64)


def test_historical_real_rate_range_uses_same_year_deflators():
    inputs = load_macro_inputs("config/parameters.yaml")
    nominal = inputs["derived"]["implicit_nominal_interest_rate_history"]
    inflation = inputs["derived"]["gdp_deflator_history"]
    real = inputs["derived"]["implicit_real_interest_rate_history"]
    assert set(nominal) == set(inflation) == set(real) == set(range(2021, 2026))
    for year in real:
        assert real[year] == pytest.approx(real_rate_from_nominal(nominal[year], inflation[year]))
    assert inputs["macro"]["effective_real_interest_rate"]["central"] == pytest.approx(
        sorted(real.values())[2]
    )


def test_pwt_backcast_reproduces_average_growth_within_quarter_point():
    pwt = read_pwt_brazil_growth("data/raw/brazil/macro/pwt1001.dta")
    validation = growth_accounting_backcast(pwt, 2000, 2019)
    assert abs(validation["average_error_pp"]) < 0.25
    assert abs(validation["dynamic_capital_average_growth_error_pp"]) < 1e-5


def test_projected_first_year_capital_growth_is_within_pwt_calibration_range():
    pwt = read_pwt_brazil_growth("data/raw/brazil/macro/pwt1001.dta")
    rates = pwt_implied_investment_rates(pwt).set_index("year")
    inputs = load_macro_inputs("config/parameters.yaml")
    projected = (
        inputs["macro"]["investment_rate"]["central"]
        / inputs["macro"]["capital_output_ratio"]["central"]
        - inputs["macro"]["depreciation_rate"]["central"]
    ) / 100
    calibration_growth = pd.concat(
        [
            rates.loc[2016:2019, "capital_growth"],
            rates.loc[2001:2019, "capital_growth"],
            rates.loc[2005:2013, "capital_growth"],
        ]
    )
    assert calibration_growth.min() <= projected <= calibration_growth.max()


def test_projection_investment_and_capital_stock_share_price_basis():
    inputs = load_macro_inputs("config/parameters.yaml")
    assert inputs["macro"]["investment_rate"]["source"]["name"] == "Penn World Table 10.01"
    assert inputs["macro"]["capital_output_ratio"]["source"]["name"] == "Penn World Table 10.01"
    validate_capital_price_basis(inputs)
    mixed = copy.deepcopy(inputs)
    mixed["macro"]["investment_rate"]["price_basis_id"] = "nominal_current_prices"
    with pytest.raises(ValueError, match="same source price basis"):
        validate_capital_price_basis(mixed)


def test_s0_debt_path_equals_textbook_recursion_with_sourced_inputs():
    scenarios = read_yaml("config/scenarios.yaml")
    annual = project_baseline(
        pd.read_csv("data/brazil/fiscal.csv"),
        pd.read_csv("data/brazil/population.csv"),
        pd.read_csv("data/brazil/age_profiles.csv"),
        read_yaml("config/parameters.yaml"),
        range(1, max(scenarios["horizons_years"]) + 1),
    )
    inputs = load_macro_inputs("config/parameters.yaml")
    result = run_corner(
        annual,
        pd.read_csv("data/brazil/population.csv"),
        scenarios,
        read_yaml("config/parameters.yaml"),
        inputs,
        "central",
        "transitory",
    )
    s0 = result.loc[result["scenario"].eq("S0")].sort_values("year")
    base_year = int(s0["year"].min())
    debt = inputs["macro"]["initial_debt_gdp"]["central"] / 100
    interest = nominal_rate_from_real(
        inputs["macro"]["effective_real_interest_rate"]["central"],
        inputs["macro"]["gdp_deflator_growth"]["central"],
    ) / 100
    inflation = inputs["macro"]["gdp_deflator_growth"]["central"] / 100
    previous_nominal_gdp = None
    expected = []
    for row in s0.itertuples():
        nominal_gdp = row.real_gdp * (1 + inflation) ** (row.year - base_year)
        if row.year == base_year:
            expected.append(debt * 100)
            previous_nominal_gdp = nominal_gdp
            continue
        nominal_growth = nominal_gdp / previous_nominal_gdp - 1
        debt = debt * (1 + interest) / (1 + nominal_growth) - row.primary_balance_gdp / 100
        expected.append(debt * 100)
        previous_nominal_gdp = nominal_gdp
    assert s0["debt_gdp"].tolist() == pytest.approx(expected)


def test_sfa_adjustment_is_sign_flipped_uniform_across_scenarios_and_additive():
    baseline, population, scenarios, parameters, inputs = (
        _baseline(), _population(), _scenarios(), _parameters(), _inputs()
    )
    plain = run_corner(baseline, population, scenarios, parameters, inputs, "central", "transitory")
    # D2 convention: positive SFA = observed debt grew more than the identity implies (debt-increasing).
    sfa = {2026: 2.0, 2027: -1.0}
    with_sfa = run_corner(
        baseline, population, scenarios, parameters, inputs, "central", "transitory",
        sfa_adjustment_by_year=sfa,
    )
    s0_plain = plain.loc[plain["scenario"].eq("S0")].set_index("year")["debt_gdp"]
    s0_sfa = with_sfa.loc[with_sfa["scenario"].eq("S0")].set_index("year")["debt_gdp"]
    s1_plain = plain.loc[plain["scenario"].eq("S1")].set_index("year")["debt_gdp"]
    s1_sfa = with_sfa.loc[with_sfa["scenario"].eq("S1")].set_index("year")["debt_gdp"]
    # A positive (debt-increasing) SFA raises debt_gdp by exactly that amount in the year it hits,
    # before any subsequent compounding, and does so identically regardless of scenario.
    assert (s0_sfa.loc[2026] - s0_plain.loc[2026]) == pytest.approx(2.0)
    assert (s1_sfa.loc[2026] - s1_plain.loc[2026]) == pytest.approx(2.0)
    # A scenario-specific debt_adjustment_by_year (e.g. privatisation) stays additive with it.
    adjusted_scenarios = copy.deepcopy(scenarios)
    adjusted_scenarios["scenarios"]["R_mod"]["debt_adjustment_by_year"] = {2026: 0.5}
    with_both = run_corner(
        baseline, population, adjusted_scenarios, parameters, inputs, "central", "transitory",
        sfa_adjustment_by_year=sfa,
    )
    with_adjustment_only = run_corner(
        baseline, population, adjusted_scenarios, parameters, inputs, "central", "transitory",
    )
    r_mod_both = with_both.loc[with_both["scenario"].eq("R_mod")].set_index("year")["debt_gdp"]
    r_mod_adjustment_only = with_adjustment_only.loc[
        with_adjustment_only["scenario"].eq("R_mod")
    ].set_index("year")["debt_gdp"]
    assert (r_mod_both.loc[2026] - r_mod_adjustment_only.loc[2026]) == pytest.approx(2.0)


def test_real_rate_path_zero_and_constant_offsets_match_scalar_rate():
    base = _inputs()
    zero = copy.deepcopy(base)
    zero["derived"] = {"real_rate_path_offset_pp": {2026: 0.0, 2027: 0.0, 2028: 0.0}}
    raised = copy.deepcopy(base)
    raised["macro"]["effective_real_interest_rate"]["central"] += 1.0
    offset = copy.deepcopy(base)
    offset["derived"] = {"real_rate_path_offset_pp": {2026: 1.0, 2027: 1.0, 2028: 1.0}}
    original = run_corner(
        _baseline(), _population(), _scenarios(), _parameters(), base, "central", "transitory"
    )
    with_zero = run_corner(
        _baseline(), _population(), _scenarios(), _parameters(), zero, "central", "transitory"
    )
    with_raised = run_corner(
        _baseline(), _population(), _scenarios(), _parameters(), raised, "central", "transitory"
    )
    with_offset = run_corner(
        _baseline(), _population(), _scenarios(), _parameters(), offset, "central", "transitory"
    )
    pd.testing.assert_frame_equal(original, with_zero)
    pd.testing.assert_series_equal(with_raised["debt_gdp"], with_offset["debt_gdp"])
    assert real_interest_rate_for_year(offset, "central", 2025) == 2.0
    assert real_interest_rate_for_year(offset, "central", 2045) == 3.0


def test_year_varying_rate_offset_enters_the_year_being_stepped():
    inputs = _inputs()
    inputs["derived"] = {"real_rate_path_offset_pp": {2026: 1.0, 2027: 2.0, 2028: 3.0}}
    result = run_corner(
        _baseline(), _population(), _scenarios(), _parameters(), inputs, "central", "transitory"
    )
    s0 = result.loc[result["scenario"].eq("S0")].sort_values("year")
    debt = inputs["macro"]["initial_debt_gdp"]["central"] / 100
    previous_nominal = None
    expected = []
    inflation = inputs["macro"]["gdp_deflator_growth"]["central"] / 100
    for row in s0.itertuples():
        nominal = row.real_gdp * (1 + inflation) ** (row.year - 2025)
        if previous_nominal is not None:
            interest = nominal_rate_from_real(2.0 + inputs["derived"]["real_rate_path_offset_pp"][row.year], 3.0) / 100
            debt = debt_step(debt, interest, nominal / previous_nominal - 1, row.primary_balance_gdp / 100)
        expected.append(debt * 100)
        previous_nominal = nominal
    assert s0["debt_gdp"].tolist() == pytest.approx(expected)


def test_protected_categories_untouched_by_default():
    _, gaps = build_spending_paths(_baseline(), _scenarios(), "central")
    assert set(_scenarios()["protected"]).isdisjoint(gaps["package"])


def test_missing_input_raises():
    inputs = copy.deepcopy(_inputs())
    inputs["macro"]["okun_coefficient"]["central"] = None
    with pytest.raises(MissingMacroInput, match=r"Null macro\.okun_coefficient\.central"):
        project_macro(_baseline(), _population(), _scenarios(), _parameters(), inputs, [1])


def test_allow_missing_skips_only_affected_output_and_records_it():
    inputs = copy.deepcopy(_inputs())
    inputs["macro"]["okun_coefficient"]["central"] = None
    result = project_macro(
        _baseline(),
        _population(),
        _scenarios(),
        _parameters(),
        inputs,
        [1],
        allow_missing=True,
    )
    assert "unemployment_change_pp" not in set(result["indicator"])
    assert set(result["indicator"]) == {
        "gdp_level_vs_s0_pct",
        "gdp_per_capita",
        "s0_potential_real_gdp_growth_pct",
        "debt_gdp",
        "primary_balance_gdp",
    }
    assert "unemployment_change_pp" in result.attrs["skipped_outputs"]


def test_allow_missing_growth_anchor_still_returns_independent_outputs():
    inputs = copy.deepcopy(_inputs())
    inputs["macro"]["base_real_gdp"]["central"] = None
    result = project_macro(
        _baseline(),
        _population(),
        _scenarios(),
        _parameters(),
        inputs,
        [1],
        allow_missing=True,
    )
    assert set(result["indicator"]) == {
        "gdp_level_vs_s0_pct",
        "unemployment_change_pp",
        "primary_balance_gdp",
    }
