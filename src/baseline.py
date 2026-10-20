"""Age-profile baseline for Brazilian general-government primary spending.

S0 applies fixed age-cost profiles to the IBGE population projection. Health
and education costs are held fixed relative to GDP per capita. Pension costs
range from GDP-per-capita indexation (low) to GDP-per-working-age-person
indexation (high). S1 holds every base-year category share, and therefore total
primary spending, constant as a share of GDP.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd
import yaml


VARIANTS = ("low", "central", "high")
AGE_CATEGORIES = ("pension", "health", "education")
OUTPUT_CATEGORIES = (*AGE_CATEGORIES, "non_age_related", "total")


def read_yaml(path: str | Path) -> dict:
    """Read a YAML mapping, rejecting empty or non-mapping documents."""
    with Path(path).open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return value


def latest_complete_base_year(fiscal: pd.DataFrame) -> tuple[int, float]:
    """Return the latest four-quarter year and its primary-spending share."""
    required = {"year", "quarters_observed", "primary_spending_pct_gdp"}
    missing = required - set(fiscal.columns)
    if missing:
        raise ValueError(f"Fiscal data missing columns: {sorted(missing)}")
    complete = fiscal.loc[fiscal["quarters_observed"].eq(4)].dropna(
        subset=["primary_spending_pct_gdp"]
    )
    if complete.empty:
        raise ValueError("Fiscal data have no complete four-quarter year")
    row = complete.sort_values("year").iloc[-1]
    return int(row["year"]), float(row["primary_spending_pct_gdp"])


def _age_band_bounds(label: str) -> tuple[int, int]:
    text = str(label).strip().replace(" ", "")
    if text.endswith("+"):
        return int(text[:-1]), 10_000
    if "-" not in text:
        age = int(text)
        return age, age
    low, high = text.split("-", maxsplit=1)
    high = high.rstrip("+")
    return int(low), int(high)


def expand_age_profiles(profiles: pd.DataFrame, ages: Iterable[int]) -> pd.DataFrame:
    """Expand profiles to population ages, mapping every age 90+ to age 90."""
    required = {"category", "relative_cost_per_capita"}
    missing = required - set(profiles.columns)
    if missing:
        raise ValueError(f"Age profiles missing columns: {sorted(missing)}")
    if not ({"age", "age_band"} & set(profiles.columns)):
        raise ValueError("Age profiles require either age or age_band")

    records: list[dict] = []
    target_ages = sorted({int(age) for age in ages})
    if target_ages and target_ages[0] < 0:
        raise ValueError("Population ages cannot be negative")
    for category in AGE_CATEGORIES:
        subset = profiles.loc[profiles["category"].eq(category)]
        if subset.empty:
            raise ValueError(f"No age profile for {category}")
        for age in target_ages:
            if "age" in subset.columns and subset["age"].notna().any():
                profile_age = min(age, 90)
                matches = subset.loc[pd.to_numeric(subset["age"]).eq(profile_age)]
            else:
                mask = subset["age_band"].map(
                    lambda band: _age_band_bounds(band)[0]
                    <= age
                    <= _age_band_bounds(band)[1]
                )
                matches = subset.loc[mask]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one {category} profile value for age {age}; "
                    f"found {len(matches)}"
                )
            value = float(matches.iloc[0]["relative_cost_per_capita"])
            if value < 0:
                raise ValueError("Relative age costs cannot be negative")
            records.append({"category": category, "age": age, "cost": value})
    return pd.DataFrame.from_records(records)


def prepare_population(population: pd.DataFrame) -> pd.DataFrame:
    """Select Brazil, both sexes, with one observation per year and age."""
    required = {"age", "year", "population"}
    missing = required - set(population.columns)
    if missing:
        raise ValueError(f"Population data missing columns: {sorted(missing)}")
    data = population.copy()
    if "iso3" in data.columns:
        data = data.loc[data["iso3"].eq("BR")]
    if "sex" in data.columns:
        both = data.loc[data["sex"].eq("Ambos")]
        if not both.empty:
            data = both
        else:
            data = (
                data.groupby(["year", "age"], as_index=False, observed=True)["population"]
                .sum()
            )
    data = data.loc[:, ["year", "age", "population"]].copy()
    data[["year", "age"]] = data[["year", "age"]].astype(int)
    data["population"] = pd.to_numeric(data["population"], errors="raise")
    if data.duplicated(["year", "age"]).any():
        raise ValueError("Population contains duplicate year-age observations")
    if (data["population"] < 0).any():
        raise ValueError("Population cannot be negative")
    return data


def _parameter(inputs: Mapping, name: str, variant: str) -> float:
    try:
        entry = inputs["baseline"][name]
        return float(entry[variant])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Missing numeric baseline.{name}.{variant}") from exc


def _profile_index(
    population: pd.DataFrame,
    expanded_profiles: pd.DataFrame,
    category: str,
    year: int,
) -> tuple[float, float]:
    year_pop = population.loc[population["year"].eq(year), ["age", "population"]]
    costs = expanded_profiles.loc[
        expanded_profiles["category"].eq(category), ["age", "cost"]
    ]
    merged = year_pop.merge(costs, on="age", how="left", validate="one_to_one")
    if merged.empty or merged["cost"].isna().any():
        raise ValueError(f"Incomplete {category} profile for population year {year}")
    total = float(merged["population"].sum())
    if total <= 0:
        raise ValueError(f"Population is zero in {year}")
    weighted_sum = float((merged["population"] * merged["cost"]).sum())
    return weighted_sum, total


def project_baseline(
    fiscal: pd.DataFrame,
    population: pd.DataFrame,
    profiles: pd.DataFrame,
    inputs: Mapping,
    horizons: Iterable[int] = (5, 10, 15, 20),
) -> pd.DataFrame:
    """Project S0/S1 and envelope profile-vintage/indexation combinations."""
    base_year, base_total = latest_complete_base_year(fiscal)
    pop = prepare_population(population)
    years = [base_year, *(base_year + int(h) for h in horizons)]
    if len(years) != len(set(years)):
        raise ValueError("Horizons must be unique and cannot include zero")
    missing_years = sorted(set(years) - set(pop["year"]))
    if missing_years:
        raise ValueError(f"Population missing projection years: {missing_years}")
    shares = {
        category: _parameter(inputs, f"{category}_gdp_share", "central")
        for category in AGE_CATEGORIES
    }
    non_age = base_total - sum(shares.values())
    if non_age < 0:
        raise ValueError("Age-related shares exceed primary spending")
    worker_min = int(_parameter(inputs, "working_age_min", "central"))
    worker_max = int(_parameter(inputs, "working_age_max", "central"))
    if worker_min > worker_max:
        raise ValueError("working_age_min exceeds working_age_max")
    worker_counts = {
        year: float(
            pop.loc[
                pop["year"].eq(year)
                & pop["age"].between(worker_min, worker_max),
                "population",
            ].sum()
        )
        for year in years
    }
    if min(worker_counts.values()) <= 0:
        raise ValueError("Working-age population is zero")

    weights = {
        variant: _parameter(inputs, "pension_gdp_per_worker_weight", variant)
        for variant in VARIANTS
    }
    if any(not 0 <= weight <= 1 for weight in weights.values()):
        raise ValueError("pension_gdp_per_worker_weight must lie in [0, 1]")

    if "profile_year" in profiles.columns and profiles["profile_year"].notna().any():
        vintages: list[int | None] = sorted(
            pd.to_numeric(profiles["profile_year"], errors="raise").astype(int).unique()
        )
        configured = inputs.get("baseline", {}).get("profile_years", {}).get("values")
        if configured is not None:
            requested = [int(value) for value in configured]
            if set(requested) != set(vintages):
                raise ValueError(
                    f"Configured profile years {requested} do not match data {vintages}"
                )
            vintages = requested
        central_vintage = int(
            inputs.get("baseline", {})
            .get("central_profile_year", {})
            .get("value", max(v for v in vintages if v is not None))
        )
        if central_vintage not in vintages:
            raise ValueError("central_profile_year is not available in profiles")
    else:
        vintages = [None]
        central_vintage = None

    stats_by_vintage: dict[int | None, dict[tuple[str, int], tuple[float, float]]] = {}
    for vintage in vintages:
        vintage_profiles = (
            profiles
            if vintage is None
            else profiles.loc[
                pd.to_numeric(profiles["profile_year"]).astype(int).eq(vintage)
            ]
        )
        expanded = expand_age_profiles(vintage_profiles, pop["age"].unique())
        stats_by_vintage[vintage] = {
            (category, year): _profile_index(pop, expanded, category, year)
            for category in AGE_CATEGORIES
            for year in years
        }

    combinations: dict[tuple[int | None, str], dict[int, dict[str, float]]] = {}
    for vintage in vintages:
        profile_stats = stats_by_vintage[vintage]
        for weight_case, pension_worker_weight in weights.items():
            projected: dict[int, dict[str, float]] = {}
            for year in years:
                s0: dict[str, float] = {"non_age_related": non_age}
                for category in AGE_CATEGORIES:
                    weighted, total_pop = profile_stats[(category, year)]
                    base_weighted, base_pop = profile_stats[(category, base_year)]
                    per_capita_multiplier = (weighted / total_pop) / (
                        base_weighted / base_pop
                    )
                    multiplier = per_capita_multiplier
                    if category == "pension":
                        per_worker_multiplier = (weighted / worker_counts[year]) / (
                            base_weighted / worker_counts[base_year]
                        )
                        multiplier = (
                            per_capita_multiplier ** (1 - pension_worker_weight)
                            * per_worker_multiplier**pension_worker_weight
                        )
                    s0[category] = shares[category] * multiplier
                s0["total"] = sum(
                    s0[category] for category in OUTPUT_CATEGORIES[:-1]
                )
                projected[year] = s0
            combinations[(vintage, weight_case)] = projected

    central_key = (central_vintage, "central")
    s1 = {**shares, "non_age_related": non_age, "total": base_total}
    records: list[dict] = []
    for year in years:
        ranked = sorted(
            combinations,
            key=lambda key: combinations[key][year]["total"],
        )
        selected = {
            "low": ranked[0],
            "central": central_key,
            "high": ranked[-1],
        }
        for variant, key in selected.items():
            vintage, weight_case = key
            s0 = combinations[key][year]
            for scenario, values in (("S0", s0), ("S1", s1)):
                for category in OUTPUT_CATEGORIES:
                    records.append(
                        {
                            "year": year,
                            "scenario": scenario,
                            "variant": variant,
                            "category": category,
                            "spending_pct_gdp": values[category],
                            "drift_pct_gdp": s0[category] - s1[category],
                            "profile_year": vintage,
                            "pension_indexation_case": weight_case,
                            "pension_gdp_per_worker_weight": weights[weight_case],
                        }
                    )

    result = pd.DataFrame.from_records(records)
    return result.sort_values(
        ["year", "scenario", "variant", "category"], ignore_index=True
    )


def _horizons_from_scenarios(path: str | Path) -> list[int]:
    config = read_yaml(path)
    try:
        return [int(value) for value in config["horizons_years"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid horizons_years in {path}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fiscal", default="data/brazil/fiscal.csv")
    parser.add_argument("--population", default="data/brazil/population.csv")
    parser.add_argument("--profiles", default="data/brazil/age_profiles.csv")
    parser.add_argument("--inputs", default="config/parameters.yaml")
    parser.add_argument("--scenarios", default="config/scenarios.yaml")
    parser.add_argument("--output", default="data/brazil/baseline.csv")
    args = parser.parse_args(argv)

    fiscal = pd.read_csv(args.fiscal)
    population = pd.read_csv(args.population)
    profiles = pd.read_csv(args.profiles)
    inputs = read_yaml(args.inputs)
    horizons = _horizons_from_scenarios(args.scenarios)
    result = project_baseline(fiscal, population, profiles, inputs, horizons)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False, float_format="%.10f")

    base_year, _ = latest_complete_base_year(fiscal)
    ten_year = result.loc[
        result["year"].eq(base_year + 10)
        & result["scenario"].eq("S0")
        & result["category"].eq("total"),
        ["variant", "drift_pct_gdp"],
    ]
    drift_by_variant = ten_year.set_index("variant")["drift_pct_gdp"]
    summary = ", ".join(
        f"{variant}={drift_by_variant.loc[variant]:.3f} pp" for variant in VARIANTS
    )
    print(f"Wrote {len(result)} rows to {output}; 10-year S0-S1 drift: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
