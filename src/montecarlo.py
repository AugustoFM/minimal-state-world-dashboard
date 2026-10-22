"""Monte Carlo over parameter ranges, scenarios and composition variants (task D1).

Each draw samples every ranged parameter the C1 -> C2 -> C4 chain uses, then
runs the existing model code unchanged: the sampled value is written into a
copy of the configuration with low = central = high, and the C1/C2 functions
are evaluated at their "central" corner. Differences between a scenario and
S0 are taken within each draw (paired), so their percentiles describe the
policy effect under shared parameter uncertainty.

Percentiles reflect parameter uncertainty only, not forecast error, external
shocks (C6) or long-run feedback (C5). Distribution indicators wait for C3 and
are written as `not_modelled` rows.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from src import corruption, education, external, feedback, micro, privatisation, programs, social
from src.baseline import project_baseline, read_yaml
from src.macro import _interpolate_by_year
from src.macro import PERSISTENCE_VARIANTS, load_macro_inputs, run_corner


SEED = 20261020
N_DRAWS = 1000
PERCENTILES = (10, 50, 90)
WEIGHT_GRID_STEP = 0.025
SCENARIO_ORDER = ("S0", "S1", "R_mod", "R_amb", "R_max")
MULTIPLIER_CATEGORIES = ("public_investment", "social_benefits", "subsidies", "other_expenditures")
MACRO_RANGED = (
    "effective_real_interest_rate", "gdp_deflator_growth", "tfp_growth",
    "human_capital_growth", "investment_rate", "okun_coefficient",
)
NOT_MODELLED: dict[str, str] = {}
MICRO_VARIANT = "default"          # C3 runs for the default composition only (runtime)
MICRO_SCENARIOS_EXCLUDED = {"S1"}
PROGRAMME_VARIANT = "default"      # P1 programme scenarios carry their own composition; added once  # C3 has no package allocation for S1's offset
MICRO_OUTPUTS = {
    "gini_change_vs_s0_points": "gini_points_0_100",
    "poverty_218_change_vs_s0_pp": "pp",
    "poverty_759_change_vs_s0_pp": "pp",
    "poverty_218_age_0_14_change_vs_s0_pp": "pp",
    "poverty_218_age_65_plus_change_vs_s0_pp": "pp",
    "poverty_218_with_65_plus_recipient_change_vs_s0_pp": "pp",
    "poverty_759_age_0_14_change_vs_s0_pp": "pp",
    "poverty_759_age_65_plus_change_vs_s0_pp": "pp",
    "poverty_759_with_65_plus_recipient_change_vs_s0_pp": "pp",
    "poverty_smoothed_218_change_vs_s0_pp": "pp",
    "poverty_smoothed_218_age_0_14_change_vs_s0_pp": "pp",
    "poverty_smoothed_218_age_65_plus_change_vs_s0_pp": "pp",
    "poverty_smoothed_218_with_65_plus_recipient_change_vs_s0_pp": "pp",
    "poverty_smoothed_759_change_vs_s0_pp": "pp",
    "poverty_smoothed_759_age_0_14_change_vs_s0_pp": "pp",
    "poverty_smoothed_759_age_65_plus_change_vs_s0_pp": "pp",
    "poverty_smoothed_759_with_65_plus_recipient_change_vs_s0_pp": "pp",
    "poverty_gap_218_change_vs_s0_pp": "pp_of_line",
    "poverty_gap_218_age_0_14_change_vs_s0_pp": "pp_of_line",
    "poverty_gap_218_age_65_plus_change_vs_s0_pp": "pp_of_line",
    "poverty_gap_218_with_65_plus_recipient_change_vs_s0_pp": "pp_of_line",
    "poverty_gap_759_change_vs_s0_pp": "pp_of_line",
    "poverty_gap_759_age_0_14_change_vs_s0_pp": "pp_of_line",
    "poverty_gap_759_age_65_plus_change_vs_s0_pp": "pp_of_line",
    "poverty_gap_759_with_65_plus_recipient_change_vs_s0_pp": "pp_of_line",
    "poverty_gap_sq_218_change_vs_s0": "fgt2_index",
    "poverty_gap_sq_759_change_vs_s0": "fgt2_index",
    "top1_share_survey_change_vs_s0_pp": "pp",
    "top10_share_survey_change_vs_s0_pp": "pp",
}
MACRO_OUTPUTS = {
    "spending_pct_gdp": "pct_gdp",
    "gdp_level_vs_s0_pct": "percent",
    "gdp_per_capita": "brl_2025",
    "gdp_per_capita_vs_s0_pct": "percent",
    "debt_gdp": "pct_gdp",
    "debt_gdp_vs_s0_pp": "pp_gdp",
    "unemployment_change_pp": "pp",
    "primary_balance_gdp": "pct_gdp",
    # C6: same external path for every scenario in a draw (src/external.py)
    "external_gdp_level_pct": "percent",
    "gdp_per_capita_with_external_vs_s0_pct": "percent",
    "debt_gdp_with_external": "pct_gdp",
    "debt_gdp_with_external_vs_s0_pp": "pp_gdp",
    "inflation_with_external_pct": "percent",
    "corruption_gdp_level_pct": "percent",
    # C5 long-run feedback (src/feedback.py); no external path, same corner as above
    "gdp_level_vs_s0_pct_with_feedback": "percent",
    "gdp_per_capita_with_feedback_vs_s0_pct": "percent",
    "debt_gdp_with_feedback": "pct_gdp",
    "debt_gdp_with_feedback_vs_s0_pp": "pp_gdp",
    "adult_mean_schooling_change_years": "years",
    "human_capital_contribution_pct": "percent",
    "health_contribution_pct": "percent",
    "public_capital_contribution_pct": "percent",
    "education_capacity_contribution_pct": "percent",
    "innovation_capacity_contribution_pct": "percent",
    "sovereign_risk_premium_debt_contribution_pp": "pp_gdp",
    "sovereign_risk_premium_pp": "pp",
    "firm_npl_change_vs_s0_pp": "pp",
    "firm_exit_rate_change_vs_s0_pp": "pp",
}
SOCIAL_OUTPUTS = {
    "real_public_health_spending_pc_change_vs_s0_pct": "percent",
    "infant_mortality_per_1000": "per_1000_live_births",
    "infant_mortality_difference_vs_s0": "per_1000_live_births",
    "life_expectancy_difference_vs_s0_years": "years",
    "hdi_health_index_difference_vs_s0": "index_0_to_1",
    # Governance sensitivity: the scenario also removes part of the leakage
    # (governance.leakage_reduction_sensitivity), compared with S0 as is.
    "effective_health_services_pc_change_vs_s0_pct_leakage_halved": "percent",
    "infant_mortality_difference_vs_s0_leakage_halved": "per_1000_live_births",
    "life_expectancy_difference_vs_s0_years_leakage_halved": "years",
    "employer_share_change_pp": "pp",
    "youth_homicide_rate_change_per_100k": "per_100k",
}


def triangular(rng: np.random.Generator, low: float, central: float, high: float) -> float:
    """Sample triangular(low, central, high); a degenerate range returns central."""
    low, central, high = float(low), float(central), float(high)
    if not low <= central <= high:
        raise ValueError(f"Range not ordered: {low}, {central}, {high}")
    if low == high:
        return central
    return float(rng.triangular(low, central, high))


def snap(value: float, step: float = WEIGHT_GRID_STEP) -> float:
    return round(round(float(value) / step) * step, 10)


def sample_draw(rng: np.random.Generator, parameters: Mapping, inputs: Mapping) -> dict:
    """Sample one value for every ranged parameter used by the chain."""
    baseline = parameters["baseline"]
    weight = baseline["pension_gdp_per_worker_weight"]
    vintages = [int(v) for v in baseline["profile_years"]["values"]]
    accumulated = parameters["fiscal_multipliers_brazil"]["accumulated"]
    efficiency = parameters["macro_modelling_choices"]["efficiency_output_effect"]
    social_choices = parameters["social_modelling_choices"]["reduction_hitting_health_education"]
    imr = parameters["social_outcome_elasticities"]["infant_mortality_wrt_public_health_spending"]
    leakage = parameters["governance"]["leakage_share_of_spending"]
    revenue_elasticity = parameters["revenue_elasticity_to_gdp"]
    lrf = parameters["long_run_feedback"]
    draw = {
        "profile_year": int(rng.choice(vintages)),
        "pension_gdp_per_worker_weight": snap(rng.uniform(weight["low"], weight["high"])),
        "efficiency_output_effect": triangular(rng, efficiency["low"], efficiency["central"], efficiency["high"]),
        "service_cut_fraction": triangular(
            rng, social_choices["service_cut_fraction"]["low"],
            social_choices["service_cut_fraction"]["central"], social_choices["service_cut_fraction"]["high"],
        ),
        "imr_elasticity": triangular(rng, imr["low"], imr["central"], imr["high"]),
        "leakage_share": float(rng.uniform(leakage["low"], leakage["high"])),
        "revenue_elasticity": float(rng.uniform(revenue_elasticity["low"], revenue_elasticity["high"])),
        "health_output_pct": float(rng.uniform(lrf["health_to_output"]["low"], lrf["health_to_output"]["high"])),
        "public_capital_elasticity": triangular(
            rng, lrf["public_capital"]["low"], lrf["public_capital"]["central"], lrf["public_capital"]["high"]
        ),
        "sovereign_risk_bp": triangular(
            rng, lrf["sovereign_risk_premium"]["low"], lrf["sovereign_risk_premium"]["central"],
            lrf["sovereign_risk_premium"]["high"],
        ),
        # C3 structural variants, equally likely (choice): how pension cuts, labour
        # effects and tax incidence land on households.
        "micro_pension_variant": str(rng.choice(micro.PENSION_VARIANTS)),
        "micro_labour_variant": str(rng.choice(micro.LABOUR_VARIANTS)),
        "micro_tax_variant": str(rng.choice(micro.TAX_VARIANTS)),
    }
    for category in MULTIPLIER_CATEGORIES:
        entry = accumulated[category]
        draw[f"multiplier_{category}"] = triangular(rng, entry["low"], entry["central"], entry["high"])
    for name in MACRO_RANGED:
        entry = inputs["macro"][name]
        draw[name] = triangular(rng, entry["low"], entry["central"], entry["high"])
    return draw


def central_draw(parameters: Mapping, inputs: Mapping) -> dict:
    """The draw with every sampled parameter at its configured central value."""
    baseline = parameters["baseline"]
    accumulated = parameters["fiscal_multipliers_brazil"]["accumulated"]
    draw = {
        "profile_year": int(baseline["central_profile_year"]["value"]),
        "pension_gdp_per_worker_weight": snap(baseline["pension_gdp_per_worker_weight"]["central"]),
        "efficiency_output_effect": float(parameters["macro_modelling_choices"]["efficiency_output_effect"]["central"]),
        "service_cut_fraction": float(
            parameters["social_modelling_choices"]["reduction_hitting_health_education"]["service_cut_fraction"]["central"]
        ),
        "imr_elasticity": float(
            parameters["social_outcome_elasticities"]["infant_mortality_wrt_public_health_spending"]["central"]
        ),
        # Leakage has no central value by design; its midpoint is used here and
        # it cancels out of every scenario-vs-S0 indicator except the sensitivity.
        "leakage_share": 0.5 * (
            parameters["governance"]["leakage_share_of_spending"]["low"]
            + parameters["governance"]["leakage_share_of_spending"]["high"]
        ),
        # The deterministic C2 rule (revenue a fixed share of GDP) is elasticity 1.
        "revenue_elasticity": 1.0,
        # Health-to-output has no central by design; the midpoint of its range.
        "health_output_pct": 0.5 * (
            parameters["long_run_feedback"]["health_to_output"]["low"]
            + parameters["long_run_feedback"]["health_to_output"]["high"]
        ),
        "public_capital_elasticity": float(parameters["long_run_feedback"]["public_capital"]["central"]),
        "sovereign_risk_bp": float(parameters["long_run_feedback"]["sovereign_risk_premium"]["central"]),
        "micro_pension_variant": "proportional",
        "micro_labour_variant": "gdp_only",
        "micro_tax_variant": "proportional",
        "education_capacity_elasticity": 0.02,
        "innovation_capacity_elasticity": 0.01,
        "firm_npl_rate_coefficient": 0.460,
        "firm_exit_rate_coefficient": 0.713,
    }
    for category in MULTIPLIER_CATEGORIES:
        draw[f"multiplier_{category}"] = float(accumulated[category]["central"])
    for name in MACRO_RANGED:
        draw[name] = float(inputs["macro"][name]["central"])
    return draw


def _collapse(entry: dict, value: float) -> None:
    for corner in ("low", "central", "high"):
        entry[corner] = value


def parameters_for_draw(parameters: Mapping, draw: Mapping) -> dict:
    result = copy.deepcopy(parameters)
    accumulated = result["fiscal_multipliers_brazil"]["accumulated"]
    for category in MULTIPLIER_CATEGORIES:
        _collapse(accumulated[category], draw[f"multiplier_{category}"])
    _collapse(result["macro_modelling_choices"]["efficiency_output_effect"], draw["efficiency_output_effect"])
    _collapse(result["revenue_elasticity_to_gdp"], draw["revenue_elasticity"])
    return result


def inputs_for_draw(inputs: Mapping, draw: Mapping) -> dict:
    result = copy.deepcopy(inputs)
    for name in MACRO_RANGED:
        _collapse(result["macro"][name], draw[name])
    return result


def c1_baseline_grid(
    fiscal: pd.DataFrame,
    population: pd.DataFrame,
    profiles: pd.DataFrame,
    parameters: Mapping,
    max_horizon: int,
) -> dict[tuple[int, float], pd.DataFrame]:
    """Annual C1 baselines for every profile vintage x snapped indexation weight."""
    weight = parameters["baseline"]["pension_gdp_per_worker_weight"]
    grid = np.round(np.arange(weight["low"], weight["high"] + WEIGHT_GRID_STEP / 2, WEIGHT_GRID_STEP), 10)
    result: dict[tuple[int, float], pd.DataFrame] = {}
    for vintage in parameters["baseline"]["profile_years"]["values"]:
        vintage = int(vintage)
        vintage_profiles = profiles.loc[pd.to_numeric(profiles["profile_year"]).astype(int).eq(vintage)]
        for value in grid:
            inputs = copy.deepcopy(parameters)
            _collapse(inputs["baseline"]["pension_gdp_per_worker_weight"], float(value))
            inputs["baseline"]["profile_years"]["values"] = [vintage]
            inputs["baseline"]["central_profile_year"]["value"] = vintage
            annual = project_baseline(fiscal, population, vintage_profiles, inputs, range(1, max_horizon + 1))
            result[(vintage, snap(value))] = annual.loc[annual["variant"].eq("central")].reset_index(drop=True)
    return result


def scenarios_for_variant(scenarios: Mapping, name: str) -> dict:
    """Scenario configuration with the composition variant's package shares."""
    result = copy.deepcopy(scenarios)
    if name == "default":
        return result
    definition = scenarios["variant_definitions"][name]
    default = {k: float(v) for k, v in scenarios["package_shares"].items()}
    if name == "compensating_transfers":
        multiple = float(definition["gross_cut_multiple_of_R"])
        shares = {k: v * multiple for k, v in default.items()}
        shares["means_tested_transfers"] = -float(definition["means_tested_transfers_increase_share_of_R"])
    else:
        shares = {k: float(v) for k, v in definition.items()}
    touched = {k for k, v in shares.items() if v != 0.0}
    # Variants that deliberately move a protected category (investment stress,
    # compensating transfers) lift that protection for this variant only.
    result["protected"] = [p for p in scenarios.get("protected", []) if p not in touched]
    result["package_shares"] = shares
    return result


