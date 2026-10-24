"""E3 older-people income, indexation, health-price and SUS analysis.

The module is offline and deterministic. It reads the archived PNAD, SIDRA,
C1 population/profile, baseline and macro files without modifying them.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from src.baseline import prepare_population, read_yaml
from src.micro import (
    EXCLUDED_CONDITIONS,
    calculate_indicators,
    simulate_household_incomes,
)


ROOT = Path(__file__).resolve().parents[1]
POVERTY_LINES = {"218": 218.0, "759": 759.0}
AGE_GROUPS = ("0-14", "15-29", "30-64", "65+")
DETAILED_INCOME = {
    "labour": ("labor_income_nominal_brl",),
    "pension": ("retirement_pension_income_brl",),
    "bpc": ("bpc_income_brl",),
    "bolsa_familia": ("bolsa_familia_income_brl",),
    "other": (
        "other_program_income_brl",
        "unemployment_insurance_income_brl",
        "private_transfer_income_brl",
        "rent_income_brl",
        "financial_and_other_income_brl",
    ),
}
PRICE_FILES = {
    "IPCA": (
        ROOT / "data/raw/brazil/rates/ibge_sidra_1419_ipca_items_2012_2019.json",
        ROOT / "data/raw/brazil/rates/ibge_sidra_7060_ipca_items_2020on.json",
    ),
    "INPC": (
        ROOT / "data/raw/brazil/rates/ibge_sidra_1100_inpc_items_2012_2019.json",
        ROOT / "data/raw/brazil/rates/ibge_sidra_7063_inpc_items_2020on.json",
    ),
}


def _weighted_rate(mask: np.ndarray, weights: np.ndarray) -> float:
    denominator = float(np.sum(weights))
    return float(100 * np.sum(weights[np.asarray(mask, dtype=bool)]) / denominator)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.average(np.asarray(values, dtype=float), weights=weights))


def _weighted_deciles(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Assign stable person-weighted deciles using each record's weight midpoint."""
    order = np.argsort(values, kind="mergesort")
    ranked = np.empty(len(values), dtype=int)
    cumulative = np.cumsum(weights[order]) - weights[order] / 2
    ranked[order] = np.minimum(10, np.floor(10 * cumulative / weights.sum()).astype(int) + 1)
    return ranked


def _profile_record(
    data: pd.DataFrame,
    row_type: str,
    age_group: str,
    decile: str,
    minimum_wage_brl: float,
) -> dict:
    weights = data["survey_weight"].to_numpy(dtype=float)
    income = data["household_income_per_capita_brl"].to_numpy(dtype=float)
    without = data["income_without_pension_bpc_pc"].to_numpy(dtype=float)
    denominator = float(np.sum(income * weights))
    record: dict[str, object] = {
        "row_type": row_type,
        "age_group": age_group,
        "income_decile": decile,
        "weighted_population": float(weights.sum()),
        "mean_household_income_per_capita_brl": _weighted_mean(income, weights),
        "household_income_pension_bpc_share_pct": float(
            100
            * np.sum(data["pension_bpc_pc"].to_numpy(dtype=float) * weights)
            / denominator
        ),
    }
    pension = data["retirement_pension_income_brl"].to_numpy(dtype=float)
    bpc = data["bpc_income_brl"].to_numpy(dtype=float)
    pension_recipient = pension > 0
    pension_recipient_weight = float(weights[pension_recipient].sum())
    record["pension_recipient_pct"] = _weighted_rate(pension_recipient, weights)
    record["bpc_recipient_pct"] = _weighted_rate(bpc > 0, weights)
    record["pension_at_or_below_1_01_minimum_wage_pct_of_recipients"] = (
        float(
            100
            * weights[pension_recipient & (pension <= 1.01 * minimum_wage_brl)].sum()
            / pension_recipient_weight
        )
        if pension_recipient_weight > 0 else float("nan")
    )
    for name, line in POVERTY_LINES.items():
        record[f"poverty_{name}_pct"] = _weighted_rate(income < line, weights)
        record[f"poverty_{name}_without_pension_bpc_pct"] = _weighted_rate(
            without < line, weights
        )
    for component in DETAILED_INCOME:
        values = data[f"{component}_pc"].to_numpy(dtype=float)
        record[f"income_share_{component}_pct"] = float(
            100 * np.sum(values * weights) / denominator
        )
    residual = income - sum(
        data[f"{component}_pc"].to_numpy(dtype=float)
        for component in DETAILED_INCOME
    )
    record["income_share_residual_pct"] = float(
        100 * np.sum(residual * weights) / denominator
    )
    return record


