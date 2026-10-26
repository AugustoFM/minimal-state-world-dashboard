from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import micro
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
        "age": [70, 10, 40, 68],
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


def test_bpc_follows_pension_indexation_by_default_and_can_be_disabled() -> None:
    persons = toy_persons()
    persons.loc[persons.hh_id.eq("d"), "bolsa_familia_income_brl"] = 0.0
    persons.loc[persons.hh_id.eq("d"), "bpc_income_brl"] = 100.0
    with_bpc = run_toy(
        persons,
        package_gaps_pp_gdp={"pension_and_indexation": 1.0},
    ).set_index("hh_id")
    assert with_bpc.loc["a", "household_income_per_capita_brl"] == pytest.approx(95.0)
    assert with_bpc.loc["d", "household_income_per_capita_brl"] == pytest.approx(395.0)
    without_bpc = run_toy(
        persons,
        package_gaps_pp_gdp={"pension_and_indexation": 1.0},
        bpc_follows_pension_indexation=False,
    )
    assert without_bpc.set_index("hh_id").loc["d", "household_income_per_capita_brl"] == 400.0


def test_age_specific_and_older_recipient_household_poverty() -> None:
    households = run_toy(toy_persons())
    result = calculate_indicators(households, {"line": 250.0})
    assert result["poverty_headcount_line_age_0_14_pct"] == pytest.approx(100.0)
    assert result["poverty_headcount_line_age_65_plus_pct"] == pytest.approx(50.0)
    assert result[
        "poverty_headcount_line_living_with_65_plus_pension_bpc_recipient_pct"
    ] == pytest.approx(100.0)


def test_mass_at_line_is_damped_and_gap_changes_continuously() -> None:
    households = pd.DataFrame({
        "survey_weight": np.ones(10),
        "income_unit_size": np.ones(10),
        "household_income_per_capita_brl": [50.0] * 3 + [100.0] * 4 + [150.0] * 3,
    })
    before = calculate_indicators(households, {"line": 100.0})
    after = calculate_indicators(
        households.assign(household_income_per_capita_brl=lambda frame:
                          frame["household_income_per_capita_brl"] - 0.01),
        {"line": 100.0},
    )

    raw_change = after["poverty_headcount_line_pct"] - before["poverty_headcount_line_pct"]
    smoothed_change = after["poverty_smoothed_line_pct"] - before["poverty_smoothed_line_pct"]
    gap_change = after["poverty_gap_line_pct"] - before["poverty_gap_line_pct"]
    assert raw_change == pytest.approx(40.0)
    assert smoothed_change == pytest.approx(40.0 / 21.0)
    assert 0 < gap_change < smoothed_change
    # The four people at the line contribute 0.004 pp; the three already-poor
    # people add 0.003 pp under the same uniform one-cent loss.
    assert gap_change == pytest.approx(0.007)


def test_smoothed_headcount_matches_raw_for_clean_uniform_case() -> None:
    # Ten equally spaced incomes have no observation in the 95-105 smoothing band.
    households = pd.DataFrame({
        "survey_weight": np.ones(10),
        "income_unit_size": np.ones(10),
        "household_income_per_capita_brl": np.arange(5.0, 100.0, 10.0),
    })
    indicators = calculate_indicators(households, {"line": 50.0})
    assert indicators["poverty_headcount_line_pct"] == pytest.approx(50.0)
    assert indicators["poverty_smoothed_line_pct"] == pytest.approx(50.0)


def test_fgt_measures_have_analytic_values_for_all_and_subgroups() -> None:
    households = pd.DataFrame({
        "survey_weight": [1.0, 1.0, 1.0],
        "income_unit_size": [1, 1, 1],
        "household_income_per_capita_brl": [50.0, 100.0, 150.0],
        "age_65_plus_count": [1, 1, 1],
    })
    indicators = calculate_indicators(households, {"line": 100.0})
    assert indicators["poverty_gap_line_pct"] == pytest.approx(100.0 / 6.0)
    assert indicators["poverty_gap_sq_line"] == pytest.approx(1.0 / 12.0)
    assert indicators["poverty_gap_line_age_65_plus_pct"] == pytest.approx(100.0 / 6.0)
    assert indicators["poverty_gap_sq_line_age_65_plus"] == pytest.approx(1.0 / 12.0)


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