def social_for_draw(
    corner: pd.DataFrame,
    annual: pd.DataFrame,
    variant_scenarios: Mapping,
    parameters: Mapping,
    base_inputs: Mapping,
    draw: Mapping,
    years: Iterable[int],
) -> pd.DataFrame:
    """C4 indicators for one draw, using the C4 functions and the variant's efficiency share."""
    choices = parameters["social_modelling_choices"]
    build_up = social._parse_build_up_years(choices)
    lower, upper = social._parse_hdi_goalposts(choices)
    le_elasticity = float(parameters["social_outcome_elasticities"]["life_expectancy_wrt_health_spending"]["central"])
    base_year = int(annual["year"].min())
    s0_base = annual.loc[annual["year"].eq(base_year) & annual["scenario"].eq("S0")].set_index("category")["spending_pct_gdp"]
    health_allocation = float(s0_base["health"]) / float(s0_base["health"] + s0_base["education"])
    efficiency_share = float(variant_scenarios["package_shares"].get("efficiency_health_education_admin", 0.0))
    base_imr = float(base_inputs["infant_mortality"]["value"])
    base_le = float(base_inputs["life_expectancy"]["value"])
    leakage = float(draw["leakage_share"])
    removed = float(parameters["governance"]["leakage_reduction_sensitivity"]["fraction_of_leakage_removed"])
    health = annual.loc[annual["category"].eq("health")].set_index(["year", "scenario"])["spending_pct_gdp"]
    gdp = corner.set_index(["year", "scenario"])["gdp_per_capita"]
    gaps = corner.set_index(["year", "scenario"])["gap_below_s0_pp"]
    records = []
    for year in years:
        horizon = year - base_year
        # Services per capita = spending x (1 - leakage). With the same leakage in
        # every scenario the factor cancels in the change vs S0.
        s0_services = social.health_spending_per_capita(health[(year, "S0")], gdp[(year, "S0")]) * (1.0 - leakage)
        for scenario in corner.loc[corner["year"].eq(year), "scenario"]:
            if scenario == "S1":
                share, reduction = health[(year, "S1")], 0.0
            else:
                share, reduction = health[(year, "S0")], (0.0 if scenario == "S0" else float(gaps[(year, scenario)]))
            scenario_share = efficiency_share
            definition = variant_scenarios["scenarios"].get(scenario)
            if isinstance(definition, Mapping) and "package_gaps_by_year" in definition:
                # Own composition (P1): pass the services-package gap itself with share 1.
                reduction = scenario_package_gaps(variant_scenarios, scenario, horizon, reduction).get(
                    "efficiency_health_education_admin", 0.0)
                scenario_share = 1.0
            spending = social.health_spending_per_capita(
                share, gdp[(year, scenario)], reduction, scenario_share,
                health_allocation, draw["service_cut_fraction"],
            )
            change = (spending * (1.0 - leakage) / s0_services - 1.0) * 100.0
            imr = social.apply_spending_elasticity(base_imr, change, draw["imr_elasticity"], horizon, build_up)
            le = social.apply_spending_elasticity(base_le, change, le_elasticity, horizon, build_up)
            change_g = (spending * (1.0 - leakage * (1.0 - removed)) / s0_services - 1.0) * 100.0
            imr_g = social.apply_spending_elasticity(base_imr, change_g, draw["imr_elasticity"], horizon, build_up)
            le_g = social.apply_spending_elasticity(base_le, change_g, le_elasticity, horizon, build_up)
            records.append({
                "year": year, "scenario": scenario,
                "real_public_health_spending_pc_change_vs_s0_pct": change,
                "infant_mortality_per_1000": imr,
                "infant_mortality_difference_vs_s0": imr - base_imr,
                "life_expectancy_difference_vs_s0_years": le - base_le,
                "hdi_health_index_difference_vs_s0": (
                    social.hdi_health_index(le, lower, upper) - social.hdi_health_index(base_le, lower, upper)
                ),
                "effective_health_services_pc_change_vs_s0_pct_leakage_halved": change_g,
                "infant_mortality_difference_vs_s0_leakage_halved": imr_g - base_imr,
                "life_expectancy_difference_vs_s0_years_leakage_halved": le_g - base_le,
            })
    return pd.DataFrame(records)


