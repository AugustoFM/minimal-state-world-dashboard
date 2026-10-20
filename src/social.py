"""Brazil social outcomes block.

The public functions operate on data frames and mappings so D1 can replace
deterministic parameter corners with Monte Carlo draws.  The CLI reads the C1
and C2 published outputs and writes sensitivity envelopes, not forecasts.
"""

from __future__ import annotations

import argparse
import json
import re
from itertools import product
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

from src.baseline import read_yaml


VARIANTS = ("low", "central", "high")
PERSISTENCE_VARIANTS = ("transitory", "persistent")
MODELLED_INDICATORS = (
    "real_public_health_spending_pc_change_vs_base_pct",
    "real_public_health_spending_pc_change_vs_s0_pct",
    "infant_mortality_per_1000",
    "infant_mortality_difference_vs_s0",
    "life_expectancy_years",
    "life_expectancy_difference_vs_s0_years",
    "hdi_health_index",
    "hdi_health_index_difference_vs_s0",
)
UNITS = {
    "real_public_health_spending_pc_change_vs_base_pct": "percent",
    "real_public_health_spending_pc_change_vs_s0_pct": "percent",
    "infant_mortality_per_1000": "per_1000_live_births",
    "infant_mortality_difference_vs_s0": "per_1000_live_births",
    "life_expectancy_years": "years",
    "life_expectancy_difference_vs_s0_years": "years",
    "hdi_health_index": "index_0_to_1",
    "hdi_health_index_difference_vs_s0": "index_0_to_1",
}


class MissingSocialParameter(ValueError):
    """Raised when a required C4 parameter is absent, null, or invalid."""


def _require(mapping: Mapping, path: str):
    value = mapping
    try:
        for key in path.split("."):
            value = value[key]
    except (KeyError, TypeError) as exc:
        raise MissingSocialParameter(f"Missing required social parameter: {path}") from exc
    if value is None:
        raise MissingSocialParameter(f"Required social parameter is null: {path}")
    return value


def _required_number(mapping: Mapping, path: str) -> float:
    value = _require(mapping, path)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MissingSocialParameter(f"Required social parameter is not numeric: {path}") from exc
    if not pd.notna(number):
        raise MissingSocialParameter(f"Required social parameter is not finite: {path}")
    return number


def load_latest_world_bank_value(path: str | Path, locator: Mapping) -> dict:
    """Read the latest non-null WDI observation identified by the locator."""
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        raise ValueError(f"Unexpected World Bank response in {path}")
    rows = payload[1]
    iso3 = str(_require(locator, "country_iso3"))
    indicator_code = str(_require(locator, "indicator_code"))
    matches = [
        row for row in rows
        if row.get("countryiso3code") == iso3
        and row.get("indicator", {}).get("id") == indicator_code
        and row.get("value") is not None
    ]
    if not matches:
        raise ValueError(f"No {indicator_code} observation for {iso3} in {path}")
    row = max(matches, key=lambda item: int(item["date"]))
    return {"year": int(row["date"]), "value": float(row["value"])}


def load_latest_undp_value(path: str | Path, locator: Mapping) -> dict:
    """Read the latest non-null UNDP observation identified by the locator."""
    with Path(path).open(encoding="utf-8") as handle:
        rows = json.load(handle)
    iso3 = str(_require(locator, "country_iso3"))
    indicator_code = str(_require(locator, "indicator_code"))
    matches = [
        row for row in rows
        if row.get("countryIsoCode") == iso3
        and row.get("indicatorCode") == indicator_code
        and row.get("actualValue") not in (None, "")
    ]
    if not matches:
        raise ValueError(f"No {indicator_code} observation for {iso3} in {path}")
    row = max(matches, key=lambda item: int(item["year"]))
    return {"year": int(row["year"]), "value": float(row["actualValue"])}


