"""2026 government programmes as model scenarios (task P1).

Builds the programme scenarios (P_lula_rule, P_lula_record, P_flavio_low/mid/high)
from the mapping in ``config/programs_2026.yaml``. Each is an ordinary C2 scenario with
``package_gaps_by_year`` (pp of GDP below S0 per package), ``revenue_by_year``
and ``debt_adjustment_by_year``, so the existing C2 -> C6 -> C4 -> C5 -> C3
chain evaluates both with the same code and the same parameter draws.

Neutrality: the same S0 path, term, delivery bias and draws are used for both
programmes. Sizes a programme does not state are ranges sampled per draw; the
central draw uses their midpoints. Items the model cannot represent are
listed in the config as not modelled, for both.

The paths are ex ante (planned): the fiscal rule is evaluated on the S0 GDP
path, and the realised primary balance then moves with the C2 multipliers and
revenue elasticity like any other scenario.
"""

from __future__ import annotations

import math
from typing import Mapping

import numpy as np
import pandas as pd

from src.macro import (
    baseline_real_gdp_path,
    debt_step,
    macro_input,
    nominal_rate_from_real,
    real_interest_rate_for_year,
)

PROGRAMMES = ("P_lula_rule", "P_lula_record", "P_flavio_low", "P_flavio_mid", "P_flavio_high")


def _range(config: Mapping, programme: str, item: str) -> tuple[float, float]:
    for entry in config["programmes"][programme]["items"]:
        if entry["id"] == item:
            low, high = entry.get("range_pp_gdp", entry.get("timing_years"))
            return float(low), float(high)
    raise KeyError(f"{programme}.{item} has no range")


def _composition(config: Mapping, programme: str, item: str) -> dict[str, float]:
    for entry in config["programmes"][programme]["items"]:
        if entry["id"] == item:
            shares = {str(k): float(v) for k, v in entry["composition"].items()}
            if not math.isclose(sum(shares.values()), 1.0, abs_tol=1e-9):
                raise ValueError(f"{programme}.{item} composition must sum to one")
            return shares
    raise KeyError(f"{programme}.{item} has no composition")


def sample_programme_draw(rng: np.random.Generator, config: Mapping, parameters: Mapping) -> dict:
    """Programme sizes the programmes do not state, sampled uniformly over their ranges."""
    draw = {
        "lula_transfers_pp": float(rng.uniform(*_range(config, "lula_pt", "L3_transfers"))),
        "lula_revenue_pp": float(rng.uniform(*_range(config, "lula_pt", "L5_tax"))),
        "flavio_revenue_pp": float(rng.uniform(*_range(config, "flavio_bolsonaro_pl", "F3_tax_cuts"))),
        "flavio_privatisation_pp": float(rng.uniform(*_range(config, "flavio_bolsonaro_pl", "F5_privatisation"))),
        "flavio_new_programmes_pp": float(rng.uniform(*_range(config, "flavio_bolsonaro_pl", "F8_new_programmes"))),
    }
    draw["delivery_bias_pp"] = delivery_bias(parameters)
    return draw


def central_programme_draw(config: Mapping, parameters: Mapping) -> dict:
    """Midpoints of every unstated range."""
    mid = lambda programme, item: sum(_range(config, programme, item)) / 2  # noqa: E731
    return {
        "lula_transfers_pp": mid("lula_pt", "L3_transfers"),
        "lula_revenue_pp": mid("lula_pt", "L5_tax"),
        "flavio_revenue_pp": mid("flavio_bolsonaro_pl", "F3_tax_cuts"),
        "flavio_privatisation_pp": mid("flavio_bolsonaro_pl", "F5_privatisation"),
        "flavio_new_programmes_pp": mid("flavio_bolsonaro_pl", "F8_new_programmes"),
        "delivery_bias_pp": delivery_bias(parameters),
    }


def delivery_bias(parameters: Mapping) -> float:
    """Pooled median outturn minus original primary target (F1), the same for both programmes."""
    return float(parameters["fiscal_delivery"]["summary"]["median"])


