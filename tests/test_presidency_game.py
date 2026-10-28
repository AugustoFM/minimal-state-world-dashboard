from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src import montecarlo
from src.macro import run_corner
from src.presidency_game import INDICATORS, PRIMARY_ACTIONS, PresidencyGameAdapter, validate_action_mappings


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def adapter() -> PresidencyGameAdapter:
    return PresidencyGameAdapter()


def test_action_sequence_is_deterministic(adapter: PresidencyGameAdapter) -> None:
    sequence = (PRIMARY_ACTIONS["Lula"][0],) * 4
    first = adapter.run_path("Lula", sequence, draw=adapter.draw(17))
    second = adapter.run_path("Lula", sequence, draw=adapter.draw(17))
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 4


def test_every_sequence_has_four_rounds() -> None:
    assert all(len(actions) ** 4 == 256 for actions in PRIMARY_ACTIONS.values())
    adapter = PresidencyGameAdapter()
    gaps = adapter.scenario_for_sequence((PRIMARY_ACTIONS["Lula"][0],) * 4, "Lula")["package_gaps_by_year"]
    assert all(value == 0.0 for path in gaps.values() for value in path.values())


def test_debt_is_carried_and_early_action_changes_later_debt(adapter: PresidencyGameAdapter) -> None:
    protected = adapter.run_path("Lula", (PRIMARY_ACTIONS["Lula"][0],) * 4, draw=adapter.draw(19))
    changed = adapter.run_path("Lula", (PRIMARY_ACTIONS["Lula"][1],) * 4, draw=adapter.draw(19))
    assert changed.loc[changed["round"].eq(1), "debt_gdp"].iloc[0] != protected.loc[protected["round"].eq(1), "debt_gdp"].iloc[0]
    assert changed.loc[changed["round"].eq(4), "debt_gdp"].iloc[0] != protected.loc[protected["round"].eq(4), "debt_gdp"].iloc[0]


def test_generated_percentiles_and_units() -> None:
    data = json.loads((ROOT / "presidency-game/game_data.json").read_text(encoding="utf-8"))
    assert set(data["indicators"]) == set(INDICATORS)
    assert all(entry["unit"] for entry in data["indicators"].values())
    for candidate_paths in data["paths"].values():
        assert set(candidate_paths) == {"current_controls", "integrity_sensitivity"}
        for integrity_paths in candidate_paths.values():
            assert len(integrity_paths) == 256
            for percentiles in integrity_paths.values():
                values = {p: percentiles[str(p)]["rounds"] for p in (10, 50, 90)}
                assert all(len(rounds) == 4 for rounds in values.values())
                for indicator in INDICATORS:
                    for index in range(4):
                        assert values[10][index][indicator] <= values[50][index][indicator] + 1e-12
                        assert values[50][index][indicator] <= values[90][index][indicator] + 1e-12

    sequence = "+".join([PRIMARY_ACTIONS["Lula"][0]] * 4)
    current = data["paths"]["Lula"]["current_controls"][sequence]["50"]["rounds"]
    sensitive = data["paths"]["Lula"]["integrity_sensitivity"][sequence]["50"]["rounds"]
    assert any(current[index][indicator] != sensitive[index][indicator] for index in range(4) for indicator in INDICATORS)
    assert data["metadata"]["integrity_variants_in_library"] == ["current_controls", "integrity_sensitivity"]
    assert "integrity_selected_for_library" not in data["actions"]
    assert set(data["metadata"]["action_definitions"]) == {"Lula", "Flavio"}
    assert set(data["metadata"]["action_definitions"]["Lula"]) == set(PRIMARY_ACTIONS["Lula"])
    assert set(data["metadata"]["action_definitions"]["Flavio"]) == set(PRIMARY_ACTIONS["Flavio"])


def test_generated_birth_proxy_metadata_is_derived_from_population() -> None:
    data = json.loads((ROOT / "presidency-game/game_data.json").read_text(encoding="utf-8"))
    births = data["metadata"]["approx_live_births_by_year"]
    years = [str(data["base_year"] + offset) for offset in range(1, 5)]
    assert set(births) == set(years)
    assert all(2_000_000 <= births[year] <= 3_500_000 for year in years)

    population = pd.read_csv(ROOT / "data/brazil/population.csv")
    expected = population.loc[
        population["iso3"].eq("BR")
        & population["age"].eq(0)
        & population["year"].isin(map(int, years))
        & population["sex"].eq("Ambos")
    ].set_index("year")["population"].to_dict()
    assert {int(year): value for year, value in births.items()} == expected


def test_action_mappings_exist() -> None:
    validate_action_mappings()


def test_candidate_actions_diverge(adapter: PresidencyGameAdapter) -> None:
    lula = adapter.run_path("Lula", ("expand_transfers_investment",) * 4, draw=adapter.draw(31))
    flavio = adapter.run_path("Flavio", ("tesourao_light_cuts",) * 4, draw=adapter.draw(31))
    assert not lula.equals(flavio)


def test_no_deviation_reproduces_current_law_s0(adapter: PresidencyGameAdapter) -> None:
    draw = montecarlo.central_draw(adapter.context["parameters"], adapter.context["inputs"])
    actual = adapter.run_path("Lula", ("fiscal_rule",) * 4, draw=draw)
    annual = adapter.context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
    annual = annual.loc[annual["year"].le(adapter.base_year + 4)]
    expected = run_corner(
        annual,
        adapter.context["population"],
        adapter.variant,
        montecarlo.parameters_for_draw(adapter.context["parameters"], draw),
        montecarlo.inputs_for_draw(adapter.context["inputs"], draw),
        "central",
        "transitory",
    )
    expected = expected.loc[expected["scenario"].eq("S0") & expected["year"].gt(adapter.base_year), ["year", "debt_gdp"]]
    pd.testing.assert_frame_equal(
        actual[["year", "debt_gdp"]].reset_index(drop=True), expected.reset_index(drop=True),
        check_exact=False, rtol=1e-9, atol=1e-9,
    )
