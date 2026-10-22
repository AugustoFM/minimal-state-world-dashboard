from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import pytest

from src import corruption, micro, montecarlo as mc, programs
from src.baseline import read_yaml


W3 = read_yaml("config/w3_anticorruption.yaml")
PROGRAMMES = read_yaml("config/programs_2026.yaml")


@pytest.fixture(scope="module")
def programme_context() -> dict:
    context = mc.load_context(variants=["default"])
    context["micro"] = None
    context["programmes"] = PROGRAMMES
    context["programme_common_composition"] = False
    return context


def central_programme_draw(context: dict) -> dict:
    draw = mc.central_draw(context["parameters"], context["inputs"])
    draw.update(programs.central_programme_draw(PROGRAMMES, context["parameters"]))
    draw["privatisation_non_tax_revenue_by_year"] = {20: 0.0}
    return draw


def test_off_path_has_no_w3_columns_and_is_bit_identical(programme_context) -> None:
    draw = central_programme_draw(programme_context)
    first = mc.evaluate_draw(draw, programme_context)
    explicit_none = copy.copy(programme_context)  # CLI 'none' deliberately adds no W3 context.
    second = mc.evaluate_draw(draw, explicit_none)
    pd.testing.assert_frame_equal(first, second, check_exact=True)
    assert not (set(first.columns) & set(mc.W3_OUTPUTS))


def test_lula_switch_changes_only_lula_rows_and_channel_signs(programme_context) -> None:
    base_draw = central_programme_draw(programme_context)
    base = mc.evaluate_draw(base_draw, programme_context)
    active_context = copy.copy(programme_context)
    active_context["w3"] = {"selection": "lula", "mapping": "programme", "config": W3}
    active_draw = {**base_draw, **mc.central_w3_draw(W3)}
    active = mc.evaluate_draw(active_draw, active_context)

    existing = list(mc.MACRO_OUTPUTS) + list(mc.SOCIAL_OUTPUTS) + list(mc.MICRO_OUTPUTS)
    unchanged = ~active["scenario"].str.startswith("P_lula_")
    pd.testing.assert_frame_equal(
        base.loc[unchanged, existing].reset_index(drop=True),
        active.loc[unchanged, existing].reset_index(drop=True),
        check_exact=True,
    )
    lula = active["scenario"].str.startswith("P_lula_")
    assert (active.loc[lula, "anticorruption_leakage_contribution_services_pct"] > 0).all()
    assert (active.loc[lula, "anticorruption_leakage_contribution_infant_mortality_per_1000"] < 0).all()
    assert (active.loc[lula, "anticorruption_leakage_contribution_life_expectancy_years"] > 0).all()
    assert np.allclose(active.loc[~lula, "anticorruption_leakage_contribution_services_pct"], 0.0)


def test_procurement_full_mapping_is_symmetric_and_positive(programme_context) -> None:
    context = copy.copy(programme_context)
    context["w3"] = {"selection": "both", "mapping": "full", "config": W3}
    draw = {**central_programme_draw(context), **mc.central_w3_draw(W3)}
    annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
    definitions = mc.with_programmes(
        context["variant_configs"]["default"], annual,
        mc.inputs_for_draw(context["inputs"], draw), draw, context,
    )
    savings = [mc.w3_fiscal_saving(definitions, scenario, 5) for scenario in programs.PROGRAMMES]
    assert min(savings) > 0
    assert max(savings) == pytest.approx(min(savings))


def test_w3_parameters_are_selection_independent() -> None:
    lula = mc.sample_w3_draw(np.random.default_rng([41, 8]), W3)
    flavio = mc.sample_w3_draw(np.random.default_rng([41, 8]), W3)
    both = mc.sample_w3_draw(np.random.default_rng([41, 8]), W3)
    assert lula == flavio == both


def test_event_thinning_is_paired_and_never_adds_a_loss() -> None:
    config = corruption.load_config("config/corruption_proposed.yaml")
    shared = pd.DataFrame({
        "corruption_event": [1, 0, 1, 0, 0],
        "corruption_event_magnitude_pct": [2.0, 0.0, 3.0, 0.0, 0.0],
    })
    uniforms = np.array([0.1, 0.9])
    first = corruption.thinned_path(shared, 0.5, uniforms, config)
    second = corruption.thinned_path(shared, 0.5, uniforms, config)
    original = corruption.level_path(np.array([1, 0, 1, 0, 0], dtype=bool), np.array([2.0, 3.0]), 5, 2, 4)
    np.testing.assert_array_equal(first, second)
    assert np.all(first >= original)


def test_inss_protection_reaches_only_pension_recipients_aged_65_plus() -> None:
    persons = pd.DataFrame({
        "hh_id": ["old", "young", "bpc"],
        "survey_weight": [1.0, 1.0, 1.0],
        "household_condition": [1, 1, 1],
        "household_income_per_capita_brl": [100.0, 100.0, 100.0],
        "age": [70, 60, 75],
        "education_level": [1.0, 1.0, 1.0],
        "employment_status": [2.0, 2.0, 2.0],
        "labor_income_nominal_brl": [0.0, 0.0, 0.0],
        "retirement_pension_income_brl": [100.0, 100.0, 0.0],
        "bpc_income_brl": [0.0, 0.0, 100.0],
        "bolsa_familia_income_brl": [0.0, 0.0, 0.0],
    })
    result = micro.simulate_household_incomes(
        persons, gdp_level_vs_s0_pct=0.0, unemployment_change_pp=0.0,
        package_gaps_pp_gdp={}, revenue_change_pp=0.0, nominal_gdp_brl=12000.0,
        minimum_wage_brl=100.0, pension_variant="proportional", labour_variant="gdp_only",
        tax_variant="proportional", consumption_like_exponent=0.8, random_seed=0,
        pensioner_income_protection_brl_annual=120.0,
    ).set_index("hh_id")
    assert result.loc["old", "household_income_per_capita_brl"] == pytest.approx(110.0)
    assert result.loc["young", "household_income_per_capita_brl"] == pytest.approx(100.0)
    assert result.loc["bpc", "household_income_per_capita_brl"] == pytest.approx(100.0)