def build_elderly_profile(
    persons: pd.DataFrame,
    minimum_wage_brl: float = 1518.0,
) -> pd.DataFrame:
    """Build age/decile income profiles and the older-recipient household row."""
    required = {
        "hh_id", "survey_weight", "household_condition", "age",
        "household_income_per_capita_brl",
        *(column for columns in DETAILED_INCOME.values() for column in columns),
    }
    missing = required - set(persons.columns)
    if missing:
        raise ValueError(f"PNAD input missing columns: {sorted(missing)}")
    data = persons.loc[~persons["household_condition"].isin(EXCLUDED_CONDITIONS)].copy()
    component_columns = [column for columns in DETAILED_INCOME.values() for column in columns]
    data[component_columns] = data[component_columns].fillna(0.0)
    if data[["age", "survey_weight", "household_income_per_capita_brl"]].isna().any().any():
        raise ValueError("Eligible PNAD records have missing age, weight or household income")

    grouped = data.groupby("hh_id", sort=False)
    hh = grouped[component_columns].sum()
    hh["income_unit_size"] = grouped.size()
    hh["older_recipient"] = grouped.apply(
        lambda group: bool(
            ((group["age"] >= 65)
             & ((group["retirement_pension_income_brl"] + group["bpc_income_brl"]) > 0)).any()
        ),
        include_groups=False,
    )
    for component, columns in DETAILED_INCOME.items():
        hh[f"{component}_pc"] = hh[list(columns)].sum(axis=1) / hh["income_unit_size"]
        data[f"{component}_pc"] = data["hh_id"].map(hh[f"{component}_pc"])
    hh["pension_bpc_pc"] = (hh["retirement_pension_income_brl"] + hh["bpc_income_brl"]) / hh["income_unit_size"]
    data["pension_bpc_pc"] = data["hh_id"].map(hh["pension_bpc_pc"])
    data["income_without_pension_bpc_pc"] = np.maximum(
        0.0, data["household_income_per_capita_brl"] - data["pension_bpc_pc"]
    )
    data["older_recipient_household"] = data["hh_id"].map(hh["older_recipient"])
    data["age_group"] = pd.cut(
        data["age"], bins=[-1, 14, 29, 64, np.inf], labels=AGE_GROUPS
    ).astype(str)
    data["income_decile"] = _weighted_deciles(
        data["household_income_per_capita_brl"].to_numpy(dtype=float),
        data["survey_weight"].to_numpy(dtype=float),
    )

    records: list[dict] = []
    for age_group in AGE_GROUPS:
        age_data = data.loc[data["age_group"].eq(age_group)]
        records.append(_profile_record(
            age_data, "age_summary", age_group, "all", minimum_wage_brl
        ))
        for decile in range(1, 11):
            cell = age_data.loc[age_data["income_decile"].eq(decile)]
            if not cell.empty:
                records.append(_profile_record(
                    cell, "age_decile", age_group, str(decile), minimum_wage_brl
                ))
    co_residents = data.loc[data["older_recipient_household"]]
    records.append(
        _profile_record(
            co_residents, "living_with_65_plus_pension_bpc_recipient", "all", "all",
            minimum_wage_brl,
        )
    )
    return pd.DataFrame.from_records(records)


def build_indexation(years: Iterable[int] = range(2026, 2036)) -> pd.DataFrame:
    """Return deterministic real minimum-benefit paths, indexed to 2025=100."""
    records: list[dict] = []
    for gain in (0.0, 0.006, 0.015, 0.025):
        case = "inpc_only" if gain == 0 else f"current_law_{gain * 100:g}_pct_real_gain"
        for year in years:
            elapsed = int(year) - 2025
            real_index = 100 * (1 + gain) ** elapsed
            records.append({
                "year": int(year),
                "case": case,
                "annual_real_gain_pct": 100 * gain,
                "real_benefit_index_2025_100": real_index,
                "cumulative_gain_vs_inpc_only_pct": real_index - 100,
                "inpc_only_shortfall_vs_case_pct": 100 * (1 - 100 / real_index),
            })
    return pd.DataFrame.from_records(records)


