"""Long-run feedback channels for one annual C2 macro corner.

The calculation is deliberately parameter driven.  ``apply_feedback`` does
not read configuration or raw files, which lets D1 pass sampled values.  The
thin ``load_feedback_defaults`` helper is the only file-reading convenience.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd
import yaml

from src.baseline import prepare_population, read_yaml
from src.macro import debt_step, load_macro_inputs


CHANNELS = (
    "human_capital",
    "health",
    "public_capital",
    "sovereign_risk_premium",
    "inequality",
)


class MissingFeedbackInput(ValueError):
    """A required C5 input is absent, null, or invalid."""


def pwt_schooling_phi(
    years: float,
    return_up_to_4: float,
    return_4_to_8: float,
    return_above_8: float,
) -> float:
    """PWT piecewise log-human-capital mapping for mean schooling years."""
    if years < 0:
        raise ValueError("Mean years of schooling cannot be negative")
    first = min(years, 4.0) * return_up_to_4
    second = min(max(years - 4.0, 0.0), 4.0) * return_4_to_8
    third = max(years - 8.0, 0.0) * return_above_8
    return first + second + third


def latest_undp_mean_schooling(path: str | Path) -> tuple[float, int]:
    """Read, rather than hand-type, Brazil's latest non-null UNDP ``mys``."""
    with Path(path).open(encoding="utf-8") as handle:
        document = json.load(handle)
    if isinstance(document, list):
        rows = document
    elif isinstance(document, dict):
        candidates = [value for value in document.values() if isinstance(value, list)]
        if len(candidates) != 1:
            raise ValueError(f"Cannot identify observation list in {path}")
        rows = candidates[0]
    else:
        raise ValueError(f"Unexpected UNDP JSON structure in {path}")
    matches = [
        row for row in rows
        if row.get("countryIsoCode") == "BRA"
        and row.get("indicatorCode") == "mys"
        and row.get("actualValue") not in (None, "")
    ]
    if not matches:
        raise MissingFeedbackInput("UNDP HDR data contain no non-null BRA mys observation")
    latest = max(matches, key=lambda row: int(row["year"]))
    return float(latest["actualValue"]), int(latest["year"])


def _number(value: object, label: str, *, minimum: float | None = None) -> float:
    if value is None:
        raise MissingFeedbackInput(f"Null {label}")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise MissingFeedbackInput(f"Non-numeric {label}") from exc
    if not math.isfinite(result) or (minimum is not None and result < minimum):
        raise MissingFeedbackInput(f"Invalid {label}: {value!r}")
    return result


def _path_values(
    path: pd.DataFrame | pd.Series | Mapping[tuple[int, str], float] | None,
    frame: pd.DataFrame,
    label: str,
) -> pd.Series:
    """Align an optional year/scenario path; values are changes versus S0."""
    if path is None:
        return pd.Series(0.0, index=frame.index, dtype=float)
    if isinstance(path, pd.Series):
        if isinstance(path.index, pd.MultiIndex) and path.index.nlevels == 2:
            lookup = {(int(year), str(scenario)): value for (year, scenario), value in path.items()}
            values = [lookup.get((int(row.year), str(row.scenario))) for row in frame.itertuples()]
            if any(value is None for value in values):
                raise ValueError(f"{label} path does not cover every year/scenario")
            result = pd.Series(values, index=frame.index, dtype=float)
        elif path.index.equals(frame.index):
            result = pd.to_numeric(path, errors="raise").astype(float)
        else:
            raise ValueError(f"{label} Series needs the corner index or a (year, scenario) MultiIndex")
    elif isinstance(path, Mapping):
        values = [path.get((int(row.year), str(row.scenario))) for row in frame.itertuples()]
        if any(value is None for value in values):
            raise ValueError(f"{label} path does not cover every year/scenario")
        result = pd.Series(values, index=frame.index, dtype=float)
    elif isinstance(path, pd.DataFrame):
        value_columns = [column for column in path.columns if column not in {"year", "scenario"}]
        if not {"year", "scenario"}.issubset(path.columns) or len(value_columns) != 1:
            raise ValueError(f"{label} path needs year, scenario, and one value column")
        if path.duplicated(["year", "scenario"]).any():
            raise ValueError(f"{label} path contains duplicate year/scenario rows")
        aligned = frame[["year", "scenario"]].merge(
            path[["year", "scenario", value_columns[0]]],
            on=["year", "scenario"], how="left", validate="many_to_one",
        )
        if aligned[value_columns[0]].isna().any():
            raise ValueError(f"{label} path does not cover every year/scenario")
        result = pd.to_numeric(aligned[value_columns[0]], errors="raise")
        result.index = frame.index
    else:
        raise TypeError(f"{label} path must be a DataFrame, Series, mapping, or None")
    # Paths are defined relative to S0, so S0 is exactly neutral even if a
    # caller supplies a noisy non-zero S0 row.
    result.loc[frame["scenario"].eq("S0")] = 0.0
    return result.astype(float)