def load_context(
    parameters_path: str = "config/parameters.yaml",
    scenarios_path: str = "config/scenarios.yaml",
    social_inputs_path: str = "config/c4_inputs_proposed.yaml",
    data_dir: str = "data/brazil",
    variants: Iterable[str] | None = None,
) -> dict:
    """Read configuration and data once, and precompute the C1 grid."""
    parameters = read_yaml(parameters_path)
    scenarios = read_yaml(scenarios_path)
    data = Path(data_dir)
    population = pd.read_csv(data / "population.csv")
    horizons = [int(h) for h in scenarios["horizons_years"]]
    variant_names = list(variants) if variants is not None else list(scenarios["variants"])
    grid = c1_baseline_grid(
        pd.read_csv(data / "fiscal.csv"), population, pd.read_csv(data / "age_profiles.csv"),
        parameters, max(horizons),
    )
    base_year = int(next(iter(grid.values()))["year"].min())
    return {
        "parameters": parameters,
        "scenarios": scenarios,
        "inputs": load_macro_inputs(parameters_path),
        "base_inputs": social.load_social_inputs(social_inputs_path),
        "population": population,
        "horizons": horizons,
        "variant_configs": {name: scenarios_for_variant(scenarios, name) for name in variant_names},
        "grid": grid,
        "base_year": base_year,
        "target_years": [base_year + h for h in horizons],
        "external_changes": (
            external.historical_changes_v2(data / "external_observed.csv", data / "backtest_observed.csv")
            if parameters["external_block"].get("gdp_model") == "c7_channel_a"
            else external.historical_changes(data / "backtest_observed.csv")
        ),
        "feedback_defaults": _feedback_defaults(parameters_path, scenarios_path),
        "micro": _micro_context(data),
        "tax_incidence": "instrument",
        "corruption": corruption.load_config("config/corruption_proposed.yaml"),
        "education": education.monte_carlo_channel_inputs(),
        "education_sensitivity": "none",
    }