def s0_path(annual: pd.DataFrame, population: pd.DataFrame, inputs: Mapping, variant: str = "central") -> pd.DataFrame:
    """S0 spending, revenue, growth, rates and debt by year (ex-ante inputs for the fiscal rules)."""
    totals = annual.loc[
        annual["variant"].eq(variant) & annual["category"].eq("total") & annual["scenario"].eq("S0"),
        ["year", "spending_pct_gdp"],
    ].sort_values("year").reset_index(drop=True)
    start, end = int(totals["year"].min()), int(totals["year"].max())
    growth = baseline_real_gdp_path(population, start, end, inputs, variant)
    frame = totals.merge(growth[["year", "real_gdp"]], on="year", validate="one_to_one")
    frame["real_growth"] = frame["real_gdp"].pct_change()
    inflation = macro_input(inputs, "gdp_deflator_growth", variant) / 100
    frame["nominal_growth"] = (1 + frame["real_growth"]) * (1 + inflation) - 1
    frame["interest"] = frame["year"].map(
        lambda year: nominal_rate_from_real(
            real_interest_rate_for_year(inputs, variant, int(year)), inflation * 100
        ) / 100
    )
    frame["revenue_gdp"] = macro_input(inputs, "revenue_gdp", variant)
    frame["primary_balance_gdp"] = frame["revenue_gdp"] - frame["spending_pct_gdp"]
    debt = [macro_input(inputs, "initial_debt_gdp", variant) / 100]
    for row in frame.iloc[1:].itertuples():
        debt.append(debt_step(debt[-1], row.interest, row.nominal_growth, row.primary_balance_gdp / 100))
    frame["debt_gdp"] = [d * 100 for d in debt]
    return frame


def _ramp(year: int, start: int, years: int) -> float:
    """Share of a term-long change reached by `year` (0 before start, 1 after start + years - 1)."""
    if years <= 0:
        raise ValueError("ramp length must be positive")
    return min(1.0, max(0.0, (year - start + 1) / years))


def debt_stabilising_primary_balance(s0: pd.DataFrame, year: int, anchor_year: int) -> float:
    """Primary balance (% GDP) that holds debt at its `anchor_year` ratio, on S0 rates and growth.

    Diagnostic for the programmes' debt objectives; it no longer sets a scenario's size (P2).
    """
    s0 = s0.set_index("year") if "year" in s0.columns else s0
    g, i = float(s0.loc[year, "nominal_growth"]), float(s0.loc[year, "interest"])
    return float(s0.loc[anchor_year, "debt_gdp"]) * (i - g) / (1 + g)