def _validate_corner(corner: pd.DataFrame) -> pd.DataFrame:
    required = {
        "year", "scenario", "spending_pct_gdp", "gdp_level_vs_s0_pct",
        "real_gdp", "gdp_per_capita", "primary_balance_gdp", "debt_gdp",
    }
    missing = required - set(corner.columns)
    if missing:
        raise ValueError(f"C2 corner missing columns: {sorted(missing)}")
    frame = corner.copy().reset_index(drop=True)
    if frame.duplicated(["year", "scenario"]).any():
        raise ValueError("C2 corner has duplicate year/scenario rows")
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    years = sorted(frame["year"].unique())
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError("C2 corner must contain consecutive annual years")
    counts = frame.groupby("scenario")["year"].nunique()
    if counts.nunique() != 1 or int(counts.iloc[0]) != len(years):
        raise ValueError("Every scenario must cover the same complete annual span")
    if "S0" not in set(frame["scenario"]):
        raise ValueError("C2 corner must include S0")
    numeric = sorted(required - {"year", "scenario"})
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="raise")
    return frame


def _spending_gap(frame: pd.DataFrame) -> pd.Series:
    s0 = frame.loc[frame["scenario"].eq("S0"), ["year", "spending_pct_gdp"]].set_index("year")
    if s0.index.duplicated().any():
        raise ValueError("Expected one S0 row per year")
    return frame["spending_pct_gdp"] - frame["year"].map(s0["spending_pct_gdp"])


def schooling_log_output_effect(
    frame: pd.DataFrame,
    population: pd.DataFrame,
    education_spending_change_pp_gdp: pd.Series,
    *,
    base_adult_schooling_years: float,
    schooling_elasticity: float,
    education_share_gdp: float,
    capital_share: float,
    return_up_to_4: float,
    return_4_to_8: float,
    return_above_8: float,
) -> tuple[pd.Series, pd.Series]:
    """Return log-output and adult mean-schooling effects by cohort replacement."""
    pop = prepare_population(population)
    base_year = int(frame["year"].min())
    base_schooling = _number(base_adult_schooling_years, "base_adult_schooling_years", minimum=0)
    elasticity = _number(schooling_elasticity, "schooling_elasticity")
    education_share = _number(education_share_gdp, "education_share_gdp", minimum=0)
    alpha = _number(capital_share, "capital_share")
    if education_share <= 0 or not 0 <= alpha <= 1:
        raise ValueError("education_share_gdp must be positive and capital_share in [0,1]")
    effects = pd.Series(0.0, index=frame.index)
    mean_years_change = pd.Series(0.0, index=frame.index)
    change_by_key = {
        (int(row.year), str(row.scenario)): float(education_spending_change_pp_gdp.loc[row.Index])
        for row in frame.itertuples()
    }
    for scenario, indices in frame.groupby("scenario", sort=False).groups.items():
        cohort_gain: dict[int, float] = {}
        for year in sorted(frame.loc[indices, "year"]):
            if year > base_year:
                ratio = change_by_key[(int(year), str(scenario))] / education_share
                if ratio <= -1:
                    raise ValueError("Education-spending change cannot eliminate more than 100% of spending")
                # A complete school-age exposure lasts 12 years. Each annual
                # observation contributes one twelfth of the published dose.
                annual_gain = base_schooling * elasticity * math.log1p(ratio) / 12.0
                for age in range(6, 18):
                    birth_year = int(year) - age
                    cohort_gain[birth_year] = cohort_gain.get(birth_year, 0.0) + annual_gain
            target_pop = pop.loc[pop["year"].eq(year) & pop["age"].ge(25), ["age", "population"]]
            if target_pop.empty or float(target_pop["population"].sum()) <= 0:
                raise ValueError(f"Population lacks adults aged 25+ in {year}")
            gains = target_pop["age"].map(lambda age: cohort_gain.get(int(year) - int(age), 0.0))
            delta_s = float((gains * target_pop["population"]).sum() / target_pop["population"].sum())
            idx = frame.index[(frame["scenario"].eq(scenario)) & (frame["year"].eq(year))][0]
            mean_years_change.loc[idx] = delta_s
            dln_hc = pwt_schooling_phi(
                base_schooling + delta_s, return_up_to_4, return_4_to_8, return_above_8
            ) - pwt_schooling_phi(
                base_schooling, return_up_to_4, return_4_to_8, return_above_8
            )
            effects.loc[idx] = (1 - alpha) * dln_hc
    return effects, mean_years_change