def _micro_context(data: Path) -> dict | None:
    """Prepared PNAD person file and C3 inputs; None when the git-ignored file is absent."""
    persons_path = data.parent / "processed/brazil/microdata/pnadc_2025_c3_input.csv"
    if not persons_path.exists():
        return None
    inputs = read_yaml("config/c3_inputs_proposed.yaml")
    prepared = micro.prepare_microdata(pd.read_csv(persons_path, low_memory=False))
    lines = {name: float(entry["value"]) for name, entry in inputs["poverty_lines_brl_month_per_capita"].items()}
    base = micro.calculate_indicators(
        micro.simulate_household_incomes(
            prepared, gdp_level_vs_s0_pct=0.0, unemployment_change_pp=0.0, package_gaps_pp_gdp={},
            revenue_change_pp=0.0, nominal_gdp_brl=float(inputs["nominal_gdp_brl_million"]["value"]) * 1e6,
            minimum_wage_brl=float(inputs["minimum_wage_brl_month"]["value"]), pension_variant="proportional",
            labour_variant="gdp_only", tax_variant="proportional",
            consumption_like_exponent=float(inputs["defaults"]["consumption_like_exponent"]),
            random_seed=0,
        ),
        lines,
    )
    return {"prepared": prepared, "inputs": inputs, "lines": lines, "base": base}


def scenario_package_gaps(variant_scenarios: Mapping, scenario: str, horizon: int, total_gap: float) -> dict[str, float]:
    """Package gaps below S0 (pp GDP): a scenario's own package paths, else the variant's shares."""
    definition = variant_scenarios["scenarios"].get(scenario)
    if isinstance(definition, Mapping) and "package_gaps_by_year" in definition:
        return {
            str(package): _interpolate_by_year(path, horizon, f"{scenario}.{package}")
            for package, path in definition["package_gaps_by_year"].items()
        }
    return {str(k): total_gap * float(v) for k, v in variant_scenarios["package_shares"].items()}


def scenario_revenue_by_instrument(
    variant_scenarios: Mapping, scenario: str, horizon: int,
) -> dict[str, float] | None:
    """Return a scenario's instrument split, when its definition provides one."""
    definition = variant_scenarios["scenarios"].get(scenario)
    if not isinstance(definition, Mapping) or "revenue_by_instrument_by_year" not in definition:
        return None
    return {
        str(instrument): _interpolate_by_year(path, horizon, f"{scenario}.{instrument}")
        for instrument, path in definition["revenue_by_instrument_by_year"].items()
    }


def with_programmes(variant_scenarios: Mapping, annual: pd.DataFrame, draw_inputs: Mapping, draw: Mapping,
                    context: Mapping) -> Mapping:
    """Add the P1 programme scenarios (built on this draw's S0 path) to a variant configuration."""
    s0 = programs.s0_path(annual, context["population"], draw_inputs)
    common = variant_scenarios["package_shares"] if context.get("programme_common_composition") else None
    definitions = programs.build_programme_scenarios(s0, context["programmes"], draw, common)
    out = dict(variant_scenarios)
    out["scenarios"] = {**variant_scenarios["scenarios"], **definitions}
    return out


def micro_for_draw(corner: pd.DataFrame, variant_scenarios: Mapping, draw: Mapping, context: Mapping) -> pd.DataFrame:
    """C3 distribution indicators vs S0 for target years (one draw, one persistence setting)."""
    ctx = context["micro"]
    inputs = ctx["inputs"]
    records = []
    for row in corner.itertuples():
        if row.scenario in MICRO_SCENARIOS_EXCLUDED:
            continue
        if row.scenario == "S0":
            records.append({"year": row.year, "scenario": row.scenario, **ctx["base"]})
            continue
        gaps = scenario_package_gaps(
            variant_scenarios, row.scenario, int(row.year) - int(context["base_year"]), float(row.gap_below_s0_pp)
        )
        revenue = float(getattr(row, "revenue_change_pp", 0.0))
        revenue_by_instrument = None
        if context.get("tax_incidence", "instrument") == "instrument":
            revenue_by_instrument = scenario_revenue_by_instrument(
                variant_scenarios, row.scenario, int(row.year) - int(context["base_year"])
            )
        households = micro.simulate_household_incomes(
            ctx["prepared"], gdp_level_vs_s0_pct=float(row.gdp_level_vs_s0_pct),
            unemployment_change_pp=float(row.unemployment_change_pp), package_gaps_pp_gdp=gaps,
            revenue_change_pp=revenue, nominal_gdp_brl=float(inputs["nominal_gdp_brl_million"]["value"]) * 1e6,
            minimum_wage_brl=float(inputs["minimum_wage_brl_month"]["value"]),
            pension_variant=draw["micro_pension_variant"], labour_variant=draw["micro_labour_variant"],
            tax_variant=draw["micro_tax_variant"],
            consumption_like_exponent=float(inputs["defaults"]["consumption_like_exponent"]),
            random_seed=int(draw.get("draw", 0)),
            revenue_change_by_instrument_pp=revenue_by_instrument,
        )
        ind = micro.calculate_indicators(households, ctx["lines"])
        records.append({"year": row.year, "scenario": row.scenario, **ind})
    frame = pd.DataFrame(records)
    s0 = frame.loc[frame["scenario"].eq("S0")].set_index("year")
    out = frame[["year", "scenario"]].copy()
    mapping = {
        "gini_change_vs_s0_points": ("gini", 100.0),
        "poverty_218_change_vs_s0_pp": ("poverty_headcount_bolsa_familia_pct", 1.0),
        "poverty_759_change_vs_s0_pp": ("poverty_headcount_half_minimum_wage_2025_pct", 1.0),
        "poverty_218_age_0_14_change_vs_s0_pp": ("poverty_headcount_bolsa_familia_age_0_14_pct", 1.0),
        "poverty_218_age_65_plus_change_vs_s0_pp": ("poverty_headcount_bolsa_familia_age_65_plus_pct", 1.0),
        "poverty_218_with_65_plus_recipient_change_vs_s0_pp": (
            "poverty_headcount_bolsa_familia_living_with_65_plus_pension_bpc_recipient_pct", 1.0
        ),
        "poverty_759_age_0_14_change_vs_s0_pp": (
            "poverty_headcount_half_minimum_wage_2025_age_0_14_pct", 1.0
        ),
        "poverty_759_age_65_plus_change_vs_s0_pp": (
            "poverty_headcount_half_minimum_wage_2025_age_65_plus_pct", 1.0
        ),
        "poverty_759_with_65_plus_recipient_change_vs_s0_pp": (
            "poverty_headcount_half_minimum_wage_2025_living_with_65_plus_pension_bpc_recipient_pct", 1.0
        ),
        "poverty_smoothed_218_change_vs_s0_pp": ("poverty_smoothed_bolsa_familia_pct", 1.0),
        "poverty_smoothed_218_age_0_14_change_vs_s0_pp": (
            "poverty_smoothed_bolsa_familia_age_0_14_pct", 1.0
        ),
        "poverty_smoothed_218_age_65_plus_change_vs_s0_pp": (
            "poverty_smoothed_bolsa_familia_age_65_plus_pct", 1.0
        ),
        "poverty_smoothed_218_with_65_plus_recipient_change_vs_s0_pp": (
            "poverty_smoothed_bolsa_familia_living_with_65_plus_pension_bpc_recipient_pct", 1.0
        ),
        "poverty_smoothed_759_change_vs_s0_pp": ("poverty_smoothed_half_minimum_wage_2025_pct", 1.0),
        "poverty_smoothed_759_age_0_14_change_vs_s0_pp": (
            "poverty_smoothed_half_minimum_wage_2025_age_0_14_pct", 1.0
        ),
        "poverty_smoothed_759_age_65_plus_change_vs_s0_pp": (
            "poverty_smoothed_half_minimum_wage_2025_age_65_plus_pct", 1.0
        ),
        "poverty_smoothed_759_with_65_plus_recipient_change_vs_s0_pp": (
            "poverty_smoothed_half_minimum_wage_2025_living_with_65_plus_pension_bpc_recipient_pct", 1.0
        ),
        "poverty_gap_218_change_vs_s0_pp": ("poverty_gap_bolsa_familia_pct", 1.0),
        "poverty_gap_218_age_0_14_change_vs_s0_pp": ("poverty_gap_bolsa_familia_age_0_14_pct", 1.0),
        "poverty_gap_218_age_65_plus_change_vs_s0_pp": ("poverty_gap_bolsa_familia_age_65_plus_pct", 1.0),
        "poverty_gap_218_with_65_plus_recipient_change_vs_s0_pp": (
            "poverty_gap_bolsa_familia_living_with_65_plus_pension_bpc_recipient_pct", 1.0
        ),
        "poverty_gap_759_change_vs_s0_pp": ("poverty_gap_half_minimum_wage_2025_pct", 1.0),
        "poverty_gap_759_age_0_14_change_vs_s0_pp": (
            "poverty_gap_half_minimum_wage_2025_age_0_14_pct", 1.0
        ),
        "poverty_gap_759_age_65_plus_change_vs_s0_pp": (
            "poverty_gap_half_minimum_wage_2025_age_65_plus_pct", 1.0
        ),
        "poverty_gap_759_with_65_plus_recipient_change_vs_s0_pp": (
            "poverty_gap_half_minimum_wage_2025_living_with_65_plus_pension_bpc_recipient_pct", 1.0
        ),
        "poverty_gap_sq_218_change_vs_s0": ("poverty_gap_sq_bolsa_familia", 1.0),
        "poverty_gap_sq_759_change_vs_s0": ("poverty_gap_sq_half_minimum_wage_2025", 1.0),
        "top1_share_survey_change_vs_s0_pp": ("survey_top_1_income_share_pct", 1.0),
        "top10_share_survey_change_vs_s0_pp": ("survey_top_10_income_share_pct", 1.0),
    }
    for name, (column, scale) in mapping.items():
        out[name] = (frame[column] - frame["year"].map(s0[column])) * scale
    return out


