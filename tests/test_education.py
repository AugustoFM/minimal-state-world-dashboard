import math

import numpy as np
import pandas as pd
import pytest

from src import education
from src.feedback import schooling_log_output_effect
from src.macro import load_macro_inputs, macro_input


def test_sidra_parser_preserves_categories_and_geography() -> None:
    result = education.parse_sidra(
        education.RAW / "ibge_sidra_7126_mean_years_schooling_2016_2025.json"
    )
    row = result.loc[
        result["geography"].eq("Brasil") & result["period"].eq("2016")
        & result["Grupo de idade"].eq("15 anos ou mais")
    ].iloc[0]
    assert row["geography_code"] == "1"
    assert row["value"] == 9.3


def test_2024_source_unit_rescale_is_explicit_and_once() -> None:
    raw = pd.DataFrame({"ANO": [2023, 2024], "value": [2.0, 3.0]})
    converted = education.rescale_2024_source_units(raw)
    assert converted["value"].tolist() == [2.0, 3_000_000.0]
    archived = education.rescale_2024_source_units(converted, already_brl=True)
    pd.testing.assert_frame_equal(converted, archived)


def test_composition_arithmetic() -> None:
    start = {"low": 60.0, "high": 40.0}
    end = {"low": 50.0, "high": 50.0}
    rates = {"low": 2.0, "high": 8.0}
    assert education.composition_change(start, end, rates) == pytest.approx(0.6)


def test_capacity_phase_in_and_symmetry() -> None:
    assert education.capacity_phase_in(0.2, 0) == 0
    assert education.capacity_phase_in(0.2, 15) == math.log1p(0.2)
    assert education.capacity_phase_in(0.2, 30) == math.log1p(0.2)
    assert education.capacity_phase_in(-0.2, 15) == -education.capacity_phase_in(0.2, 15)


def _synthetic_population() -> pd.DataFrame:
    return pd.DataFrame([
        {"year": year, "age": age, "population": 1.0}
        for year in range(2025, 2031) for age in range(0, 81)
    ])


def test_zero_inputs_produce_zero_c5_effects() -> None:
    params = load_macro_inputs(education.ROOT / "config/parameters.yaml")
    years = list(range(2025, 2031))
    human, schooling = education.c5_schooling_channel(
        years, _synthetic_population(), np.zeros(len(years)), params
    )
    assert np.allclose(human, 0)
    assert np.allclose(schooling, 0)


def test_c5_spending_dose_is_symmetric_for_increase_and_cut() -> None:
    share = 5.1
    mapped = education.symmetric_c5_spending_change(np.array([0.3, -0.3]), share)
    doses = np.log1p(mapped / share)
    assert doses[0] == pytest.approx(-doses[1])


def test_cohort_replacement_is_exactly_c5_on_synthetic_case() -> None:
    params = load_macro_inputs(education.ROOT / "config/parameters.yaml")
    years = list(range(2025, 2031))
    changes = np.array([0.0, 0.1, 0.1, 0.1, 0.1, 0.1])
    population = _synthetic_population()
    actual_h, actual_s = education.c5_schooling_channel(years, population, changes, params)
    frame = pd.DataFrame({"year": years, "scenario": "ED"})
    returns = params["long_run_feedback"]["human_capital_from_schooling"]["returns_per_year_of_schooling"]
    expected_h, expected_s = schooling_log_output_effect(
        frame, population, pd.Series(changes),
        base_adult_schooling_years=10.4,
        schooling_elasticity=params["social_outcome_elasticities"]["schooling_years_wrt_local_public_spending"]["central"],
        education_share_gdp=params["baseline"]["education_gdp_share"]["central"],
        capital_share=macro_input(params, "capital_share", "central"),
        return_up_to_4=returns["up_to_4_years"],
        return_4_to_8=returns["years_4_to_8"],
        return_above_8=returns["above_8_years"],
    )
    assert np.allclose(actual_h, expected_h)
    assert np.allclose(actual_s, expected_s)


def test_if_mask_finds_compact_and_full_names() -> None:
    frame = pd.DataFrame({
        "UNIDADE ORCAMENTARIA DESCRICAO": [
            "INST.FED.DE EDUC.,CIENC.E TEC.DO AMAZONAS",
            "INSTITUTO FEDERAL DO PARANA - IFPR",
            "CENTRO FED.DE EDUC.TECNOL.DE MINAS GERAIS",
            "COLEGIO PEDRO II",
            "UNIVERSIDADE FEDERAL DO CEARA",
        ],
        "CLASSIFICACAO COFOG DESCRICAO": [""] * 5,
        "CLASSIFICACAO ECONOMICA GFS DESCRICAO": [""] * 5,
        "UNIDADE ORCAMENTARIA": ["26403", "26432", "26257", "26201", "26233"],
    })
    assert education.spending_masks(frame)["federal_network"].tolist() == [True, True, True, True, False]


def test_programme_spending_path_uses_one_fiscal_path_across_parameter_sets() -> None:
    params = load_macro_inputs(education.ROOT / "config/parameters.yaml")
    definition = {
        "package_gaps_by_year": {
            "efficiency_health_education_admin": {2: 0.2, 5: 0.4},
        }
    }
    years = [2025, 2027, 2030, 2045]
    low = education.programme_spending_changes(definition, years, "low", params, 0.1)
    high = education.programme_spending_changes(definition, years, "high", params, 0.1)
    assert np.allclose(low[0], high[0])
    assert np.allclose(low[1], high[1])
    assert low[0][0] == 0
    assert low[0][1] < 0
    assert low[0][2] == pytest.approx(low[0][3])
    assert np.allclose(low[1] / 0.1, low[0] / params["baseline"]["education_gdp_share"]["central"])


def test_ed_config_maps_all_five_p1_paths_and_no_current_law_programme_costs() -> None:
    config = education.yaml.safe_load(education.PATHS["config"].read_text(encoding="utf-8"))
    mapped = {entry["programme_scenario"] for entry in config["scenarios"].values()}
    assert set(education.programs.PROGRAMMES).issubset(mapped)
    for entry in config["scenarios"].values():
        assert "pe_de_meia" not in entry
        assert "if_campi" not in entry
        assert "pbia" not in entry