def public_capital_log_output_effect(
    frame: pd.DataFrame,
    investment_change_pp_gdp: pd.Series,
    *,
    initial_public_capital_gdp: float | None,
    public_capital_depreciation: float | None,
    public_capital_elasticity: float,
    allow_missing: bool = False,
) -> tuple[pd.Series, str]:
    """Accumulate scenario-minus-S0 investment into the public capital stock."""
    if initial_public_capital_gdp is None or public_capital_depreciation is None:
        if allow_missing:
            return pd.Series(0.0, index=frame.index), "skipped: missing IMF public-capital input"
        missing = "initial_public_capital_gdp" if initial_public_capital_gdp is None else "public_capital_depreciation"
        raise MissingFeedbackInput(f"Null {missing}; download the IMF ICSD input or pass allow_missing=True")
    stock_ratio = _number(initial_public_capital_gdp, "initial_public_capital_gdp", minimum=0)
    depreciation = _number(public_capital_depreciation, "public_capital_depreciation", minimum=0)
    elasticity = _number(public_capital_elasticity, "public_capital_elasticity")
    if stock_ratio <= 0 or not 0 <= depreciation <= 1:
        raise ValueError("Public capital/GDP must be positive and depreciation in [0,1]")
    output = pd.Series(0.0, index=frame.index)
    base_year = int(frame["year"].min())
    s0_gdp = frame.loc[frame["scenario"].eq("S0"), ["year", "real_gdp"]].set_index("year")["real_gdp"]
    initial_stock = stock_ratio * float(s0_gdp.loc[base_year])
    for scenario, indices in frame.groupby("scenario", sort=False).groups.items():
        baseline_stock = scenario_stock = initial_stock
        for idx in frame.loc[indices].sort_values("year").index:
            year = int(frame.loc[idx, "year"])
            if year == base_year:
                continue
            # In the absence of an IMF investment-flow series, depreciation
            # times the initial K/Y ratio is the transparent maintenance flow.
            maintenance = depreciation * stock_ratio * float(s0_gdp.loc[year])
            baseline_stock = (1 - depreciation) * baseline_stock + maintenance
            scenario_stock = (
                (1 - depreciation) * scenario_stock + maintenance
                + float(investment_change_pp_gdp.loc[idx]) / 100 * float(s0_gdp.loc[year])
            )
            if baseline_stock <= 0 or scenario_stock <= 0:
                raise ValueError("Public-capital path became non-positive")
            output.loc[idx] = elasticity * math.log(scenario_stock / baseline_stock)
    return output, "modelled"


def inequality_log_output_effect(
    frame: pd.DataFrame,
    gini_change: pd.Series,
    inequality_growth_pp_per_gini: float,
) -> pd.Series:
    """Compound the configured annual growth effect of a net-Gini deviation."""
    coefficient = _number(inequality_growth_pp_per_gini, "inequality_growth_pp_per_gini")
    output = pd.Series(0.0, index=frame.index)
    base_year = int(frame["year"].min())
    for scenario, indices in frame.groupby("scenario", sort=False).groups.items():
        cumulative = 0.0
        for idx in frame.loc[indices].sort_values("year").index:
            if int(frame.loc[idx, "year"]) > base_year:
                growth = coefficient * float(gini_change.loc[idx]) / 100
                if growth <= -1:
                    raise ValueError("Inequality feedback implies growth at or below -100%")
                cumulative += math.log1p(growth)
            output.loc[idx] = cumulative
    return output


