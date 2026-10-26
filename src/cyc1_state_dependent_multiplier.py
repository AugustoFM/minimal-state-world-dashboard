"""CYC1: a state-dependent (cyclical) fiscal-multiplier diagnostic.

An independent review of this project's academic paper
(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`) argued the model's fiscal
multipliers never vary with the business cycle, despite the paper citing
state-dependence evidence (Auerbach & Gorodnichenko 2012; Pires 2014) that it
does not use. Investigating this surfaced a prior, more basic fact: this
model's own deterministic growth trend is perfectly smooth year to year (no
cyclical fluctuation at all without the external shock block), so there is no
"recession regime" concept to condition a multiplier on unless genuine
year-to-year variation is reintroduced -- which this model already has, in
the stochastic commodity/FX shock path (`src.external`).

This module therefore layers a state-dependent multiplier diagnostic on top
of the *external-shock-adjusted* S0 growth path (reusing
`external.bootstrap_path`/`gdp_and_inflation_effects`/`apply_external`
exactly as `src.montecarlo.evaluate_draw` does), classifies each year as a
recession or expansion regime using the same real-time, trailing-mean proxy
as PCY1 (`src.pcy1_fiscal_timing`), and rescales the fiscal-multiplier-driven
GDP effect of two headline reduction scenarios (R_mod, R_amb) by a sampled
state-dependence ratio (`config/parameters.yaml
multiplier_state_dependence_ratio`, itself sampled rather than fixed because
the underlying literature is contested -- see that key's own sourcing notes)
in recession years only.

This is a first-order diagnostic, not a full re-derivation: it rescales the
reported `gdp_level_vs_s0_pct` directly, which is correct for the GDP effect
itself (S0's own gap is zero by construction, so this column *is* the
multiplier's effect), but does not re-run the resulting debt consequence
through the capital-accumulation/debt identity a genuinely state-dependent
multiplier would also affect (the same simplification D4's fiscal-reaction-
function diagnostics already make and document). It never modifies
`src.montecarlo.run()`'s published output; nothing here is read by any other
module.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src import external
from src.macro import run_corner
from src.montecarlo import central_draw, inputs_for_draw, load_context, parameters_for_draw, sample_draw
from src.pcy1_fiscal_timing import TREND_WINDOW_YEARS

DEFAULT_PATHS = {
    "data": Path("data/brazil/cyc1_state_dependent_multiplier.csv"),
    "report": Path("outputs/cyc1_state_dependent_multiplier.md"),
}
N_DRAWS = 300
SEED = 20261020
STREAM_INDEX = 11  # unused by any of src.montecarlo.run()'s streams (1-9) or D4's (10)
SCENARIOS = ("R_mod", "R_amb")


def classify_recession_years(effective_level: pd.Series, trend_window_years: int = TREND_WINDOW_YEARS) -> pd.Series:
    """True for years whose growth is below its own trailing-mean trend (PCY1-style proxy)."""
    growth = effective_level.pct_change() * 100.0
    trend = growth.rolling(trend_window_years, min_periods=trend_window_years).mean()
    gap = growth - trend
    return gap < 0


def run_draws(n_draws: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    context = load_context(variants=["default"])
    params = context["parameters"]
    ratio_cfg = params["multiplier_state_dependence_ratio"]
    base_year = context["base_year"]
    target_years = context["target_years"]
    steps = max(target_years) - base_year
    rng = np.random.default_rng(seed)
    ratio_rng = np.random.default_rng([seed, STREAM_INDEX])
    external_rng = np.random.default_rng([seed, STREAM_INDEX, 1])
    changes = external.historical_changes()

    rows: list[dict] = []
    for index in range(n_draws):
        draw = (
            central_draw(params, context["inputs"])
            if index == 0
            else sample_draw(rng, params, context["inputs"])
        )
        ratio = (
            float(ratio_cfg["central"])
            if index == 0
            else float(ratio_rng.uniform(ratio_cfg["low"], ratio_cfg["high"]))
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

        s0 = corner.loc[corner["scenario"].eq("S0")].sort_values("year").set_index("year")
        effective_level_s0 = s0["real_gdp"] * (1.0 + s0["external_gdp_level_pct"] / 100.0)
        recession = classify_recession_years(effective_level_s0)

        for scenario in SCENARIOS:
            scen = corner.loc[corner["scenario"].eq(scenario)].sort_values("year").set_index("year")
            fixed = scen["gdp_level_vs_s0_pct"]
            recession_years = recession.reindex(fixed.index).fillna(False)
            scaled = fixed.where(~recession_years, fixed * ratio)
            for year in target_years:
                if year not in fixed.index:
                    continue
                rows.append({
                    "draw": index,
                    "scenario": scenario,
                    "year": int(year),
                    "horizon": int(year) - base_year,
                    "ratio_sampled": ratio,
                    "n_recession_years_to_date": int(recession_years.loc[:year].sum()),
                    "gdp_level_vs_s0_pct_fixed_multiplier": float(fixed.loc[year]),
                    "gdp_level_vs_s0_pct_state_dependent": float(scaled.loc[year]),
                })
    return pd.DataFrame(rows)


def summarise(draws: pd.DataFrame) -> pd.DataFrame:
    """Median [p10, p90] of both multiplier variants, by scenario and horizon, across sampled draws."""
    sampled = draws.loc[draws["draw"] > 0]
    records = []
    for (scenario, horizon), group in sampled.groupby(["scenario", "horizon"], sort=False):
        record = {"scenario": scenario, "horizon": int(horizon)}
        for column in ("gdp_level_vs_s0_pct_fixed_multiplier", "gdp_level_vs_s0_pct_state_dependent"):
            record[f"{column}_p10"] = float(np.nanpercentile(group[column], 10))
            record[f"{column}_p50"] = float(np.nanpercentile(group[column], 50))
            record[f"{column}_p90"] = float(np.nanpercentile(group[column], 90))
        record["mean_recession_years_to_horizon"] = float(group["n_recession_years_to_date"].mean())
        records.append(record)
    return pd.DataFrame(records).sort_values(["scenario", "horizon"]).reset_index(drop=True)


def render_report(draws: pd.DataFrame, summary: pd.DataFrame, n_draws: int, seed: int) -> str:
    ratio_draws = draws.loc[draws["draw"] > 0, "ratio_sampled"]
    lines = [
        "# CYC1: state-dependent (cyclical) fiscal-multiplier diagnostic",
        "",
        "Built in direct response to an independent review of this project's academic paper "
        "(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the model's fiscal "
        "multipliers never vary with the business cycle. Investigating this surfaced a prior "
        "fact worth stating plainly: this model's own deterministic growth trend has no "
        "cyclical fluctuation at all on its own (year-over-year growth decelerates smoothly "
        "and monotonically, with no booms or slowdowns, under the central draw with no external "
        "shocks) -- the model is acyclical by construction at its core, exactly as the review "
        "argued, independently of whether multipliers are state-dependent. This diagnostic "
        "reintroduces genuine cyclical variation by reusing the existing stochastic external "
        "shock path (`src.external`), classifies each year as a recession or expansion regime "
        "on a real-time, trailing-mean proxy (the same method as `src.pcy1_fiscal_timing`), and "
        f"rescales R\\_mod and R\\_amb's fiscal-multiplier-driven GDP effect by a sampled "
        "state-dependence ratio in recession years only. The ratio is sampled, not fixed, "
        "because the underlying literature is genuinely contested (see "
        "`config/parameters.yaml`'s `multiplier_state_dependence_ratio` for the full sourcing "
        "note, including a citation this project explicitly declined to use for lack of "
        "verification). This is a first-order diagnostic: it rescales the GDP effect directly "
        "but does not re-run the resulting debt consequence through the capital-accumulation/"
        "debt identity a genuinely state-dependent multiplier would also move.",
        "",
        f"Draws: {n_draws} (seed {seed}, central draw plus {n_draws - 1} sampled; independent RNG "
        "streams, cannot perturb any `src.montecarlo` output). Sampled state-dependence ratio: "
        f"median {float(np.nanpercentile(ratio_draws, 50)):.2f} "
        f"[{float(np.nanpercentile(ratio_draws, 10)):.2f}, {float(np.nanpercentile(ratio_draws, 90)):.2f}].",
        "",
        "## GDP level vs S0 (%), fixed multiplier vs state-dependent multiplier",
        "",
        "| Scenario | Horizon | Fixed multiplier (p50 [p10,p90]) | State-dependent (p50 [p10,p90]) | "
        "Mean recession years to horizon |",
        "|---|---:|---|---|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.horizon} | "
            f"{row.gdp_level_vs_s0_pct_fixed_multiplier_p50:+.3f} "
            f"[{row.gdp_level_vs_s0_pct_fixed_multiplier_p10:+.3f}, "
            f"{row.gdp_level_vs_s0_pct_fixed_multiplier_p90:+.3f}] | "
            f"{row.gdp_level_vs_s0_pct_state_dependent_p50:+.3f} "
            f"[{row.gdp_level_vs_s0_pct_state_dependent_p10:+.3f}, "
            f"{row.gdp_level_vs_s0_pct_state_dependent_p90:+.3f}] | "
            f"{row.mean_recession_years_to_horizon:.1f} |"
        )
    lines += [
        "",
        "## Limitations",
        "",
        "- The recession/expansion classification depends on the external shock block's own "
        "stochastic draw, which is independent of the fiscal scenario; a genuinely endogenous "
        "cycle (in which the fiscal contraction itself helps cause the slack it is then "
        "penalised or rewarded for) is not modelled.",
        "- Only the GDP effect is rescaled; the debt consequence is the existing fixed-multiplier "
        "debt path, not re-derived from the state-dependent GDP path.",
        "- The state-dependence ratio range (1.0-2.5, central 1.5) is a sampled, sourced-but-"
        "contested choice, not a fitted Brazilian estimate; see `config/parameters.yaml` for the "
        "full provenance, including why Pires (2014) -- cited elsewhere in this paper for "
        "Brazilian multipliers generally -- is explicitly NOT used as a source for this specific "
        "ratio.",
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
