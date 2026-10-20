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
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from src import external, social
from src.baseline import project_baseline, read_yaml
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
NOT_MODELLED = {
    "gini": "C3 pending",
    "top1_share": "C3 pending",
    "top10_share": "C3 pending",
    "poverty_rate": "C3 pending",
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
            spending = social.health_spending_per_capita(
                share, gdp[(year, scenario)], reduction, efficiency_share,
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
        "external_changes": external.historical_changes(data / "backtest_observed.csv"),
    }


def evaluate_draw(draw: Mapping, context: Mapping, external_effects: pd.DataFrame | None = None) -> pd.DataFrame:
    """Run C1 -> C2 -> C4 (+ C6 external path) for one draw, every variant and persistence setting."""
    annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
    draw_parameters = parameters_for_draw(context["parameters"], draw)
    draw_inputs = inputs_for_draw(context["inputs"], draw)
    target_years = context["target_years"]
    results = []
    for variant, variant_scenarios in context["variant_configs"].items():
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
            outcomes = social_for_draw(
                corner, annual, variant_scenarios, context["parameters"], context["base_inputs"], draw, target_years
            )
            merged = corner.merge(outcomes, on=["year", "scenario"], validate="one_to_one")
            merged["draw"], merged["variant"], merged["persistence"] = draw.get("draw", 0), variant, persistence
            results.append(merged[["draw", "variant", "persistence", "year", "scenario", *MACRO_OUTPUTS, *SOCIAL_OUTPUTS]])
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
    steps = max(context["target_years"]) - base_year
    draws, results = [], []
    for index in range(n_draws):
        draw = sample_draw(rng, parameters, inputs)
        draw["draw"] = index
        path = external.bootstrap_path(external_rng, context["external_changes"], steps)
        effects = external.gdp_and_inflation_effects(path, parameters)
        draw["external_tot_cumulative_change_pct"] = float(path["tot_change_pct"].sum())
        draw["external_fx_cumulative_change_pct"] = float(path["fx_change_pct"].sum())
        draws.append(draw)
        results.append(evaluate_draw(draw, context, effects))
    draw_results = pd.concat(results, ignore_index=True)
    metadata = {
        "seed": seed, "n_draws": n_draws, "variants": variant_names,
        "persistence": list(PERSISTENCE_VARIANTS), "horizons": horizons, "base_year": base_year,
        "sampled": {
            **{f"multiplier_{c}": "triangular(low, central, high) from fiscal_multipliers_brazil.accumulated" for c in MULTIPLIER_CATEGORIES},
            **{name: "triangular(low, central, high) from parameters.yaml macro inputs (C2)" for name in MACRO_RANGED},
            "efficiency_output_effect": "triangular(low, central, high) from macro_modelling_choices",
            "service_cut_fraction": "triangular(low, central, high) from social_modelling_choices",
            "imr_elasticity": "triangular(low, central, high) from social_outcome_elasticities",
            "pension_gdp_per_worker_weight": f"uniform(low, high), snapped to a {WEIGHT_GRID_STEP} grid",
            "revenue_elasticity": "uniform(0.92, 0.98) from revenue_elasticity_to_gdp (IFI EE16 long run; C2 deterministic rule is 1.0)",
            "leakage_share": "uniform(low, high) from governance.leakage_share_of_spending (cancels in scenario-vs-S0 comparisons; drives the leakage_halved sensitivity)",
            "profile_year": "discrete, equal probability over profile_years.values",
        },
        "fixed": {
            "life_expectancy_elasticity": "central only (point estimate)",
            "point_inputs": "every macro input with low = central = high (initial debt, revenue/GDP, capital share, K/Y, depreciation, GDP anchors)",
            "c1_category_shares": "point values (COFOG 2024)",
        },
        "external": "C6 block bootstrap (3-year blocks) of joint observed 2006-2024 terms-of-trade and BRL/USD changes, same path for every scenario in a draw; separate random stream [seed, 1]",
        "choices": [
            "triangular sampling for ranges is a modelling choice (fiscal_multipliers_brazil.sampling_rule), not a sourced distribution",
            "parameters are sampled independently: no sourced correlations",
            "persistence (transitory/persistent) is reported as a dimension, not sampled",
            "percentiles describe parameter uncertainty only, not forecast error or external shocks",
        ],
        "not_modelled": NOT_MODELLED,
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
    units = {**MACRO_OUTPUTS, **SOCIAL_OUTPUTS}
    summary["unit"] = summary["indicator"].map(units)
    summary["n_draws"] = n_draws
    summary["status"] = "modelled: parameter uncertainty only"
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
    steps = max(context["target_years"]) - context["base_year"]
    frames = []
    for name in ("boom", "neutral", "bust"):
        path = external.reference_path(name, context["external_changes"], steps)
        effects = external.gdp_and_inflation_effects(path, context["parameters"])
        frame = evaluate_draw(draw, context, effects)
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
    args = parser.parse_args(argv)
    started = time.time()
    context = load_context()
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
