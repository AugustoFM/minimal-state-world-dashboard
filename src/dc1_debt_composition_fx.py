"""DC1: a direct FX-linked debt-stock revaluation diagnostic.

An independent review of this project's academic paper
(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`) argued the debt stock should
be split by currency, holder and maturity, since a sustained depreciation
would directly revalue any foreign-currency-linked debt upward in domestic-
currency terms -- a channel the model's debt identity does not have (the
exchange rate currently affects debt only indirectly, through the inflation
pass-through already in `src.external.apply_external`).

A full multi-instrument debt-composition model (splitting the stock by
indexer, holder and maturity, with its own historical series) was scoped down
for two reasons, both discovered during this task:

1. Brazil's FX-linked share of federal debt is small and historically stable
   (the Treasury's own published figure, already fetched, verified and cited
   in the paper's RV0 limitations paragraph: a stable 3.7-4.4% of the DPF,
   `tesourormd2026`), so the channel this closes is a bounded, second-order
   one, not the dominant risk the review's general critique implies for a
   currency-exposed emerging market.
2. A genuine multi-decade, machine-readable historical series of DPF
   composition by indexer could not be obtained in this environment: the
   Treasury's Relatorio Mensal da Divida (RMD) publishes it only inside
   monthly PDF tables, and this environment cannot extract text from those
   PDFs (the same PDF-extraction limitation already hit, and documented, for
   CYC1's Auerbach-Gorodnichenko/Pires literature sources). Rather than
   fabricate a historical series from unverified secondary sources turned up
   in a web search (a finance blog, a 19-year-old working-paper excerpt),
   `data/brazil/debt_composition.csv` records only the two verified Treasury
   snapshots (Dec 2025, Aug 2026) already cited in the paper, plus the PAF
   2026 target bands -- not a time series.

This module therefore implements the one specific channel the review names
that the available data can actually support: it revalues only the
FX-linked share of debt/GDP directly by the same bootstrapped cumulative
BRL/USD path `src.external` already draws per Monte Carlo draw (reusing
`external.historical_changes`/`bootstrap_path`/`gdp_and_inflation_effects`/
`apply_external` exactly as `src.cyc1_state_dependent_multiplier` does), as
an *additive* layer on top of `debt_gdp_with_external`. This is a distinct
economic mechanism from the existing inflation-pass-through effect (a stock
revaluation, not an income/inflation effect), so it is not a double-count of
anything already in the model. It never modifies `src.montecarlo.run()`'s
published output; nothing here is read by any other module.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src import external
from src.macro import run_corner
from src.montecarlo import central_draw, inputs_for_draw, load_context, parameters_for_draw, sample_draw

DEFAULT_PATHS = {
    "data": Path("data/brazil/dc1_debt_composition_fx.csv"),
    "report": Path("outputs/dc1_debt_composition_fx.md"),
}
N_DRAWS = 300
SEED = 20261026
STREAM_INDEX = 12  # unused by run()'s streams (1-9), D4's (10) or CYC1's (11)
SCENARIOS = ("S0", "R_mod", "R_amb")


def cumulative_depreciation(fx_change_pct: pd.Series) -> pd.Series:
    """Cumulative BRL/USD depreciation (fraction) vs the base year from annual log changes (x100)."""
    return np.exp(fx_change_pct.cumsum() / 100.0) - 1.0


def run_draws(n_draws: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    context = load_context(variants=["default"])
    params = context["parameters"]
    share_cfg = params["debt_composition_fx"]["fx_linked_share_pct_of_dpf"]
    base_year = context["base_year"]
    target_years = context["target_years"]
    steps = max(target_years) - base_year
    rng = np.random.default_rng(seed)
    share_rng = np.random.default_rng([seed, STREAM_INDEX])
    external_rng = np.random.default_rng([seed, STREAM_INDEX, 1])
    changes = external.historical_changes()

    rows: list[dict] = []
    for index in range(n_draws):
        draw = (
            central_draw(params, context["inputs"])
            if index == 0
            else sample_draw(rng, params, context["inputs"])
        )
        fx_share_pct = (
            float(share_cfg["central"])
            if index == 0
            else float(share_rng.uniform(share_cfg["low"], share_cfg["high"]))
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
        depreciation = cumulative_depreciation(bootstrapped["fx_change_pct"]).to_numpy()
        depreciation_by_step = {0: 0.0, **{i + 1: float(v) for i, v in enumerate(depreciation)}}

        for scenario in SCENARIOS:
            scen = corner.loc[corner["scenario"].eq(scenario)].sort_values("year")
            for row in scen.itertuples():
                year = int(row.year)
                if year not in target_years:
                    continue
                step = year - base_year
                depreciation_frac = depreciation_by_step.get(step, 0.0)
                baseline = float(row.debt_gdp_with_external)
                additional_pp = fx_share_pct / 100.0 * baseline * depreciation_frac
                rows.append({
                    "draw": index,
                    "scenario": scenario,
                    "year": year,
                    "horizon": step,
                    "fx_share_pct_sampled": fx_share_pct,
                    "cumulative_brl_depreciation_pct": depreciation_frac * 100.0,
                    "debt_gdp_with_external": baseline,
                    "additional_debt_gdp_pp_from_fx_revaluation": additional_pp,
                    "debt_gdp_with_fx_revaluation": baseline + additional_pp,
                })
    return pd.DataFrame(rows)


def summarise(draws: pd.DataFrame) -> pd.DataFrame:
    """Median [p10, p90] of the baseline, the increment and the revalued debt/GDP, by scenario/horizon."""
    sampled = draws.loc[draws["draw"] > 0]
    records = []
    for (scenario, horizon), group in sampled.groupby(["scenario", "horizon"], sort=False):
        record = {"scenario": scenario, "horizon": int(horizon)}
        for column in (
            "debt_gdp_with_external", "additional_debt_gdp_pp_from_fx_revaluation", "debt_gdp_with_fx_revaluation",
        ):
            record[f"{column}_p10"] = float(np.nanpercentile(group[column], 10))
            record[f"{column}_p50"] = float(np.nanpercentile(group[column], 50))
            record[f"{column}_p90"] = float(np.nanpercentile(group[column], 90))
        records.append(record)
    return pd.DataFrame(records).sort_values(["scenario", "horizon"]).reset_index(drop=True)


def render_report(draws: pd.DataFrame, summary: pd.DataFrame, n_draws: int, seed: int) -> str:
    share_draws = draws.loc[draws["draw"] > 0, "fx_share_pct_sampled"]
    lines = [
        "# DC1: FX-linked debt-stock revaluation diagnostic",
        "",
        "Built in direct response to an independent review of this project's academic paper "
        "(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the debt stock should be "
        "split by currency, holder and maturity so a depreciation directly revalues foreign-"
        "currency-linked debt. A full multi-instrument decomposition was scoped down: Brazil's "
        "FX-linked share of federal debt is small and stable (3.7-4.4% of the DPF, Secretaria do "
        "Tesouro Nacional, already cited in the paper as `tesourormd2026`), and a genuine "
        "multi-decade historical composition series could not be machine-read in this environment "
        "(the Treasury publishes it only inside monthly PDF tables). This diagnostic instead "
        "revalues only that FX-linked tranche directly by the same bootstrapped cumulative BRL/USD "
        "path `src.external` already draws per Monte Carlo draw, additive to the existing "
        "inflation-pass-through effect, not a replacement for it.",
        "",
        f"Draws: {n_draws} (seed {seed}, central draw plus {n_draws - 1} sampled; independent RNG "
        "streams, cannot perturb any `src.montecarlo` output). Sampled FX-linked share: median "
        f"{float(np.nanpercentile(share_draws, 50)):.2f}% "
        f"[{float(np.nanpercentile(share_draws, 10)):.2f}%, {float(np.nanpercentile(share_draws, 90)):.2f}%].",
        "",
        "## Debt/GDP (%): external baseline vs with direct FX-linked revaluation",
        "",
        "| Scenario | Horizon | Baseline (p50 [p10,p90]) | Additional pp from FX revaluation (p50 [p10,p90]) | "
        "With FX revaluation (p50 [p10,p90]) |",
        "|---|---:|---|---|---|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.horizon} | "
            f"{row.debt_gdp_with_external_p50:.2f} "
            f"[{row.debt_gdp_with_external_p10:.2f}, {row.debt_gdp_with_external_p90:.2f}] | "
            f"{row.additional_debt_gdp_pp_from_fx_revaluation_p50:+.3f} "
            f"[{row.additional_debt_gdp_pp_from_fx_revaluation_p10:+.3f}, "
            f"{row.additional_debt_gdp_pp_from_fx_revaluation_p90:+.3f}] | "
            f"{row.debt_gdp_with_fx_revaluation_p50:.2f} "
            f"[{row.debt_gdp_with_fx_revaluation_p10:.2f}, {row.debt_gdp_with_fx_revaluation_p90:.2f}] |"
        )
    lines += [
        "",
        "## Limitations",
        "",
        "- `data/brazil/debt_composition.csv` holds two verified point-in-time Treasury snapshots and "
        "the PAF 2026 target bands, not a historical time series; the FX-linked share is therefore "
        "held constant over the projection horizon rather than estimated as a trend.",
        "- Only the FX-linked tranche is revalued; the Selic-linked, inflation-linked and fixed-rate "
        "shares (which make up the other ~96% of the DPF) are not modelled separately and remain "
        "inside the single blended interest rate the debt identity already uses.",
        "- The revaluation is a direct stock effect only; it does not re-run the resulting debt "
        "change through the sovereign-risk-premium feedback channel (the same first-order "
        "simplification CYC1 and D4 already make and document).",
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
