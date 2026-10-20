from __future__ import annotations

import copy

import pandas as pd
import pytest

from src.social import (
    MissingSocialParameter,
    apply_spending_elasticity,
    build_up_factor,
    hdi_health_index,
    health_spending_per_capita,
    project_social,
)


def _scenarios(reduction=2.0):
    return {
        "horizons_years": [5, 10],
        "scenarios": {
            "S0": {},
            "S1": {},
            "R_mod": {"by_year": {5: reduction, 10: reduction}},
            "R_amb": {"by_year": {5: 2 * reduction, 10: 2 * reduction}},
        },
        "package_shares": {"efficiency_health_education_admin": 0.2},
    }


def _parameters(service=(0.0, 0.5, 1.0)):
    return {
        "social_modelling_choices": {
            "health_spending_measure": "share times GDP per capita",
            "reduction_hitting_health_education": {
                "allocation": "cofog_2024_proportional",
                "service_cut_fraction": {
                    "low": service[0], "central": service[1], "high": service[2]
                },
            },
            "elasticity_build_up": {
                "rule": "effect ramps linearly to full elasticity over 10 years, then stays"
            },
            "cuts_vs_increases": {"rule": "apply the same elasticity to cuts as to increases"},
            "life_expectancy_to_hdi": {"rule": "UNDP HDI health index = (LE - 20) / (85 - 20)"},
            "not_modelled": [
                "schooling (mean and expected years): no sourced elasticity",
                "physicians per 1,000: no sourced elasticity",
            ],
        },
        "social_outcome_elasticities": {
            "infant_mortality_wrt_public_health_spending": {
                "low": -0.2, "central": -0.1, "high": -0.05
            },
            "life_expectancy_wrt_health_spending": {
                "low": None, "central": 0.04, "high": None
            },
        },
    }


def _baseline():
    rows = []
    for year in (2025, 2030, 2035):
        for scenario in ("S0", "S1"):
            for variant in ("low", "central", "high"):
                rows.extend([
                    {
                        "year": year, "scenario": scenario, "variant": variant,
                        "category": "health", "spending_pct_gdp": 5.0,
                    },
                    {
                        "year": year, "scenario": scenario, "variant": variant,
                        "category": "education", "spending_pct_gdp": 5.0,
                    },
                ])
    return pd.DataFrame(rows)


def _macro(reform_gdp=100.0):
    rows = []
    for year, horizon in ((2030, 5), (2035, 10)):
        for scenario in ("S0", "S1", "R_mod", "R_amb"):
            for variant in ("low", "central", "high"):
                for persistence in ("transitory", "persistent"):
                    rows.append({
                        "year": year, "horizon": horizon, "scenario": scenario,
                        "variant": variant, "persistence": persistence,
                        "indicator": "gdp_per_capita",
                        "value": 100.0 if scenario in ("S0", "S1") else reform_gdp,
                    })
    return pd.DataFrame(rows)


def _inputs():
    return {
        "infant_mortality": {"year": 2024, "value": 12.3},
        "life_expectancy": {"year": 2023, "value": 75.848},
    }


def _base_gdp():
    return {"low": 100.0, "central": 100.0, "high": 100.0}


def _value(result, scenario, horizon, indicator, variant="central"):
    selected = result[
        result["scenario"].eq(scenario)
        & result["horizon"].eq(horizon)
        & result["indicator"].eq(indicator)
        & result["variant"].eq(variant)
    ]
    assert len(selected) == 1
    return float(selected.iloc[0]["value"])


def test_zero_reduction_and_s0_inputs_give_zero_effect_vs_s0():
    result = project_social(
        _baseline(), _macro(), _scenarios(0), _parameters(), _inputs(), _base_gdp(), [5, 10]
    )
    for scenario in ("S0", "R_mod", "R_amb"):
        assert _value(result, scenario, 10, "real_public_health_spending_pc_change_vs_s0_pct") == pytest.approx(0)
        assert _value(result, scenario, 10, "infant_mortality_difference_vs_s0") == pytest.approx(0)


def test_service_cut_fraction_zero_removes_efficiency_outcome_effect():
    result = project_social(
        _baseline(), _macro(), _scenarios(), _parameters(service=(0, 0, 0)),
        _inputs(), _base_gdp(), [5, 10],
    )
    assert _value(result, "R_mod", 10, "real_public_health_spending_pc_change_vs_s0_pct") == pytest.approx(0)
    assert _value(result, "R_mod", 10, "infant_mortality_difference_vs_s0") == pytest.approx(0)
    assert _value(result, "R_mod", 10, "life_expectancy_difference_vs_s0_years") == pytest.approx(0)


def test_health_spending_cut_raises_imr_and_lowers_life_expectancy():
    result = project_social(
        _baseline(), _macro(), _scenarios(), _parameters(), _inputs(), _base_gdp(), [5, 10]
    )
    assert _value(result, "R_mod", 10, "real_public_health_spending_pc_change_vs_s0_pct") < 0
    assert _value(result, "R_mod", 10, "infant_mortality_difference_vs_s0") > 0
    assert _value(result, "R_mod", 10, "life_expectancy_difference_vs_s0_years") < 0


def test_build_up_at_five_years_is_half_ten_year_effect_for_constant_cut():
    five = apply_spending_elasticity(100, -10, -0.1, 5)
    ten = apply_spending_elasticity(100, -10, -0.1, 10)
    assert five - 100 == pytest.approx((ten - 100) / 2)
    assert build_up_factor(15, 10) == 1


def test_hdi_health_index_formula():
    assert hdi_health_index(20) == pytest.approx(0)
    assert hdi_health_index(85) == pytest.approx(1)
    assert hdi_health_index(75.5) == pytest.approx((75.5 - 20) / 65)


def test_not_modelled_indicators_are_present_with_empty_values():
    result = project_social(
        _baseline(), _macro(), _scenarios(), _parameters(), _inputs(), _base_gdp(), [5]
    )
    rows = result[result["status"].str.startswith("not_modelled:")]
    assert set(rows["indicator"]) == {
        "schooling_mean_and_expected_years", "physicians_per_1_000"
    }
    assert rows["value"].isna().all()


def test_missing_required_parameter_raises():
    parameters = copy.deepcopy(_parameters())
    del parameters["social_outcome_elasticities"]["infant_mortality_wrt_public_health_spending"]["central"]
    with pytest.raises(MissingSocialParameter, match="central"):
        project_social(
            _baseline(), _macro(), _scenarios(), parameters, _inputs(), _base_gdp(), [5]
        )


def test_health_spending_measure_service_fraction_zero():
    unchanged = health_spending_per_capita(5, 100, 2, 0.2, 0.5, 0)
    cut = health_spending_per_capita(5, 100, 2, 0.2, 0.5, 1)
    assert unchanged == pytest.approx(5)
    assert cut < unchanged
