"""C3 household microsimulation for the Brazil scenarios.

The public functions are deterministic and side-effect free. Monetary inputs
are monthly 2025 BRL unless their argument says otherwise; fiscal gaps are
percentage points of annual nominal GDP. Person-level data are read only by the
CLI and are never written.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from src.baseline import read_yaml


EXCLUDED_CONDITIONS = frozenset({17, 18, 19})
INCOME_COLUMNS = (
    "labor_income_nominal_brl",
    "retirement_pension_income_brl",
    "bpc_income_brl",
    "bolsa_familia_income_brl",
)
PENSION_VARIANTS = ("proportional", "indexation_floor")
LABOUR_VARIANTS = ("gdp_only", "employment")
TAX_VARIANTS = ("proportional", "consumption_like")
TAX_INSTRUMENTS = (
    "top_income",
    "consumption",
    "fuel_energy",
    "payroll",
    "tax_expenditures",
    "business_capital",
)


@dataclass(frozen=True)
class PreparedMicrodata:
    """Immutable arrays reused across scenario-year evaluations."""

    hh_ids: np.ndarray
    household_codes: np.ndarray
    household_size: np.ndarray
    household_weight: np.ndarray
    base_pc: np.ndarray
    person_weight: np.ndarray
    age: np.ndarray
    education: np.ndarray
    employment_status: np.ndarray
    labour: np.ndarray
    pension: np.ndarray
    bpc: np.ndarray
    bolsa: np.ndarray


def weighted_gini(values: np.ndarray, weights: np.ndarray) -> float:
    """Return the weighted Gini on a 0--1 scale (negative incomes rejected)."""
    x = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    valid = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[valid], w[valid]
    if len(x) == 0:
        raise ValueError("weighted_gini requires at least one positive weight")
    if (x < 0).any():
        raise ValueError("weighted_gini does not accept negative incomes")
    order = np.argsort(x, kind="mergesort")
    x, w = x[order], w[order]
    wx = w * x
    total_income = wx.sum()
    if total_income == 0:
        return 0.0
    cumulative_weight = np.cumsum(w)
    return float((wx * (2 * cumulative_weight - w)).sum() / (w.sum() * total_income) - 1)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    """Return the inverse-CDF weighted quantile."""
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between zero and one")
    x = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    valid = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[valid], w[valid]
    if len(x) == 0:
        raise ValueError("weighted_quantile requires at least one positive weight")
    order = np.argsort(x, kind="mergesort")
    x, w = x[order], w[order]
    return float(x[np.searchsorted(np.cumsum(w), quantile * w.sum(), side="left")])


def top_income_share(values: np.ndarray, weights: np.ndarray, top_fraction: float) -> float:
    """Weighted share of income held by the richest fraction of people."""
    if not 0 < top_fraction <= 1:
        raise ValueError("top_fraction must be in (0, 1]")
    x = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    valid = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[valid], w[valid]
    if (x < 0).any():
        raise ValueError("top_income_share does not accept negative incomes")
    total_income = np.sum(x * w)
    if total_income == 0:
        return 0.0
    order = np.argsort(-x, kind="mergesort")
    x, w = x[order], w[order]
    target = top_fraction * w.sum()
    before = np.r_[0.0, np.cumsum(w)[:-1]]
    included_weight = np.clip(target - before, 0.0, w)
    return float(np.sum(x * included_weight) / total_income)


def _validate_person_table(persons: pd.DataFrame) -> None:
    required = {
        "hh_id", "survey_weight", "household_condition",
        "household_income_per_capita_brl", "age", "education_level",
        "employment_status", *INCOME_COLUMNS,
    }
    missing = required - set(persons.columns)
    if missing:
        raise ValueError(f"Person table missing columns: {sorted(missing)}")
    if persons["hh_id"].isna().any():
        raise ValueError("hh_id cannot be missing")
    if (persons["survey_weight"] <= 0).any():
        raise ValueError("survey_weight must be positive")
    if persons["age"].isna().any() or (persons["age"] < 0).any():
        raise ValueError("age must be present and non-negative")


def _weighted_total(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sum(values * weights))


def _component_delta(
    amount: np.ndarray,
    weights: np.ndarray,
    gap_pp_gdp: float,
    nominal_gdp_brl: float,
    allocation_base: np.ndarray,
) -> np.ndarray:
    """Allocate the exact monthly survey-weighted cash change over recipients."""
    target = -float(gap_pp_gdp) / 100 * float(nominal_gdp_brl) / 12
    denominator = _weighted_total(allocation_base, weights)
    if target == 0:
        return np.zeros_like(amount)
    if denominator <= 0:
        raise ValueError("A non-zero package gap has no recipient income in the survey")
    delta = target * allocation_base / denominator
    # A cut cannot take more than the component itself. Current configured gaps
    # do not bind this safeguard; failing is preferable to silently missing GDP.
    if np.any(amount + delta < -1e-8):
        raise ValueError("Package cut exceeds the survey income component")
    return delta


def _weighted_random_mask(candidates: np.ndarray, weights: np.ndarray, target: float, seed: int) -> np.ndarray:
    mask = np.zeros(len(candidates), dtype=bool)
    indices = np.flatnonzero(candidates)
    if target <= 0 or len(indices) == 0:
        return mask
    order = indices[np.random.default_rng(seed).permutation(len(indices))]
    take = np.searchsorted(np.cumsum(weights[order]), target, side="left") + 1
    mask[order[: min(take, len(order))]] = True
    return mask


def _employment_delta(
    status: np.ndarray,
    education: np.ndarray,
    weights: np.ndarray,
    labour_after_gdp: np.ndarray,
    unemployment_change_pp: float,
    seed: int,
) -> np.ndarray:
    labour_force_weight = weights[np.isin(status, (1.0, 2.0))].sum()
    target = abs(float(unemployment_change_pp)) / 100 * labour_force_weight
    delta = np.zeros(len(status), dtype=float)
    if unemployment_change_pp > 0:
        selected = _weighted_random_mask(status == 1, weights, target, seed)
        delta[selected] = -labour_after_gdp[selected]
    elif unemployment_change_pp < 0:
        selected = _weighted_random_mask(status == 2, weights, target, seed)
        employed = (status == 1) & (labour_after_gdp > 0)
        overall = weighted_quantile(labour_after_gdp[employed], weights[employed], 0.5)
        medians: dict[float, float] = {}
        for level in np.unique(education[np.isfinite(education)]):
            group = employed & (education == level)
            if group.any():
                medians[level] = weighted_quantile(labour_after_gdp[group], weights[group], 0.5)
        awards = np.array([medians.get(level, overall) for level in education], dtype=float)
        delta[selected] = awards[selected]
    return delta


def prepare_microdata(persons: pd.DataFrame) -> PreparedMicrodata:
    """Validate and convert a person table to reusable scenario arrays."""
    _validate_person_table(persons)
    eligible = persons.loc[~persons["household_condition"].isin(EXCLUDED_CONDITIONS)]
    if eligible["household_income_per_capita_brl"].isna().any():
        raise ValueError("Eligible records require official per-capita household income")
    codes, hh_ids = pd.factorize(eligible["hh_id"], sort=False)
    grouped = eligible.groupby("hh_id", sort=False)
    minimum_weight = grouped["survey_weight"].min().to_numpy(dtype=float)
    maximum_weight = grouped["survey_weight"].max().to_numpy(dtype=float)
    if not np.allclose(minimum_weight, maximum_weight):
        raise ValueError("survey_weight must be constant within household")
    return PreparedMicrodata(
        hh_ids=np.asarray(hh_ids),
        household_codes=codes,
        household_size=np.bincount(codes).astype(int),
        household_weight=grouped["survey_weight"].first().to_numpy(dtype=float),
        base_pc=grouped["household_income_per_capita_brl"].first().to_numpy(dtype=float),
        person_weight=eligible["survey_weight"].to_numpy(dtype=float),
        age=eligible["age"].to_numpy(dtype=float),
        education=eligible["education_level"].to_numpy(dtype=float),
        employment_status=eligible["employment_status"].to_numpy(dtype=float),
        labour=eligible["labor_income_nominal_brl"].fillna(0).to_numpy(dtype=float),
        pension=eligible["retirement_pension_income_brl"].fillna(0).to_numpy(dtype=float),
        bpc=eligible["bpc_income_brl"].fillna(0).to_numpy(dtype=float),
        bolsa=eligible["bolsa_familia_income_brl"].fillna(0).to_numpy(dtype=float),
    )


def _tax_burden_reference(
    capacity: np.ndarray, score: np.ndarray, weights: np.ndarray, target: float
) -> np.ndarray:
    """Original bisection retained as a numerical oracle for optimisation tests."""
    if target <= 0:
        return np.zeros_like(capacity)
    available = _weighted_total(capacity, weights)
    if target > available + 1e-6:
        raise ValueError("Tax change exceeds total non-negative survey household income")
    valid = score > 0
    if not valid.any():
        raise ValueError("Positive tax change has no positive allocation base")
    low, high = 0.0, max(1.0, target / _weighted_total(score, weights))
    while _weighted_total(np.minimum(capacity, high * score), weights) < target:
        high *= 2
    for _ in range(50):
        middle = (low + high) / 2
        paid = _weighted_total(np.minimum(capacity, middle * score), weights)
        if paid < target:
            low = middle
        else:
            high = middle
    return np.minimum(capacity, high * score)


def _tax_burden(capacity: np.ndarray, score: np.ndarray, weights: np.ndarray, target: float) -> np.ndarray:
    """Allocate a capped score-proportional burden by solving its breakpoints."""
    if target <= 0:
        return np.zeros_like(capacity)
    available = _weighted_total(capacity, weights)
    if target > available + 1e-6:
        raise ValueError("Tax change exceeds total non-negative survey household income")
    valid = score > 0
    if not valid.any():
        raise ValueError("Positive tax change has no positive allocation base")
    valid_positions = np.flatnonzero(valid)
    ratios = capacity[valid] / score[valid]
    order = np.argsort(ratios, kind="stable")
    positions = valid_positions[order]
    ordered_ratios = ratios[order]
    weighted_capacity = capacity[positions] * weights[positions]
    weighted_score = score[positions] * weights[positions]
    cumulative_capacity = np.r_[0.0, np.cumsum(weighted_capacity)]
    cumulative_score = np.r_[0.0, np.cumsum(weighted_score)]
    valid_available = float(cumulative_capacity[-1])
    if target > valid_available + 1e-6:
        raise ValueError("Tax change exceeds income with a positive allocation score")
    remaining_score = cumulative_score[-1] - cumulative_score[:-1]
    lambdas = np.divide(
        target - cumulative_capacity[:-1], remaining_score,
        out=np.full_like(remaining_score, np.inf), where=remaining_score > 0,
    )
    feasible = np.flatnonzero(lambdas <= ordered_ratios)
    multiplier = float(lambdas[feasible[0]]) if len(feasible) else float(ordered_ratios[-1])
    return np.minimum(capacity, multiplier * score)


def _instrument_tax_scores(
    prepared: PreparedMicrodata,
    household_total: np.ndarray,
    consumption_like_exponent: float,
) -> dict[str, np.ndarray]:
    """Return household allocation bases for the supported tax instruments."""
    hh_size = prepared.household_size
    income_pc = household_total / hh_size
    top_cut = weighted_quantile(
        income_pc, prepared.household_weight * hh_size, 0.99,
    )
    top_income = hh_size * np.maximum(income_pc - top_cut, 0.0)
    consumption = hh_size * np.power(income_pc, consumption_like_exponent)
    payroll = np.bincount(
        prepared.household_codes,
        weights=np.where(prepared.employment_status == 1, prepared.labour, 0.0),
        minlength=len(hh_size),
    )
    return {
        "top_income": top_income,
        "consumption": consumption,
        "fuel_energy": consumption.copy(),
        "payroll": payroll,
        "tax_expenditures": household_total.copy(),
        "business_capital": top_income.copy(),
    }


def _apply_instrument_taxes(
    household_total: np.ndarray,
    prepared: PreparedMicrodata,
    changes_pp_gdp: Mapping[str, float],
    nominal_gdp_brl: float,
    consumption_like_exponent: float,
) -> np.ndarray:
    """Apply rises and cuts with the same fixed base for each instrument."""
    unknown = set(changes_pp_gdp) - set(TAX_INSTRUMENTS)
    if unknown:
        raise ValueError(f"Unknown tax instrument(s): {sorted(unknown)}")
    scores = _instrument_tax_scores(prepared, household_total, consumption_like_exponent)
    result = household_total.copy()
    for instrument, change_pp in changes_pp_gdp.items():
        monthly_tax = float(change_pp) / 100 * nominal_gdp_brl / 12
        if monthly_tax == 0:
            continue
        score = scores[instrument]
        if monthly_tax > 0:
            result -= _tax_burden(result, score, prepared.household_weight, monthly_tax)
        else:
            denominator = _weighted_total(score, prepared.household_weight)
            if denominator <= 0:
                raise ValueError(f"Non-zero {instrument} tax change has no positive allocation base")
            result -= monthly_tax * score / denominator
    return result


def simulate_household_incomes(
    persons: pd.DataFrame | PreparedMicrodata,
    *,
    gdp_level_vs_s0_pct: float,
    unemployment_change_pp: float,
    package_gaps_pp_gdp: Mapping[str, float],
    revenue_change_pp: float,
    nominal_gdp_brl: float,
    minimum_wage_brl: float,
    pension_variant: str,
    labour_variant: str,
    tax_variant: str,
    consumption_like_exponent: float,
    random_seed: int,
    bpc_follows_pension_indexation: bool = True,
    revenue_change_by_instrument_pp: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    """Return one row per IBGE income-unit household after one scenario-year.

    Every behavioural setting is explicit so D1 can supply draw-specific values.
    Conditions 17--19 are excluded from both income changes and the denominator.
    """
    prepared = prepare_microdata(persons) if isinstance(persons, pd.DataFrame) else persons
    if pension_variant not in PENSION_VARIANTS:
        raise ValueError(f"Unknown pension_variant: {pension_variant}")
    if labour_variant not in LABOUR_VARIANTS:
        raise ValueError(f"Unknown labour_variant: {labour_variant}")
    if tax_variant not in TAX_VARIANTS:
        raise ValueError(f"Unknown tax_variant: {tax_variant}")
    if nominal_gdp_brl <= 0 or minimum_wage_brl <= 0 or consumption_like_exponent <= 0:
        raise ValueError("GDP, minimum wage and consumption exponent must be positive")

    weights = prepared.person_weight
    delta = np.zeros(len(weights), dtype=float)

    pension = prepared.pension
    bpc = prepared.bpc
    pension_base = pension if pension_variant == "proportional" else np.minimum(pension, minimum_wage_brl)
    pension_amount = pension
    if bpc_follows_pension_indexation:
        pension_amount = pension + bpc
        # BPC is wholly minimum-wage-linked. Under the proportional variant,
        # pension and BPC changes are proportional to their observed amounts.
        pension_base = pension_base + bpc
    delta += _component_delta(
        pension_amount, weights, package_gaps_pp_gdp.get("pension_and_indexation", 0.0),
        nominal_gdp_brl, pension_base,
    )

    bolsa = prepared.bolsa
    transfers = bpc + bolsa
    delta += _component_delta(
        transfers, weights, package_gaps_pp_gdp.get("means_tested_transfers", 0.0),
        nominal_gdp_brl, transfers,
    )

    labour = prepared.labour
    labour_after_gdp = labour * (1 + float(gdp_level_vs_s0_pct) / 100)
    if (labour_after_gdp < 0).any():
        raise ValueError("GDP scaling implies negative labour income")
    delta += labour_after_gdp - labour
    if labour_variant == "employment":
        delta += _employment_delta(
            prepared.employment_status, prepared.education, weights,
            labour_after_gdp, unemployment_change_pp, random_seed,
        )

    codes, hh_ids = prepared.household_codes, prepared.hh_ids
    hh_size, hh_weight, base_pc = prepared.household_size, prepared.household_weight, prepared.base_pc
    base_total = base_pc * hh_size
    household_total = np.maximum(0.0, base_total + np.bincount(codes, weights=delta))

    if revenue_change_by_instrument_pp is not None:
        household_total = _apply_instrument_taxes(
            household_total, prepared, revenue_change_by_instrument_pp,
            nominal_gdp_brl, consumption_like_exponent,
        )
    else:
        monthly_tax = revenue_change_pp / 100 * nominal_gdp_brl / 12
        if tax_variant == "proportional":
            score = household_total.copy()
        else:
            score = hh_size * np.power(np.divide(household_total, hh_size), consumption_like_exponent)
        if monthly_tax >= 0:
            household_total -= _tax_burden(household_total, score, hh_weight, monthly_tax)
        else:
            # Tax relief follows the same incidence score as a rise; no capacity
            # cap is needed for a transfer into the household.
            household_total -= monthly_tax * score / _weighted_total(score, hh_weight)

    age_0_14 = np.bincount(codes, weights=(prepared.age <= 14).astype(float)).astype(int)
    age_65_plus = np.bincount(codes, weights=(prepared.age >= 65).astype(float)).astype(int)
    older_recipient = (prepared.age >= 65) & ((pension + bpc) > 0)
    has_older_recipient = np.bincount(codes, weights=older_recipient.astype(float)) > 0

    return pd.DataFrame({
        "hh_id": hh_ids,
        "survey_weight": hh_weight,
        "income_unit_size": hh_size,
        "household_income_per_capita_brl": household_total / hh_size,
        "age_0_14_count": age_0_14,
        "age_65_plus_count": age_65_plus,
        "living_with_65_plus_pension_bpc_recipient_count": hh_size * has_older_recipient,
    })


def _calculate_indicators_reference(
    households: pd.DataFrame, poverty_lines_brl: Mapping[str, float]
) -> dict[str, float]:
    """Original repeated-sort implementation retained as a numerical oracle."""
    required = {"survey_weight", "income_unit_size", "household_income_per_capita_brl"}
    missing = required - set(households.columns)
    if missing:
        raise ValueError(f"Household table missing columns: {sorted(missing)}")
    income = households["household_income_per_capita_brl"].to_numpy(dtype=float)
    person_weight = (
        households["survey_weight"].to_numpy(dtype=float)
        * households["income_unit_size"].to_numpy(dtype=float)
    )
    income_order = np.argsort(income, kind="stable")
    sorted_income = income[income_order]

    def smoothed_headcount(weights: np.ndarray, denominator: float, line: float) -> float:
        cumulative_weight = np.concatenate(([0.0], np.cumsum(weights[income_order])))
        band_lines = np.linspace(0.95 * line, 1.05 * line, 21)
        positions = np.searchsorted(sorted_income, band_lines, side="left")
        return float(np.mean(100 * cumulative_weight[positions] / denominator))

    result = {
        "gini": weighted_gini(income, person_weight),
        "survey_top_1_income_share_pct": 100 * top_income_share(income, person_weight, 0.01),
        "survey_top_10_income_share_pct": 100 * top_income_share(income, person_weight, 0.10),
        "weighted_income_unit_population": float(person_weight.sum()),
        "weighted_household_count": float(households["survey_weight"].sum()),
    }
    for name, line in poverty_lines_brl.items():
        line = float(line)
        result[f"poverty_headcount_{name}_pct"] = float(100 * person_weight[income < line].sum() / person_weight.sum())
        result[f"poverty_smoothed_{name}_pct"] = smoothed_headcount(person_weight, float(person_weight.sum()), line)
        normalised_gap = np.maximum((line - income) / line, 0.0)
        result[f"poverty_gap_{name}_pct"] = float(100 * np.average(normalised_gap, weights=person_weight))
        result[f"poverty_gap_sq_{name}"] = float(np.average(normalised_gap ** 2, weights=person_weight))
        subgroup_columns = {
            "age_0_14": "age_0_14_count", "age_65_plus": "age_65_plus_count",
            "living_with_65_plus_pension_bpc_recipient": "living_with_65_plus_pension_bpc_recipient_count",
        }
        for subgroup, column in subgroup_columns.items():
            if column not in households:
                continue
            subgroup_weight = households["survey_weight"].to_numpy(dtype=float) * households[column].to_numpy(dtype=float)
            denominator = subgroup_weight.sum()
            result[f"poverty_headcount_{name}_{subgroup}_pct"] = float(100 * subgroup_weight[income < line].sum() / denominator) if denominator > 0 else float("nan")
            result[f"poverty_smoothed_{name}_{subgroup}_pct"] = smoothed_headcount(subgroup_weight, float(denominator), line) if denominator > 0 else float("nan")
            result[f"poverty_gap_{name}_{subgroup}_pct"] = float(100 * np.average(normalised_gap, weights=subgroup_weight)) if denominator > 0 else float("nan")
            result[f"poverty_gap_sq_{name}_{subgroup}"] = float(np.average(normalised_gap ** 2, weights=subgroup_weight)) if denominator > 0 else float("nan")
    return result


def calculate_indicators(households: pd.DataFrame, poverty_lines_brl: Mapping[str, float]) -> dict[str, float]:
    """Calculate person-weighted distribution indicators from household rows."""
    required = {"survey_weight", "income_unit_size", "household_income_per_capita_brl"}
    missing = required - set(households.columns)
    if missing:
        raise ValueError(f"Household table missing columns: {sorted(missing)}")
    income = households["household_income_per_capita_brl"].to_numpy(dtype=float)
    person_weight = (
        households["survey_weight"].to_numpy(dtype=float)
        * households["income_unit_size"].to_numpy(dtype=float)
    )
    income_order = np.argsort(income, kind="stable")
    sorted_income = income[income_order]
    sorted_person_weight = person_weight[income_order]
    sorted_weighted_income = sorted_income * sorted_person_weight
    total_weight = float(person_weight.sum())
    total_income = float(sorted_weighted_income.sum())

    def smoothed_headcount(weights: np.ndarray, denominator: float, line: float) -> float:
        """Average 21 weighted CDF values without materialising 21 boolean arrays."""
        cumulative_weight = np.concatenate(([0.0], np.cumsum(weights[income_order])))
        band_lines = np.linspace(0.95 * line, 1.05 * line, 21)
        positions = np.searchsorted(sorted_income, band_lines, side="left")
        return float(np.mean(100 * cumulative_weight[positions] / denominator))

    if total_income == 0:
        gini = top_1 = top_10 = 0.0
    else:
        cumulative_weight = np.cumsum(sorted_person_weight)
        gini = float(
            (sorted_weighted_income * (2 * cumulative_weight - sorted_person_weight)).sum()
            / (total_weight * total_income) - 1
        )

        descending_income = sorted_income[::-1]
        descending_weight = sorted_person_weight[::-1]
        before = np.r_[0.0, np.cumsum(descending_weight)[:-1]]

        def sorted_top_share(fraction: float) -> float:
            included = np.clip(fraction * total_weight - before, 0.0, descending_weight)
            return float(np.sum(descending_income * included) / total_income)

        top_1, top_10 = sorted_top_share(0.01), sorted_top_share(0.10)

    result = {
        "gini": gini,
        "survey_top_1_income_share_pct": 100 * top_1,
        "survey_top_10_income_share_pct": 100 * top_10,
        "weighted_income_unit_population": total_weight,
        "weighted_household_count": float(households["survey_weight"].sum()),
    }
    for name, line in poverty_lines_brl.items():
        line = float(line)
        result[f"poverty_headcount_{name}_pct"] = float(
            100 * person_weight[income < line].sum() / person_weight.sum()
        )
        result[f"poverty_smoothed_{name}_pct"] = smoothed_headcount(
            person_weight, float(person_weight.sum()), line
        )
        normalised_gap = np.maximum((line - income) / line, 0.0)
        result[f"poverty_gap_{name}_pct"] = float(
            100 * np.average(normalised_gap, weights=person_weight)
        )
        result[f"poverty_gap_sq_{name}"] = float(
            np.average(normalised_gap ** 2, weights=person_weight)
        )
        subgroup_columns = {
            "age_0_14": "age_0_14_count",
            "age_65_plus": "age_65_plus_count",
            "living_with_65_plus_pension_bpc_recipient":
                "living_with_65_plus_pension_bpc_recipient_count",
        }
        for subgroup, column in subgroup_columns.items():
            if column not in households:
                continue
            subgroup_weight = (
                households["survey_weight"].to_numpy(dtype=float)
                * households[column].to_numpy(dtype=float)
            )
            denominator = subgroup_weight.sum()
            result[f"poverty_headcount_{name}_{subgroup}_pct"] = (
                float(100 * subgroup_weight[income < line].sum() / denominator)
                if denominator > 0 else float("nan")
            )
            result[f"poverty_smoothed_{name}_{subgroup}_pct"] = (
                smoothed_headcount(subgroup_weight, float(denominator), line)
                if denominator > 0 else float("nan")
            )
            result[f"poverty_gap_{name}_{subgroup}_pct"] = (
                float(100 * np.average(normalised_gap, weights=subgroup_weight))
                if denominator > 0 else float("nan")
            )
            result[f"poverty_gap_sq_{name}_{subgroup}"] = (
                float(np.average(normalised_gap ** 2, weights=subgroup_weight))
                if denominator > 0 else float("nan")
            )
    return result


def tax_data_context(path: str | Path) -> dict[str, float]:
    """Return Table-V RB4 shares among declarants, without survey correction."""
    data = pd.read_csv(path)
    column = "RB4 | Soma de RB4 do Centil"
    partition = data.loc[(data["table"] == "V") & data["partition"].astype(str).str.lower().eq("true")]
    total = float(partition[column].sum())
    return {
        "tax_data_top_1_share_declarants_not_population_pct": 100 * float(partition.loc[partition["p_low"] >= 99, column].sum()) / total,
        "tax_data_top_10_share_declarants_not_population_pct": 100 * float(partition.loc[partition["p_low"] >= 90, column].sum()) / total,
    }


def _scenario_inputs(config: Mapping, scenario: str, horizon: int) -> tuple[dict[str, float], float]:
    definition = config["scenarios"].get(scenario, {})
    if scenario == "S0":
        total_gap = 0.0
    elif scenario == "S1":
        raise ValueError("S1 has no package allocation in scenarios.yaml")
    else:
        size = float(definition.get("by_year", {}).get(horizon, 0.0))
        total_gap = -size if definition.get("direction") == "above_S0" else size
    gaps = {str(k): total_gap * float(v) for k, v in config["package_shares"].items()}
    revenue = float(definition.get("revenue_by_year", {}).get(horizon, 0.0))
    return gaps, revenue


def _config_values(inputs: Mapping) -> tuple[float, float, dict[str, float], int, float]:
    gdp = float(inputs["nominal_gdp_brl_million"]["value"]) * 1_000_000
    wage = float(inputs["minimum_wage_brl_month"]["value"])
    lines = {name: float(entry["value"]) for name, entry in inputs["poverty_lines_brl_month_per_capita"].items()}
    defaults = inputs["defaults"]
    return gdp, wage, lines, int(defaults["random_seed"]), float(defaults["consumption_like_exponent"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persons", default="data/processed/brazil/microdata/pnadc_2025_c3_input.csv")
    parser.add_argument("--macro", default="data/brazil/macro.csv")
    parser.add_argument("--scenarios", default="config/scenarios.yaml")
    parser.add_argument("--inputs", default="config/c3_inputs_proposed.yaml")
    parser.add_argument("--tax-centiles", default="data/brazil/micro/tax_centiles_2024.csv")
    parser.add_argument("--output", default="data/brazil/micro.csv")
    args = parser.parse_args(argv)

    persons = pd.read_csv(args.persons)
    prepared = prepare_microdata(persons)
    macro = pd.read_csv(args.macro)
    central = macro.loc[
        macro["variant"].eq("central")
        & macro["indicator"].isin(["gdp_level_vs_s0_pct", "unemployment_change_pp"])
    ]
    wide = central.pivot(index=["year", "horizon", "scenario", "persistence"], columns="indicator", values="value").reset_index()
    # S1's aggregate offset to ageing is in C1/C2 but has no package-level gap
    # in either CLI input. Omitting it is safer than assigning a cash incidence.
    wide = wide.loc[wide["scenario"].ne("S1")]
    scenarios, inputs = read_yaml(args.scenarios), read_yaml(args.inputs)
    gdp, wage, poverty_lines, seed, exponent = _config_values(inputs)
    records: list[dict] = []
    for row in wide.itertuples(index=False):
        gaps, revenue = _scenario_inputs(scenarios, row.scenario, int(row.horizon))
        for pension_variant in PENSION_VARIANTS:
            for labour_variant in LABOUR_VARIANTS:
                for tax_variant in TAX_VARIANTS:
                    households = simulate_household_incomes(
                        prepared,
                        gdp_level_vs_s0_pct=float(row.gdp_level_vs_s0_pct),
                        unemployment_change_pp=float(row.unemployment_change_pp),
                        package_gaps_pp_gdp=gaps,
                        revenue_change_pp=revenue,
                        nominal_gdp_brl=gdp,
                        minimum_wage_brl=wage,
                        pension_variant=pension_variant,
                        labour_variant=labour_variant,
                        tax_variant=tax_variant,
                        consumption_like_exponent=exponent,
                        random_seed=seed,
                    )
                    indicators = calculate_indicators(households, poverty_lines)
                    common = {
                        "year": int(row.year), "horizon": int(row.horizon), "scenario": row.scenario,
                        "persistence": row.persistence, "composition_variant": "default",
                        "pension_variant": pension_variant,
                        "labour_variant": labour_variant, "tax_variant": tax_variant,
                    }
                    records.extend({**common, "indicator": name, "value": value} for name, value in indicators.items())
    context = tax_data_context(args.tax_centiles)
    records.extend({
        "year": 2024, "horizon": 0, "scenario": "tax_data_context", "persistence": "not_applicable",
        "composition_variant": "not_applicable", "pension_variant": "not_applicable",
        "labour_variant": "not_applicable", "tax_variant": "not_applicable",
        "indicator": name, "value": value,
    } for name, value in context.items())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(records).sort_values(
        ["year", "scenario", "persistence", "composition_variant", "pension_variant", "labour_variant", "tax_variant", "indicator"],
        ignore_index=True,
    )
    result.to_csv(output, index=False, float_format="%.10f")
    print(f"Wrote {len(result)} aggregate rows to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
