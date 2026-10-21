"""Brazil macro block: multiplier effects, growth accounting, and debt.

The public functions accept data frames and mappings so that D1 can supply
parameter draws without going through the command-line interface.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import statistics
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

from src.baseline import prepare_population, project_baseline, read_yaml


VARIANTS = ("low", "central", "high")
PERSISTENCE_VARIANTS = ("transitory", "persistent")
INDICATORS = (
    "gdp_level_vs_s0_pct",
    "gdp_per_capita",
    "s0_potential_real_gdp_growth_pct",
    "debt_gdp",
    "unemployment_change_pp",
    "primary_balance_gdp",
)


class MissingMacroInput(ValueError):
    """Raised when a required C2 input is null, absent, or non-numeric."""


def read_bcb_debt_history(path: str | Path, years: Iterable[int]) -> dict[int, float]:
    """Read December observations from the untouched BCB SGS 13762 JSON."""
    with Path(path).open(encoding="utf-8") as handle:
        observations = json.load(handle)
    december = {
        int(str(row["data"])[-4:]): float(row["valor"])
        for row in observations
        if str(row.get("data", "")).startswith("01/12/")
    }
    requested = [int(year) for year in years]
    missing = sorted(set(requested) - set(december))
    if missing:
        raise ValueError(f"BCB debt history missing December years: {missing}")
    return {year: december[year] for year in requested}


def read_pwt_brazil_growth(path: str | Path, countrycode: str = "BRA") -> pd.DataFrame:
    """Read the PWT columns used by C2 for one country; never hand-type them."""
    columns = ["countrycode", "year", "rgdpna", "rnna", "delta", "emp", "avh", "hc", "labsh", "rtfpna"]
    frame = pd.read_stata(path, columns=columns)
    frame = frame.loc[frame["countrycode"].eq(countrycode)].copy()
    if frame.empty:
        raise ValueError(f"PWT has no observations for {countrycode}")
    numeric = [column for column in columns if column != "countrycode"]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="raise")
    return frame.sort_values("year", ignore_index=True)


def _compound_average(series: pd.Series, start: int, end: int) -> float:
    values = series.copy()
    if start not in values.index or end not in values.index or end <= start:
        raise ValueError(f"Invalid PWT calibration period {start}-{end}")
    return (float(values.loc[end]) / float(values.loc[start])) ** (1 / (end - start)) - 1


def pwt_implied_investment_rates(pwt: pd.DataFrame) -> pd.DataFrame:
    """Return PWT-consistent annual investment and capital growth rates.

    PWT ``rnna`` and ``rgdpna`` are both at constant 2017 national prices, so
    this avoids combining a current-price national-accounts investment share
    with PWT's real capital stock.
    """
    data = pwt.sort_values("year").copy()
    prior_capital = data["rnna"].shift(1)
    consecutive = data["year"].diff().eq(1)
    data["implied_investment_rate"] = (
        data["rnna"] - (1 - data["delta"]) * prior_capital
    ) / data["rgdpna"]
    data["capital_growth"] = data["rnna"] / prior_capital - 1
    data.loc[~consecutive, ["implied_investment_rate", "capital_growth"]] = math.nan
    return data[["year", "implied_investment_rate", "capital_growth"]]


def growth_accounting_backcast(
    pwt: pd.DataFrame, start_year: int = 2000, end_year: int = 2019
) -> dict[str, float]:
    """Dynamically backcast output after accumulating, rather than feeding, K."""
    data = pwt.loc[pwt["year"].between(start_year, end_year)].set_index("year")
    expected = list(range(start_year, end_year + 1))
    if list(data.index) != expected:
        raise ValueError("PWT backcast requires a complete annual span")
    rates = pwt_implied_investment_rates(pwt).set_index("year")
    actual: list[float] = []
    fitted: list[float] = []
    actual_capital_growth: list[float] = []
    fitted_capital_growth: list[float] = []
    projected_capital = float(data.loc[start_year, "rnna"])
    for year in expected[1:]:
        prior = data.loc[year - 1]
        current = data.loc[year]
        prior_projected_capital = projected_capital
        investment_rate = float(rates.loc[year, "implied_investment_rate"])
        projected_capital = (
            (1 - float(current["delta"])) * prior_projected_capital
            + investment_rate * float(current["rgdpna"])
        )
        projected_capital_growth = projected_capital / prior_projected_capital - 1
        observed_capital_growth = float(current["rnna"] / prior["rnna"] - 1)
        alpha = 1 - float((prior["labsh"] + current["labsh"]) / 2)
        prediction = (
            float(current["rtfpna"] / prior["rtfpna"])
            * (1 + projected_capital_growth) ** alpha
            * float((current["hc"] * current["emp"]) / (prior["hc"] * prior["emp"]))
            ** (1 - alpha)
            - 1
        )
        fitted.append(prediction * 100)
        actual.append((float(current["rgdpna"] / prior["rgdpna"]) - 1) * 100)
        fitted_capital_growth.append(projected_capital_growth * 100)
        actual_capital_growth.append(observed_capital_growth * 100)
    errors = [estimate - observed for estimate, observed in zip(fitted, actual)]
    capital_errors = [
        estimate - observed
        for estimate, observed in zip(fitted_capital_growth, actual_capital_growth)
    ]
    return {
        "start_year": float(start_year),
        "end_year": float(end_year),
        "actual_average_growth_pct": statistics.mean(actual),
        "fitted_average_growth_pct": statistics.mean(fitted),
        "average_error_pp": statistics.mean(errors),
        "mean_absolute_error_pp": statistics.mean(abs(error) for error in errors),
        "actual_average_capital_growth_pct": statistics.mean(actual_capital_growth),
        "dynamic_average_capital_growth_pct": statistics.mean(fitted_capital_growth),
        "dynamic_capital_average_growth_error_pp": statistics.mean(capital_errors),
    }


def read_general_government_fiscal_workbook(
    path: str | Path,
    year: int,
    sheet_name: str = "1.2.a",
    label_row: int = 3,
    rows: Mapping[str, int] | None = None,
) -> dict[str, float | int | str]:
    """Read one Q4 rolling-12-month fiscal calibration from Tesouro.

    The workbook stores shares as fractions. Returned fiscal shares are percent
    of GDP, and primary revenue/spending exclude interest on both sides.
    """
    row_numbers = dict(
        rows
        or {
            "total_revenue": 4,
            "interest_receivable": 15,
            "total_expense": 17,
            "interest_payable": 22,
            "primary_balance": 33,
        }
    )
    required = {
        "total_revenue",
        "interest_receivable",
        "total_expense",
        "interest_payable",
        "primary_balance",
    }
    if set(row_numbers) != required:
        raise ValueError(f"Fiscal workbook rows must be exactly {sorted(required)}")
    frame = pd.read_excel(path, sheet_name=sheet_name, header=None)
    label = f"{int(year)}-IV"
    matches = frame.columns[frame.iloc[label_row].astype(str).eq(label)].tolist()
    if len(matches) != 1:
        raise ValueError(f"Expected one {label!r} column in sheet {sheet_name!r}; found {len(matches)}")
    column = int(matches[0])

    def percent(name: str) -> float:
        value = frame.iloc[row_numbers[name], column]
        try:
            number = float(value) * 100
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Non-numeric {name} at iloc[{row_numbers[name]}, {column}]") from exc
        if not math.isfinite(number):
            raise ValueError(f"Non-finite {name} at iloc[{row_numbers[name]}, {column}]")
        return number

    total_revenue = percent("total_revenue")
    interest_receivable = percent("interest_receivable")
    total_expense = percent("total_expense")
    interest_payable = percent("interest_payable")
    primary_revenue = total_revenue - interest_receivable
    primary_spending = total_expense - interest_payable
    reported_primary_balance = percent("primary_balance")
    return {
        "year": int(year),
        "column_label": label,
        "column_iloc": column,
        "total_revenue_gdp": total_revenue,
        "interest_receivable_gdp": interest_receivable,
        "primary_revenue_gdp": primary_revenue,
        "total_expense_gdp": total_expense,
        "interest_payable_gdp": interest_payable,
        "primary_spending_gdp": primary_spending,
        "reported_primary_balance_gdp": reported_primary_balance,
        "calculated_primary_balance_gdp": primary_revenue - primary_spending,
    }


def load_macro_inputs(path: str | Path) -> dict:
    """Load C2 inputs and calculate all raw-file-backed calibrations."""
    inputs = read_yaml(path)
    try:
        calibration = inputs["fiscal_calibration"]
        workbook = calibration["workbook"]
        workbook_path = workbook["path"]
        sheet_name = workbook["sheet"]
        label_row = int(workbook["label_row_iloc"])
        rows = workbook["rows_iloc"]
        base_year = int(calibration["base_year"])
        debt_source = calibration["gross_debt_gdp_history"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Incomplete fiscal_calibration in C2 inputs") from exc

    base = read_general_government_fiscal_workbook(
        workbook_path, base_year, sheet_name, label_row, rows
    )
    revenue = float(base["primary_revenue_gdp"])
    inputs["macro"]["revenue_gdp"].update({variant: revenue for variant in VARIANTS})

    debt_history = read_bcb_debt_history(debt_source["path"], debt_source["years"])
    rate_history: dict[int, float] = {}
    for year, debt_value in debt_history.items():
        fiscal = read_general_government_fiscal_workbook(
            workbook_path, year, sheet_name, label_row, rows
        )
        debt = float(debt_value)
        if debt <= 0:
            raise ValueError(f"Gross debt must be positive for {year}")
        rate_history[year] = float(fiscal["interest_payable_gdp"]) / debt * 100
    rates = list(rate_history.values())
    interest_entry = inputs["macro"]["effective_nominal_interest_rate"]
    interest_entry.update(
        {
            "low": min(rates),
            "central": statistics.median(rates),
            "high": max(rates),
        }
    )
    try:
        rate_calibration = inputs["interest_rate_calibration"]
        deflator_history = {
            int(year): float(value)
            for year, value in rate_calibration.get("gdp_deflator_history_pct", {}).items()
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Incomplete interest_rate_calibration in C2 inputs") from exc
    missing_deflators = sorted(set(rate_history) - set(deflator_history))
    legacy_fallback = bool(rate_calibration.get("use_legacy_nominal_rate_fallback", False))
    if missing_deflators and not legacy_fallback:
        urls = rate_calibration.get("downloads_needed", [])
        raise ValueError(
            "GDP-deflator history missing years "
            f"{missing_deflators}; download one of {urls} or explicitly enable "
            "use_legacy_nominal_rate_fallback"
        )
    real_rate_history = {
        year: real_rate_from_nominal(rate, deflator_history[year])
        for year, rate in rate_history.items()
        if year in deflator_history
    }
    if real_rate_history:
        real_rates = list(real_rate_history.values())
        inputs["macro"]["effective_real_interest_rate"].update(
            {
                "low": min(real_rates),
                "central": statistics.median(real_rates),
                "high": max(real_rates),
            }
        )
    latest_debt = debt_history[base_year]
    inputs["macro"]["initial_debt_gdp"].update(
        {variant: latest_debt for variant in VARIANTS}
    )

    try:
        growth = inputs["growth_calibration"]
        pwt = read_pwt_brazil_growth(growth["path"], growth.get("countrycode", "BRA"))
        pwt_base_year = int(growth["base_year"])
        tfp_periods = growth["tfp_periods"]
        human_capital_periods = growth["human_capital_periods"]
        investment_periods = growth["investment_rate_periods"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Incomplete growth_calibration in C2 inputs") from exc
    indexed = pwt.set_index("year")
    if pwt_base_year not in indexed.index:
        raise ValueError(f"PWT missing growth base year {pwt_base_year}")
    base_pwt = indexed.loc[pwt_base_year]
    implied_investment = pwt_implied_investment_rates(pwt).set_index("year")
    for variant in VARIANTS:
        start, end = (int(value) for value in tfp_periods[variant])
        inputs["macro"]["tfp_growth"][variant] = _compound_average(
            indexed["rtfpna"], start, end
        ) * 100
        start, end = (int(value) for value in human_capital_periods[variant])
        inputs["macro"]["human_capital_growth"][variant] = _compound_average(
            indexed["hc"], start, end
        ) * 100
        start, end = (int(value) for value in investment_periods[variant])
        # A 2000-2019 capital calibration contains the 19 transitions ending
        # in 2001 through 2019, matching the CAGR period convention above.
        period_rates = implied_investment.loc[start + 1 : end, "implied_investment_rate"]
        if period_rates.isna().any() or len(period_rates) != end - start:
            raise ValueError(f"Incomplete PWT investment calibration period {start}-{end}")
        inputs["macro"]["investment_rate"][variant] = float(period_rates.mean()) * 100
    point_values = {
        "capital_share": 1 - float(base_pwt["labsh"]),
        "capital_output_ratio": float(base_pwt["rnna"] / base_pwt["rgdpna"]),
        "depreciation_rate": float(base_pwt["delta"]) * 100,
    }
    for name, value in point_values.items():
        inputs["macro"][name].update({variant: value for variant in VARIANTS})
    inputs["derived"] = {
        "base_year_fiscal": base,
        "gross_debt_gdp_history": debt_history,
        "implicit_nominal_interest_rate_history": rate_history,
        "gdp_deflator_history": deflator_history,
        "implicit_real_interest_rate_history": real_rate_history,
        "projected_nominal_interest_rate": {
            variant: (
                float(inputs["macro"]["effective_nominal_interest_rate"][variant])
                if legacy_fallback
                else nominal_rate_from_real(
                    float(inputs["macro"]["effective_real_interest_rate"][variant]),
                    float(inputs["macro"]["gdp_deflator_growth"][variant]),
                )
            )
            for variant in VARIANTS
        },
        "interest_rate_mode": (
            "legacy_historical_nominal"
            if legacy_fallback
            else "historical_real_reinflated_with_projected_deflator"
        ),
        "pwt_base": {
            "year": pwt_base_year,
            "employment_millions": float(base_pwt["emp"]),
            "hours_per_worker": float(base_pwt["avh"]),
            "human_capital_index": float(base_pwt["hc"]),
        },
        "pwt_investment_rate_history": {
            int(year): float(value * 100)
            for year, value in implied_investment["implied_investment_rate"].dropna().items()
        },
        "pwt_backcast": growth_accounting_backcast(pwt),
    }
    return inputs


def macro_input(inputs: Mapping, name: str, variant: str) -> float:
    """Return one numeric macro input with a clear null/missing error."""
    try:
        value = inputs["macro"][name][variant]
    except (KeyError, TypeError) as exc:
        raise MissingMacroInput(f"Missing macro.{name}.{variant}") from exc
    if value is None:
        raise MissingMacroInput(f"Null macro.{name}.{variant}")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MissingMacroInput(f"Non-numeric macro.{name}.{variant}") from exc
    if not math.isfinite(number):
        raise MissingMacroInput(f"Non-finite macro.{name}.{variant}")
    return number


def real_interest_rate_for_year(inputs: Mapping, variant: str, year: int) -> float:
    """Return the drawn real rate plus an optional common annual offset."""
    base = macro_input(inputs, "effective_real_interest_rate", variant)
    offsets = inputs.get("derived", {}).get("real_rate_path_offset_pp", {})
    if not offsets or int(year) <= 2025:
        return base
    annual = {int(key): float(value) for key, value in offsets.items()}
    if int(year) > max(annual):
        return base + annual[max(annual)]
    return base + annual.get(int(year), 0.0)


def validate_capital_price_basis(inputs: Mapping) -> None:
    """Require investment and the projected capital stock to share a basis."""
    try:
        investment_basis = inputs["macro"]["investment_rate"]["price_basis_id"]
        capital_basis = inputs["macro"]["capital_output_ratio"]["price_basis_id"]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "investment_rate and capital_output_ratio require price_basis_id metadata"
        ) from exc
    if investment_basis != capital_basis:
        raise ValueError(
            "investment_rate and capital stock must use the same source price basis"
        )


def multiplier_by_package(parameters: Mapping, variant: str) -> dict[str, dict]:
    """Map scenario packages to accumulated multipliers and response horizons."""
    try:
        choices = parameters["macro_modelling_choices"]
        mapping = choices["package_to_multiplier_category"]
        estimates = parameters["fiscal_multipliers_brazil"]["accumulated"]
    except (KeyError, TypeError) as exc:
        raise ValueError("Incomplete C2 multiplier configuration") from exc
    result: dict[str, dict] = {}
    for package, category in mapping.items():
        # The configured personnel rule is applied whenever a future package maps
        # to personnel; no current default package does so.
        if category == "personnel":
            category = "other_expenditures"
        if category == "efficiency":
            entry = choices["efficiency_output_effect"]
            horizon = estimates["other_expenditures"]["horizon_months"]
        else:
            try:
                entry = estimates[category]
                horizon = entry["horizon_months"]
            except (KeyError, TypeError) as exc:
                raise ValueError(f"No multiplier configured for {package!r}") from exc
        value = entry.get(variant)
        if value is None:
            raise ValueError(f"Null multiplier for {package}.{variant}")
        result[str(package)] = {
            "multiplier": float(value),
            "horizon_months": float(horizon),
        }
    revenue = estimates.get("total_revenue")
    if revenue is None or revenue.get(variant) is None:
        # Without a configured revenue multiplier, tax paths are not allowed
        # (checked in run_corner); zero keeps spending-only scenarios unchanged.
        result["revenue"] = {"multiplier": 0.0, "horizon_months": 12.0, "configured": False}
    else:
        result["revenue"] = {
            "multiplier": float(revenue[variant]),
            "horizon_months": float(revenue["horizon_months"]),
        }
    return result


def validate_protected_categories(scenarios: Mapping) -> None:
    """Reject a default package that assigns reductions to protected categories."""
    protected = set(scenarios.get("protected", []))
    shares = scenarios.get("package_shares", {})
    touched = {name for name in protected if float(shares.get(name, 0.0)) != 0.0}
    if touched:
        raise ValueError(f"Protected categories have non-zero package shares: {sorted(touched)}")


def _interpolate_by_year(path: Mapping, elapsed: int, label: str) -> float:
    """Linear ramp between horizon points, starting from zero at the base year."""
    try:
        points = {0: 0.0} | {int(horizon): float(value) for horizon, value in path.items()}
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid by-year path for {label}") from exc
    horizons = sorted(points)
    if elapsed < 0 or elapsed > horizons[-1]:
        raise ValueError(f"Projection year is outside {label}")
    upper = next(horizon for horizon in horizons if horizon >= elapsed)
    lower = max(horizon for horizon in horizons if horizon <= elapsed)
    if upper == lower:
        return points[lower]
    weight = (elapsed - lower) / (upper - lower)
    return points[lower] + weight * (points[upper] - points[lower])


def build_spending_paths(
    baseline: pd.DataFrame,
    scenarios: Mapping,
    variant: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return annual scenario spending totals and package gaps below S0.

    S0/S1 totals come directly from C1. Reform scenarios are linear ramps below
    S0 and use the configured package shares. S1's offset to demographic drift
    uses the same package, because C1 does not assign that offset to packages.
    """
    validate_protected_categories(scenarios)
    required = {"year", "scenario", "variant", "category", "spending_pct_gdp"}
    missing = required - set(baseline.columns)
    if missing:
        raise ValueError(f"Baseline missing columns: {sorted(missing)}")
    data = baseline.loc[
        baseline["variant"].eq(variant) & baseline["category"].eq("total")
    ].copy()
    pivot = data.pivot(index="year", columns="scenario", values="spending_pct_gdp")
    if not {"S0", "S1"}.issubset(pivot.columns):
        raise ValueError("Baseline requires S0 and S1 total rows")
    years = sorted(int(year) for year in pivot.index)
    if not years or years != list(range(years[0], years[-1] + 1)):
        raise ValueError("Macro debt dynamics require an annual C1 baseline")
    base_year = years[0]
    shares = {str(k): float(v) for k, v in scenarios["package_shares"].items()}
    if not math.isclose(sum(shares.values()), 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValueError("package_shares must sum to one")

    totals: list[dict] = []
    gaps: list[dict] = []
    for year in years:
        s0 = float(pivot.loc[year, "S0"])
        scenario_gaps = {"S0": 0.0, "S1": s0 - float(pivot.loc[year, "S1"])}
        revenue_changes = {"S0": 0.0, "S1": 0.0}
        debt_adjustments = {"S0": 0.0, "S1": 0.0}
        package_paths: dict[str, dict[str, float]] = {}
        elapsed = year - base_year
        for scenario, definition in scenarios["scenarios"].items():
            if not isinstance(definition, dict):
                continue
            if "package_gaps_by_year" in definition:
                # Package-level paths (pp GDP below S0 per package; negative =
                # above S0), used by the 2026 programme scenarios (P1).
                package_paths[str(scenario)] = {
                    str(package): _interpolate_by_year(path, elapsed, f"{scenario}.package_gaps_by_year.{package}")
                    for package, path in definition["package_gaps_by_year"].items()
                }
                gap = sum(package_paths[str(scenario)].values())
                scenario_gaps[str(scenario)] = gap
            elif "by_year" in definition:
                # Reductions (R_*) sit below S0; expansions (direction: above_S0)
                # sit above it, so their gap below S0 is negative.
                sign = -1.0 if definition.get("direction") == "above_S0" else 1.0
                gap = _interpolate_by_year(definition["by_year"], elapsed, f"{scenario}.by_year")
                scenario_gaps[str(scenario)] = sign * gap
            else:
                continue
            # Stock adjustment (e.g. privatisation receipts): pp of GDP of debt
            # retired in that year, outside the primary balance.
            adjustment_path = definition.get("debt_adjustment_by_year")
            debt_adjustments[str(scenario)] = (
                0.0 if adjustment_path is None
                else _interpolate_by_year(adjustment_path, elapsed, f"{scenario}.debt_adjustment_by_year")
            )
            # Tax policy: revenue above S0 in pp of GDP (positive = tax increase).
            revenue_path = definition.get("revenue_by_year")
            revenue_changes[str(scenario)] = (
                0.0 if revenue_path is None
                else _interpolate_by_year(revenue_path, elapsed, f"{scenario}.revenue_by_year")
            )
        for scenario, total_gap in scenario_gaps.items():
            totals.append(
                {
                    "year": year,
                    "scenario": scenario,
                    "spending_pct_gdp": s0 - total_gap,
                    "gap_below_s0_pp": total_gap,
                    "revenue_change_pp": revenue_changes[scenario],
                    "debt_adjustment_pp": debt_adjustments[scenario],
                }
            )
            # A tax increase enters the multiplier machinery as a negative gap on
            # the "revenue" package, so the (negative) revenue multiplier lowers GDP.
            gaps.append(
                {
                    "year": year,
                    "scenario": scenario,
                    "package": "revenue",
                    "gap_below_s0_pp": -revenue_changes[scenario],
                }
            )
            scenario_packages = package_paths.get(
                scenario, {package: total_gap * share for package, share in shares.items()}
            )
            for package, package_gap in scenario_packages.items():
                gaps.append(
                    {
                        "year": year,
                        "scenario": scenario,
                        "package": package,
                        "gap_below_s0_pp": package_gap,
                    }
                )
    return pd.DataFrame(totals), pd.DataFrame(gaps)


def multiplier_level_effect(
    package_gaps: pd.DataFrame,
    multipliers: Mapping[str, Mapping[str, float]],
    persistence: str,
) -> pd.DataFrame:
    """Calculate the annual GDP level gap in percent relative to S0."""
    if persistence not in PERSISTENCE_VARIANTS:
        raise ValueError(f"Unknown persistence variant: {persistence}")
    required = {"year", "scenario", "package", "gap_below_s0_pp"}
    missing = required - set(package_gaps.columns)
    if missing:
        raise ValueError(f"Spending path missing columns: {sorted(missing)}")
    records: list[dict] = []
    for scenario, scenario_data in package_gaps.groupby("scenario", sort=False):
        effects = {int(year): 0.0 for year in sorted(scenario_data["year"].unique())}
        for package, package_data in scenario_data.groupby("package", sort=False):
            if package not in multipliers:
                raise ValueError(f"No multiplier for package {package!r}")
            multiplier = float(multipliers[package]["multiplier"])
            horizon_years = float(multipliers[package]["horizon_months"]) / 12.0
            series = package_data.set_index("year")["gap_below_s0_pp"].sort_index()
            if persistence == "persistent":
                for year, gap in series.items():
                    effects[int(year)] -= float(gap) * multiplier
            else:
                increments = series.diff().fillna(series.iloc[0])
                for shock_year, increment in increments.items():
                    for year in effects:
                        age = year - int(shock_year)
                        if age < 0 or age >= math.ceil(horizon_years):
                            continue
                        active_fraction = min(1.0, max(0.0, horizon_years - age))
                        effects[year] -= float(increment) * multiplier * active_fraction
        records.extend(
            {"year": year, "scenario": scenario, "gdp_level_vs_s0_pct": value}
            for year, value in effects.items()
        )
    return pd.DataFrame(records)


def revenue_elasticity(parameters: Mapping, variant: str) -> float:
    """Revenue elasticity to GDP; the C2 rule (1.0) when no value is configured.

    `revenue_elasticity_to_gdp` has a sourced low/high (IFI EE16) and no central;
    deterministic C2 corners therefore keep elasticity 1.0, and D1 samples it.
    """
    entry = parameters.get("revenue_elasticity_to_gdp") or {}
    value = entry.get("central")
    return 1.0 if value is None else float(value)


def debt_step(previous_debt: float, interest: float, nominal_growth: float, primary_balance: float) -> float:
    """Apply d_t=d_(t-1)(1+i)/(1+g)-pb, all arguments as ratios."""
    if nominal_growth <= -1:
        raise ValueError("Nominal growth must exceed -100%")
    return previous_debt * (1 + interest) / (1 + nominal_growth) - primary_balance


def real_rate_from_nominal(nominal_rate_pct: float, inflation_pct: float) -> float:
    """Convert percent nominal interest and inflation to a percent real rate."""
    inflation = inflation_pct / 100
    if inflation <= -1:
        raise ValueError("Inflation must exceed -100%")
    return ((1 + nominal_rate_pct / 100) / (1 + inflation) - 1) * 100


def nominal_rate_from_real(real_rate_pct: float, inflation_pct: float) -> float:
    """Reinflate a percent real interest rate, returning a nominal percent rate."""
    return ((1 + real_rate_pct / 100) * (1 + inflation_pct / 100) - 1) * 100


def baseline_real_gdp_path(
    population: pd.DataFrame,
    start_year: int,
    end_year: int,
    inputs: Mapping,
    variant: str,
) -> pd.DataFrame:
    """PWT-consistent Cobb-Douglas accounting with IBGE working-age labour."""
    pop = prepare_population(population)
    totals = pop.groupby("year", as_index=True)["population"].sum()
    working_age = pop.loc[pop["age"].between(15, 64)].groupby("year")["population"].sum()
    years = list(range(start_year, end_year + 1))
    absent = sorted(set(years) - set(totals.index))
    if absent:
        raise ValueError(f"Population missing years: {absent}")
    validate_capital_price_basis(inputs)
    tfp = macro_input(inputs, "tfp_growth", variant) / 100
    human_capital_growth = macro_input(inputs, "human_capital_growth", variant) / 100
    alpha = macro_input(inputs, "capital_share", variant)
    investment = macro_input(inputs, "investment_rate", variant) / 100
    capital_output = macro_input(inputs, "capital_output_ratio", variant)
    depreciation = macro_input(inputs, "depreciation_rate", variant) / 100
    if not 0 <= alpha <= 1 or capital_output <= 0:
        raise ValueError("capital_share must be in [0,1] and capital_output_ratio positive")
    level = macro_input(inputs, "base_real_gdp", variant)
    capital = capital_output * level
    base_year = int(inputs["macro"]["base_real_gdp"]["year"])
    base_pc = macro_input(inputs, "base_gdp_per_capita", variant)
    pc_year = int(inputs["macro"]["base_gdp_per_capita"]["year"])
    if base_year != pc_year or base_year != start_year:
        raise ValueError("GDP anchors must be dated to the C1 base year")
    pwt_base = inputs.get("derived", {}).get("pwt_base", {})
    pwt_year = int(pwt_base.get("year", start_year))
    employment = float(pwt_base.get("employment_millions", 1.0)) * 1_000_000
    if pwt_year not in working_age.index:
        pwt_year = start_year
    employment_rate = employment / float(working_age.loc[pwt_year])
    labour = working_age * employment_rate
    rows = [
        {
            "year": base_year,
            "real_gdp": level,
            "baseline_gdp_per_capita": base_pc,
            "s0_potential_real_gdp_growth_pct": math.nan,
        }
    ]
    for year in range(start_year + 1, end_year + 1):
        labour_growth = float(labour.loc[year] / labour.loc[year - 1] - 1)
        next_capital = (1 - depreciation) * capital + investment * level
        capital_growth = next_capital / capital - 1
        growth = (
            (1 + tfp)
            * (1 + capital_growth) ** alpha
            * ((1 + human_capital_growth) * (1 + labour_growth)) ** (1 - alpha)
            - 1
        )
        level *= 1 + growth
        capital = next_capital
        base_pc *= (1 + growth) / float(totals.loc[year] / totals.loc[year - 1])
        rows.append(
            {
                "year": year,
                "real_gdp": level,
                "baseline_gdp_per_capita": base_pc,
                "s0_potential_real_gdp_growth_pct": growth * 100,
            }
        )
    return pd.DataFrame(rows)


def run_corner(
    annual_baseline: pd.DataFrame,
    population: pd.DataFrame,
    scenarios: Mapping,
    parameters: Mapping,
    inputs: Mapping,
    variant: str,
    persistence: str,
) -> pd.DataFrame:
    """Evaluate one aligned low/central/high parameter corner."""
    spending, package_gaps = build_spending_paths(annual_baseline, scenarios, variant)
    multipliers = multiplier_by_package(parameters, variant)
    if multipliers["revenue"].get("configured") is False and (
        package_gaps.loc[package_gaps["package"].eq("revenue"), "gap_below_s0_pp"].abs() > 0
    ).any():
        raise ValueError("A scenario sets revenue_by_year but no total_revenue multiplier is configured")
    effects = multiplier_level_effect(package_gaps, multipliers, persistence)
    frame = spending.merge(effects, on=["year", "scenario"], validate="one_to_one")
    start_year, end_year = int(frame["year"].min()), int(frame["year"].max())
    growth = baseline_real_gdp_path(population, start_year, end_year, inputs, variant)
    frame = frame.merge(growth, on="year", how="left", validate="many_to_one")
    frame["gdp_per_capita"] = frame["baseline_gdp_per_capita"] * (
        1 + frame["gdp_level_vs_s0_pct"] / 100
    )
    okun = macro_input(inputs, "okun_coefficient", variant)
    frame["unemployment_change_pp"] = -okun * frame["gdp_level_vs_s0_pct"]
    revenue = macro_input(inputs, "revenue_gdp", variant)
    elasticity = revenue_elasticity(parameters, variant)
    # Revenue in reais moves with GDP^elasticity relative to S0, so its share of
    # GDP scales by (Y/Y_S0)^(elasticity-1); elasticity 1 is the original C2 rule.
    frame["revenue_gdp"] = (
        revenue * (1 + frame["gdp_level_vs_s0_pct"] / 100) ** (elasticity - 1)
        + frame["revenue_change_pp"]
    )
    frame["primary_balance_gdp"] = frame["revenue_gdp"] - frame["spending_pct_gdp"]
    inflation = macro_input(inputs, "gdp_deflator_growth", variant) / 100
    mode = inputs.get("derived", {}).get(
        "interest_rate_mode", "historical_real_reinflated_with_projected_deflator"
    )
    if mode == "legacy_historical_nominal":
        interest = macro_input(inputs, "effective_nominal_interest_rate", variant) / 100
    initial_debt = macro_input(inputs, "initial_debt_gdp", variant) / 100
    initial_year = int(inputs["macro"]["initial_debt_gdp"]["year"])
    if initial_year != start_year:
        raise ValueError("initial_debt_gdp must be dated to the C1 base year")
    for scenario, index in frame.groupby("scenario", sort=False).groups.items():
        ordered = frame.loc[index].sort_values("year")
        previous_debt = initial_debt
        previous_nominal_gdp = None
        debt_values: dict[int, float] = {}
        for row in ordered.itertuples():
            nominal_gdp = row.real_gdp * (1 + inflation) ** (row.year - start_year) * (
                1 + row.gdp_level_vs_s0_pct / 100
            )
            if row.year == start_year:
                debt_values[int(row.year)] = previous_debt * 100
                previous_nominal_gdp = nominal_gdp
                continue
            if previous_nominal_gdp is None:
                raise RuntimeError("Missing base-year nominal GDP")
            if mode != "legacy_historical_nominal":
                real_interest = real_interest_rate_for_year(inputs, variant, int(row.year))
                interest = nominal_rate_from_real(real_interest, inflation * 100) / 100
            nominal_growth = nominal_gdp / previous_nominal_gdp - 1
            previous_debt = debt_step(
                previous_debt,
                interest,
                nominal_growth,
                row.primary_balance_gdp / 100,
            ) - float(getattr(row, "debt_adjustment_pp", 0.0)) / 100
            debt_values[int(row.year)] = previous_debt * 100
            previous_nominal_gdp = nominal_gdp
        mask = frame["scenario"].eq(scenario)
        frame.loc[mask, "debt_gdp"] = frame.loc[mask, "year"].map(debt_values)
    return frame


def _indicator_dependencies(inputs: Mapping) -> dict[str, set[str]]:
    growth = {"tfp_growth", "human_capital_growth", "capital_share", "investment_rate", "capital_output_ratio", "depreciation_rate", "base_real_gdp", "base_gdp_per_capita"}
    rate_input = (
        "effective_nominal_interest_rate"
        if inputs.get("derived", {}).get("interest_rate_mode") == "legacy_historical_nominal"
        else "effective_real_interest_rate"
    )
    return {
        "gdp_level_vs_s0_pct": set(),
        "gdp_per_capita": growth,
        "s0_potential_real_gdp_growth_pct": growth,
        "unemployment_change_pp": {"okun_coefficient"},
        "primary_balance_gdp": {"revenue_gdp"},
        "debt_gdp": growth | {"revenue_gdp", "initial_debt_gdp", rate_input, "gdp_deflator_growth"},
    }


def project_macro(
    annual_baseline: pd.DataFrame,
    population: pd.DataFrame,
    scenarios: Mapping,
    parameters: Mapping,
    inputs: Mapping,
    horizons: Iterable[int] = (5, 10, 15, 20),
    allow_missing: bool = False,
) -> pd.DataFrame:
    """Project macro indicators and return low/central/high corner envelopes."""
    base_year = int(annual_baseline["year"].min())
    target_years = {base_year + int(horizon): int(horizon) for horizon in horizons}
    dependencies = _indicator_dependencies(inputs)
    unavailable: dict[str, str] = {}
    for indicator, names in dependencies.items():
        try:
            for name in names:
                for variant in VARIANTS:
                    macro_input(inputs, name, variant)
        except MissingMacroInput as exc:
            if not allow_missing:
                raise
            unavailable[indicator] = str(exc)

    evaluation_inputs = inputs
    if unavailable:
        # Missing-dependent columns are discarded below. Harmless finite
        # placeholders let the remaining independent columns be evaluated by
        # the same code path; they are never reported for an affected output.
        evaluation_inputs = copy.deepcopy(inputs)
        positive_placeholders = {
            "capital_output_ratio": 1.0,
            "base_real_gdp": 1.0,
            "base_gdp_per_capita": 1.0,
        }
        for name in set().union(*dependencies.values()):
            entry = evaluation_inputs.get("macro", {}).get(name)
            if not isinstance(entry, dict):
                continue
            for variant in VARIANTS:
                if entry.get(variant) is None:
                    entry[variant] = positive_placeholders.get(name, 0.0)

    raw: list[pd.DataFrame] = []
    for persistence in PERSISTENCE_VARIANTS:
        for corner in VARIANTS:
            evaluated = run_corner(
                annual_baseline,
                population,
                scenarios,
                parameters,
                evaluation_inputs,
                corner,
                persistence,
            )
            evaluated["corner"] = corner
            evaluated["persistence"] = persistence
            raw.append(evaluated)
    combined = pd.concat(raw, ignore_index=True)
    records: list[dict] = []
    for (year, scenario, persistence), group in combined.loc[combined["year"].isin(target_years)].groupby(
        ["year", "scenario", "persistence"], sort=True
    ):
        for indicator in INDICATORS:
            if indicator in unavailable or indicator not in group.columns:
                continue
            if indicator == "s0_potential_real_gdp_growth_pct" and scenario != "S0":
                continue
            values = group.set_index("corner")[indicator].astype(float)
            envelope = {
                "low": float(values.min()),
                "central": float(values.loc["central"]),
                "high": float(values.max()),
            }
            for variant, value in envelope.items():
                records.append(
                    {
                        "year": int(year),
                        "horizon": target_years[int(year)],
                        "scenario": scenario,
                        "variant": variant,
                        "persistence": persistence,
                        "indicator": indicator,
                        "value": value,
                    }
                )
    result = pd.DataFrame(records, columns=["year", "horizon", "scenario", "variant", "persistence", "indicator", "value"])
    result.attrs["skipped_outputs"] = unavailable
    return result.sort_values(["year", "scenario", "persistence", "indicator", "variant"], ignore_index=True)


def _annual_c1_baseline(args: argparse.Namespace, scenarios: Mapping) -> pd.DataFrame:
    """Regenerate C1 annually, validating its published horizon snapshots."""
    fiscal = pd.read_csv(args.fiscal)
    population = pd.read_csv(args.population)
    profiles = pd.read_csv(args.profiles)
    c1_inputs = read_yaml(args.c1_inputs)
    annual = project_baseline(
        fiscal, population, profiles, c1_inputs, range(1, max(scenarios["horizons_years"]) + 1)
    )
    published = pd.read_csv(args.baseline)
    keys = ["year", "scenario", "variant", "category"]
    check = published.merge(annual, on=keys, suffixes=("_published", "_annual"), validate="one_to_one")
    if len(check) != len(published) or not (
        (check["spending_pct_gdp_published"] - check["spending_pct_gdp_annual"]).abs() < 1e-8
    ).all():
        raise ValueError("Annual C1 regeneration does not match data/brazil/baseline.csv")
    return annual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", default="config/parameters.yaml")
    parser.add_argument("--inputs", default="config/parameters.yaml")
    parser.add_argument("--scenarios", default="config/scenarios.yaml")
    parser.add_argument("--baseline", default="data/brazil/baseline.csv")
    parser.add_argument("--population", default="data/brazil/population.csv")
    parser.add_argument("--fiscal", default="data/brazil/fiscal.csv")
    parser.add_argument("--profiles", default="data/brazil/age_profiles.csv")
    parser.add_argument("--c1-inputs", default="config/parameters.yaml")
    parser.add_argument("--output", default="data/brazil/macro.csv")
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args(argv)

    scenarios = read_yaml(args.scenarios)
    annual_baseline = _annual_c1_baseline(args, scenarios)
    result = project_macro(
        annual_baseline,
        pd.read_csv(args.population),
        scenarios,
        read_yaml(args.parameters),
        load_macro_inputs(args.inputs),
        scenarios["horizons_years"],
        args.allow_missing,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False, float_format="%.10f")
    skipped = result.attrs.get("skipped_outputs", {})
    suffix = f"; skipped {skipped}" if skipped else ""
    print(f"Wrote {len(result)} rows to {output}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