def load_social_inputs(path: str | Path) -> dict:
    """Resolve the raw-file locators in the C4 input register."""
    inputs = read_yaml(path)
    imr = _require(inputs, "infant_mortality")
    le = _require(inputs, "life_expectancy")
    return {
        "infant_mortality": load_latest_world_bank_value(_require(imr, "path"), imr),
        "life_expectancy": load_latest_undp_value(_require(le, "path"), le),
    }


def build_up_factor(horizon_years: int | float, full_effect_years: int | float = 10) -> float:
    """Linear ramp to one, capped at the configured full-effect horizon."""
    horizon = float(horizon_years)
    full = float(full_effect_years)
    if horizon < 0 or full <= 0:
        raise ValueError("Build-up horizons must be non-negative and full_effect_years positive")
    return min(horizon / full, 1.0)


def apply_spending_elasticity(
    base_value: float,
    health_spending_change_pct: float,
    elasticity: float,
    horizon_years: int | float,
    full_effect_years: int | float = 10,
) -> float:
    """Apply a symmetric percent elasticity with a linear time build-up."""
    proportional_effect = (
        float(elasticity)
        * float(health_spending_change_pct) / 100.0
        * build_up_factor(horizon_years, full_effect_years)
    )
    return float(base_value) * (1.0 + proportional_effect)


def hdi_health_index(life_expectancy: float, lower_goalpost: float = 20, upper_goalpost: float = 85) -> float:
    """UNDP health index from life expectancy and its goalposts."""
    if upper_goalpost <= lower_goalpost:
        raise ValueError("HDI upper goalpost must exceed lower goalpost")
    return (float(life_expectancy) - lower_goalpost) / (upper_goalpost - lower_goalpost)


def health_spending_per_capita(
    health_share_gdp: float,
    real_gdp_per_capita: float,
    reduction_pct_gdp: float = 0.0,
    efficiency_package_share: float = 0.0,
    health_allocation_share: float = 0.0,
    service_cut_fraction: float = 0.0,
) -> float:
    """Real public health spending per capita under the C4 measure."""
    adjusted_share = float(health_share_gdp) - (
        float(reduction_pct_gdp)
        * float(efficiency_package_share)
        * float(health_allocation_share)
        * float(service_cut_fraction)
    )
    if adjusted_share < 0:
        raise ValueError("Health spending share cannot be negative")
    return adjusted_share / 100.0 * float(real_gdp_per_capita)


def _percentage_change(value: float, reference: float) -> float:
    if reference <= 0:
        raise ValueError("Percentage-change reference must be positive")
    return (value / reference - 1.0) * 100.0


def _parse_build_up_years(choices: Mapping) -> float:
    rule = str(_require(choices, "elasticity_build_up.rule"))
    match = re.search(r"over\s+(\d+(?:\.\d+)?)\s+years", rule, flags=re.IGNORECASE)
    if not match:
        raise MissingSocialParameter("Could not parse full-effect years from social_modelling_choices.elasticity_build_up.rule")
    return float(match.group(1))


def _parse_hdi_goalposts(choices: Mapping) -> tuple[float, float]:
    rule = str(_require(choices, "life_expectancy_to_hdi.rule"))
    match = re.search(r"\(\s*LE\s*-\s*([\d.]+)\s*\)\s*/\s*\(\s*([\d.]+)\s*-\s*([\d.]+)\s*\)", rule, flags=re.IGNORECASE)
    if not match or float(match.group(1)) != float(match.group(3)):
        raise MissingSocialParameter("Could not parse HDI goalposts from social_modelling_choices.life_expectancy_to_hdi.rule")
    return float(match.group(1)), float(match.group(2))


