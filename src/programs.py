"""2026 government programmes as model scenarios (task P1).

Builds two scenario definitions, ``P_lula`` and ``P_flavio``, from the mapping
in ``config/programs_2026.yaml``. Each is an ordinary C2 scenario with
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

from src.macro import baseline_real_gdp_path, debt_step, macro_input, nominal_rate_from_real

PROGRAMMES = ("P_lula", "P_flavio")


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
    low_t, high_t = _range(config, "flavio_bolsonaro_pl", "F1_fiscal_rule")
    draw = {
        "lula_transfers_pp": float(rng.uniform(*_range(config, "lula_pt", "L3_transfers"))),
        "lula_revenue_pp": float(rng.uniform(*_range(config, "lula_pt", "L5_tax"))),
        "flavio_years_to_target": int(rng.integers(int(low_t), int(high_t) + 1)),
        "flavio_revenue_pp": float(rng.uniform(*_range(config, "flavio_bolsonaro_pl", "F3_tax_cuts"))),
        "flavio_privatisation_pp": float(rng.uniform(*_range(config, "flavio_bolsonaro_pl", "F5_privatisation"))),
        "flavio_new_programmes_pp": float(rng.uniform(*_range(config, "flavio_bolsonaro_pl", "F8_new_programmes"))),
    }
    draw["delivery_bias_pp"] = delivery_bias(parameters)
    return draw


def central_programme_draw(config: Mapping, parameters: Mapping) -> dict:
    """Midpoints of every unstated range; T rounded to the nearest whole year."""
    mid = lambda programme, item: sum(_range(config, programme, item)) / 2  # noqa: E731
    return {
        "lula_transfers_pp": mid("lula_pt", "L3_transfers"),
        "lula_revenue_pp": mid("lula_pt", "L5_tax"),
        "flavio_years_to_target": int(round(mid("flavio_bolsonaro_pl", "F1_fiscal_rule"))),
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
    real_rate = macro_input(inputs, "effective_real_interest_rate", variant)
    frame["interest"] = nominal_rate_from_real(real_rate, inflation * 100) / 100
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


def build_programme_scenarios(
    s0: pd.DataFrame,
    config: Mapping,
    draw: Mapping,
    common_composition: Mapping[str, float] | None = None,
) -> dict[str, dict]:
    """Return C2 scenario definitions for both programmes (keys: elapsed years from the base year).

    ``common_composition`` (sensitivity) replaces both programmes' assumed cut
    compositions with the same shares, so only size, timing and taxes differ.
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

    # --- Lula: LC 200/2023 rule on federal primary spending (L1), transfers (L3), revenue (L5).
    lula_comp = {str(k): float(v) for k, v in model["lula_compression_composition"]["shares"].items()}
    if common_composition is not None:
        lula_comp = {str(k): float(v) for k, v in common_composition.items()}
    federal = federal_share * float(s0.loc[start - 1, "spending_pct_gdp"])  # pp GDP in the year before the term
    lula_total: dict[int, float] = {}
    lula_revenue: dict[int, float] = {}
    for year in years:
        if year < start:
            lula_total[year], lula_revenue[year] = 0.0, 0.0
            continue
        if year <= last:
            revenue_now = float(draw["lula_revenue_pp"]) * _ramp(year, start, term)
            revenue_before = float(draw["lula_revenue_pp"]) * _ramp(year - 1, start, term)
            base_revenue = float(s0.loc[year, "revenue_gdp"])
            real_revenue_growth = (
                (1 + s0.loc[year, "real_growth"]) * (base_revenue + revenue_now) / (base_revenue + revenue_before) - 1
            )
            spending_growth = min(
                float(rule["ceiling"]),
                max(float(rule["floor"]), float(rule["share_of_revenue_growth"]) * real_revenue_growth),
            )
            federal *= (1 + spending_growth) / (1 + s0.loc[year, "real_growth"])
            lula_total[year] = federal_share * float(s0.loc[year, "spending_pct_gdp"]) - federal + bias
            lula_revenue[year] = revenue_now
        else:  # after the term the 2030 gap vs S0 is held
            lula_total[year], lula_revenue[year] = lula_total[last], lula_revenue[last]

    # --- Flávio: primary balance reaches the 2026 debt-stabilising level in T years (F1),
    # tax cuts (F3), cut composition (F2), new programmes (F8), privatisation (F5).
    flavio_comp = _composition(config, "flavio_bolsonaro_pl", "F2_spending_cuts")
    if common_composition is not None:
        flavio_comp = {str(k): float(v) for k, v in common_composition.items()}
    years_to_target = int(draw["flavio_years_to_target"])
    anchor_debt = float(s0.loc[start - 1, "debt_gdp"]) / 100
    pb_start = float(s0.loc[start - 1, "primary_balance_gdp"])
    flavio_total: dict[int, float] = {}
    flavio_revenue: dict[int, float] = {}
    flavio_new: dict[int, float] = {}
    flavio_debt: dict[int, float] = {}
    for year in years:
        if year < start:
            flavio_total[year] = flavio_revenue[year] = flavio_new[year] = flavio_debt[year] = 0.0
            continue
        if year <= last:
            g, i = float(s0.loc[year, "nominal_growth"]), float(s0.loc[year, "interest"])
            target = anchor_debt * (i - g) / (1 + g) * 100
            planned_pb = pb_start + (target - pb_start) * _ramp(year, start, years_to_target)
            revenue = float(draw["flavio_revenue_pp"]) * _ramp(year, start, term)
            # gap = change in primary balance minus change in revenue (pb = revenue - spending)
            flavio_total[year] = planned_pb - float(s0.loc[year, "primary_balance_gdp"]) - revenue + bias
            flavio_revenue[year] = revenue
            flavio_new[year] = float(draw["flavio_new_programmes_pp"]) * _ramp(year, start, term)
            flavio_debt[year] = float(draw["flavio_privatisation_pp"]) / term
        else:
            flavio_total[year], flavio_revenue[year] = flavio_total[last], flavio_revenue[last]
            flavio_new[year], flavio_debt[year] = flavio_new[last], 0.0

    def horizon_path(values: Mapping[int, float]) -> dict[int, float]:
        return {year - base_year: float(values[year]) for year in years if year > base_year}

    def merge(packages: dict[str, dict[int, float]], package: str, path: dict[int, float]) -> None:
        old = packages.get(package, {})
        packages[package] = {h: old.get(h, 0.0) + v for h, v in path.items()}

    lula_packages = {
        package: horizon_path({y: (lula_total[y] + float(draw["lula_transfers_pp"]) * _ramp(y, start, term)) * share
                               for y in years})
        for package, share in lula_comp.items()
    }
    transfers = horizon_path({y: -float(draw["lula_transfers_pp"]) * _ramp(y, start, term) for y in years})
    merge(lula_packages, "means_tested_transfers", transfers)
    flavio_packages = {
        package: horizon_path({y: (flavio_total[y] + flavio_new[y]) * share for y in years})
        for package, share in flavio_comp.items()
    }
    services = "efficiency_health_education_admin"
    merge(flavio_packages, services, horizon_path({y: -flavio_new[y] for y in years}))
    return {
        "P_lula": {
            "name": "programme_lula_pt_2026",
            "package_gaps_by_year": lula_packages,
            "revenue_by_year": horizon_path(lula_revenue),
        },
        "P_flavio": {
            "name": "programme_flavio_bolsonaro_pl_2026",
            "package_gaps_by_year": flavio_packages,
            "revenue_by_year": horizon_path(flavio_revenue),
            "debt_adjustment_by_year": horizon_path(flavio_debt),
        },
    }


def package_gaps(definition: Mapping, horizon: int) -> dict[str, float]:
    """Package gaps (pp GDP below S0) of a programme definition at an elapsed year."""
    return {
        package: float(path.get(horizon, 0.0))
        for package, path in definition["package_gaps_by_year"].items()
    }