def _evaluate(
    frame: pd.DataFrame,
    log_effects: Mapping[str, pd.Series],
    active: set[str],
    *,
    sovereign_risk_bp_per_debt_pp: float,
    base_real_interest_rate_pct: float,
    inflation_pct: float,
    initial_debt_gdp: float,
    real_rate_path_offset_pp: Mapping[int, float] | None = None,
    risk_premium_cap_pp: float | None = 50.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    supply_channels = {"human_capital", "health", "public_capital", "inequality"}
    total_log = sum(
        (log_effects[name] for name in supply_channels & active),
        start=pd.Series(0.0, index=frame.index),
    )
    supply_is_zero = (total_log.abs() < 1e-15).all()
    factor = total_log.map(math.exp)
    if supply_is_zero:
        gdp_gap = frame["gdp_level_vs_s0_pct"].copy()
        gdp_pc = frame["gdp_per_capita"].copy()
    else:
        gdp_gap = ((1 + frame["gdp_level_vs_s0_pct"] / 100) * factor - 1) * 100
        gdp_pc = frame["gdp_per_capita"] * factor
    debt = pd.Series(index=frame.index, dtype=float)
    start_year = int(frame["year"].min())
    inflation = inflation_pct / 100
    offsets = {int(key): float(value) for key, value in (real_rate_path_offset_pp or {}).items()}
    risk_bp = sovereign_risk_bp_per_debt_pp if "sovereign_risk_premium" in active else 0.0
    for scenario, indices in frame.groupby("scenario", sort=False).groups.items():
        ordered = frame.loc[indices].sort_values("year")
        previous_debt = initial_debt_gdp / 100
        previous_nominal_gdp: float | None = None
        for idx in ordered.index:
            year = int(frame.loc[idx, "year"])
            nominal_gdp = (
                float(frame.loc[idx, "real_gdp"])
                * (1 + inflation) ** (year - start_year)
                * (1 + float(gdp_gap.loc[idx]) / 100)
            )
            if year == start_year:
                debt.loc[idx] = initial_debt_gdp
                previous_nominal_gdp = nominal_gdp
                continue
            if previous_nominal_gdp is None:
                raise RuntimeError("Missing prior nominal GDP")
            # Lead-developer choice (2026-10-20): the premium responds to debt
            # relative to the base year for every scenario, S0 included, and the
            # deviation is capped as an out-of-sample guard (Baldacci & Kumar
            # estimate it on much smaller debt changes).
            deviation_pp = (previous_debt - initial_debt_gdp / 100) * 100
            if risk_premium_cap_pp is not None:
                deviation_pp = max(-risk_premium_cap_pp, min(risk_premium_cap_pp, deviation_pp))
            premium = risk_bp / 10_000 * deviation_pp
            offset = offsets.get(year, 0.0)
            if offsets and year > max(offsets):
                offset = offsets[max(offsets)]
            base_real_rate = (base_real_interest_rate_pct + offset) / 100
            nominal_interest = (1 + base_real_rate + premium) * (1 + inflation) - 1
            nominal_growth = nominal_gdp / previous_nominal_gdp - 1
            previous_debt = debt_step(
                previous_debt, nominal_interest, nominal_growth,
                float(frame.loc[idx, "primary_balance_gdp"]) / 100,
            ) - (float(frame.loc[idx, "debt_adjustment_pp"]) / 100 if "debt_adjustment_pp" in frame else 0.0)
            debt.loc[idx] = previous_debt * 100
            previous_nominal_gdp = nominal_gdp
    # Exact pass-through is an important invariant and avoids harmless
    # round-off when no channel can change a row.
    if risk_bp == 0 and supply_is_zero:
        debt = frame["debt_gdp"].copy()
    return gdp_gap, gdp_pc, debt


def apply_feedback(
    corner: pd.DataFrame,
    population: pd.DataFrame,
    *,
    base_adult_schooling_years: float,
    schooling_elasticity: float,
    return_up_to_4: float,
    return_4_to_8: float,
    return_above_8: float,
    capital_share: float,
    education_share_gdp: float,
    health_share_gdp: float,
    efficiency_package_share: float | Mapping[tuple[int, str], float],
    service_cut_fraction: float,
    life_expectancy_change: pd.DataFrame | pd.Series | Mapping[tuple[int, str], float] | None,
    health_output_pct_per_year: float,
    public_investment_package_share: float | Mapping[tuple[int, str], float],
    public_capital_elasticity: float,
    initial_public_capital_gdp: float | None,
    public_capital_depreciation: float | None,
    sovereign_risk_bp_per_debt_pp: float,
    base_real_interest_rate_pct: float,
    inflation_pct: float,
    initial_debt_gdp: float,
    real_rate_path_offset_pp: Mapping[int, float] | None = None,
    gini_change: pd.DataFrame | pd.Series | Mapping[tuple[int, str], float] | None = None,
    inequality_growth_pp_per_gini: float = 0.0,
    allow_missing: bool = False,
    risk_premium_cap_pp: float | None = 50.0,
) -> pd.DataFrame:
    """Add feedback-adjusted outcomes and switch-off channel attributions."""
    frame = _validate_corner(corner)
    for label, value in {
        "health_share_gdp": health_share_gdp,
        "service_cut_fraction": service_cut_fraction,
        "health_output_pct_per_year": health_output_pct_per_year,
        "sovereign_risk_bp_per_debt_pp": sovereign_risk_bp_per_debt_pp,
        "base_real_interest_rate_pct": base_real_interest_rate_pct,
        "inflation_pct": inflation_pct,
        "initial_debt_gdp": initial_debt_gdp,
    }.items():
        _number(value, label)
    if health_share_gdp <= 0:
        raise ValueError("health_share_gdp must be positive")
    if not 0 <= service_cut_fraction <= 1:
        raise ValueError("service_cut_fraction must lie in [0,1]")
    gap = _spending_gap(frame)  # positive means spending above S0
    # Package shares are scalars, or (year, scenario) paths when a scenario has
    # its own package composition (P1 programme scenarios).
    shares = {}
    for label, value in {
        "efficiency_package_share": efficiency_package_share,
        "public_investment_package_share": public_investment_package_share,
    }.items():
        shares[label] = _path_values(value, frame, label) if isinstance(value, Mapping) else _number(value, label)
    efficiency_package_share = shares["efficiency_package_share"]
    public_investment_package_share = shares["public_investment_package_share"]
    education_allocation = education_share_gdp / (education_share_gdp + health_share_gdp)
    education_change = gap * efficiency_package_share * education_allocation * service_cut_fraction
    investment_change = gap * public_investment_package_share
    human_log, schooling_change = schooling_log_output_effect(
        frame, population, education_change,
        base_adult_schooling_years=base_adult_schooling_years,
        schooling_elasticity=schooling_elasticity,
        education_share_gdp=education_share_gdp,
        capital_share=capital_share,
        return_up_to_4=return_up_to_4,
        return_4_to_8=return_4_to_8,
        return_above_8=return_above_8,
    )
    le_change = _path_values(life_expectancy_change, frame, "life_expectancy_change")
    health_level = le_change * health_output_pct_per_year / 100
    if (health_level <= -1).any():
        raise ValueError("Health feedback implies output at or below zero")
    health_log = health_level.map(math.log1p)
    public_log, public_status = public_capital_log_output_effect(
        frame, investment_change,
        initial_public_capital_gdp=initial_public_capital_gdp,
        public_capital_depreciation=public_capital_depreciation,
        public_capital_elasticity=public_capital_elasticity,
        allow_missing=allow_missing,
    )
    gini = _path_values(gini_change, frame, "gini_change")
    inequality_log = inequality_log_output_effect(frame, gini, inequality_growth_pp_per_gini)
    log_effects = {
        "human_capital": human_log,
        "health": health_log,
        "public_capital": public_log,
        "inequality": inequality_log,
    }
    active = set(CHANNELS)
    all_gdp, all_pc, all_debt = _evaluate(
        frame, log_effects, active,
        sovereign_risk_bp_per_debt_pp=sovereign_risk_bp_per_debt_pp,
        base_real_interest_rate_pct=base_real_interest_rate_pct,
        inflation_pct=inflation_pct,
        initial_debt_gdp=initial_debt_gdp,
        real_rate_path_offset_pp=real_rate_path_offset_pp,
        risk_premium_cap_pp=risk_premium_cap_pp,
    )
    frame["gdp_level_vs_s0_pct_with_feedback"] = all_gdp
    frame["gdp_per_capita_with_feedback"] = all_pc
    frame["debt_gdp_with_feedback"] = all_debt
    frame["adult_mean_schooling_change_years"] = schooling_change
    frame["public_capital_status"] = public_status
    frame["inequality_status"] = "inactive: no Gini path (until C3)" if gini_change is None else "modelled"
    for channel in CHANNELS:
        without_gdp, _, without_debt = _evaluate(
            frame, log_effects, active - {channel},
            sovereign_risk_bp_per_debt_pp=sovereign_risk_bp_per_debt_pp,
            base_real_interest_rate_pct=base_real_interest_rate_pct,
            inflation_pct=inflation_pct,
            initial_debt_gdp=initial_debt_gdp,
            real_rate_path_offset_pp=real_rate_path_offset_pp,
            risk_premium_cap_pp=risk_premium_cap_pp,
        )
        frame[f"{channel}_contribution_pct"] = all_gdp - without_gdp
        frame[f"{channel}_debt_contribution_pp"] = all_debt - without_debt
    return frame


def load_feedback_defaults(
    parameters_path: str | Path = "config/parameters.yaml",
    scenarios_path: str | Path = "config/scenarios.yaml",
    c5_inputs_path: str | Path = "config/c5_inputs_proposed.yaml",
    hdr_path: str | Path = "data/raw/hdr-data.json",
    *,
    variant: str = "central",
) -> dict[str, object]:
    """Assemble explicit keyword defaults for ``apply_feedback``.

    The health coefficient remains ``None`` at the central variant by design;
    D1 must sample it uniformly. Public-capital inputs also remain null until
    the IMF data are downloaded.
    """
    parameters = read_yaml(parameters_path)
    scenarios = read_yaml(scenarios_path)
    with Path(c5_inputs_path).open(encoding="utf-8") as handle:
        proposed = yaml.safe_load(handle)
    macro_inputs = load_macro_inputs(parameters_path)
    feedback = parameters["long_run_feedback"]
    returns = feedback["human_capital_from_schooling"]["returns_per_year_of_schooling"]
    schooling, schooling_year = latest_undp_mean_schooling(hdr_path)
    public = proposed["public_capital"]
    return {
        "base_adult_schooling_years": schooling,
        "base_adult_schooling_year": schooling_year,
        "schooling_elasticity": parameters["social_outcome_elasticities"]["schooling_years_wrt_local_public_spending"][variant],
        "return_up_to_4": returns["up_to_4_years"],
        "return_4_to_8": returns["years_4_to_8"],
        "return_above_8": returns["above_8_years"],
        "capital_share": macro_inputs["macro"]["capital_share"][variant],
        "education_share_gdp": parameters["baseline"]["education_gdp_share"][variant],
        "health_share_gdp": parameters["baseline"]["health_gdp_share"][variant],
        "efficiency_package_share": scenarios["package_shares"].get("efficiency_health_education_admin", 0.0),
        "service_cut_fraction": parameters["social_modelling_choices"]["reduction_hitting_health_education"]["service_cut_fraction"][variant],
        "health_output_pct_per_year": feedback["health_to_output"][variant],
        "public_investment_package_share": scenarios["package_shares"].get("public_investment", 0.0),
        "public_capital_elasticity": feedback["public_capital"][variant],
        "initial_public_capital_gdp": public["initial_stock_gdp"]["central"],
        "public_capital_depreciation": public["depreciation_rate"]["central"],
        "sovereign_risk_bp_per_debt_pp": feedback["sovereign_risk_premium"][variant],
        "base_real_interest_rate_pct": macro_inputs["macro"]["effective_real_interest_rate"][variant],
        "inflation_pct": macro_inputs["macro"]["gdp_deflator_growth"][variant],
        "initial_debt_gdp": macro_inputs["macro"]["initial_debt_gdp"][variant],
        "inequality_growth_pp_per_gini": feedback["inequality_to_growth"]["central"],
        "risk_premium_cap_pp": feedback["sovereign_risk_premium"].get("deviation_cap_pp"),
    }