def _validate_parameters(parameters: Mapping, scenarios: Mapping) -> dict:
    choices = _require(parameters, "social_modelling_choices")
    elasticities = _require(parameters, "social_outcome_elasticities")
    _require(choices, "health_spending_measure")
    allocation = _require(choices, "reduction_hitting_health_education.allocation")
    if allocation != "cofog_2024_proportional":
        raise MissingSocialParameter(f"Unsupported health/education allocation: {allocation}")
    service_cuts = {
        variant: _required_number(choices, f"reduction_hitting_health_education.service_cut_fraction.{variant}")
        for variant in VARIANTS
    }
    if any(value < 0 or value > 1 for value in service_cuts.values()):
        raise MissingSocialParameter("service_cut_fraction values must lie in [0, 1]")
    imr_elasticities = {
        variant: _required_number(elasticities, f"infant_mortality_wrt_public_health_spending.{variant}")
        for variant in VARIANTS
    }
    le_central = _required_number(elasticities, "life_expectancy_wrt_health_spending.central")
    _require(choices, "cuts_vs_increases.rule")
    not_modelled = _require(choices, "not_modelled")
    if not isinstance(not_modelled, list):
        raise MissingSocialParameter("social_modelling_choices.not_modelled must be a list")
    efficiency_share = _required_number(scenarios, "package_shares.efficiency_health_education_admin")
    return {
        "choices": choices,
        "service_cuts": service_cuts,
        "imr_elasticities": imr_elasticities,
        "le_central": le_central,
        "build_up_years": _parse_build_up_years(choices),
        "hdi_goalposts": _parse_hdi_goalposts(choices),
        "not_modelled": not_modelled,
        "efficiency_share": efficiency_share,
    }


def _health_rows(baseline: pd.DataFrame) -> pd.DataFrame:
    required = {"year", "scenario", "variant", "category", "spending_pct_gdp"}
    missing = required - set(baseline.columns)
    if missing:
        raise ValueError(f"C1 baseline missing columns: {sorted(missing)}")
    rows = baseline.loc[baseline["category"].eq("health"), ["year", "scenario", "variant", "spending_pct_gdp"]].copy()
    rows["year"] = rows["year"].astype(int)
    return rows


def _macro_gdp_rows(macro: pd.DataFrame) -> pd.DataFrame:
    required = {"year", "scenario", "variant", "persistence", "indicator", "value"}
    missing = required - set(macro.columns)
    if missing:
        raise ValueError(f"C2 macro output missing columns: {sorted(missing)}")
    rows = macro.loc[macro["indicator"].eq("gdp_per_capita")].copy()
    rows["year"] = rows["year"].astype(int)
    return rows


def _not_modelled_name_reason(entry: str) -> tuple[str, str]:
    text = str(entry)
    name, separator, reason = text.partition(":")
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug, reason.strip() if separator else text


def _combination(**parts: str) -> str:
    return ";".join(f"{key}={value}" for key, value in parts.items())


def _lookup_one(frame: pd.DataFrame, description: str, **filters) -> float:
    selected = frame
    for column, value in filters.items():
        selected = selected.loc[selected[column].eq(value)]
    if len(selected) != 1:
        raise ValueError(f"Expected one {description} row for {filters}, found {len(selected)}")
    column = "spending_pct_gdp" if "spending_pct_gdp" in selected.columns else "value"
    return float(selected.iloc[0][column])