def build_programme_scenarios(
    s0: pd.DataFrame,
    config: Mapping,
    draw: Mapping,
    common_composition: Mapping[str, float] | None = None,
) -> dict[str, dict]:
    """Return C2 scenario definitions for every programme scenario (keys: elapsed years).

    P_lula_rule    LC 200/2023 rule on federal primary spending (L1), transfers (L3), revenue (L5).
    P_lula_record  2022-2025 general-government spending and tax-revenue trends continued over the term.
    P_flavio_low/mid/high  spending cuts of the sizes and compositions in model_parameters.flavio_cut_scenarios,
                   with tax cuts (F3), privatisation (F5) and new programmes financed inside (F8).
    Plans (rule and cut scenarios) add the F1 delivery bias; the record scenario is an outturn and does not.
    After the term every gap vs S0 is held. ``common_composition`` (sensitivity) gives every scenario the
    same package shares, so only size, timing and taxes differ.
    """
    model = config["model_parameters"]
    start = int(model["start_year"])
    term = int(model["term_years"])
    last = start + term - 1
    federal_share = float(model["federal_share_of_general_government_primary"]["value"])
    rule = model["lc200_rule"]
    base_year = int(s0["year"].min())
    s0 = s0.set_index("year")
    years = list(s0.index)
    bias = float(draw["delivery_bias_pp"])
    ramp = {y: _ramp(y, start, term) for y in years}

    def shares(raw: Mapping[str, float]) -> dict[str, float]:
        chosen = common_composition if common_composition is not None else raw
        out = {str(k): float(v) for k, v in chosen.items()}
        if not math.isclose(sum(out.values()), 1.0, abs_tol=1e-9):
            raise ValueError("composition must sum to one")
        return out

    def held(values: dict[int, float]) -> dict[int, float]:
        return {y: (0.0 if y < start else values[min(y, last)]) for y in years}

    def horizon_path(values: Mapping[int, float]) -> dict[int, float]:
        return {year - base_year: float(values[year]) for year in years if year > base_year}

    def packages(total: Mapping[int, float], composition: Mapping[str, float]) -> dict[str, dict[int, float]]:
        return {package: horizon_path({y: total[y] * share for y in years}) for package, share in composition.items()}

    def merge(target: dict[str, dict[int, float]], package: str, path: dict[int, float]) -> None:
        old = target.get(package, {})
        target[package] = {h: old.get(h, 0.0) + v for h, v in path.items()}

    out: dict[str, dict] = {}

    # --- Lula, rule: LC 200/2023 on the federal share of S0 spending.
    federal = federal_share * float(s0.loc[start - 1, "spending_pct_gdp"])
    rule_total: dict[int, float] = {}
    rule_revenue: dict[int, float] = {}
    for year in years:
        if year < start or year > last:
            continue
        revenue_now = float(draw["lula_revenue_pp"]) * ramp[year]
        revenue_before = float(draw["lula_revenue_pp"]) * ramp.get(year - 1, 0.0)
        base_revenue = float(s0.loc[year, "revenue_gdp"])
        real_revenue_growth = (
            (1 + s0.loc[year, "real_growth"]) * (base_revenue + revenue_now) / (base_revenue + revenue_before) - 1
        )
        spending_growth = min(
            float(rule["ceiling"]),
            max(float(rule["floor"]), float(rule["share_of_revenue_growth"]) * real_revenue_growth),
        )
        federal *= (1 + spending_growth) / (1 + s0.loc[year, "real_growth"])
        rule_total[year] = federal_share * float(s0.loc[year, "spending_pct_gdp"]) - federal + bias
        rule_revenue[year] = revenue_now
    rule_total, rule_revenue = held(rule_total), held(rule_revenue)
    transfers = {y: float(draw["lula_transfers_pp"]) * ramp[y] for y in years}
    lula_rule = packages({y: rule_total[y] + transfers[y] for y in years},
                         shares(model["lula_compression_composition"]["shares"]))
    merge(lula_rule, "means_tested_transfers", horizon_path({y: -transfers[y] for y in years}))
    out["P_lula_rule"] = {
        "name": "programme_lula_pt_2026_lc200_rule",
        "package_gaps_by_year": lula_rule,
        "revenue_by_year": horizon_path(rule_revenue),
    }

    # --- Lula, record: spending/GDP and tax revenue/GDP keep their 2022-2025 trends during the term.
    record = model["lula_record_trend"]
    anchor = start - 1
    record_total: dict[int, float] = {}
    record_revenue: dict[int, float] = {}
    for year in years:
        if year < start or year > last:
            continue
        elapsed = year - anchor
        s0_drift = float(s0.loc[year, "spending_pct_gdp"] - s0.loc[anchor, "spending_pct_gdp"])
        # gap below S0: S0's own drift minus the record trend (negative = spending above S0)
        record_total[year] = s0_drift - float(record["spending_pp_gdp_per_year"]["value"]) * elapsed
        record_revenue[year] = float(record["tax_revenue_pp_gdp_per_year"]["value"]) * elapsed
    record_total, record_revenue = held(record_total), held(record_revenue)
    out["P_lula_record"] = {
        "name": "programme_lula_pt_2026_record_trend",
        "package_gaps_by_year": packages(record_total, shares(record["composition"]["shares"])),
        "revenue_by_year": horizon_path(record_revenue),
    }

    # --- Flávio: three cut sizes, F3 tax cuts, F5 privatisation, F8 new programmes financed inside.
    new_programmes = {y: float(draw["flavio_new_programmes_pp"]) * ramp[y] for y in years}
    tax = horizon_path({y: float(draw["flavio_revenue_pp"]) * ramp[y] for y in years})
    privatisation = horizon_path(
        {y: (float(draw["flavio_privatisation_pp"]) / term if start <= y <= last else 0.0) for y in years}
    )
    for name, scenario in model["flavio_cut_scenarios"].items():
        if not isinstance(scenario, Mapping):
            continue  # notes
        size = float(scenario["cut_pp_gdp_by_end_of_term"])
        total = {y: (size * ramp[y] + bias if y >= start else 0.0) for y in years}
        gross = {y: total[y] + new_programmes[y] for y in years}
        flavio = packages(gross, shares(scenario["composition"]))
        merge(flavio, "efficiency_health_education_admin", horizon_path({y: -new_programmes[y] for y in years}))
        out[f"P_flavio_{name}"] = {
            "name": f"programme_flavio_bolsonaro_pl_2026_{name}",
            "package_gaps_by_year": flavio,
            "revenue_by_year": dict(tax),
            "debt_adjustment_by_year": dict(privatisation),
        }
    return out


def package_gaps(definition: Mapping, horizon: int) -> dict[str, float]:
    """Package gaps (pp GDP below S0) of a programme definition at an elapsed year."""
    return {
        package: float(path.get(horizon, 0.0))
        for package, path in definition["package_gaps_by_year"].items()
    }
