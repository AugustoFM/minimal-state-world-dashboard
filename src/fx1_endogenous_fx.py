"""FX1: an endogenous exchange-rate response to fiscal stress.

An independent review of this project's academic paper
(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`) argued the exchange rate
should respond to a scenario's own fiscal stress -- a sustained,
debt-financed expansion would plausibly widen the sovereign spread and
weaken the real, on top of whatever the economy-wide, policy-blind external
shock path happens to do. `src.external`'s bootstrapped BRL/USD path is
purely exogenous: every scenario in a draw receives the identical path, by
design, so that external luck is never credited to or blamed on a policy.
FX1 adds the one channel the reviewer specifically named without disturbing
that design: an extra, scenario-specific depreciation driven by that
scenario's own debt deviation, layered on top of the common bootstrapped
path, not replacing it.

**Why this is a modelling choice, not a fitted regression.** This project
already tried fitting a debt-to-spread relationship directly for Brazil (C7
"channel B": fit 2000-2014, test 2015-2024) and found it **not supported out
of sample** (`config/parameters.yaml external_block.output_channel_c7.
not_wired`) -- a direct, in-repo precedent against repeating that mistake
for the FX analogue. FX1 instead chains two pieces that are each already
either verified or theory-grounded, never a new fitted elasticity: (1) the
model's own already-verified debt-to-risk-premium parameter
(`long_run_feedback.sovereign_risk_premium`, Baldacci & Kumar 2010), reused
via `src.feedback.sovereign_risk_premium_path` rather than re-derived, and
(2) a sampled, not fitted, spread-to-depreciation elasticity anchored on
uncovered interest parity (a standard theoretical relationship, not an
empirical estimate) with its upper bound informed only qualitatively by a
BIS working paper on the fiscal-FX channel in emerging markets -- whose own
numeric tables, like CYC1's and MR1's literature sources before it, could
not be read in this environment. See `config/parameters.yaml
fx1_endogenous_fx` for the full citation and sourcing notes.

**A structural finding that reshaped this module's design.** The first
implementation routed the extra depreciation through the existing
exchange-rate-pass-through-to-inflation channel and re-ran the debt
identity exactly as `external.apply_external` does, substituting the
higher inflation. That produced an *exactly zero* debt/GDP effect (to
floating-point precision) at every draw and horizon. This is not a bug: in
this model's Fisher-consistent debt identity, the nominal interest rate and
nominal GDP growth both reprice by the same inflation factor, so a pure
inflation shock with no real-economy effect cannot move the debt/GDP ratio
at all, by construction -- the same kind of independently-confirming
structural fact CYC1 found for the model's acyclical growth core. FX1
therefore routes its depreciation through the one channel in this model
that genuinely is not Fisher-neutral: **DC1's FX-linked debt tranche**,
which is a real foreign-currency liability that revalues directly in BRL
terms when the real weakens, regardless of domestic inflation. FX1 reuses
DC1's own `fx_linked_share_pct_of_dpf` parameter rather than introducing a
second debt-composition assumption, and reports the (confirmed-inert)
extra-inflation figures alongside the (genuinely non-zero) FX-linked
revaluation effect, so the zero-by-construction finding stays visible
rather than being quietly dropped.

**Design.** A standalone, additive diagnostic: it reuses `run_corner` and
`external.apply_external` unchanged, then (1) computes each scenario's own
debt-deviation-driven premium from the *baseline* (no-FX1) debt path --
deliberately not self-referential, to avoid a new compounding feedback loop
-- (2) turns that into an extra depreciation, and (3) revalues the FX-linked
share of that scenario's baseline debt/GDP by it, exactly as DC1 revalues
that same tranche against the common bootstrapped path. It never calls
`src.montecarlo.run()`/`evaluate_draw()` and cannot change any published
output.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src import external
from src.feedback import sovereign_risk_premium_path
from src.macro import macro_input, run_corner
from src.montecarlo import central_draw, inputs_for_draw, load_context, parameters_for_draw, sample_draw

DEFAULT_PATHS = {
    "data": Path("data/brazil/fx1_endogenous_fx.csv"),
    "report": Path("outputs/fx1_endogenous_fx.md"),
}
N_DRAWS = 300
SEED = 20261026
STREAM_INDEX = 15  # unused by run()'s streams (1-9), D4's (10), CYC1's (11), DC1's (12), IY1's (13), MR1's (14)
SCENARIOS = ("R_mod", "R_amb", "E_mod", "E_amb")
RISK_PREMIUM_CAP_PP = 50.0  # same out-of-sample guard already used by src.feedback


def extra_inflation_from_depreciation(extra_fx_pct: pd.Series, pass_12: float, pass_24: float) -> pd.Series:
    """Same two-period pass-through formula as `external.gdp_and_inflation_effects`. Reported as a
    diagnostic value only -- see the module docstring for why this does not move debt/GDP here."""
    previous = extra_fx_pct.shift(1).fillna(0.0)
    return pass_12 * extra_fx_pct + (pass_24 - pass_12) * previous


def run_draws(n_draws: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    context = load_context(variants=["default"])
    params = context["parameters"]
    elasticity_cfg = params["fx1_endogenous_fx"]["spread_to_depreciation_elasticity_pct_per_premium_pp"]
    premium_cfg = params["long_run_feedback"]["sovereign_risk_premium"]
    fx_share_cfg = params["debt_composition_fx"]["fx_linked_share_pct_of_dpf"]
    pass_12 = float(params["external_block"]["exchange_rate_pass_through"]["horizon_12m"]["central"])
    pass_24 = float(params["external_block"]["exchange_rate_pass_through"]["horizon_24m"]["central"])
    base_year = context["base_year"]
    target_years = context["target_years"]
    steps = max(target_years) - base_year
    rng = np.random.default_rng(seed)
    elasticity_rng = np.random.default_rng([seed, STREAM_INDEX])
    premium_rng = np.random.default_rng([seed, STREAM_INDEX, 1])
    fx_share_rng = np.random.default_rng([seed, STREAM_INDEX, 2])
    external_rng = np.random.default_rng([seed, STREAM_INDEX, 3])
    changes = external.historical_changes()

    rows: list[dict] = []
    for index in range(n_draws):
        draw = (
            central_draw(params, context["inputs"])
            if index == 0
            else sample_draw(rng, params, context["inputs"])
        )
        elasticity = (
            float(elasticity_cfg["central"])
            if index == 0
            else float(elasticity_rng.uniform(elasticity_cfg["low"], elasticity_cfg["high"]))
        )
        premium_bp = (
            float(premium_cfg["central"])
            if index == 0
            else float(premium_rng.uniform(premium_cfg["low"], premium_cfg["high"]))
        )
        fx_share_pct = (
            float(fx_share_cfg["central"])
            if index == 0
            else float(fx_share_rng.uniform(fx_share_cfg["low"], fx_share_cfg["high"]))
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
        initial_debt_gdp_pp = macro_input(draw_inputs, "initial_debt_gdp", "central")

        premium_pp = sovereign_risk_premium_path(
            corner, corner["debt_gdp_with_external"],
            sovereign_risk_bp_per_debt_pp=premium_bp, initial_debt_gdp=initial_debt_gdp_pp,
            risk_premium_cap_pp=RISK_PREMIUM_CAP_PP,
        )
        extra_fx_pct = elasticity * premium_pp

        extra_inflation_pp = pd.Series(0.0, index=corner.index)
        for _, group in corner.groupby("scenario", sort=False):
            ordered_index = group.sort_values("year").index
            fx_in_year_order = extra_fx_pct.loc[ordered_index].reset_index(drop=True)
            inflation_in_year_order = extra_inflation_from_depreciation(fx_in_year_order, pass_12, pass_24)
            extra_inflation_pp.loc[ordered_index] = inflation_in_year_order.to_numpy()

        # FX-linked debt revaluation (the one channel that is not Fisher-neutral): same formula
        # as src.dc1_debt_composition_fx, driven by FX1's own stress-induced depreciation instead
        # of the common bootstrapped path.
        additional_debt_gdp_pp = (
            fx_share_pct / 100.0 * corner["debt_gdp_with_external"] * (extra_fx_pct / 100.0)
        )
        corner["debt_gdp_with_fx1"] = corner["debt_gdp_with_external"] + additional_debt_gdp_pp
        corner["extra_fx_pct"] = extra_fx_pct
        corner["extra_inflation_pp_inert"] = extra_inflation_pp

        for scenario in SCENARIOS:
            scen = corner.loc[corner["scenario"].eq(scenario)].sort_values("year").set_index("year")
            for year in target_years:
                if year not in scen.index:
                    continue
                row = scen.loc[year]
                rows.append({
                    "draw": index, "scenario": scenario, "year": int(year), "horizon": int(year) - base_year,
                    "elasticity_sampled": elasticity, "premium_bp_sampled": premium_bp,
                    "fx_share_pct_sampled": fx_share_pct,
                    "extra_depreciation_pct": float(row.extra_fx_pct),
                    "extra_inflation_pp_inert": float(row.extra_inflation_pp_inert),
                    "debt_gdp_baseline": float(row.debt_gdp_with_external),
                    "debt_gdp_with_fx1": float(row.debt_gdp_with_fx1),
                    "incremental_debt_gdp_from_fx1_pp": float(row.debt_gdp_with_fx1 - row.debt_gdp_with_external),
                })
    return pd.DataFrame(rows)


def summarise(draws: pd.DataFrame) -> pd.DataFrame:
    sampled = draws.loc[draws["draw"] > 0]
    records = []
    for (scenario, horizon), group in sampled.groupby(["scenario", "horizon"], sort=False):
        record = {"scenario": scenario, "horizon": int(horizon)}
        for column in ("extra_depreciation_pct", "incremental_debt_gdp_from_fx1_pp"):
            record[f"{column}_p10"] = float(np.nanpercentile(group[column], 10))
            record[f"{column}_p50"] = float(np.nanpercentile(group[column], 50))
            record[f"{column}_p90"] = float(np.nanpercentile(group[column], 90))
        records.append(record)
    return pd.DataFrame(records).sort_values(["scenario", "horizon"]).reset_index(drop=True)


def render_report(draws: pd.DataFrame, summary: pd.DataFrame, n_draws: int, seed: int) -> str:
    elasticity = draws.loc[draws["draw"] > 0, "elasticity_sampled"]
    lines = [
        "# FX1: endogenous exchange-rate response to fiscal stress",
        "",
        "Built in direct response to an independent review of this project's academic paper "
        "(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the exchange rate should "
        "respond to a scenario's own fiscal stress, not only to the common, policy-blind external "
        "shock path. Rather than fit a new debt-to-FX regression -- this project already tried the "
        "closest analogue (C7 channel B, debt-to-spread) and found it not supported out of sample "
        "-- FX1 chains the model's own already-verified debt-to-risk-premium parameter to a "
        "sampled, UIP-anchored (not fitted) spread-to-depreciation elasticity.",
        "",
        "**A structural finding along the way**: routing this extra depreciation through the "
        "existing inflation-pass-through channel and re-running the debt identity produced an "
        "*exactly zero* debt/GDP effect at every draw -- a genuine, not a bugged, result: this "
        "model's Fisher-consistent debt identity reprices the nominal rate and nominal GDP growth "
        "by the same inflation factor, so a pure inflation shock with no real-economy effect cannot "
        "move the debt/GDP ratio at all. FX1 therefore routes its depreciation through DC1's "
        "FX-linked debt tranche instead -- a genuine foreign-currency liability that is not "
        "Fisher-neutral -- reusing DC1's own `fx_linked_share_pct_of_dpf` rather than a new "
        "assumption.",
        "",
        f"Draws: {n_draws} (seed {seed}, central draw plus {n_draws - 1} sampled). Sampled "
        f"elasticity (% extra depreciation per 1pp of sovereign risk premium): median "
        f"{float(np.nanpercentile(elasticity, 50)):.2f} [{float(np.nanpercentile(elasticity, 10)):.2f}, "
        f"{float(np.nanpercentile(elasticity, 90)):.2f}].",
        "",
        "## Extra depreciation and incremental debt/GDP from switching FX1 on",
        "",
        "| Scenario | Horizon | Extra depreciation (%, p50 [p10,p90]) | Incremental debt/GDP from FX1 "
        "(pp, p50 [p10,p90]) |",
        "|---|---:|---|---|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.horizon} | "
            f"{row.extra_depreciation_pct_p50:+.3f} "
            f"[{row.extra_depreciation_pct_p10:+.3f}, {row.extra_depreciation_pct_p90:+.3f}] | "
            f"{row.incremental_debt_gdp_from_fx1_pp_p50:+.4f} "
            f"[{row.incremental_debt_gdp_from_fx1_pp_p10:+.4f}, {row.incremental_debt_gdp_from_fx1_pp_p90:+.4f}] |"
        )
    lines += [
        "",
        "## Limitations",
        "",
        "- The spread-to-depreciation elasticity is sampled from a UIP-anchored, literature-informed "
        "range, not fitted to a Brazilian or EM-panel estimate (see `config/parameters.yaml "
        "fx1_endogenous_fx` for the full sourcing note and why a new fitted regression was not "
        "attempted, given C7 channel B's own out-of-sample failure).",
        "- The debt/GDP effect runs only through the FX-linked debt tranche (DC1's channel): the "
        "inflation-pass-through route is reported (`extra_inflation_pp_inert`) but is, by "
        "construction, inert for debt/GDP in this model's Fisher-consistent debt identity.",
        "- The premium driving the extra depreciation is computed from the baseline (no-FX1) debt "
        "path, not re-derived each year from the FX1-adjusted path, to avoid a new compounding "
        "feedback loop; this is a first-order diagnostic, the same simplification CYC1/DC1/MR1 "
        "already document.",
        "- Models only a smooth, contemporaneous level relationship, not a discrete currency-crisis "
        "or overshooting event.",
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
