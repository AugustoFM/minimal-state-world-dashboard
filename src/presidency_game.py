"""Adapter for the offline four-round presidency policy game.

The adapter deliberately keeps the model's stateful annual chain intact: one
draw and one four-year scenario are passed through C2, C4, and C3.  It does
not add economic coefficients; menu labels resolve to existing scenario
parameters and package mappings.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from src import montecarlo
from src.baseline import read_yaml
from src.macro import run_corner


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_ACTIONS = (
    "protect_services_transfers",
    "administrative_efficiency",
    "cut_subsidies_discretionary",
    "pension_indexation_adjustment",
)
INTEGRITY_CHOICES = ("current_controls", "integrity_sensitivity")
INDICATORS = {
    "debt_to_gdp": ("percent_gdp", "debt_gdp"),
    "unemployment_change": ("percentage_points", "unemployment_change_pp"),
    "infant_mortality": ("per_1000_live_births", "infant_mortality_per_1000"),
    "poverty_change": ("percentage_points", "poverty_218_change_vs_s0_pp"),
    "gini_change": ("gini_points_0_to_100", "gini_change_vs_s0_points"),
}


def approx_live_births_by_year(years: Sequence[int]) -> dict[int, int]:
    """Return Brazil age-0 population by year as an approximate birth proxy.

    Source: data/brazil/population.csv, IBGE Population Projections, 2024
    revision. Age-0 population is a demographic proxy for live births, not an
    exact birth registry count.
    """
    population = pd.read_csv(ROOT / "data/brazil/population.csv")
    age_zero = population.loc[
        population["iso3"].eq("BR") & population["age"].eq(0) & population["year"].isin(years)
    ]
    result: dict[int, int] = {}
    for year in years:
        rows = age_zero.loc[age_zero["year"].eq(year)]
        if rows.empty:
            raise ValueError(f"Missing Brazil age-0 population for game year {year}")
        ambos = rows.loc[rows["sex"].eq("Ambos"), "population"]
        if not ambos.empty:
            value = ambos.sum()
        else:
            value = rows["population"].sum()
        result[int(year)] = int(value)
    return result


class PresidencyGameAdapter:
    """Run one coherent candidate/action path through the existing model."""

    def __init__(self, config_path: str | Path = "config/presidency_game.yaml") -> None:
        self.game_config = read_yaml(config_path)
        self.context = montecarlo.load_context(variants=["default"])
        self.context["tax_incidence"] = "instrument"
        self.base_year = int(self.context["base_year"])
        self.years = [self.base_year + i for i in range(1, int(self.game_config["rounds"]) + 1)]
        # Approximation: age-0 population proxies for live births; this is not
        # an exact birth registry count.
        self.approx_live_births_by_year = approx_live_births_by_year(self.years)
        self.variant = self.context["variant_configs"]["default"]
        self.scenarios = read_yaml("config/scenarios.yaml")
        self.w3_config = read_yaml("config/w3_anticorruption.yaml")

    def _package_shares(self, action: str) -> dict[str, float]:
        if action not in PRIMARY_ACTIONS:
            raise ValueError(f"Unknown primary action: {action}")
        if action == "protect_services_transfers":
            return {}
        if action == "administrative_efficiency":
            return {"efficiency_health_education_admin": 1.0}
        if action == "pension_indexation_adjustment":
            return {"pension_and_indexation": 1.0}
        # The source scenario's package shares are retained intact.  The menu
        # label is a voter-facing simplification of this broader discretionary
        # package, rather than a claim that the full model isolates subsidies.
        return {str(k): float(v) for k, v in self.scenarios["package_shares"].items()}

    def scenario_for_sequence(self, sequence: Sequence[str]) -> dict:
        if len(sequence) != 4 or any(action not in PRIMARY_ACTIONS for action in sequence):
            raise ValueError("A path must contain exactly four primary actions")
        pace = float(self.scenarios["scenarios"]["R_mod"]["pace_pp_gdp_per_year_below_S0"])
        package_names = set(self.scenarios["package_shares"])
        package_names.update({"efficiency_health_education_admin", "pension_and_indexation"})
        package_paths: dict[str, dict[int, float]] = {
            package: {horizon: 0.0 for horizon in range(1, 5)}
            for package in package_names
        }
        for horizon, action in enumerate(sequence, start=1):
            for package, share in self._package_shares(action).items():
                package_paths[package][horizon] = pace * horizon * share
        return {"package_gaps_by_year": package_paths}

    def _integrity_context(self, scenario_name: str, integrity: str) -> dict:
        context = dict(self.context)
        if integrity == "current_controls":
            context.pop("w3", None)
            return context
        if integrity not in INTEGRITY_CHOICES:
            raise ValueError(f"Unknown integrity choice: {integrity}")
        config = copy.deepcopy(self.w3_config)
        config.setdefault("cli_programme_names", {})["neutral"] = "neutral"
        config.setdefault("programme_mapping", {})["neutral"] = ["leakage_reduction"]
        config.setdefault("scenario_programmes", {})[scenario_name] = "neutral"
        context["w3"] = {"selection": "both", "mapping": "programme", "config": config}
        return context

    def draw(self, seed: int, draw_number: int = 0) -> dict:
        rng = np.random.default_rng(seed)
        draw = montecarlo.sample_draw(rng, self.context["parameters"], self.context["inputs"])
        draw.update(montecarlo.central_w3_draw(self.w3_config))
        draw["draw"] = int(draw_number)
        return draw

    def run_path(
        self,
        candidate: str,
        sequence: Sequence[str],
        integrity: str = "current_controls",
        draw: Mapping | None = None,
    ) -> pd.DataFrame:
        """Return annual indicators for one candidate path and one shared draw."""
        scenario_name = f"{candidate}_game"
        variant_scenarios = copy.deepcopy(self.variant)
        variant_scenarios["scenarios"] = {
            **variant_scenarios["scenarios"],
            scenario_name: self.scenario_for_sequence(sequence),
        }
        draw = dict(draw or self.draw(20261020))
        draw_parameters = montecarlo.parameters_for_draw(self.context["parameters"], draw)
        draw_inputs = montecarlo.inputs_for_draw(self.context["inputs"], draw)
        annual = self.context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
        annual = annual.loc[annual["year"].le(self.base_year + len(sequence))].copy()
        # One call is the complete macro path; subsequent calls consume that
        # same path and the same state, rather than sampling annual draws.
        corner = run_corner(
            annual, self.context["population"], variant_scenarios, draw_parameters,
            draw_inputs, "central", self.game_config["model"]["persistence"],
        )
        context = self._integrity_context(scenario_name, integrity)
        all_years = sorted(int(year) for year in corner["year"].unique())
        social = montecarlo.social_for_draw(
            corner, annual, variant_scenarios, draw_parameters, context["base_inputs"], draw,
            all_years, context,
        )
        micro = montecarlo.micro_for_draw(corner, variant_scenarios, draw, context)
        policy = corner.loc[
            corner["scenario"].eq(scenario_name) & corner["year"].gt(self.base_year),
            ["year", *INDICATORS["debt_to_gdp"][1:], "unemployment_change_pp"],
        ].copy()
        policy = policy.rename(columns={"debt_gdp": "debt_gdp"})
        policy = policy.merge(social.loc[social["scenario"].eq(scenario_name), ["year", "infant_mortality_per_1000"]], on="year", validate="one_to_one")
        policy = policy.merge(micro.loc[micro["scenario"].eq(scenario_name), ["year", "poverty_218_change_vs_s0_pp", "gini_change_vs_s0_points"]], on="year", validate="one_to_one")
        policy["candidate"] = candidate
        policy["integrity"] = integrity
        policy["round"] = policy["year"] - self.base_year
        return policy[["candidate", "integrity", "round", "year", "debt_gdp", "unemployment_change_pp", "infant_mortality_per_1000", "poverty_218_change_vs_s0_pp", "gini_change_vs_s0_points"]]


def validate_action_mappings(config_path: str | Path = "config/presidency_game.yaml") -> None:
    """Fail fast if a declared source mapping no longer exists."""
    config = read_yaml(config_path)
    scenarios = read_yaml("config/scenarios.yaml")
    assert "S0" in scenarios["scenarios"] and "R_mod" in scenarios["scenarios"]
    assert "package_shares" in scenarios
    for action in config["primary_actions"].values():
        for source in action["source_parameters"].values():
            if source.endswith("scenarios.S0") or source.endswith("scenarios.R_mod.pace_pp_gdp_per_year_below_S0"):
                continue
            if source.endswith("package_shares") or source.endswith("variant_definitions.efficiency_only") or source.endswith("variant_definitions.pension_only"):
                continue
            raise ValueError(f"Unvalidated config mapping: {source}")
