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
from src.programs import _incidence_shares


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_ACTIONS = {
    "Lula": (
        "fiscal_rule",
        "expand_transfers_investment",
        "tax_justice_revenue",
        "continue_record_trend",
    ),
    "Flavio": (
        "tesourao_light_cuts",
        "deeper_cuts",
        "brasil_mais_barato_tax_cuts",
        "resume_privatisation",
    ),
}
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
        self._corner_cache: dict[tuple, tuple[pd.DataFrame, dict]] = {}
        self.scenarios = read_yaml("config/scenarios.yaml")
        self.programmes = read_yaml("config/programs_2026.yaml")
        self.model_parameters = self.programmes["model_parameters"]
        self.w3_config = read_yaml("config/w3_anticorruption.yaml")

    @staticmethod
    def _midpoint(item: Mapping) -> float:
        low, high = item["range_pp_gdp"]
        return (float(low) + float(high)) / 2.0

    def _programme_item(self, candidate: str, item_id: str) -> Mapping:
        programme = "lula_pt" if candidate == "Lula" else "flavio_bolsonaro_pl"
        return next(item for item in self.programmes["programmes"][programme]["items"] if item["id"] == item_id)

    def _package_shares(self, candidate: str, action: str) -> dict[str, float]:
        if action not in PRIMARY_ACTIONS[candidate]:
            raise ValueError(f"Unknown {candidate} primary action: {action}")
        if candidate == "Lula":
            if action == "expand_transfers_investment":
                return {"means_tested_transfers": -self._midpoint(self._programme_item(candidate, "L3_transfers"))}
            if action == "continue_record_trend":
                return {
                    str(k): -float(v) * float(self.model_parameters["lula_record_trend"]["spending_pp_gdp_per_year"]["value"])
                    for k, v in self.model_parameters["lula_record_trend"]["composition"]["shares"].items()
                }
            return {}
        if action == "tesourao_light_cuts":
            item = self.model_parameters["flavio_cut_scenarios"]["low"]
            return {str(k): float(v) * float(item["cut_pp_gdp_by_end_of_term"]) for k, v in item["composition"].items()}
        if action == "deeper_cuts":
            item = self.model_parameters["flavio_cut_scenarios"]["mid"]
            return {str(k): float(v) * float(item["cut_pp_gdp_by_end_of_term"]) for k, v in item["composition"].items()}
        return {}

    def scenario_for_sequence(self, sequence: Sequence[str], candidate: str = "Lula") -> dict:
        if candidate not in PRIMARY_ACTIONS:
            raise ValueError(f"Unknown candidate: {candidate}")
        if len(sequence) != 4 or any(action not in PRIMARY_ACTIONS[candidate] for action in sequence):
            raise ValueError("A path must contain exactly four primary actions")
        package_names = set(self.scenarios["package_shares"])
        package_names.update({"efficiency_health_education_admin", "pension_and_indexation", "means_tested_transfers", "public_investment"})
        package_paths: dict[str, dict[int, float]] = {
            package: {horizon: 0.0 for horizon in range(1, 5)}
            for package in package_names
        }
        revenue_by_year: dict[int, float] = {horizon: 0.0 for horizon in range(1, 5)}
        revenue_by_instrument_by_year: dict[str, dict[int, float]] = {}
        debt_adjustment_by_year: dict[int, float] = {horizon: 0.0 for horizon in range(1, 5)}
        non_tax_revenue_by_year: dict[int, float] = {horizon: 0.0 for horizon in range(1, 5)}
        if candidate == "Lula":
            revenue_item = self._programme_item(candidate, "L5_tax")
            revenue_instruments = _incidence_shares(self.programmes, "lula_pt", "L5_tax")
        else:
            revenue_item = self._programme_item(candidate, "F3_tax_cuts")
            revenue_instruments = _incidence_shares(self.programmes, "flavio_bolsonaro_pl", "F3_tax_cuts")
        revenue_by_instrument_by_year = {
            str(instrument): {horizon: 0.0 for horizon in range(1, 5)}
            for instrument in revenue_instruments
        }
        for horizon, action in enumerate(sequence, start=1):
            if candidate == "Lula" and action == "tax_justice_revenue":
                value = self._midpoint(revenue_item) * horizon
                revenue_by_year[horizon] = revenue_by_year.get(horizon, 0.0) + value
                for instrument, share in revenue_instruments.items():
                    revenue_by_instrument_by_year[instrument][horizon] = value * float(share)
            elif candidate == "Flavio" and action == "brasil_mais_barato_tax_cuts":
                value = self._midpoint(revenue_item) * horizon
                revenue_by_year[horizon] = revenue_by_year.get(horizon, 0.0) + value
                for instrument, share in revenue_instruments.items():
                    revenue_by_instrument_by_year[instrument][horizon] = value * float(share)
            elif candidate == "Flavio" and action == "resume_privatisation":
                # Central programme draw: F5 midpoint spread evenly across the four sale years.
                debt_adjustment_by_year[horizon] = self._midpoint(self._programme_item(candidate, "F5_privatisation")) / 4.0 * horizon
            else:
                for package, pace in self._package_shares(candidate, action).items():
                    package_paths[package][horizon] = pace * horizon
        # The central programme draw has no sourced lost-dividend estimate;
        # keep the path explicitly zero rather than inventing non-tax revenue.
        return {
            "package_gaps_by_year": package_paths,
            "revenue_by_year": revenue_by_year,
            "revenue_by_instrument_by_year": revenue_by_instrument_by_year,
            "debt_adjustment_by_year": debt_adjustment_by_year,
            "non_tax_revenue_by_year": non_tax_revenue_by_year,
        }

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
            scenario_name: self.scenario_for_sequence(sequence, candidate),
        }
        draw = dict(draw or self.draw(20261020))
        draw_parameters = montecarlo.parameters_for_draw(self.context["parameters"], draw)
        draw_inputs = montecarlo.inputs_for_draw(self.context["inputs"], draw)
        annual = self.context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
        annual = annual.loc[annual["year"].le(self.base_year + len(sequence))].copy()
        # One call is the complete macro path; subsequent calls consume that
        # same path and the same state, rather than sampling annual draws.
        cache_key = (candidate, tuple(sequence), int(draw.get("draw", -1)))
        cached = self._corner_cache.pop(cache_key, None) if integrity == "integrity_sensitivity" else None
        if cached is None:
            corner = run_corner(
                annual, self.context["population"], variant_scenarios, draw_parameters,
                draw_inputs, "central", self.game_config["model"]["persistence"],
            )
            if integrity == "current_controls":
                self._corner_cache[cache_key] = (corner, variant_scenarios)
        else:
            corner, variant_scenarios = cached
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
    programmes = read_yaml("config/programs_2026.yaml")
    assert "S0" in scenarios["scenarios"] and "R_mod" in scenarios["scenarios"]
    assert "package_shares" in scenarios
    for candidate, actions in config["primary_actions"].items():
        programme = "lula_pt" if candidate == "Lula" else "flavio_bolsonaro_pl"
        item_ids = {item["id"] for item in programmes["programmes"][programme]["items"]}
        for action in actions.values():
            for item_id in action["source_items"]:
                if item_id not in item_ids:
                    raise ValueError(f"Unvalidated programme item: {candidate}.{item_id}")
        for source in action["source_parameters"].values():
            if source.endswith("scenarios.S0") or source.endswith("scenarios.R_mod.pace_pp_gdp_per_year_below_S0"):
                continue
            if source.startswith("config/programs_2026.yaml:"):
                continue
            if source.endswith("package_shares") or source.endswith("variant_definitions.efficiency_only") or source.endswith("variant_definitions.pension_only"):
                continue
            raise ValueError(f"Unvalidated config mapping: {source}")