def _price_category(label: str) -> str | None:
    if label == "Índice geral":
        return "general"
    if "Saúde e cuidados pessoais" in label:
        return "health_group"
    if label.startswith("6101."):
        return "medicines"
    if label.startswith("6201."):
        return "medical_services"
    if label.startswith("6203001."):
        return "health_plans"
    return None


def read_price_series(files: Mapping[str, tuple[Path, Path]] = PRICE_FILES) -> pd.DataFrame:
    """Read selected monthly SIDRA price changes, joining old/new tables."""
    records: list[dict] = []
    for index_name, paths in files.items():
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            for result in payload[0]["resultados"]:
                label = next(iter(result["classificacoes"][0]["categoria"].values()))
                category = _price_category(label)
                if category is None:
                    continue
                series = result["series"][0]["serie"]
                records.extend({
                    "index": index_name,
                    "category": category,
                    "period": str(period),
                    "monthly_change_pct": float(value),
                } for period, value in series.items() if value not in (None, "...", "-") )
    frame = pd.DataFrame.from_records(records)
    if frame.duplicated(["index", "category", "period"]).any():
        raise ValueError("Duplicate SIDRA price observations")
    expected = {"general", "health_group", "medicines", "medical_services", "health_plans"}
    for index_name, group in frame.groupby("index"):
        if set(group["category"]) != expected:
            raise ValueError(f"Incomplete price categories for {index_name}")
    return frame.sort_values(["index", "category", "period"], ignore_index=True)


def _annualised(monthly_pct: pd.Series) -> float:
    factor = float(np.prod(1 + monthly_pct.to_numpy(dtype=float) / 100))
    return 100 * (factor ** (12 / len(monthly_pct)) - 1)


def _real_change(indexation_pct: float, deflator_pct: float) -> float:
    return 100 * ((1 + indexation_pct / 100) / (1 + deflator_pct / 100) - 1)


def build_health_prices(monthly: pd.DataFrame) -> pd.DataFrame:
    """Annualise archived prices and add explicitly labelled exposure proxies."""
    observed: list[dict] = []
    for (index_name, category), group in monthly.groupby(["index", "category"], sort=True):
        observed.append({
            "row_type": "observed_series",
            "index": index_name,
            "category": category,
            "start_period": group["period"].min(),
            "end_period": group["period"].max(),
            "months": len(group),
            "annualised_inflation_pct": _annualised(group["monthly_change_pct"]),
            "inpc_benefit_real_change_pct_per_year": np.nan,
            "feasibility": "exact_archived_monthly_series",
        })
    result = pd.DataFrame.from_records(observed)
    rates = result.set_index(["index", "category"])["annualised_inflation_pct"]
    inpc = float(rates.loc[("INPC", "general")])
    result.loc[result["row_type"].eq("observed_series"), "inpc_benefit_real_change_pct_per_year"] = [
        _real_change(inpc, value) for value in result["annualised_inflation_pct"]
    ]

    nonholder = 100 * (
        np.sqrt(
            (1 + float(rates.loc[("INPC", "medicines")]) / 100)
            * (1 + float(rates.loc[("INPC", "medical_services")]) / 100)
        ) - 1
    )
    sensitivities = (
        ("inpc_weights", inpc, "exact_by_construction"),
        (
            "older_double_health_exposure_proxy",
            float(rates.loc[("INPC", "health_group")]),
            "closest_feasible_no_archived_expenditure_weight",
        ),
        (
            "plan_holder_extra_health_exposure_proxy",
            float(rates.loc[("INPC", "health_plans")]),
            "closest_feasible_no_archived_expenditure_weight",
        ),
        (
            "nonholder_equal_medicines_services_proxy",
            nonholder,
            "robustness_equal_item_weights_not_primary_definition",
        ),
    )
    start, end = monthly["period"].min(), monthly["period"].max()
    extra = pd.DataFrame.from_records([{
        "row_type": "health_adjusted_sensitivity",
        "index": "INPC-indexed benefit",
        "category": name,
        "start_period": start,
        "end_period": end,
        "months": int(monthly.loc[monthly["index"].eq("INPC"), "period"].nunique()),
        "annualised_inflation_pct": deflator,
        "inpc_benefit_real_change_pct_per_year": _real_change(inpc, deflator),
        "feasibility": feasibility,
    } for name, deflator, feasibility in sensitivities])
    return pd.concat([result, extra], ignore_index=True)