def _feedback_defaults(parameters_path: str, scenarios_path: str) -> dict:
    defaults = feedback.load_feedback_defaults(parameters_path, scenarios_path)
    defaults.pop("base_adult_schooling_year", None)
    return defaults


def feedback_for_draw(
    corner: pd.DataFrame, life_expectancy: pd.DataFrame, variant_scenarios: Mapping,
    draw: Mapping, context: Mapping,
) -> pd.DataFrame:
    """Apply C5 to one annual C2 corner with this draw's sampled values."""
    shares = variant_scenarios["package_shares"]
    efficiency_share: float | dict = float(shares.get("efficiency_health_education_admin", 0.0))
    investment_share: float | dict = float(shares.get("public_investment", 0.0))
    own = [s for s, d in variant_scenarios["scenarios"].items()
           if isinstance(d, Mapping) and "package_gaps_by_year" in d]
    if own:
        # Effective shares per row, so that share x total gap = the scenario's own package gap.
        efficiency_share, investment_share = {}, {}
        base_year = int(corner["year"].min())
        for row in corner.itertuples():
            key, total = (int(row.year), str(row.scenario)), float(row.gap_below_s0_pp)
            packages = scenario_package_gaps(variant_scenarios, row.scenario, key[0] - base_year, total)
            efficiency_share[key] = packages.get("efficiency_health_education_admin", 0.0) / total if total else 0.0
            investment_share[key] = packages.get("public_investment", 0.0) / total if total else 0.0
    kwargs = dict(context["feedback_defaults"])
    kwargs.update(
        efficiency_package_share=efficiency_share,
        public_investment_package_share=investment_share,
        service_cut_fraction=float(draw["service_cut_fraction"]),
        health_output_pct_per_year=float(draw["health_output_pct"]),
        public_capital_elasticity=float(draw["public_capital_elasticity"]),
        sovereign_risk_bp_per_debt_pp=float(draw["sovereign_risk_bp"]),
        base_real_interest_rate_pct=float(draw["effective_real_interest_rate"]),
        real_rate_path_offset_pp=context["inputs"].get("derived", {}).get("real_rate_path_offset_pp"),
        inflation_pct=float(draw["gdp_deflator_growth"]),
        life_expectancy_change={
            (int(r.year), r.scenario): float(r.life_expectancy_difference_vs_s0_years)
            for r in life_expectancy.itertuples()
        },
    )
    education_paths = education_for_draw(corner, variant_scenarios, draw, context)
    kwargs.update(
        education_capacity_log_effect=education_paths["capacity"],
        innovation_capacity_log_effect=education_paths["innovation"],
    )
    result = feedback.apply_feedback(corner, context["population"], **kwargs)
    employer = np.zeros(len(result), dtype=float)
    homicide = np.zeros(len(result), dtype=float)
    for scenario, indices in result.groupby("scenario", sort=False).groups.items():
        ordered = result.loc[indices].sort_values("year")
        positions = ordered.index.to_numpy()
        emp, hom = education.composition_indicator_paths(
            ordered["year"].to_numpy(), education_paths["education_change"].loc[positions].to_numpy(),
            ordered["adult_mean_schooling_change_years"].to_numpy(), context["parameters"], context["education"],
        )
        employer[positions] = emp
        homicide[positions] = hom
    result["employer_share_change_pp"] = employer
    result["youth_homicide_rate_change_per_100k"] = homicide
    return result


def education_for_draw(
    corner: pd.DataFrame, variant_scenarios: Mapping, draw: Mapping, context: Mapping,
) -> dict[str, pd.Series]:
    """Build ED capacity, innovation and indicator doses for one C5 corner."""
    result = {
        name: pd.Series(0.0, index=corner.index, dtype=float)
        for name in ("capacity", "innovation", "education_change")
    }
    base_year = int(corner["year"].min())
    s0_base_gdp = float(corner.loc[
        corner["scenario"].eq("S0") & corner["year"].eq(base_year), "real_gdp"
    ].iloc[0])
    rd_baseline_pp = float(context["education"]["mcti_2024_bn"]) / (s0_base_gdp / 1000.0) * 100.0
    education_share = float(context["parameters"]["baseline"]["education_gdp_share"]["central"])
    for scenario, indices in corner.groupby("scenario", sort=False).groups.items():
        ordered = corner.loc[indices].sort_values("year")
        positions = ordered.index.to_numpy()
        years = ordered["year"].to_numpy(dtype=int)
        service_gap = np.asarray([
            scenario_package_gaps(
                variant_scenarios, str(scenario), int(row.year) - base_year, float(row.gap_below_s0_pp)
            ).get("efficiency_health_education_admin", 0.0)
            for row in ordered.itertuples()
        ])
        education_change, rd_change = education.package_spending_changes(
            service_gap, context["parameters"], rd_baseline_pp
        )
        university, mcti = education.sensitivity_budget_paths(
            str(scenario), years, context.get("education_sensitivity", "none"), context["education"]
        )
        capacity, innovation = education.capacity_innovation_log_effects(
            years, education_change, rd_change, university, mcti,
            education_share_gdp=education_share, rd_baseline_pp_gdp=rd_baseline_pp,
            capacity_elasticity=float(draw["education_capacity_elasticity"]),
            innovation_elasticity=float(draw["innovation_capacity_elasticity"]),
            inputs=context["education"],
        )
        result["capacity"].loc[positions] = capacity
        result["innovation"].loc[positions] = innovation
        result["education_change"].loc[positions] = education_change
    return result


