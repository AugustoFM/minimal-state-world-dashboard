"""MR1: a Taylor-rule monetary-reaction-function diagnostic.

An independent review of this project's academic paper
(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`) argued the model has no
monetary-policy reaction function at all: the real interest rate
(`src.macro.real_interest_rate_for_year`) is a fixed macro input (optionally
nudged by the I1 market-rate sensitivity path), regardless of inflation or
the output gap a scenario itself creates. A sustained, debt-financed
expansion would plausibly raise both, and a central bank following anything
like a textbook reaction function would raise the Selic in response -- a
channel this model does not have.

This is deliberately built as a standalone, off-to-the-side diagnostic, not
a change to `src.macro.run_corner`'s own rate determination. Wiring a
genuinely state-dependent rate into the shared function every other
diagnostic (CYC1, DC1, D4) and the published Monte Carlo itself depend on
was the plan's own stated highest-interaction-risk option; recomputing the
debt path afterwards, on top of the already-external-adjusted corner, gets
the same answer -- "what would this scenario's debt path look like under a
Taylor rule instead of the fixed rate" -- without touching that shared
function at all.

**Specification.** Taylor (1993)'s classic form, i_t = r*_t + pi_t +
phi_pi*(pi_t - pi*) + phi_y*y_gap_t. Expressed in the real-rate terms this
model already keeps separate from nominal (`src.macro.nominal_rate_from_real`
does the Fisher reinflation), this reduces to r_taylor_t = r*_t +
phi_pi*(pi_t - pi*) + phi_y*y_gap_t, where r*_t is the model's own existing
`real_interest_rate_for_year`, pi_t is `inflation_with_external_pct` (common
to every scenario in this model, so it shifts every scenario's rate by the
same amount), pi* is the 3.0% BCB continuous inflation target already used
elsewhere (`config/parameters.yaml macro.gdp_deflator_growth.central`), and
y_gap_t is `gdp_level_vs_s0_pct` -- zero for S0 by construction, so this is
exactly the term that makes a scenario's Selic path diverge from S0's.

**Coefficients.** A WebSearch pass found several Brazil-specific Taylor-rule
estimates, all reporting a positive, significant Selic response to both
gaps but describing the magnitude only qualitatively ("smaller than
advanced economies," "varying over time") -- their full tables are in PDFs
this environment cannot read (the same limitation already hit for CYC1's
literature sources, reconfirmed here by fetching one paper's own HTML
repository page directly and finding no numbers there either). See
`config/parameters.yaml mr1_taylor_rule` for the full citation and the
resulting choice: phi_pi and phi_y are sampled together as a discount on
Taylor's classic 0.5 coefficient, not fitted to a Brazilian estimate.
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
    "data": Path("data/brazil/mr1_taylor_rule.csv"),
    "report": Path("outputs/mr1_taylor_rule.md"),
}
N_DRAWS = 300
SEED = 20261026
STREAM_INDEX = 14  # unused by run()'s streams (1-9), D4's (10), CYC1's (11), DC1's (12), IY1's (13)
SCENARIOS = ("R_mod", "R_amb", "E_mod", "E_amb")
TAYLOR_1993_COEFFICIENT = 0.5


def taylor_real_rate(
    base_real_rate_pct: float, inflation_pct: float, output_gap_pct: float,
    inflation_target_pct: float, phi_pi: float, phi_y: float,
) -> float:
    """Taylor (1993)'s rule, expressed as a real-rate adjustment to the model's own base rate."""
    return base_real_rate_pct + phi_pi * (inflation_pct - inflation_target_pct) + phi_y * output_gap_pct


def _rerun_debt_with_rate_rule(
    frame: pd.DataFrame, draw_inputs: Mapping, variant: str,
    inflation_target_pct: float, phi_pi: float, phi_y: float,
) -> pd.Series:
    """Re-run the debt identity for every scenario in `frame`, replacing the fixed base real rate
    with a Taylor-rule rate, otherwise identical to `src.external.apply_external`'s own debt loop."""
    start_year = int(frame["year"].min())
    initial_debt = macro_input(draw_inputs, "initial_debt_gdp", variant) / 100.0
    debt: dict[tuple[int, str], float] = {}
    for scenario, group in frame.groupby("scenario", sort=False):
        ordered = group.sort_values("year")
        previous_debt, previous_nominal, price = initial_debt, None, 1.0
        for row in ordered.itertuples():
            if row.year > start_year:
                price *= 1.0 + row.inflation_with_external_pct / 100.0
            nominal = (
                row.real_gdp * price * (1 + row.gdp_level_vs_s0_pct / 100) * (1 + row.external_gdp_level_pct / 100)
            )
            if previous_nominal is not None:
                base_real_rate = real_interest_rate_for_year(draw_inputs, variant, int(row.year))
                real_rate = taylor_real_rate(
                    base_real_rate, float(row.inflation_with_external_pct), float(row.gdp_level_vs_s0_pct),
                    inflation_target_pct, phi_pi, phi_y,
                )
                interest = nominal_rate_from_real(real_rate, row.inflation_with_external_pct) / 100.0
                previous_debt = debt_step(
                    previous_debt, interest, nominal / previous_nominal - 1.0,
                    (row.primary_balance_gdp + row.external_revenue_pp_gdp) / 100.0,
                )
                previous_debt -= float(getattr(row, "debt_adjustment_pp", 0.0)) / 100.0
            debt[(int(row.year), str(scenario))] = previous_debt * 100.0
            previous_nominal = nominal
    return pd.Series(
        [debt[(int(y), str(s))] for y, s in zip(frame["year"], frame["scenario"])], index=frame.index,
    )