def build_sus(
    profiles: pd.DataFrame,
    population: pd.DataFrame,
    baseline: pd.DataFrame,
    macro: pd.DataFrame,
    base_gdp_per_capita: float,
) -> pd.DataFrame:
    """Compare real health spending per age-cost unit at observed C1 horizons."""
    health = baseline.loc[
        baseline["scenario"].eq("S0")
        & baseline["variant"].eq("central")
        & baseline["category"].eq("health")
    ].sort_values("year")
    years = health["year"].astype(int).tolist()
    profile_year = int(health["profile_year"].dropna().iloc[0])
    costs = profiles.loc[
        profiles["category"].eq("health")
        & profiles["profile_year"].eq(profile_year),
        ["age", "relative_cost_per_capita"],
    ].rename(columns={"relative_cost_per_capita": "relative_cost"})
    pop = prepare_population(population)
    merged = pop.loc[pop["year"].isin(years)].merge(costs, on="age", how="left", validate="many_to_one")
    if merged["relative_cost"].isna().any():
        raise ValueError("Health profile does not cover all population ages")
    age_units = merged.assign(
        age_weighted=lambda x: x["population"] * x["relative_cost"]
    ).groupby("year", as_index=False).agg(
        population=("population", "sum"),
        age_weighted_population=("age_weighted", "sum"),
    ).set_index("year")

    gdp_pc = {years[0]: float(base_gdp_per_capita)}
    macro_pc = macro.loc[
        macro["scenario"].eq("S0")
        & macro["variant"].eq("central")
        & macro["persistence"].eq("persistent")
        & macro["indicator"].eq("gdp_per_capita"),
        ["year", "value"],
    ].drop_duplicates("year")
    gdp_pc.update(dict(zip(macro_pc["year"].astype(int), macro_pc["value"].astype(float))))
    if set(years) - set(gdp_pc):
        raise ValueError("Macro file lacks S0 GDP per capita for a C1 health year")
    real_gdp = {
        year: gdp_pc[year] * float(age_units.loc[year, "population"])
        for year in years
    }
    base_year = years[0]
    gdp_index = {year: real_gdp[year] / real_gdp[base_year] for year in years}
    share = dict(zip(health["year"].astype(int), health["spending_pct_gdp"].astype(float)))
    base_share = share[base_year]
    spending_indices = {
        "s0_health_path": {
            year: gdp_index[year] * share[year] / base_share for year in years
        },
        # No 2027 observation is archived. The closest feasible version holds
        # the observed 2025 real level, rather than interpolating a 2027 anchor.
        "constant_real_from_2025_proxy_for_2027_floor": {year: 1.0 for year in years},
        "current_law_revenue_linked": gdp_index,
    }
    base_units = float(age_units.loc[base_year, "age_weighted_population"])
    records: list[dict] = []
    for path, indices in spending_indices.items():
        for year in years:
            units = float(age_units.loc[year, "age_weighted_population"])
            feasibility = (
                "closest_feasible_2025_anchor_no_2027_observation"
                if path.startswith("constant_real") else "primary_specification"
            )
            records.append({
                "year": year,
                "path": path,
                "population": float(age_units.loc[year, "population"]),
                "age_weighted_population": units,
                "age_weighted_population_index_2025_100": 100 * units / base_units,
                "real_health_spending_index_2025_100": 100 * indices[year],
                "real_spending_per_age_weighted_person_index_2025_100": (
                    100 * indices[year] / (units / base_units)
                ),
                "health_spending_pct_gdp": (
                    share[year] if path == "s0_health_path"
                    else base_share / gdp_index[year] if path.startswith("constant_real")
                    else base_share
                ),
                "feasibility": feasibility,
            })
    return pd.DataFrame.from_records(records)