def test_tax_cut_relief_follows_incidence_score() -> None:
    # Monthly GDP 1,000; a 1 pp cut returns 10 in proportion to household income.
    households = run_toy(toy_persons(), revenue_change_pp=-1.0)
    assert households["household_income_per_capita_brl"].tolist() == pytest.approx([101, 202, 303, 404])


def test_none_instrument_mapping_is_bit_identical_to_previous_path() -> None:
    previous = run_toy(toy_persons(), revenue_change_pp=0.5, tax_variant="consumption_like")
    explicit_none = run_toy(
        toy_persons(), revenue_change_pp=0.5, tax_variant="consumption_like",
        revenue_change_by_instrument_pp=None,
    )
    pd.testing.assert_frame_equal(previous, explicit_none)


def test_instrument_allocations_sum_to_their_targets_and_are_symmetric() -> None:
    persons = toy_persons()
    base = run_toy(persons).set_index("hh_id")["household_income_per_capita_brl"]
    for instrument in ("consumption", "fuel_energy", "payroll", "tax_expenditures"):
        rise = run_toy(
            persons, revenue_change_by_instrument_pp={instrument: 0.1},
        ).set_index("hh_id")["household_income_per_capita_brl"]
        cut = run_toy(
            persons, revenue_change_by_instrument_pp={instrument: -0.1},
        ).set_index("hh_id")["household_income_per_capita_brl"]
        # Monthly GDP is 1,000, so 0.1 pp is one currency unit.
        assert (base - rise).sum() == pytest.approx(1.0)
        assert (cut - base).sum() == pytest.approx(1.0)
        np.testing.assert_allclose(rise + cut, 2 * base)


def test_top_income_rise_changes_no_household_below_top_one_percent_cut() -> None:
    persons = pd.concat([toy_persons().iloc[[0]].assign(
        hh_id=str(i), survey_weight=1.0, household_income_per_capita_brl=float(i),
        labor_income_nominal_brl=float(i), employment_status=1.0,
        retirement_pension_income_brl=0.0,
    ) for i in range(1, 101)], ignore_index=True)
    base = run_toy(persons).set_index("hh_id")["household_income_per_capita_brl"]
    changed = run_toy(
        persons, nominal_gdp_brl=1_200.0,
        revenue_change_by_instrument_pp={"top_income": 0.1},
    ).set_index("hh_id")["household_income_per_capita_brl"]
    assert changed.loc[[str(i) for i in range(1, 100)]].equals(base.loc[[str(i) for i in range(1, 100)]])
    assert changed.loc["100"] == pytest.approx(99.9)


def test_business_capital_uses_top_income_base_and_unknown_instrument_fails() -> None:
    persons = pd.concat([toy_persons().iloc[[0]].assign(
        hh_id=str(i), survey_weight=1.0, household_income_per_capita_brl=float(i),
    ) for i in range(1, 101)], ignore_index=True)
    base = run_toy(persons).set_index("hh_id")["household_income_per_capita_brl"]
    top_rise = run_toy(persons, nominal_gdp_brl=1_200.0,
                       revenue_change_by_instrument_pp={"top_income": 0.1})
    top = run_toy(persons, nominal_gdp_brl=1_200.0,
                  revenue_change_by_instrument_pp={"top_income": -0.1})
    capital = run_toy(persons, nominal_gdp_brl=1_200.0,
                      revenue_change_by_instrument_pp={"business_capital": -0.1})
    pd.testing.assert_frame_equal(top, capital)
    np.testing.assert_allclose(
        top_rise.set_index("hh_id")["household_income_per_capita_brl"]
        + top.set_index("hh_id")["household_income_per_capita_brl"],
        2 * base,
    )
    with pytest.raises(ValueError, match="Unknown tax instrument"):
        run_toy(toy_persons(), revenue_change_by_instrument_pp={"unknown": 0.1})


def test_optimised_indicators_and_tax_match_references() -> None:
    households = run_toy(toy_persons())
    lines = {"low": 218.0, "high": 759.0}
    expected = micro._calculate_indicators_reference(households, lines)
    actual = calculate_indicators(households, lines)
    assert actual == pytest.approx(expected, nan_ok=True, abs=1e-12)
    rng = np.random.default_rng(17)
    capacity = rng.uniform(1, 1000, 1000)
    score = rng.uniform(0.1, 500, 1000)
    weights = rng.uniform(0.1, 20, 1000)
    target = float(np.sum(capacity * weights) * 0.4)
    old = micro._tax_burden_reference(capacity, score, weights, target)
    new = micro._tax_burden(capacity, score, weights, target)
    np.testing.assert_allclose(new, old, atol=1e-9, rtol=1e-12)


