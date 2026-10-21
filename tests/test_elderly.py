import numpy as np
import pandas as pd
import pytest

from src.elderly import (
    build_elderly_profile,
    build_health_prices,
    build_indexation,
    build_sus,
    read_price_series,
)


def toy_people() -> pd.DataFrame:
    rows = [
        ("a", 1.0, 70, 400.0, 0.0, 300.0, 100.0, 0.0),
        ("a", 1.0, 10, 400.0, 0.0, 0.0, 0.0, 0.0),
        ("b", 2.0, 25, 200.0, 200.0, 0.0, 0.0, 0.0),
        ("c", 1.0, 50, 800.0, 800.0, 0.0, 0.0, 0.0),
    ]
    frame = pd.DataFrame(rows, columns=[
        "hh_id", "survey_weight", "age", "household_income_per_capita_brl",
        "labor_income_nominal_brl", "retirement_pension_income_brl",
        "bpc_income_brl", "bolsa_familia_income_brl",
    ])
    frame["household_condition"] = 1
    for column in (
        "other_program_income_brl", "unemployment_insurance_income_brl",
        "private_transfer_income_brl", "rent_income_brl",
        "financial_and_other_income_brl",
    ):
        frame[column] = 0.0
    return frame


def test_profile_subtracts_household_pension_and_bpc_for_all_members() -> None:
    result = build_elderly_profile(toy_people())
    older = result[(result.row_type == "age_summary") & (result.age_group == "65+")].iloc[0]
    child = result[(result.row_type == "age_summary") & (result.age_group == "0-14")].iloc[0]
    coresident = result[result.row_type == "living_with_65_plus_pension_bpc_recipient"].iloc[0]
    assert older["poverty_759_pct"] == 100.0
    assert older["poverty_218_without_pension_bpc_pct"] == 100.0
    assert child["poverty_218_without_pension_bpc_pct"] == 100.0
    assert coresident["weighted_population"] == pytest.approx(2.0)


def test_indexation_compounds_real_gains_and_inpc_is_flat() -> None:
    result = build_indexation([2030, 2035])
    inpc = result[result.case == "inpc_only"]
    assert inpc["real_benefit_index_2025_100"].tolist() == [100.0, 100.0]
    central = result[result.case == "current_law_1.5_pct_real_gain"].set_index("year")
    assert central.loc[2030, "real_benefit_index_2025_100"] == pytest.approx(100 * 1.015**5)
    assert central.loc[2035, "real_benefit_index_2025_100"] == pytest.approx(100 * 1.015**10)


def test_archived_health_prices_have_complete_common_window() -> None:
    monthly = read_price_series()
    assert set(monthly["index"]) == {"IPCA", "INPC"}
    assert monthly["period"].min() == "201201"
    assert monthly["period"].max() == "202609"
    result = build_health_prices(monthly)
    assert len(result[result.row_type == "observed_series"]) == 10
    exact = result[result.category == "inpc_weights"].iloc[0]
    assert exact["inpc_benefit_real_change_pct_per_year"] == pytest.approx(0.0)


def test_sus_paths_use_age_cost_denominator_without_interpolation() -> None:
    profiles = pd.DataFrame({
        "category": ["health", "health"],
        "profile_year": [2018, 2018],
        "age": [0, 1],
        "relative_cost_per_capita": [1.0, 2.0],
    })
    population = pd.DataFrame({
        "year": [2025, 2025, 2030, 2030],
        "age": [0, 1, 0, 1],
        "population": [100, 100, 80, 120],
        "sex": ["Ambos"] * 4,
        "iso3": ["BR"] * 4,
    })
    baseline = pd.DataFrame({
        "year": [2025, 2030], "scenario": ["S0", "S0"],
        "variant": ["central", "central"], "category": ["health", "health"],
        "spending_pct_gdp": [5.0, 6.0], "profile_year": [2018, 2018],
    })
    macro = pd.DataFrame({
        "year": [2030], "scenario": ["S0"], "variant": ["central"],
        "persistence": ["persistent"], "indicator": ["gdp_per_capita"],
        "value": [110.0],
    })
    result = build_sus(profiles, population, baseline, macro, 100.0)
    assert set(result.year) == {2025, 2030}
    assert len(result) == 6
    constant = result[
        (result.path == "constant_real_from_2025_proxy_for_2027_floor")
        & (result.year == 2030)
    ].iloc[0]
    assert constant["real_spending_per_age_weighted_person_index_2025_100"] == pytest.approx(93.75)