def stylised_micro_check(persons: pd.DataFrame, inputs: Mapping) -> pd.DataFrame:
    """Run an isolated 0.1-point pension/indexation cut with BPC on and off."""
    common = dict(
        gdp_level_vs_s0_pct=0.0,
        unemployment_change_pp=0.0,
        package_gaps_pp_gdp={"pension_and_indexation": 0.1},
        revenue_change_pp=0.0,
        nominal_gdp_brl=float(inputs["nominal_gdp_brl_million"]["value"]) * 1_000_000,
        minimum_wage_brl=float(inputs["minimum_wage_brl_month"]["value"]),
        pension_variant="indexation_floor",
        labour_variant="gdp_only",
        tax_variant="proportional",
        consumption_like_exponent=float(inputs["defaults"]["consumption_like_exponent"]),
        random_seed=int(inputs["defaults"]["random_seed"]),
    )
    records: list[dict] = []
    for follows in (True, False):
        households = simulate_household_incomes(
            persons, **common, bpc_follows_pension_indexation=follows
        )
        indicators = calculate_indicators(households, POVERTY_LINES)
        records.extend({
            "bpc_follows_pension_indexation": follows,
            "indicator": name,
            "value": value,
        } for name, value in indicators.items())
    return pd.DataFrame.from_records(records)


def _markdown(frame: pd.DataFrame, decimals: int = 2) -> list[str]:
    display = frame.copy()
    for column in display.select_dtypes(include=[np.number]):
        display[column] = display[column].map(lambda value: f"{value:.{decimals}f}")
    headers = [str(column) for column in display.columns]
    rows = [[str(value) for value in row] for row in display.itertuples(index=False, name=None)]
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
        *("| " + " | ".join(row) + " |" for row in rows),
    ]