# --- IY1: interest-income / inflation-tax distribution channels (off by default) -----------------

def test_iy1_channels_off_by_default() -> None:
    before = run_toy(toy_persons())
    after = run_toy(toy_persons(), capital_income_windfall_brl_monthly=0.0, transfer_inflation_erosion_pct=0.0)
    pd.testing.assert_frame_equal(before, after)


def test_iy1_windfall_requires_both_share_args() -> None:
    with pytest.raises(ValueError, match="capital_income_windfall_brl_monthly requires"):
        run_toy(toy_persons(), capital_income_windfall_brl_monthly=10.0, capital_income_top1_share_pct=70.0)


def test_weighted_percentile_rank_matches_hand_computation() -> None:
    # Four equally-weighted observations: midpoint rule gives ranks 12.5/37.5/62.5/87.5.
    rank = micro._weighted_percentile_rank(np.array([100.0, 200.0, 300.0, 400.0]), np.ones(4))
    np.testing.assert_allclose(rank, [12.5, 37.5, 62.5, 87.5])


def test_allocate_by_income_band_conserves_the_pool_and_is_proportional_to_income() -> None:
    household_total = np.array([100.0, 300.0, 600.0])
    hh_weight = np.array([2.0, 1.0, 1.0])
    band_mask = np.array([True, True, False])
    allocation = micro._allocate_by_income_band(1000.0, band_mask, household_total, hh_weight)
    assert allocation[2] == 0.0
    # Re-weighting by hh_weight and summing must reproduce the pool exactly.
    assert float(np.sum(allocation * hh_weight)) == pytest.approx(1000.0)
    # Proportional to each household's own income within the band (not to its weight).
    assert allocation[1] / allocation[0] == pytest.approx(300.0 / 100.0)


def test_iy1_windfall_is_conserved_and_concentrated_at_the_top() -> None:
    rng = np.random.default_rng(3)
    n = 500
    persons = pd.DataFrame({
        "hh_id": [f"h{i}" for i in range(n)],
        "survey_weight": rng.uniform(1.0, 5.0, n),
        "household_condition": np.ones(n, dtype=int),
        "household_income_per_capita_brl": rng.uniform(100.0, 10_000.0, n),
        "age": np.full(n, 40.0),
        "education_level": np.ones(n),
        "employment_status": np.ones(n),
        "labor_income_nominal_brl": np.zeros(n),
        "retirement_pension_income_brl": np.zeros(n),
        "bpc_income_brl": np.zeros(n),
        "bolsa_familia_income_brl": np.zeros(n),
    })
    pool = 50_000.0
    result = run_toy(
        persons, capital_income_windfall_brl_monthly=pool,
        capital_income_top1_share_pct=50.0, capital_income_top10_share_pct=90.0,
    ).set_index("hh_id")
    baseline = run_toy(persons).set_index("hh_id")
    delta = result["household_income_per_capita_brl"] - baseline["household_income_per_capita_brl"]
    weight = persons.set_index("hh_id")["survey_weight"]
    assert float((delta * weight).sum()) == pytest.approx(pool, rel=1e-6)
    richest = baseline["household_income_per_capita_brl"].idxmax()
    poorest = baseline["household_income_per_capita_brl"].idxmin()
    assert delta.loc[richest] > delta.loc[poorest]


def test_iy1_transfer_inflation_erosion_shrinks_only_bolsa_by_the_given_fraction() -> None:
    persons = toy_persons()
    baseline = run_toy(persons).set_index("hh_id")
    eroded = run_toy(persons, transfer_inflation_erosion_pct=10.0).set_index("hh_id")
    # Only household d has a Bolsa Familia amount (100.0); erosion removes 10% of it.
    assert eroded.loc["d", "household_income_per_capita_brl"] == pytest.approx(
        baseline.loc["d", "household_income_per_capita_brl"] - 10.0
    )
    for hh in ("a", "b", "c"):
        assert eroded.loc[hh, "household_income_per_capita_brl"] == pytest.approx(
            baseline.loc[hh, "household_income_per_capita_brl"]
        )