def firm_distress_for_draw(corner: pd.DataFrame, draw: Mapping) -> pd.DataFrame:
    """Add indicator-only BK responses to the C5 premium gap versus S0."""
    s0 = corner.loc[corner["scenario"].eq("S0")].set_index("year")["sovereign_risk_premium_pp"]
    deviation = corner["sovereign_risk_premium_pp"] - corner["year"].map(s0)
    result = corner.copy()
    result["firm_npl_change_vs_s0_pp"] = float(draw["firm_npl_rate_coefficient"]) * deviation
    result["firm_exit_rate_change_vs_s0_pp"] = float(draw["firm_exit_rate_coefficient"]) * deviation
    return result


def evaluate_draw(draw: Mapping, context: Mapping, external_effects: pd.DataFrame | None = None) -> pd.DataFrame:
    """Run C1 -> C2 -> C4 (+ C6 external path) for one draw, every variant and persistence setting."""
    annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
    draw_parameters = parameters_for_draw(context["parameters"], draw)
    draw_inputs = inputs_for_draw(context["inputs"], draw)
    target_years = context["target_years"]
    results = []
    for variant, variant_scenarios in context["variant_configs"].items():
        if context.get("programmes") is not None and variant == PROGRAMME_VARIANT:
            variant_scenarios = with_programmes(variant_scenarios, annual, draw_inputs, draw, context)
        for persistence in PERSISTENCE_VARIANTS:
            corner = run_corner(
                annual, context["population"], variant_scenarios, draw_parameters, draw_inputs, "central", persistence
            )
            effects = external_effects
            if effects is None:
                neutral = external.reference_path(
                    "neutral", context["external_changes"], int(corner["year"].max() - corner["year"].min())
                )
                effects = external.gdp_and_inflation_effects(neutral, context["parameters"])
            corner = external.apply_external(corner, effects, draw_inputs)
            all_years = sorted(int(y) for y in corner["year"].unique())
            annual_social = social_for_draw(
                corner, annual, variant_scenarios, context["parameters"], context["base_inputs"], draw, all_years
            )
            corner = feedback_for_draw(corner, annual_social, variant_scenarios, draw, context)
            corner = firm_distress_for_draw(corner, draw)
            corner = corner.loc[corner["year"].isin(target_years)].copy()
            s0 = corner.loc[corner["scenario"].eq("S0")].set_index("year")
            corner["gdp_per_capita_vs_s0_pct"] = (
                corner["gdp_per_capita"] / corner["year"].map(s0["gdp_per_capita"]) - 1.0
            ) * 100.0
            corner["debt_gdp_vs_s0_pp"] = corner["debt_gdp"] - corner["year"].map(s0["debt_gdp"])
            corner["gdp_per_capita_with_external_vs_s0_pct"] = (
                corner["gdp_per_capita_with_external"] / corner["year"].map(s0["gdp_per_capita_with_external"]) - 1.0
            ) * 100.0
            corner["debt_gdp_with_external_vs_s0_pp"] = (
                corner["debt_gdp_with_external"] - corner["year"].map(s0["debt_gdp_with_external"])
            )
            corner["gdp_per_capita_with_feedback_vs_s0_pct"] = (
                corner["gdp_per_capita_with_feedback"] / corner["year"].map(s0["gdp_per_capita_with_feedback"]) - 1.0
            ) * 100.0
            corner["debt_gdp_with_feedback_vs_s0_pp"] = (
                corner["debt_gdp_with_feedback"] - corner["year"].map(s0["debt_gdp_with_feedback"])
            )
            outcomes = annual_social.loc[annual_social["year"].isin(target_years)]
            merged = corner.merge(outcomes, on=["year", "scenario"], validate="one_to_one")
            if context.get("micro") is not None and variant == MICRO_VARIANT:
                merged = merged.merge(micro_for_draw(corner, variant_scenarios, draw, context),
                                      on=["year", "scenario"], how="left", validate="one_to_one")
            else:
                for name in MICRO_OUTPUTS:
                    merged[name] = np.nan
            merged["draw"], merged["variant"], merged["persistence"] = draw.get("draw", 0), variant, persistence
            results.append(merged[["draw", "variant", "persistence", "year", "scenario", *MACRO_OUTPUTS, *SOCIAL_OUTPUTS, *MICRO_OUTPUTS]])
    frame = pd.concat(results, ignore_index=True)
    frame["horizon"] = frame["year"] - context["base_year"]
    return frame