def render_report(
    profile: pd.DataFrame,
    indexation: pd.DataFrame,
    prices: pd.DataFrame,
    sus: pd.DataFrame,
    micro_check: pd.DataFrame,
) -> str:
    """Render the neutral E3 evidence report from computed tables."""
    ages = profile.loc[profile["row_type"].eq("age_summary"), [
        "age_group", "weighted_population", "poverty_218_pct", "poverty_759_pct",
        "poverty_759_without_pension_bpc_pct", "household_income_pension_bpc_share_pct",
        "pension_recipient_pct", "bpc_recipient_pct",
        "pension_at_or_below_1_01_minimum_wage_pct_of_recipients",
    ]]
    coresident = profile.loc[
        profile["row_type"].eq("living_with_65_plus_pension_bpc_recipient"),
        ["weighted_population", "poverty_218_pct", "poverty_759_pct",
         "poverty_759_without_pension_bpc_pct"],
    ]
    gaps = indexation.loc[indexation["year"].isin([2030, 2035]), [
        "year", "case", "real_benefit_index_2025_100",
        "cumulative_gain_vs_inpc_only_pct", "inpc_only_shortfall_vs_case_pct",
    ]]
    observed = prices.loc[prices["row_type"].eq("observed_series"), [
        "index", "category", "start_period", "end_period",
        "annualised_inflation_pct", "inpc_benefit_real_change_pct_per_year",
    ]]
    sensitivity = prices.loc[prices["row_type"].eq("health_adjusted_sensitivity"), [
        "category", "annualised_inflation_pct",
        "inpc_benefit_real_change_pct_per_year", "feasibility",
    ]]
    check_names = [
        "gini", "poverty_headcount_218_pct", "poverty_headcount_759_pct",
        "poverty_headcount_759_age_65_plus_pct",
        "poverty_headcount_759_living_with_65_plus_pension_bpc_recipient_pct",
    ]
    check = micro_check.loc[micro_check["indicator"].isin(check_names)].pivot(
        index="indicator", columns="bpc_follows_pension_indexation", values="value"
    ).reset_index().rename(columns={False: "BPC off", True: "BPC on"})
    sus_end = sus.loc[sus["year"].isin([2025, 2045]), [
        "year", "path", "age_weighted_population_index_2025_100",
        "real_health_spending_index_2025_100",
        "real_spending_per_age_weighted_person_index_2025_100", "feasibility",
    ]]
    return "\n".join([
        "# Older people: pensions, BPC, poverty and health costs", "",
        "All results are descriptive scenario arithmetic. They compare measures and exposure channels; they do not identify causal effects.", "",
        "## 2025 income profile", "",
        "PNAD income-unit conditions 17-19 are excluded. Poverty without pension and BPC subtracts observed household pension and BPC receipts, holds every other income fixed, and floors income at zero.", "",
        *_markdown(ages), "",
        "People of any age sharing an income unit with a pension/BPC recipient aged 65 or older:", "",
        *_markdown(coresident), "",
        "The full CSV reports income composition for every age-group/weighted-income-decile cell. Component income is aggregated within the income unit and shared per capita; the residual reconciles detailed PNAD components to official household per-capita income.", "",
        "## Minimum-benefit indexation", "",
        "Real values use 2025=100. INPC-only indexation remains at 100 in INPC purchasing power; current-law sensitivities compound annual real gains of 0.6%, 1.5%, and 2.5%.", "",
        *_markdown(gaps, 3), "",
        "## C3 stylised allocation check", "",
        "This check isolates a 0.1 percentage-point-of-GDP pension/indexation reduction, uses the indexation-floor allocation, and changes no macro, labour, tax, or means-tested-transfer input. `BPC on` allocates the gap across minimum-wage-linked pension income and all BPC income; `BPC off` retains the former pension-only treatment.", "",
        *_markdown(check, 4), "",
        "## Health prices and benefit purchasing power", "",
        "Monthly changes are compounded over the common archived window and annualised. A negative real-change entry is annual erosion for a benefit indexed to INPC.", "",
        *_markdown(observed, 3), "",
        "Regulated medicine prices rose less than INPC over this window, while health plans rose more. The raw files contain price changes but no expenditure weights, so an exact double-health-weight index is infeasible. The labelled older-household row uses the health-group price as an extra-health-exposure proxy. The plan-holder row uses the plan series. The non-holder robustness proxy gives medicines and medical services equal multiplicative weight; it is not an official basket.", "",
        *_markdown(sensitivity, 3), "",
        "## SUS resources per age-weighted person", "",
        "The age-cost denominator applies the C1 2018 health profile to the IBGE projection. S0 combines C1's health share with S0 real GDP. The revenue-linked path keeps the 2025 health share constant while real GDP grows. Because no 2027 health-spending observation is archived and interpolation is prohibited, the inflation-only-floor path is the closest feasible version: real spending is held at its observed 2025 level and is explicitly labelled as a proxy.", "",
        *_markdown(sus_end, 3), "",
        "## Data limits", "",
        "The PNAD calculation is static and does not model take-up, behavioural responses, mortality, household re-formation, or private health spending. SIDRA 2026 observations end in September, so the annualised price comparison is a common-window rate rather than a calendar-2026 rate. The C1 health profile is a relative public-transfer-cost profile, not a clinical need measure. The requested literature file `docs/elderly_review.md` was unavailable at build time, so no literature result is restated here; it remains the designated review source when supplied.", "",
    ])