def run_draws(n_draws: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    context = load_context(variants=["default"])
    params = context["parameters"]
    discount_cfg = params["mr1_taylor_rule"]["discount_vs_taylor_1993"]
    base_year = context["base_year"]
    target_years = context["target_years"]
    steps = max(target_years) - base_year
    rng = np.random.default_rng(seed)
    discount_rng = np.random.default_rng([seed, STREAM_INDEX])
    external_rng = np.random.default_rng([seed, STREAM_INDEX, 1])
    changes = external.historical_changes()

    rows: list[dict] = []
    for index in range(n_draws):
        draw = (
            central_draw(params, context["inputs"])
            if index == 0
            else sample_draw(rng, params, context["inputs"])
        )
        discount = (
            float(discount_cfg["central"])
            if index == 0
            else float(discount_rng.uniform(discount_cfg["low"], discount_cfg["high"]))
        )
        phi_pi = phi_y = TAYLOR_1993_COEFFICIENT * discount
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
        inflation_target_pct = macro_input(draw_inputs, "gdp_deflator_growth", "central")

        corner["debt_gdp_with_taylor_rule"] = _rerun_debt_with_rate_rule(
            corner, draw_inputs, "central", inflation_target_pct, phi_pi, phi_y,
        )
        s0 = corner.loc[corner["scenario"].eq("S0")].sort_values("year").set_index("year")

        for scenario in SCENARIOS:
            scen = corner.loc[corner["scenario"].eq(scenario)].sort_values("year").set_index("year")
            for year in target_years:
                if year not in scen.index:
                    continue
                row = scen.loc[year]
                s0_row = s0.loc[year]
                base_real_rate = real_interest_rate_for_year(draw_inputs, "central", int(year))
                scen_taylor_rate = taylor_real_rate(
                    base_real_rate, float(row.inflation_with_external_pct), float(row.gdp_level_vs_s0_pct),
                    inflation_target_pct, phi_pi, phi_y,
                )
                s0_taylor_rate = taylor_real_rate(
                    base_real_rate, float(s0_row.inflation_with_external_pct), float(s0_row.gdp_level_vs_s0_pct),
                    inflation_target_pct, phi_pi, phi_y,
                )
                debt_vs_s0_baseline = float(row.debt_gdp_with_external - s0_row.debt_gdp_with_external)
                debt_vs_s0_taylor = float(row.debt_gdp_with_taylor_rule - s0_row.debt_gdp_with_taylor_rule)
                rows.append({
                    "draw": index, "scenario": scenario, "year": int(year), "horizon": int(year) - base_year,
                    "phi_pi_sampled": phi_pi, "phi_y_sampled": phi_y,
                    "real_rate_differential_vs_s0_pp": scen_taylor_rate - s0_taylor_rate,
                    "debt_gdp_vs_s0_baseline_pp": debt_vs_s0_baseline,
                    "debt_gdp_vs_s0_with_taylor_rule_pp": debt_vs_s0_taylor,
                    "incremental_debt_gdp_from_taylor_rule_pp": debt_vs_s0_taylor - debt_vs_s0_baseline,
                })
    return pd.DataFrame(rows)


def summarise(draws: pd.DataFrame) -> pd.DataFrame:
    sampled = draws.loc[draws["draw"] > 0]
    records = []
    for (scenario, horizon), group in sampled.groupby(["scenario", "horizon"], sort=False):
        record = {"scenario": scenario, "horizon": int(horizon)}
        for column in (
            "real_rate_differential_vs_s0_pp", "debt_gdp_vs_s0_baseline_pp",
            "debt_gdp_vs_s0_with_taylor_rule_pp", "incremental_debt_gdp_from_taylor_rule_pp",
        ):
            record[f"{column}_p10"] = float(np.nanpercentile(group[column], 10))
            record[f"{column}_p50"] = float(np.nanpercentile(group[column], 50))
            record[f"{column}_p90"] = float(np.nanpercentile(group[column], 90))
        records.append(record)
    return pd.DataFrame(records).sort_values(["scenario", "horizon"]).reset_index(drop=True)


def render_report(draws: pd.DataFrame, summary: pd.DataFrame, n_draws: int, seed: int) -> str:
    phi = draws.loc[draws["draw"] > 0, "phi_pi_sampled"]
    lines = [
        "# MR1: Taylor-rule monetary-reaction-function diagnostic",
        "",
        "Built in direct response to an independent review of this project's academic paper "
        "(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the model has no monetary "
        "reaction function: the real interest rate is a fixed input regardless of inflation or the "
        "output gap a scenario itself creates. This diagnostic recomputes each scenario's debt path "
        "under a textbook Taylor (1993) rule instead of the fixed rate, as a standalone layer on top "
        "of the already-external-adjusted corner -- it never modifies `src.macro.run_corner` or the "
        "published Monte Carlo.",
        "",
        f"Draws: {n_draws} (seed {seed}, central draw plus {n_draws - 1} sampled). Sampled Taylor "
        f"coefficient (phi_pi = phi_y, a discount on Taylor's classic 0.5): median "
        f"{float(np.nanpercentile(phi, 50)):.3f} [{float(np.nanpercentile(phi, 10)):.3f}, "
        f"{float(np.nanpercentile(phi, 90)):.3f}].",
        "",
        "## Real-rate differential and incremental debt/GDP vs S0, from switching on the Taylor rule",
        "",
        "| Scenario | Horizon | Rate differential vs S0 (pp, p50 [p10,p90]) | Incremental debt/GDP vs S0 "
        "from the Taylor rule (pp, p50 [p10,p90]) |",
        "|---|---:|---|---|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.horizon} | "
            f"{row.real_rate_differential_vs_s0_pp_p50:+.3f} "
            f"[{row.real_rate_differential_vs_s0_pp_p10:+.3f}, {row.real_rate_differential_vs_s0_pp_p90:+.3f}] | "
            f"{row.incremental_debt_gdp_from_taylor_rule_pp_p50:+.3f} "
            f"[{row.incremental_debt_gdp_from_taylor_rule_pp_p10:+.3f}, "
            f"{row.incremental_debt_gdp_from_taylor_rule_pp_p90:+.3f}] |"
        )
    lines += [
        "",
        "## Limitations",
        "",
        "- The inflation-gap term is common to every scenario (this model's inflation input does not "
        "vary by scenario), so only the output-gap term differentiates a scenario's Selic path from "
        "S0's; see `config/parameters.yaml mr1_taylor_rule` for why the coefficients are sampled, "
        "not fitted to a Brazil-specific estimate.",
        "- No interest-rate smoothing/gradualism term, which several of the Brazil-specific studies "
        "surveyed for this task report explicitly for the BCB.",
        "- First-order diagnostic: the Taylor-adjusted debt path is not re-run through the sovereign-"
        "risk-premium feedback channel (`src.feedback`), the same simplification CYC1/DC1 already "
        "document.",
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
