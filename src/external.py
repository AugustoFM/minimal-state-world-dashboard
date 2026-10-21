"""External block (task C6): terms of trade and exchange rate as exogenous paths.

The external environment is not a policy choice, so every scenario in a draw
receives the same external path and differences between scenarios stay
attributable to policy. Paths are built from observed annual changes only:

- stochastic paths: block bootstrap of joint (terms of trade, BRL/USD) annual
  log changes, keeping their observed co-movement;
- reference paths: the observed 2005-2011 boom, the 2011-2016 bust, neutral.

Terms of trade move GDP through `external_block.gdp_wrt_commodity_prices`;
part of the effect is permanent (potential output, per
`potential_vs_actual_output`) and the rest is cyclical and fades. Depreciation
raises inflation through `exchange_rate_pass_through`. Debt is re-run with
`src.macro.debt_step`, keeping the nominal rate Fisher-consistent with the
real rate, so inflation alone does not erode debt (the FX-linked debt share is
a recorded gap).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from src.macro import debt_step, macro_input, nominal_rate_from_real


TOT = "net_barter_terms_of_trade"
FX = "brl_per_usd"
BLOCK_YEARS = 3                 # choice: keeps short-run persistence of commodity cycles
POTENTIAL_SHARE = 0.5           # actual output co-moves twice as strongly as potential (IMF WEO 2015)
CYCLICAL_HALF_LIFE_YEARS = 2.0  # choice: cyclical part fades; documented as an assumption
REFERENCE_PERIODS = {"boom": (2005, 2011), "bust": (2011, 2016)}
C7_PRICE = "commodity_export_price_index"
C7_WORLD = "world_gdp_growth_pct"


def historical_changes(path: str | Path = "data/brazil/backtest_observed.csv") -> pd.DataFrame:
    """Joint annual log changes (x100) of terms of trade and BRL/USD, observed years only."""
    table = pd.read_csv(path)
    wide = table.pivot(index="year", columns="indicator", values="value")[[TOT, FX]].dropna()
    changes = np.log(wide).diff().dropna() * 100.0
    changes.columns = ["tot_change_pct", "fx_change_pct"]
    return changes


def historical_changes_v2(
    external_path: str | Path = "data/brazil/external_observed.csv",
    backtest_path: str | Path = "data/brazil/backtest_observed.csv",
) -> pd.DataFrame:
    """Joint annual changes for the C7 output channel: commodity export prices (log x100),
    world growth and BRL/USD (log x100). Price changes and world growth are demeaned
    over the sample, so a bootstrap path adds shocks but no trend."""
    external_table = pd.read_csv(external_path).pivot(index="year", columns="indicator", values="value")
    backtest = pd.read_csv(backtest_path).pivot(index="year", columns="indicator", values="value")
    frame = pd.DataFrame({
        "dlnp_pct": np.log(external_table[C7_PRICE]).diff() * 100.0,
        "world_growth_dev_pp": external_table[C7_WORLD],
        "fx_change_pct": np.log(backtest[FX]).diff() * 100.0,
    }).dropna()
    frame = frame.loc[frame.index >= 2001]
    for column in ("dlnp_pct", "world_growth_dev_pp"):
        frame[column] = frame[column] - frame[column].mean()
    return frame


def channel_a_coefficients(parameters: Mapping, window: str | None = None) -> dict[str, float]:
    """C7 channel A coefficients: one estimation window, or the average of both (central)."""
    sets = parameters["external_block"]["output_channel_c7"]["coefficient_sets"]
    if window is not None:
        return {k: float(v) for k, v in sets[window].items()}
    keys = next(iter(sets.values())).keys()
    return {k: sum(float(s[k]) for s in sets.values()) / len(sets) for k in keys}


def bootstrap_path(
    rng: np.random.Generator, changes: pd.DataFrame, years: int, block: int = BLOCK_YEARS
) -> pd.DataFrame:
    """Moving-block bootstrap of joint changes for `years` projection years."""
    if len(changes) < block:
        raise ValueError("Not enough observed years for the block length")
    rows: list[np.ndarray] = []
    values = changes.to_numpy()
    while len(rows) < years:
        start = int(rng.integers(0, len(values) - block + 1))
        rows.extend(values[start:start + block])
    path = pd.DataFrame(rows[:years], columns=changes.columns)
    path.insert(0, "step", range(1, years + 1))
    return path


def reference_path(name: str, changes: pd.DataFrame, years: int) -> pd.DataFrame:
    """Observed boom/bust sequence, then zero change; or all-zero neutral path."""
    columns = list(changes.columns)
    path = pd.DataFrame({"step": range(1, years + 1), **{column: 0.0 for column in columns}})
    if name == "neutral":
        return path
    start, end = REFERENCE_PERIODS[name]
    observed = changes.loc[(changes.index > start) & (changes.index <= end)].to_numpy()
    n = min(len(observed), years)
    path.loc[: n - 1, columns] = observed[:n]
    return path


def gdp_and_inflation_effects(
    path: pd.DataFrame, parameters: Mapping, elasticity: float | None = None,
    channel_a: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    """GDP level effect (%) and extra inflation (pp) by projection step.

    Paths with a `dlnp_pct` column (from historical_changes_v2) use the C7 output
    channel; terms-of-trade paths use the C6 coefficient and potential/cyclical split.
    """
    if "dlnp_pct" in path.columns:
        return _effects_c7(path, parameters, channel_a or channel_a_coefficients(parameters))
    block = parameters["external_block"]
    beta = float(block["gdp_wrt_commodity_prices"]["central"] if elasticity is None else elasticity)
    pass_12 = float(block["exchange_rate_pass_through"]["horizon_12m"]["central"])
    pass_24 = float(block["exchange_rate_pass_through"]["horizon_24m"]["central"])
    decay = 0.5 ** (1.0 / CYCLICAL_HALF_LIFE_YEARS)
    permanent, cyclical, previous_fx = 0.0, 0.0, 0.0
    records = []
    for row in path.itertuples(index=False):
        impulse = beta * row.tot_change_pct
        permanent += POTENTIAL_SHARE * impulse
        cyclical = cyclical * decay + (1.0 - POTENTIAL_SHARE) * impulse
        # 12-month pass-through in the year of the depreciation, the rest of the
        # 24-month cumulative effect the following year.
        extra_inflation = pass_12 * row.fx_change_pct + (pass_24 - pass_12) * previous_fx
        previous_fx = row.fx_change_pct
        records.append({
            "step": int(row.step),
            "external_gdp_level_pct": permanent + cyclical,
            "external_potential_level_pct": permanent,
            "external_extra_inflation_pp": extra_inflation,
        })
    return pd.DataFrame(records)


def _effects_c7(path: pd.DataFrame, parameters: Mapping, coefficients: Mapping[str, float]) -> pd.DataFrame:
    block = parameters["external_block"]
    pass_12 = float(block["exchange_rate_pass_through"]["horizon_12m"]["central"])
    pass_24 = float(block["exchange_rate_pass_through"]["horizon_24m"]["central"])
    level, previous_price, previous_fx, cumulative_log_price = 1.0, 0.0, 0.0, 0.0
    dividends = block["output_channel_c7"].get("dividend_revenue")
    dividend_coefficient = 0.0 if dividends is None else float(dividends["lnP"])
    records = []
    for row in path.itertuples(index=False):
        growth = (
            coefficients["dlnP"] * row.dlnp_pct
            + coefficients["dlnP_lag"] * previous_price
            + coefficients["world_gdp_growth_pct"] * row.world_growth_dev_pp
        )
        level *= 1.0 + growth / 100.0
        cumulative_log_price += row.dlnp_pct / 100.0
        extra_inflation = pass_12 * row.fx_change_pct + (pass_24 - pass_12) * previous_fx
        previous_price, previous_fx = row.dlnp_pct, row.fx_change_pct
        records.append({
            "step": int(row.step),
            "external_gdp_level_pct": (level - 1.0) * 100.0,
            # C7 estimates the total response; no potential/cyclical split is identified.
            "external_potential_level_pct": float("nan"),
            "external_extra_inflation_pp": extra_inflation,
            "external_revenue_pp_gdp": dividend_coefficient * cumulative_log_price,
        })
    return pd.DataFrame(records)


def apply_external(corner: pd.DataFrame, effects: pd.DataFrame, inputs: Mapping, variant: str = "central") -> pd.DataFrame:
    """Add external effects to an annual C2 corner and re-run its debt path.

    `corner` is the frame returned by `src.macro.run_corner` (all years, all
    scenarios). Returns it with gdp_per_capita_with_external,
    debt_gdp_with_external and inflation_with_external_pct.
    """
    frame = corner.copy()
    start_year = int(frame["year"].min())
    steps = effects.set_index("step")
    level = frame["year"].map(lambda y: 0.0 if y == start_year else float(steps.loc[y - start_year, "external_gdp_level_pct"]))
    # G2 corruption shock (if present in the effects frame): a common GDP level path added to the external one.
    if "corruption_gdp_level_pct" in steps.columns:
        corruption = frame["year"].map(
            lambda y: 0.0 if y == start_year else float(steps.loc[y - start_year, "corruption_gdp_level_pct"]))
        frame["corruption_gdp_level_pct"] = corruption
        level = ((1.0 + level / 100.0) * (1.0 + corruption / 100.0) - 1.0) * 100.0
    else:
        frame["corruption_gdp_level_pct"] = 0.0
    extra = frame["year"].map(lambda y: 0.0 if y == start_year else float(steps.loc[y - start_year, "external_extra_inflation_pp"]))
    frame["external_gdp_level_pct"] = level  # external and (G2) corruption shocks combined
    frame["gdp_per_capita_with_external"] = frame["gdp_per_capita"] * (1.0 + level / 100.0)
    base_inflation = macro_input(inputs, "gdp_deflator_growth", variant)
    real_rate = macro_input(inputs, "effective_real_interest_rate", variant)
    frame["inflation_with_external_pct"] = base_inflation + extra
    # C7 commodity-linked dividends (0 for C6 paths): added to the primary balance in this debt path.
    if "external_revenue_pp_gdp" in steps.columns:
        frame["external_revenue_pp_gdp"] = frame["year"].map(
            lambda y: 0.0 if y == start_year else float(steps.loc[y - start_year, "external_revenue_pp_gdp"]))
    else:
        frame["external_revenue_pp_gdp"] = 0.0
    initial_debt = macro_input(inputs, "initial_debt_gdp", variant) / 100.0
    debt = {}
    for scenario, group in frame.groupby("scenario", sort=False):
        ordered = group.sort_values("year")
        previous_debt, previous_nominal, price = initial_debt, None, 1.0
        for row in ordered.itertuples():
            if row.year > start_year:
                price *= 1.0 + row.inflation_with_external_pct / 100.0
            nominal = row.real_gdp * price * (1 + row.gdp_level_vs_s0_pct / 100) * (1 + row.external_gdp_level_pct / 100)
            if previous_nominal is not None:
                interest = nominal_rate_from_real(real_rate, row.inflation_with_external_pct) / 100.0
                previous_debt = debt_step(previous_debt, interest, nominal / previous_nominal - 1.0,
                                          (row.primary_balance_gdp + row.external_revenue_pp_gdp) / 100.0)
                previous_debt -= float(getattr(row, "debt_adjustment_pp", 0.0)) / 100.0
            debt[(row.year, scenario)] = previous_debt * 100.0
            previous_nominal = nominal
    frame["debt_gdp_with_external"] = [debt[(y, s)] for y, s in zip(frame["year"], frame["scenario"])]
    if not math.isfinite(frame["debt_gdp_with_external"].sum()):
        raise ValueError("Non-finite debt path with external effects")
    return frame
