"""COR1: a jointly-correlated macro-fiscal shock diagnostic.

A wider literature benchmark of this project's own debt-sustainability methodology
(2026-10-26, `reports/Debt model methodology and journal fit.md`) found the field's actual 2025
frontier development is not machine learning and not (yet) copulas, but correlated-shock design:
two institutional papers published within weeks of each other -- a Banque de France working paper
on France and the European Stability Mechanism's own operational fan-chart engine -- both replace
independent parameter draws with a jointly-correlated shock structure, and both find this produces
*wider*, not narrower, uncertainty bands than independent sampling. This model's own published
Monte Carlo samples its structural parameters (growth, interest rate, multipliers) independently
per draw; COR1 tests directly whether Brazil's own historical experience shows the same pattern.

**Design choice: a joint historical block bootstrap, not a fitted VAR.** A classical or Bayesian
vector autoregression needs enough data to estimate its own coefficient matrix; this model's
overlapping annual window for growth, inflation, the primary balance and the exchange rate is only
23 years (2002-2024), too thin to fit a multi-variable VAR with any confidence distinguishable from
noise. Rather than report a VAR coefficient estimated on 23 observations as if it were reliable,
COR1 instead resamples 3-year blocks of the *actual, jointly observed* historical deviations
(growth, inflation, the primary balance and FX change, together, preserving whatever correlation
they actually had in a given historical window) -- the same block-bootstrap convention, at the same
block length, this project already uses for its own stock-flow-adjustment noise term (Section 7)
and its external commodity/world-rate shocks (`src.external`). This is not a new methodological
risk: it is the project's own already-accepted technique, applied to one more variable bundle.

**What this tests.** The baseline, published Monte Carlo treats growth, inflation/the interest
rate, and the primary balance as independently sampled (each from its own literature-sourced
range). COR1 instead perturbs a scenario's already-computed corner with a *jointly drawn* historical
shock vector, re-runs the debt identity, and compares the resulting debt/GDP percentile *band width*
at each horizon against the baseline Monte Carlo's own already-published band width (from
`outputs/runs/summary_percentiles.csv`) for the same scenario and horizon. If Brazil's own history
shows the same pattern the Banque de France and ESM found -- that correlated shocks widen the band
relative to independent sampling -- COR1's bands should come out wider, not narrower, than the
baseline's.

Never modifies `run_corner`, `apply_external`, or the published Monte Carlo; re-runs the debt
identity on a copy of the already-external-adjusted corner, exactly as MR1/FX1/JMC1 already do.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from src import external
from src.macro import debt_step, macro_input, nominal_rate_from_real, real_interest_rate_for_year, run_corner
from src.montecarlo import central_draw, inputs_for_draw, load_context, parameters_for_draw, sample_draw

DEFAULT_PATHS = {
    "observed": Path("data/brazil/backtest_observed.csv"),
    "summary": Path("outputs/runs/summary_percentiles.csv"),
    "data": Path("data/brazil/cor1_correlated_shocks.csv"),
    "report": Path("outputs/cor1_correlated_shocks.md"),
}
N_DRAWS = 300
SEED = 20261026
STREAM_INDEX = 18  # unused by run()'s streams (1-9), D4's (10), CYC1's (11), DC1's (12), IY1's (13),
                   # MR1's (14), FX1's (15), JMC1's (16), DIS1's (17)
SCENARIOS = ("S0", "R_mod", "R_amb", "E_mod", "E_amb")
BLOCK_YEARS = 3  # same convention as Section 7's own stock-flow-adjustment bootstrap
JOINT_COLUMNS = ("gdp_growth_pct", "cpi_inflation_pct", "primary_result_pct_gdp", "brl_per_usd")


def load_joint_historical_deviations(observed_path: Path = DEFAULT_PATHS["observed"]) -> pd.DataFrame:
    """Demeaned, jointly-observed annual deviations for growth, inflation, the primary balance
    (sign-flipped to surplus-positive) and FX log-change, over their common available window."""
    raw = pd.read_csv(observed_path)
    wide = raw.pivot(index="year", columns="indicator", values="value")
    joint = wide[list(JOINT_COLUMNS)].dropna().sort_index()
    joint = joint.rename(columns={"primary_result_pct_gdp": "primary_balance_pct_gdp"})
    joint["primary_balance_pct_gdp"] = -joint["primary_balance_pct_gdp"]
    joint["fx_change_pct"] = 100.0 * np.log(wide["brl_per_usd"] / wide["brl_per_usd"].shift(1))
    joint = joint.drop(columns=["brl_per_usd"]).dropna()
    return joint - joint.mean()


def block_bootstrap_joint(
    rng: np.random.Generator, deviations: pd.DataFrame, steps: int, block_years: int = BLOCK_YEARS,
) -> pd.DataFrame:
    """Resample `steps` years of jointly-observed deviations in `block_years`-year blocks, preserving
    cross-variable and short-run within-block correlation, exactly as `src.external.bootstrap_path`
    resamples the external shock block and as Section 7's own SFA term is bootstrapped."""
    n_obs = len(deviations)
    if n_obs < block_years:
        raise ValueError("Not enough joint historical observations for the requested block length")
    n_blocks = -(-steps // block_years)  # ceiling division
    starts = rng.integers(0, n_obs - block_years + 1, size=n_blocks)
    rows = []
    for start in starts:
        rows.append(deviations.iloc[start:start + block_years])
    return pd.concat(rows, ignore_index=True).iloc[:steps].reset_index(drop=True)


def _rerun_with_joint_shocks(
    frame: pd.DataFrame,
    draw_inputs: Mapping,
    variant: str,
    shocks: pd.DataFrame,
    fx_share_pct: float,
) -> pd.Series:
    """Re-run the debt identity for every scenario in `frame`, perturbing growth, inflation, the
    primary balance and (via DC1's own FX-linked-tranche formula) the debt stock by a single,
    jointly-drawn historical shock path shared across every scenario within the draw -- otherwise
    identical to `external.apply_external`'s own debt loop."""
    start_year = int(frame["year"].min())
    initial_debt = macro_input(draw_inputs, "initial_debt_gdp", variant) / 100.0
    shocks_by_step = {
        int(i) + 1: row for i, row in shocks.reset_index(drop=True).iterrows()
    }
    debt: dict[tuple[int, str], float] = {}
    for scenario, group in frame.groupby("scenario", sort=False):
        ordered = group.sort_values("year")
        previous_debt, previous_nominal, price = initial_debt, None, 1.0
        cumulative_shocked_growth_factor = 1.0
        cumulative_fx_dev_pct = 0.0
        for row in ordered.itertuples():
            step = int(row.year) - start_year
            shock = shocks_by_step.get(step)
            growth_dev_pp = float(shock["gdp_growth_pct"]) if shock is not None else 0.0
            inflation_dev_pp = float(shock["cpi_inflation_pct"]) if shock is not None else 0.0
            balance_dev_pp = float(shock["primary_balance_pct_gdp"]) if shock is not None else 0.0
            fx_dev_pct = float(shock["fx_change_pct"]) if shock is not None else 0.0
            cumulative_fx_dev_pct += fx_dev_pct
            shocked_inflation_pct = float(row.inflation_with_external_pct) + inflation_dev_pp
            if row.year > start_year:
                price *= 1.0 + shocked_inflation_pct / 100.0
                cumulative_shocked_growth_factor *= 1.0 + growth_dev_pp / 100.0
            # Same direct formula apply_external/MR1/FX1/JMC1 all use (real_gdp * price * gap *
            # external), not a telescoping growth-factor shortcut: gap and external_gdp_level_pct
            # both change from year to year by scenario, so only recomputing nominal directly from
            # this year's own row -- never from last year's nominal times a growth ratio -- keeps
            # the zero-shock case an exact reproduction of the published corner.
            nominal = (
                row.real_gdp * price * cumulative_shocked_growth_factor
                * (1 + row.gdp_level_vs_s0_pct / 100) * (1 + row.external_gdp_level_pct / 100)
            )
            if row.year == start_year:
                debt[(int(row.year), str(scenario))] = initial_debt * 100.0
                previous_nominal = nominal
                continue
            real_rate = real_interest_rate_for_year(draw_inputs, variant, int(row.year))
            nominal_interest = nominal_rate_from_real(real_rate, shocked_inflation_pct) / 100.0
            shocked_balance = (row.primary_balance_gdp + balance_dev_pp + float(getattr(row, "external_revenue_pp_gdp", 0.0))) / 100.0
            new_debt = debt_step(previous_debt, nominal_interest, nominal / previous_nominal - 1.0, shocked_balance)
            new_debt -= float(getattr(row, "debt_adjustment_pp", 0.0)) / 100.0
            fx_revaluation_pp = fx_share_pct / 100.0 * (previous_debt * 100.0) * (
                (np.exp(cumulative_fx_dev_pct / 100.0) - 1.0)
            )
            new_debt += fx_revaluation_pp / 100.0
            debt[(int(row.year), str(scenario))] = new_debt * 100.0
            previous_debt = new_debt
            previous_nominal = nominal
    idx = list(zip(frame["year"].astype(int), frame["scenario"].astype(str)))
    return pd.Series([debt[k] for k in idx], index=frame.index)


def run_draws(n_draws: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    context = load_context(variants=["default"])
    params = context["parameters"]
    fx_share_pct = float(params["debt_composition_fx"]["fx_linked_share_pct_of_dpf"]["central"])
    base_year = context["base_year"]
    target_years = context["target_years"]
    steps = max(target_years) - base_year
    rng = np.random.default_rng(seed)
    block_rng = np.random.default_rng([seed, STREAM_INDEX])
    external_rng = np.random.default_rng([seed, STREAM_INDEX, 1])
    changes = external.historical_changes()
    deviations = load_joint_historical_deviations()

    rows: list[dict] = []
    for index in range(n_draws):
        draw = (
            central_draw(params, context["inputs"]) if index == 0 else sample_draw(rng, params, context["inputs"])
        )
        annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
        draw_parameters = parameters_for_draw(params, draw)
        draw_inputs = inputs_for_draw(context["inputs"], draw)
        corner = run_corner(
            annual, context["population"], context["variant_configs"]["default"],
            draw_parameters, draw_inputs, "central", "transitory",
        )
        bootstrapped = external.bootstrap_path(external_rng, changes, steps)
        effects = external.gdp_and_inflation_effects(bootstrapped, params)
        corner = external.apply_external(corner, effects, draw_inputs)

        if index == 0:
            shocks = pd.DataFrame(0.0, index=range(steps), columns=deviations.columns)
        else:
            shocks = block_bootstrap_joint(block_rng, deviations, steps)
        corner = corner.assign(
            debt_gdp_correlated=_rerun_with_joint_shocks(corner, draw_inputs, "central", shocks, fx_share_pct)
        )

        s0 = corner.loc[corner["scenario"].eq("S0")].sort_values("year").set_index("year")
        for scenario in SCENARIOS:
            scen = corner.loc[corner["scenario"].eq(scenario)].sort_values("year").set_index("year")
            for year in target_years:
                if year not in scen.index:
                    continue
                row = scen.loc[year]
                s0_row = s0.loc[year]
                rows.append({
                    "draw": index, "scenario": scenario, "year": int(year), "horizon": int(year) - base_year,
                    "debt_gdp_baseline_vs_s0_pp": float(row.debt_gdp_with_external - s0_row.debt_gdp_with_external),
                    "debt_gdp_correlated_vs_s0_pp": float(row.debt_gdp_correlated - s0_row.debt_gdp_correlated),
                })
    return pd.DataFrame(rows)


def summarise(draws: pd.DataFrame) -> pd.DataFrame:
    sampled = draws.loc[draws["draw"] > 0]
    records = []
    for (scenario, horizon), group in sampled.groupby(["scenario", "horizon"], sort=False):
        record = {"scenario": scenario, "horizon": int(horizon)}
        for column in ("debt_gdp_baseline_vs_s0_pp", "debt_gdp_correlated_vs_s0_pp"):
            p10 = float(np.nanpercentile(group[column], 10))
            p90 = float(np.nanpercentile(group[column], 90))
            record[f"{column}_p10"] = p10
            record[f"{column}_p50"] = float(np.nanpercentile(group[column], 50))
            record[f"{column}_p90"] = p90
            record[f"{column}_width"] = p90 - p10
        records.append(record)
    return pd.DataFrame(records).sort_values(["scenario", "horizon"]).reset_index(drop=True)


def published_band_widths(summary_path: Path = DEFAULT_PATHS["summary"]) -> pd.DataFrame:
    """p90-p10 band width of the *published* Monte Carlo's own debt_gdp_vs_s0_pp, for direct
    comparison against COR1's own independent-draw-0 and correlated-shock band widths."""
    data = pd.read_csv(summary_path)
    mask = (
        data["variant"].eq("default") & data["persistence"].eq("transitory")
        & data["indicator"].eq("debt_gdp_vs_s0_pp") & data["scenario"].isin(SCENARIOS)
    )
    out = data.loc[mask, ["scenario", "horizon", "p10", "p90"]].copy()
    out["published_width"] = out["p90"] - out["p10"]
    return out[["scenario", "horizon", "published_width"]]


def render_report(draws: pd.DataFrame, summary: pd.DataFrame, n_draws: int, seed: int) -> str:
    published = published_band_widths()
    merged = summary.merge(published, on=["scenario", "horizon"], how="left")
    wider_count = int((merged["debt_gdp_correlated_vs_s0_pp_width"] > merged["published_width"]).sum())
    lines = [
        "# COR1: jointly-correlated macro-fiscal shock diagnostic",
        "",
        "Built in response to a wider literature benchmark of this project's own methodology, which "
        "found that two 2025 institutional debt-sustainability papers (Banque de France; the ESM's "
        "own operational fan-chart engine) replace independent parameter sampling with a jointly-"
        "correlated shock structure, both finding this *widens* uncertainty bands relative to "
        "simpler approaches. COR1 tests the same question against Brazil's own 2002-2024 history: "
        "a joint 3-year block bootstrap of growth, inflation, the primary balance and the exchange "
        "rate together (preserving whatever correlation they actually had), compared against the "
        "published Monte Carlo's own independent-sampling band width at the same scenario/horizon. "
        "See the module docstring for why a block bootstrap, not a fitted VAR, was used (23 years "
        "of overlapping data is too thin to fit a multi-variable VAR with confidence).",
        "",
        f"Draws: {n_draws} (seed {seed}, central draw -- zero shock -- plus {n_draws - 1} sampled).",
        f"Band width wider than the published Monte Carlo's own: {wider_count} of {len(merged)} "
        "scenario-horizon cells.",
        "",
        "## Debt/GDP vs S0: band width, correlated-shock diagnostic vs published Monte Carlo (pp)",
        "",
        "| Scenario | Horizon | Published width | COR1 (correlated) width | Wider? |",
        "|---|---:|---:|---:|---|",
    ]
    for row in merged.itertuples(index=False):
        wider = "yes" if row.debt_gdp_correlated_vs_s0_pp_width > row.published_width else "no"
        lines.append(
            f"| {row.scenario} | {row.horizon} | {row.published_width:.3f} | "
            f"{row.debt_gdp_correlated_vs_s0_pp_width:.3f} | {wider} |"
        )
    lines += [
        "",
        "## Limitations",
        "",
        "- A joint historical block bootstrap, not a fitted VAR or Bayesian VAR -- a deliberate "
        "choice given the thin (23-year) overlapping sample, not a claim this fully replicates the "
        "Banque de France/ESM methodology, only that it tests the same underlying question "
        "(correlated vs. independent shocks) with a technique this project already uses elsewhere.",
        "- The FX-linked revaluation reuses DC1's own formula and config parameter rather than "
        "introducing a new assumption; growth and inflation shocks are applied additively to the "
        "already-external-adjusted corner, the same first-order-diagnostic simplification CYC1, "
        "DC1, FX1, MR1 and JMC1 already document.",
        "- The shared joint shock path is common to every scenario within a draw (like the external "
        "and corruption shock blocks already are), so this diagnostic widens uncertainty without "
        "mechanically favouring any policy path.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=N_DRAWS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--data", type=Path, default=DEFAULT_PATHS["data"])
    parser.add_argument("--report", type=Path, default=DEFAULT_PATHS["report"])
    args = parser.parse_args(argv)
    draws = run_draws(args.draws, args.seed)
    summary = summarise(draws)
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    draws.to_csv(args.data, index=False, float_format="%.6f")
    args.report.write_text(render_report(draws, summary, args.draws, args.seed), encoding="utf-8")
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print(f"Wrote {len(draws)} draw-horizon rows to {args.data} and {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