def render_docs() -> str:
    return "\n".join([
        "# E3 older-people analysis method", "",
        "`python -m src.elderly` deterministically rebuilds the four E3 CSVs, the evidence report, and this method note from local files only.", "",
        "## Income", "",
        "The PNAD input is restricted to income-unit conditions other than 17-19. Survey weights are constant within an income unit. Age groups are 0-14, 15-29, 30-64 and 65+. National income deciles are assigned from household per-capita income using person-weighted rank midpoints. Detailed individual receipts are summed within the income unit and divided by its eligible member count before composition is measured. Counterfactual income removes observed pension and BPC receipts without replacing them or allowing negative income.", "",
        "## Microsimulation", "",
        "Prepared microdata retain age. Simulated household rows contain member counts aged 0-14 and 65+, plus the count living in an income unit containing a pension/BPC recipient aged 65+. `calculate_indicators` applies household post-simulation income to those person-count denominators. With `bpc_follows_pension_indexation=True`, the pension/indexation fiscal amount is allocated over pension and BPC income. In the indexation-floor variant, pension exposure is capped at one minimum wage while all BPC income is exposed. Negative fiscal gaps work symmetrically.", "",
        "## Indexation and prices", "",
        "The indexation table compounds fixed real gains from 2025. Price rates compound every archived monthly change from January 2012 through the shared last month and annualise by the exact number of months. Real benefit change is `(1 + INPC)/(1 + comparison deflator) - 1`. No expenditure weights are present in the archived SIDRA extracts; consequently the double-health-weight and plan-status rows are clearly labelled exposure proxies, with an equal-item non-holder row reported only as robustness.", "",
        "## SUS", "",
        "The denominator is the sum over age of IBGE population times the C1 2018 relative health-cost profile. Results remain at C1's observed five-year horizons; no year is interpolated. Real GDP is GDP per capita times population, using the sourced 2025 parameter and S0 macro output thereafter. S0 health spending is its GDP share times real GDP; the revenue-linked path grows with GDP at a fixed 2025 share. The constant-real proxy holds the 2025 real level because an exact 2027 anchor is absent.", "",
        "## Reproduction and limitations", "",
        "Raw downloads are read-only. Monetary microsimulation inputs come from `config/c3_inputs_proposed.yaml`; the sourced 2025 GDP-per-capita anchor comes from `config/parameters.yaml`. Outputs are deterministic CSV/Markdown files. The literature synthesis is designated to `docs/elderly_review.md`; if that file is absent, the report states the gap rather than inventing a review.", "",
    ])


def run(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]:
    persons = pd.read_csv(args.persons)
    micro_inputs = read_yaml(args.micro_inputs)
    profile = build_elderly_profile(
        persons, float(micro_inputs["minimum_wage_brl_month"]["value"])
    )
    indexation = build_indexation()
    prices = build_health_prices(read_price_series())
    parameters = read_yaml(args.parameters)
    sus = build_sus(
        pd.read_csv(args.age_profiles),
        pd.read_csv(args.population),
        pd.read_csv(args.baseline),
        pd.read_csv(args.macro),
        float(parameters["macro"]["base_gdp_per_capita"]["central"]),
    )
    micro_check = stylised_micro_check(persons, micro_inputs)
    return profile, indexation, prices, sus, render_report(
        profile, indexation, prices, sus, micro_check
    ), render_docs()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persons", default="data/processed/brazil/microdata/pnadc_2025_c3_input.csv")
    parser.add_argument("--age-profiles", default="data/brazil/age_profiles.csv")
    parser.add_argument("--population", default="data/brazil/population.csv")
    parser.add_argument("--baseline", default="data/brazil/baseline.csv")
    parser.add_argument("--macro", default="data/brazil/macro.csv")
    parser.add_argument("--parameters", default="config/parameters.yaml")
    parser.add_argument("--micro-inputs", default="config/c3_inputs_proposed.yaml")
    parser.add_argument("--profile-output", default="data/brazil/elderly_profile.csv")
    parser.add_argument("--indexation-output", default="data/brazil/elderly_indexation.csv")
    parser.add_argument("--prices-output", default="data/brazil/elderly_health_prices.csv")
    parser.add_argument("--sus-output", default="data/brazil/elderly_sus.csv")
    parser.add_argument("--report-output", default="outputs/elderly.md")
    parser.add_argument("--docs-output", default="docs/elderly.md")
    args = parser.parse_args(argv)

    profile, indexation, prices, sus, report, docs = run(args)
    outputs = (
        (profile, Path(args.profile_output)),
        (indexation, Path(args.indexation_output)),
        (prices, Path(args.prices_output)),
        (sus, Path(args.sus_output)),
    )
    for frame, path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False, float_format="%.10f")
    Path(args.report_output).write_text(report, encoding="utf-8")
    Path(args.docs_output).write_text(docs, encoding="utf-8")
    print(
        f"Wrote {len(profile)} profile, {len(indexation)} indexation, "
        f"{len(prices)} health-price and {len(sus)} SUS rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