def project_social(
    baseline: pd.DataFrame,
    macro: pd.DataFrame,
    scenarios: Mapping,
    parameters: Mapping,
    base_inputs: Mapping,
    base_gdp_per_capita: Mapping,
    horizons: Iterable[int] = (5, 10, 15, 20),
) -> pd.DataFrame:
    """Project C4 indicators and return sensitivity envelopes with provenance."""
    spec = _validate_parameters(parameters, scenarios)
    health = _health_rows(baseline)
    gdp = _macro_gdp_rows(macro)
    base_year = int(health["year"].min())
    horizons = [int(value) for value in horizons]
    target_years = {base_year + horizon: horizon for horizon in horizons}
    configured = _require(scenarios, "scenarios")
    scenario_names = [name for name in ("S0", "S1", "R_mod", "R_amb", "R_max") if name in configured]
    base_imr = _required_number(base_inputs, "infant_mortality.value")
    base_imr_year = int(_required_number(base_inputs, "infant_mortality.year"))
    base_le = _required_number(base_inputs, "life_expectancy.value")
    base_le_year = int(_required_number(base_inputs, "life_expectancy.year"))
    lower_goalpost, upper_goalpost = spec["hdi_goalposts"]

    base_health = {
        variant: _lookup_one(health, "base C1 health", year=base_year, scenario="S0", variant=variant)
        for variant in VARIANTS
    }
    base_gdp = {variant: _required_number(base_gdp_per_capita, variant) for variant in VARIANTS}
    education_base = baseline.loc[
        baseline["year"].eq(base_year) & baseline["scenario"].eq("S0") & baseline["category"].eq("education")
    ]
    if education_base.empty:
        raise ValueError("C1 baseline has no base-year S0 education share for proportional allocation")
    health_allocation = base_health["central"] / (
        base_health["central"] + float(education_base.loc[education_base["variant"].eq("central"), "spending_pct_gdp"].iloc[0])
    )

    raw_records: list[dict] = []
    for year, horizon in target_years.items():
        for scenario in scenario_names:
            scenario_config = configured[scenario] or {}
            reduction = 0.0
            if scenario.startswith("R_"):
                by_year = scenario_config.get("by_year", {})
                reduction_value = by_year.get(horizon, by_year.get(str(horizon)))
                if reduction_value is None:
                    raise MissingSocialParameter(f"Missing scenario reduction: scenarios.{scenario}.by_year.{horizon}")
                reduction = float(reduction_value)
            c1_source = "S1" if scenario == "S1" else "S0"
            service_variants = ("central",) if scenario in ("S0", "S1") else VARIANTS
            for c1_variant, c2_variant, persistence, service_variant, elasticity_variant in product(
                VARIANTS, VARIANTS, PERSISTENCE_VARIANTS, service_variants, VARIANTS
            ):
                c1_share = _lookup_one(health, "C1 health", year=year, scenario=c1_source, variant=c1_variant)
                scenario_gdp = _lookup_one(
                    gdp, "C2 GDP per capita", year=year, scenario=scenario,
                    variant=c2_variant, persistence=persistence,
                )
                s0_gdp = _lookup_one(
                    gdp, "C2 S0 GDP per capita", year=year, scenario="S0",
                    variant=c2_variant, persistence=persistence,
                )
                service_cut = spec["service_cuts"][service_variant]
                spending = health_spending_per_capita(
                    c1_share, scenario_gdp, reduction, spec["efficiency_share"],
                    health_allocation, service_cut,
                )
                s0_share = _lookup_one(health, "C1 S0 health", year=year, scenario="S0", variant=c1_variant)
                s0_spending = health_spending_per_capita(s0_share, s0_gdp)
                base_spending = health_spending_per_capita(base_health[c1_variant], base_gdp[c2_variant])
                change_base = _percentage_change(spending, base_spending)
                change_s0 = _percentage_change(spending, s0_spending)
                imr = apply_spending_elasticity(
                    base_imr, change_s0, spec["imr_elasticities"][elasticity_variant],
                    horizon, spec["build_up_years"],
                )
                le = apply_spending_elasticity(
                    base_le, change_s0, spec["le_central"], horizon, spec["build_up_years"]
                )
                health_index = hdi_health_index(le, lower_goalpost, upper_goalpost)
                base_health_index = hdi_health_index(base_le, lower_goalpost, upper_goalpost)
                imr_combo = _combination(
                    elasticity=elasticity_variant,
                    service_cut_fraction=service_variant,
                    c1=c1_variant,
                    c2=c2_variant,
                    persistence=persistence,
                )
                health_combo = _combination(
                    elasticity="not_applicable",
                    service_cut_fraction=service_variant,
                    c1=c1_variant,
                    c2=c2_variant,
                    persistence=persistence,
                )
                le_combo = _combination(
                    elasticity="central_only",
                    service_cut_fraction=service_variant,
                    c1=c1_variant,
                    c2=c2_variant,
                    persistence=persistence,
                )
                values = [
                    ("infant_mortality_per_1000", imr, imr_combo),
                    ("infant_mortality_difference_vs_s0", imr - base_imr, imr_combo),
                ]
                # Health spending has no elasticity dimension, and the LE source
                # reports only a central elasticity. Avoid duplicating those rows
                # across the three IMR elasticity corners.
                if elasticity_variant == "central":
                    values.extend([
                        ("real_public_health_spending_pc_change_vs_base_pct", change_base, health_combo),
                        ("real_public_health_spending_pc_change_vs_s0_pct", change_s0, health_combo),
                        ("life_expectancy_years", le, le_combo),
                        ("life_expectancy_difference_vs_s0_years", le - base_le, le_combo),
                        ("hdi_health_index", health_index, le_combo),
                        ("hdi_health_index_difference_vs_s0", health_index - base_health_index, le_combo),
                    ])
                for indicator, value, combo in values:
                    raw_records.append({
                        "year": year, "horizon": horizon, "scenario": scenario,
                        "indicator": indicator, "value": value, "combination": combo,
                        "is_central": (
                            c1_variant == c2_variant == service_variant == elasticity_variant == "central"
                            and persistence == "transitory"
                        ),
                    })

    raw = pd.DataFrame(raw_records)
    output: list[dict] = []
    status_modelled = (
        f"modelled sensitivity envelope; IMR base {base_imr_year}; LE base {base_le_year}; "
        "S0 no trend assumed; LE elasticity central only; symmetric cuts-vs-increases caveat applies"
    )
    for keys, group in raw.groupby(["year", "horizon", "scenario", "indicator"], sort=True):
        year, horizon, scenario, indicator = keys
        central_rows = group.loc[group["is_central"]]
        if len(central_rows) != 1:
            raise ValueError(f"Expected one central social corner for {keys}, found {len(central_rows)}")
        bounds = {
            "low": group.loc[group["value"].idxmin()],
            "central": central_rows.iloc[0],
            "high": group.loc[group["value"].idxmax()],
        }
        for variant, bound in bounds.items():
            output.append({
                "year": year, "horizon": horizon, "scenario": scenario,
                "variant": variant, "indicator": indicator, "value": float(bound["value"]),
                "unit": UNITS[indicator], "status": status_modelled,
                "bound_combination": bound["combination"],
            })

    for year, horizon in target_years.items():
        for scenario, variant, entry in product(scenario_names, VARIANTS, spec["not_modelled"]):
            indicator, reason = _not_modelled_name_reason(entry)
            output.append({
                "year": year, "horizon": horizon, "scenario": scenario,
                "variant": variant, "indicator": indicator, "value": None,
                "unit": "", "status": f"not_modelled: {reason}", "bound_combination": "",
            })
    columns = ["year", "horizon", "scenario", "variant", "indicator", "value", "unit", "status", "bound_combination"]
    return pd.DataFrame(output, columns=columns).sort_values(
        ["year", "scenario", "indicator", "variant"], ignore_index=True
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", default="config/parameters.yaml")
    parser.add_argument("--scenarios", default="config/scenarios.yaml")
    parser.add_argument("--inputs", default="config/c4_inputs_proposed.yaml")
    parser.add_argument("--c2-inputs", default="config/parameters.yaml")
    parser.add_argument("--baseline", default="data/brazil/baseline.csv")
    parser.add_argument("--macro", default="data/brazil/macro.csv")
    parser.add_argument("--output", default="data/brazil/social.csv")
    args = parser.parse_args(argv)

    scenarios = read_yaml(args.scenarios)
    c2_inputs = read_yaml(args.c2_inputs)
    result = project_social(
        pd.read_csv(args.baseline), pd.read_csv(args.macro), scenarios,
        read_yaml(args.parameters), load_social_inputs(args.inputs),
        _require(c2_inputs, "macro.base_gdp_per_capita"), scenarios["horizons_years"],
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False, float_format="%.10f")
    print(f"Wrote {len(result)} rows to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