def run(
    n_draws: int = N_DRAWS,
    seed: int = SEED,
    context: Mapping | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (draw-level results, sampled parameters, metadata)."""
    context = context or load_context()
    parameters, inputs = context["parameters"], context["inputs"]
    variant_names = list(context["variant_configs"])
    horizons, base_year = context["horizons"], context["base_year"]
    rng = np.random.default_rng(seed)
    # Separate stream so adding the external block leaves parameter draws unchanged.
    external_rng = np.random.default_rng([seed, 1])
    c7_rng = np.random.default_rng([seed, 3])  # C7 coefficient window per draw
    corruption_rng = np.random.default_rng([seed, 4])  # G2 scandal shocks
    corruption_config = context.get("corruption")
    c7 = "dlnp_pct" in context["external_changes"].columns
    c7_windows = sorted(parameters["external_block"]["output_channel_c7"]["coefficient_sets"]) if c7 else []
    programme_rng = np.random.default_rng([seed, 2])  # P1 sizes; leaves the other streams unchanged
    privatisation_rng = np.random.default_rng([seed, 5])  # PZ sales; leaves every existing stream unchanged
    education_rng = np.random.default_rng([seed, 6])  # ED responses; leaves every existing stream unchanged
    firm_rng = np.random.default_rng([seed, 7])  # BK coefficients; leaves every existing stream unchanged
    steps = max(context["target_years"]) - base_year
    draws, results = [], []
    started = time.monotonic()
    for index in range(n_draws):
        draw = sample_draw(rng, parameters, inputs)
        draw["draw"] = index
        draw["education_capacity_elasticity"] = float(education_rng.uniform(0.0, 0.04))
        draw["innovation_capacity_elasticity"] = float(education_rng.uniform(0.0, 0.02))
        draw["firm_npl_rate_coefficient"] = float(firm_rng.normal(0.460, (0.664 - 0.256) / 3.92))
        draw["firm_exit_rate_coefficient"] = float(firm_rng.normal(0.713, (1.512 + 0.085) / 3.92))
        path = external.bootstrap_path(external_rng, context["external_changes"], steps)
        if c7:
            draw["external_c7_window"] = str(c7_rng.choice(c7_windows))
            effects = external.gdp_and_inflation_effects(
                path, parameters, channel_a=external.channel_a_coefficients(parameters, draw["external_c7_window"])
            )
            draw["external_commodity_price_cumulative_change_pct"] = float(path["dlnp_pct"].sum())
        else:
            effects = external.gdp_and_inflation_effects(path, parameters)
            draw["external_tot_cumulative_change_pct"] = float(path["tot_change_pct"].sum())
        draw["external_fx_cumulative_change_pct"] = float(path["fx_change_pct"].sum())
        if corruption_config is not None:
            shock = corruption.draw_path(corruption_rng, steps, corruption_config)
            effects = effects.merge(shock[["step", "corruption_gdp_level_pct"]], on="step", validate="one_to_one")
            draw["corruption_probability"] = float(shock.attrs["sampled_probability"])
            draw["corruption_events"] = int(shock["corruption_event"].sum())
        if context.get("programmes") is not None:
            draw.update(programs.sample_programme_draw(programme_rng, context["programmes"], parameters))
            petroleum_factor: dict[int, float] = {}
            if "dlnp_pct" in path.columns:
                cumulative = np.exp(path["dlnp_pct"].to_numpy().cumsum() / 100.0)
                petroleum_factor = {
                    base_year + int(step): float(factor)
                    for step, factor in zip(path["step"], cumulative)
                }
            sale = privatisation.sale_paths(
                context["privatisation_inventory"], context.get("privatisation_package", "f5"),
                privatisation_rng, context["privatisation_nominal_gdp_brl_million"],
                f5_target_pp=float(draw["flavio_privatisation_pp"]),
                base_year=base_year, end_year=base_year + steps, petroleum_factor_by_year=petroleum_factor,
            )
            draw["privatisation_debt_adjustment_by_year"] = sale["debt_adjustment_by_year"]
            draw["privatisation_non_tax_revenue_by_year"] = sale["non_tax_revenue_by_year"]
        draws.append(draw)
        results.append(evaluate_draw(draw, context, effects))
        done = index + 1
        if done % 25 == 0:
            elapsed = time.monotonic() - started
            eta = elapsed / done * (n_draws - done)
            print(f"{done}/{n_draws} draws, elapsed {elapsed:.1f}s, ETA {eta:.1f}s", file=sys.stderr, flush=True)
    draw_results = pd.concat(results, ignore_index=True)
    metadata = {
        "seed": seed, "n_draws": n_draws, "variants": variant_names,
        "tax_incidence": context.get("tax_incidence", "instrument"),
        "privatisation_package": context.get("privatisation_package", "f5"),
        "persistence": list(PERSISTENCE_VARIANTS), "horizons": horizons, "base_year": base_year,
        "sampled": {
            **{f"multiplier_{c}": "triangular(low, central, high) from fiscal_multipliers_brazil.accumulated" for c in MULTIPLIER_CATEGORIES},
            **{name: "triangular(low, central, high) from parameters.yaml macro inputs (C2)" for name in MACRO_RANGED},
            "efficiency_output_effect": "triangular(low, central, high) from macro_modelling_choices",
            "service_cut_fraction": "triangular(low, central, high) from social_modelling_choices",
            "imr_elasticity": "triangular(low, central, high) from social_outcome_elasticities",
            "pension_gdp_per_worker_weight": f"uniform(low, high), snapped to a {WEIGHT_GRID_STEP} grid",
            "health_output_pct": "uniform(0, 4) from long_run_feedback.health_to_output (two conflicting studies)",
            "public_capital_elasticity": "triangular(0.083, 0.106, 0.122) from long_run_feedback.public_capital",
            "sovereign_risk_bp": "triangular(2, 5, 7) from long_run_feedback.sovereign_risk_premium; deviation vs base-year debt capped at 50 pp (choice)",
            "revenue_elasticity": "uniform(0.92, 0.98) from revenue_elasticity_to_gdp (IFI EE16 long run; C2 deterministic rule is 1.0)",
            "leakage_share": "uniform(low, high) from governance.leakage_share_of_spending (cancels in scenario-vs-S0 comparisons; drives the leakage_halved sensitivity)",
            "profile_year": "discrete, equal probability over profile_years.values",
            "education_capacity_elasticity": "uniform(0, 0.04), separate stream [seed, 6]",
            "innovation_capacity_elasticity": "uniform(0, 0.02), separate stream [seed, 6]",
            "firm_npl_rate_coefficient": "normal(0.460, (0.664 - 0.256) / 3.92), separate stream [seed, 7]",
            "firm_exit_rate_coefficient": "normal(0.713, (1.512 + 0.085) / 3.92), separate stream [seed, 7]; imprecise, CI includes zero",
        },
        "corruption": (
            "G2 major-scandal shock: annual probability uniform(0.03, 0.08), GDP level loss triangular(1.0, 2.25, 3.6)%, "
            "2-year build-up, 4-year recovery half-life; one event sequence per draw shared by every scenario and "
            "programme (stream [seed, 4]); included in external_gdp_level_pct and the *_with_external outputs"
        ),
        "fixed": {
            "life_expectancy_elasticity": "central only (point estimate)",
            "point_inputs": "every macro input with low = central = high (initial debt, revenue/GDP, capital share, K/Y, depreciation, GDP anchors)",
            "c1_category_shares": "point values (COFOG 2024)",
        },
        "external": (
            "C7 output channel: block bootstrap (3-year blocks) of joint 2001-2024 commodity export price, world growth "
            "(both demeaned) and BRL/USD changes, same path for every scenario in a draw (stream [seed, 1]); "
            "channel-A coefficient set drawn per draw from the two prespecified estimation windows (stream [seed, 3])"
            if "dlnp_pct" in context["external_changes"].columns else
            "C6 block bootstrap (3-year blocks) of joint observed 2006-2024 terms-of-trade and BRL/USD changes, "
            "same path for every scenario in a draw; separate random stream [seed, 1]"
        ),
        "choices": [
            "triangular sampling for ranges is a modelling choice (fiscal_multipliers_brazil.sampling_rule), not a sourced distribution",
            "parameters are sampled independently: no sourced correlations",
            "persistence (transitory/persistent) is reported as a dimension, not sampled",
            "percentiles describe parameter uncertainty only, not forecast error or external shocks",
        ],
        "not_modelled": NOT_MODELLED,
        "education_sensitivity": context.get("education_sensitivity", "none"),
        "firm_distress": "BK NPL and exit-rate indicators are associational and indicator-only; they do not feed back to GDP or debt. The exit-rate CI includes zero.",
    }
    if context.get("real_rate_path") is not None:
        metadata.update(context["real_rate_path"])
    metadata["micro_outputs"] = (
        "C3 distribution indicators are changes versus S0; poverty outputs include all-person, age 0-14, "
        "age 65+, and people living with a 65+ pension/BPC recipient headcounts for both poverty lines"
    )
    if context.get("programmes") is not None:
        metadata["programmes"] = {
            "scenarios": list(programs.PROGRAMMES),
            "variant": PROGRAMME_VARIANT,
            "sampling": context["programmes"]["model_parameters"]["sampling"],
            "stream": "separate random stream [seed, 2]",
            "privatisation_package": context.get("privatisation_package", "f5"),
            "privatisation_stream": "separate random stream [seed, 5]",
            "composition": "default package shares for both (sensitivity)" if context.get("programme_common_composition")
            else "programme-specific assumed compositions (programs_2026.yaml)",
            "status": "unpublished until the D2 gate and lead/user review",
        }
    return draw_results, pd.DataFrame(draws), metadata


def summarise(draw_results: pd.DataFrame, n_draws: int) -> pd.DataFrame:
    """Percentiles 10/50/90 per variant, persistence, scenario, horizon and indicator."""
    keys = ["variant", "persistence", "scenario", "horizon", "year"]
    long = draw_results.melt(id_vars=["draw", *keys], var_name="indicator", value_name="value")
    grouped = long.groupby([*keys, "indicator"], sort=True)["value"]
    summary = grouped.quantile([p / 100 for p in PERCENTILES]).unstack()
    summary.columns = [f"p{p}" for p in PERCENTILES]
    summary = summary.reset_index()
    units = {**MACRO_OUTPUTS, **SOCIAL_OUTPUTS, **MICRO_OUTPUTS}
    summary["unit"] = summary["indicator"].map(units)
    summary["n_draws"] = n_draws
    summary["status"] = "modelled: parameter uncertainty only"
    summary.loc[summary["indicator"].eq("firm_exit_rate_change_vs_s0_pp"), "status"] = (
        "modelled: imprecise association; coefficient CI includes zero"
    )
    micro_gap = summary["indicator"].isin(list(MICRO_OUTPUTS)) & summary["p50"].isna()
    summary.loc[micro_gap, "status"] = (
        f"not_modelled: C3 runs for the {MICRO_VARIANT} composition only and has no package allocation for S1"
    )
    gaps = []
    for key, _ in draw_results.groupby(keys, sort=True):
        for indicator, reason in NOT_MODELLED.items():
            gaps.append({**dict(zip(keys, key)), "indicator": indicator, "p10": np.nan, "p50": np.nan,
                         "p90": np.nan, "unit": "", "n_draws": n_draws, "status": f"not_modelled: {reason}"})
    order = ["variant", "persistence", "scenario", "horizon", "year", "indicator", "unit", "p10", "p50", "p90", "n_draws", "status"]
    return pd.concat([summary, pd.DataFrame(gaps)], ignore_index=True)[order]


def reference_paths(context: Mapping) -> pd.DataFrame:
    """Central-parameter results under the fixed boom / neutral / bust external paths."""
    draw = central_draw(context["parameters"], context["inputs"])
    if context.get("programmes") is not None:
        draw.update(programs.central_programme_draw(context["programmes"], context["parameters"]))
    steps = max(context["target_years"]) - context["base_year"]
    frames = []
    for name in ("boom", "neutral", "bust"):
        path = external.reference_path(name, context["external_changes"], steps)
        effects = external.gdp_and_inflation_effects(path, context["parameters"])
        path_draw = dict(draw)
        if context.get("programmes") is not None:
            petroleum_factor = {}
            if "dlnp_pct" in path.columns:
                cumulative = np.exp(path["dlnp_pct"].to_numpy().cumsum() / 100.0)
                petroleum_factor = {
                    context["base_year"] + int(step): float(factor)
                    for step, factor in zip(path["step"], cumulative)
                }
            sale = privatisation.sale_paths(
                context["privatisation_inventory"], context.get("privatisation_package", "f5"),
                np.random.default_rng([SEED, 5]), context["privatisation_nominal_gdp_brl_million"],
                f5_target_pp=float(path_draw["flavio_privatisation_pp"]),
                base_year=context["base_year"], end_year=context["base_year"] + steps,
                petroleum_factor_by_year=petroleum_factor,
            )
            path_draw["privatisation_debt_adjustment_by_year"] = sale["debt_adjustment_by_year"]
            path_draw["privatisation_non_tax_revenue_by_year"] = sale["non_tax_revenue_by_year"]
        frame = evaluate_draw(path_draw, context, effects)
        frame.insert(0, "external_path", name)
        frames.append(frame.drop(columns="draw"))
    return pd.concat(frames, ignore_index=True)


def _git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=N_DRAWS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output-dir", default="outputs/runs")
    parser.add_argument("--rate-path", choices=("i1",), default=None,
                        help="sensitivity: add the proposed I1 annual offsets to every scenario's real rate")
    parser.add_argument("--programmes", action="store_true",
                        help="add the P1 2026 programme scenarios (config/programs_2026.yaml)")
    parser.add_argument("--programmes-common-composition", action="store_true",
                        help="P1 sensitivity: both programmes cut with the default package shares")
    parser.add_argument("--privatisation", choices=privatisation.PACKAGES, default="f5",
                        help="PZ sale package for programme scenarios (default: f5)")
    parser.add_argument("--tax-incidence", choices=("instrument", "uniform"), default="instrument",
                        help="household incidence for programme revenue changes (default: instrument)")
    parser.add_argument("--education-sensitivity", choices=tuple(education.EDUCATION_SENSITIVITIES), default="none",
                        help="ED historical-record/recomposition sensitivity (default: none)")
    args = parser.parse_args(argv)
    started = time.time()
    context = load_context()
    context["tax_incidence"] = args.tax_incidence
    context["education_sensitivity"] = args.education_sensitivity
    if args.rate_path == "i1":
        source = Path("config/i1_proposed.yaml")
        config = read_yaml(source)
        offsets = {
            int(row["year"]): float(row["difference_from_fixed_5_05_pp"])
            for row in config["s0_path_before_fiscal_term"]
        }
        context["inputs"].setdefault("derived", {})["real_rate_path_offset_pp"] = offsets
        context["real_rate_path"] = {
            "real_rate_path": "i1_proposed_offsets",
            "real_rate_path_offset_pp": offsets,
            "real_rate_path_source_file": str(source),
            "real_rate_path_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
    if args.programmes or args.programmes_common_composition:
        context["programmes"] = read_yaml("config/programs_2026.yaml")
        context["programme_common_composition"] = args.programmes_common_composition
        context["privatisation_package"] = args.privatisation
        context["privatisation_inventory"] = pd.read_csv(privatisation.INVENTORY_PATH)
        context["privatisation_nominal_gdp_brl_million"] = privatisation.nominal_gdp_by_year()[2025]
    draw_results, draws, metadata = run(args.draws, args.seed, context=context)
    summary = summarise(draw_results, args.draws)
    output = Path(args.output_dir)
    (output / "draws").mkdir(parents=True, exist_ok=True)
    summary.to_csv(output / "summary_percentiles.csv", index=False, float_format="%.6f")
    draw_results.to_csv(output / "draws" / "draw_results.csv.gz", index=False, float_format="%.6f")
    draws.to_csv(output / "draws" / "sampled_parameters.csv", index=False, float_format="%.8f")
    reference_paths(context).to_csv(output / "external_reference_paths.csv", index=False, float_format="%.6f")
    metadata.update({
        "inputs_commit": _git_commit(),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runtime_seconds": round(time.time() - started, 1),
    })
    (output / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"{args.draws} draws in {metadata['runtime_seconds']} s -> {output / 'summary_percentiles.csv'} ({len(summary)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
