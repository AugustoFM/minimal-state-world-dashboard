from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.micro import (
    calculate_indicators,
    simulate_household_incomes,
    tax_data_context,
    top_income_share,
    weighted_gini,
)


MICRO_PATH = Path("data/processed/brazil/microdata/pnadc_2025_c3_input.csv")


def toy_persons() -> pd.DataFrame:
    return pd.DataFrame({
        "hh_id": ["a", "b", "c", "d"],
        "survey_weight": [1.0, 1.0, 1.0, 1.0],
        "household_condition": [1, 1, 1, 1],
        "household_income_per_capita_brl": [100.0, 200.0, 300.0, 400.0],
        "education_level": [1.0, 1.0, 2.0, 2.0],
        "employment_status": [2.0, 1.0, 1.0, 2.0],
        "labor_income_nominal_brl": [0.0, 200.0, 300.0, 0.0],
        "retirement_pension_income_brl": [100.0, 0.0, 0.0, 0.0],
        "bpc_income_brl": [0.0, 0.0, 0.0, 0.0],
        "bolsa_familia_income_brl": [0.0, 0.0, 0.0, 100.0],
    })


def run_toy(persons: pd.DataFrame, **overrides) -> pd.DataFrame:
    arguments = dict(
        gdp_level_vs_s0_pct=0.0,
        unemployment_change_pp=0.0,
        package_gaps_pp_gdp={},
        revenue_change_pp=0.0,
        nominal_gdp_brl=12_000.0,
        minimum_wage_brl=100.0,
        pension_variant="proportional",
        labour_variant="gdp_only",
        tax_variant="proportional",
        consumption_like_exponent=0.8,
        random_seed=7,
    )
    arguments.update(overrides)
    return simulate_household_incomes(persons, **arguments)


def test_weighted_gini_known_cases() -> None:
    assert weighted_gini(np.ones(4), np.ones(4)) == pytest.approx(0.0)
    assert weighted_gini(np.array([0.0, 0.0, 0.0, 1.0]), np.ones(4)) == pytest.approx(3 / 4)
    assert top_income_share(np.array([0.0, 0.0, 0.0, 1.0]), np.ones(4), 0.25) == pytest.approx(1.0)


def test_no_change_and_zero_tax_leave_everything_unchanged() -> None:
    before = run_toy(toy_persons(), tax_variant="proportional")
    after = run_toy(toy_persons(), revenue_change_pp=0.0, tax_variant="consumption_like")
    assert before["household_income_per_capita_brl"].tolist() == pytest.approx([100, 200, 300, 400])
    pd.testing.assert_frame_equal(before, after)


@pytest.mark.parametrize("variant", ["proportional", "indexation_floor"])
def test_pension_cut_only_lowers_pensioner_household(variant: str) -> None:
    result = run_toy(
        toy_persons(),
        package_gaps_pp_gdp={"pension_and_indexation": 1.0},
        pension_variant=variant,
    ).set_index("hh_id")
    assert result.loc["a", "household_income_per_capita_brl"] == pytest.approx(90.0)
    assert result.loc[["b", "c", "d"], "household_income_per_capita_brl"].tolist() == pytest.approx([200, 300, 400])


def test_means_tested_increase_reduces_low_line_poverty() -> None:
    persons = toy_persons()
    persons.loc[persons.hh_id == "a", "retirement_pension_income_brl"] = 0.0
    persons.loc[persons.hh_id == "a", "bolsa_familia_income_brl"] = 100.0
    base = calculate_indicators(run_toy(persons), {"line": 105})["poverty_headcount_line_pct"]
    changed = calculate_indicators(
        run_toy(persons, package_gaps_pp_gdp={"means_tested_transfers": -1.0}),
        {"line": 105},
    )["poverty_headcount_line_pct"]
    assert changed < base


def test_excluded_conditions_are_outside_income_unit() -> None:
    persons = toy_persons()
    excluded = persons.iloc[[0]].copy()
    excluded["household_condition"] = 17
    excluded["labor_income_nominal_brl"] = 10_000
    excluded["household_income_per_capita_brl"] = np.nan
    persons = pd.concat([persons, excluded], ignore_index=True)
    result = run_toy(persons)
    assert len(result) == 4
    assert result.loc[result.hh_id.eq("a"), "income_unit_size"].iat[0] == 1
    assert result.loc[result.hh_id.eq("a"), "household_income_per_capita_brl"].iat[0] == 100


def test_tax_context_is_explicitly_declarant_based() -> None:
    context = tax_data_context("data/brazil/micro/tax_centiles_2024.csv")
    assert context["tax_data_top_1_share_declarants_not_population_pct"] == pytest.approx(25.068, abs=0.001)
    assert context["tax_data_top_10_share_declarants_not_population_pct"] == pytest.approx(52.195, abs=0.001)


@pytest.mark.skipif(not MICRO_PATH.exists(), reason="git-ignored PNAD C3 input is unavailable")
def test_pnad_no_change_reproduces_validation_anchors() -> None:
    persons = pd.read_csv(MICRO_PATH)
    households = simulate_household_incomes(
        persons,
        gdp_level_vs_s0_pct=0.0,
        unemployment_change_pp=0.0,
        package_gaps_pp_gdp={},
        revenue_change_pp=0.0,
        nominal_gdp_brl=12_738_566_000_000.0,
        minimum_wage_brl=1518.0,
        pension_variant="proportional",
        labour_variant="gdp_only",
        tax_variant="proportional",
        consumption_like_exponent=0.8,
        random_seed=20261020,
    )
    indicators = calculate_indicators(households, {"218": 218, "759": 759})
    assert indicators["gini"] == pytest.approx(0.5112, abs=0.0005)
    assert persons["survey_weight"].sum() == pytest.approx(212.7e6, abs=0.1e6)
    assert indicators["weighted_household_count"] == pytest.approx(79.3e6, abs=0.1e6)
    assert 0 <= indicators["poverty_headcount_218_pct"] <= 100
    assert 0 <= indicators["poverty_headcount_759_pct"] <= 100
