"""D4: debt-level diagnostics for the S0 baseline (follow-up to the D2 gate).

D2's Tier 2 (absolute debt/GDP levels) fails and is expected to keep failing: its
dominant residual is discretionary Treasury<->BNDES/BCB stock-flow operations that
no macro covariate in this model predicts (`docs/sfa.md`). Rather than chase a
point fix, this module answers the questions the D2/D3 reviews raised about
S0's debt *level* honestly, using only data and estimates already produced
elsewhere in the repository:

- an EC/IFI-style probability of breaching stated debt thresholds, instead of a
  bare point path;
- the primary balance that would stabilise debt at each horizon's own implied
  (i-g)/(1+g), and the gap between that and S0's actual primary balance
  (`outputs/debt_panel.md`'s "Implications for a lead-developer decision");
- two off-to-the-side diagnostic variants of S0 itself, never mixed into the
  R/E-vs-S0 policy grid: a fiscal-reaction-function path using the D3 emerging-
  panel estimate (`config/d3_proposed.yaml`), with Brazil's own (oppositely
  signed) estimate reported alongside as an explicit robustness note, and a
  nonlinear, fiscal-fatigue-style risk-premium path flagged as a modelling
  choice, not an estimated ceiling (D3 itself: "no evidence-based hard
  feedback ceiling is estimated");
- a comparison of debt-level bands under Brazil's own 14-year stock-flow-
  adjustment history (the existing default) against a cross-country emerging-
  panel-calibrated alternative.

This module never re-estimates anything: every coefficient it uses is already
in `config/d3_proposed.yaml` or `config/parameters.yaml`, or is an explicitly
labelled choice. It never modifies `config/scenarios.yaml`'s policy grid or any
existing Monte Carlo output; `python -m src.montecarlo` is untouched and its
published columns are unaffected (see `tests/test_debt_level_diagnostics.py`'s
regression check).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
import yaml

from src import external
from src.montecarlo import (
    central_draw,
    inputs_for_draw,
    load_context,
    parameters_for_draw,
    sample_draw,
)
from src.macro import run_corner


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = {
    "d3": ROOT / "config/d3_proposed.yaml",
    "report": ROOT / "outputs/debt_level_diagnostics.md",
    "data": ROOT / "data/brazil/debt_level_diagnostics.csv",
}

N_DRAWS = 300
SEED = 20261020
# Independent stream: [seed, 1]..[seed, 9] are already used by src.montecarlo.run()
# (external, programmes, C7, corruption, privatisation, education, firm distress,
# W3, SFA). [seed, 10] is unused by any existing stream, so this module cannot
# perturb any published Monte Carlo output even if run with the same seed.
STREAM_INDEX = 10

BREACH_THRESHOLDS_PCT_GDP = (90.0, 100.0, 120.0)
HORIZONS = (5, 10, 15, 20)


def _yaml(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def implied_r_minus_g(frame: pd.DataFrame) -> pd.Series:
    """Annual effective (1+i)/(1+g) - 1, backed out of the debt identity alone.

    From ``src.macro.run_corner``'s recursion, ``debt_t = debt_{t-1} * (1+i)/(1+g)
    - pb_t - adj_t`` (all terms in pp of GDP), so ``(1+i)/(1+g) = (debt_t + pb_t +
    adj_t) / debt_{t-1}``. This needs no separate rate/growth input: it is exactly
    D3's own r-g decomposition (`docs/debt_models_review.md`), applied to this
    model's own annual path instead of the cross-country panel.
    """
    ordered = frame.sort_values("year")
    debt = ordered["debt_gdp"].to_numpy()
    pb = ordered["primary_balance_gdp"].to_numpy()
    adj = ordered.get("debt_adjustment_pp", pd.Series(0.0, index=ordered.index)).fillna(0.0).to_numpy()
    r_minus_g = np.full(len(ordered), np.nan)
    r_minus_g[1:] = (debt[1:] + pb[1:] + adj[1:]) / debt[:-1] - 1.0
    return pd.Series(r_minus_g, index=ordered["year"].to_numpy(), name="r_minus_g")


def stabilising_primary_balance_pp(debt_gdp_prev: pd.Series, r_minus_g: pd.Series) -> pd.Series:
    """The primary balance (pp GDP) that would hold debt flat at r_minus_g."""
    return debt_gdp_prev.reindex(r_minus_g.index) * r_minus_g


def fiscal_reaction_debt_path(s0: pd.DataFrame, rho: float, base_year: int) -> pd.Series:
    """Recompute S0's debt path with an endogenous primary-balance reaction.

    ``pb_t = pb_s0,t + rho * (debt_{t-1} - debt_{base_year})``: the primary
    balance improves (or worsens, for Brazil's own negative estimate) in
    proportion to how far debt has drifted from its 2025 level, using S0's own
    (1+i)/(1+g) ratio each year (``implied_r_minus_g``) so this stays a pure
    financing-side diagnostic: it does not re-run the multiplier/GDP chain that
    a changed primary balance would, in reality, also affect. That omission is
    deliberate and documented, not a bug: re-deriving the GDP-side consequences
    of a different fiscal-reaction regime is outside this diagnostic's scope.
    """
    ordered = s0.sort_values("year").set_index("year")
    r_minus_g = implied_r_minus_g(s0.sort_values("year"))
    adj = ordered.get("debt_adjustment_pp", pd.Series(0.0, index=ordered.index)).fillna(0.0)
    years = ordered.index.to_numpy()
    debt_base = float(ordered.loc[base_year, "debt_gdp"])
    debt = {base_year: debt_base}
    for year in years[years > base_year]:
        prior = debt[year - 1]
        pb = float(ordered.loc[year, "primary_balance_gdp"]) + rho * (prior - debt_base)
        ratio = 1.0 + float(r_minus_g.loc[year])
        debt[year] = prior * ratio - pb - float(adj.loc[year])
    return pd.Series(debt, name="debt_gdp_frf").reindex(years)


PREMIUM_CAP_BP = 2_000.0  # choice: 20 pp added to the effective rate is treated as lost market
# access (D3: "flag paths beyond the D3 historical maximum as crisis indicators, not levels"),
# so the premium itself is capped here rather than left to compound without bound.


def nonlinear_premium_debt_path(
    s0: pd.DataFrame,
    base_year: int,
    threshold_pct_gdp: float,
    bp_per_pp_squared: float,
) -> pd.Series:
    """Recompute S0's debt path with a fiscal-fatigue-style nonlinear premium.

    Flat (zero extra premium) at or below ``threshold_pct_gdp`` of GDP;
    ``bp_per_pp_squared * (debt_{t-1} - threshold)^2`` basis points above it,
    capped at ``PREMIUM_CAP_BP`` (beyond that, debt is in crisis territory the
    identity cannot usefully quantify further), added directly to the
    effective (1+i)/(1+g) ratio (an approximation that avoids decomposing i
    and g separately, adequate for a diagnostic of this precision). This is a
    documented modelling choice illustrating the qualitative shape in Bi
    (2011) / Ghosh et al. (2013), not an estimated sustainability ceiling:
    `config/d3_proposed.yaml` is explicit that "no evidence-based hard
    feedback ceiling is estimated" from this model's data.
    """
    ordered = s0.sort_values("year").set_index("year")
    r_minus_g = implied_r_minus_g(s0.sort_values("year"))
    adj = ordered.get("debt_adjustment_pp", pd.Series(0.0, index=ordered.index)).fillna(0.0)
    years = ordered.index.to_numpy()
    debt = {base_year: float(ordered.loc[base_year, "debt_gdp"])}
    for year in years[years > base_year]:
        prior = debt[year - 1]
        excess = max(0.0, prior - threshold_pct_gdp)
        premium_bp = min(PREMIUM_CAP_BP, bp_per_pp_squared * excess ** 2)
        ratio = 1.0 + float(r_minus_g.loc[year]) + premium_bp / 10_000.0
        pb = float(ordered.loc[year, "primary_balance_gdp"])
        debt[year] = prior * ratio - pb - float(adj.loc[year])
    return pd.Series(debt, name="debt_gdp_premium_nonlinear").reindex(years)


def sfa_source_path(rng: np.random.Generator, steps: int, source: str, d3: Mapping) -> dict[int, float]:
    """One bootstrapped SFA path, keyed by step (1..steps), pp of GDP.

    ``"brazil"`` reuses the existing default mechanism exactly (block bootstrap
    of Brazil's own demeaned 2011-2024 series, `src.external.historical_sfa_changes`
    / `bootstrap_path`). ``"emerging"`` has no raw annual cross-country series
    checked into this repository, only the summary moments in
    `config/d3_proposed.yaml` (`stock_flow_adjustment_pp.emerging`, low-inflation
    sample), so it is sampled i.i.d. per year from a triangular distribution
    anchored on that sample's p10/median/p90 -- a documented choice, not a
    block bootstrap, because there is no observed sequence to resample.
    """
    if source == "brazil":
        changes = external.historical_sfa_changes()
        path = external.bootstrap_path(rng, changes, steps)
        return {int(step): float(value) for step, value in zip(path["step"], path["sfa_pp"])}
    if source == "emerging":
        moments = d3["stock_flow_adjustment_pp"]["emerging"]
        low, mode, high = float(moments["p10"]), float(moments["median"]), float(moments["p90"])
        draws = rng.triangular(low, mode, high, size=steps)
        return {step: float(value) for step, value in zip(range(1, steps + 1), draws)}
    raise ValueError(f"Unknown SFA source: {source!r}")


def run_s0_draws(n_draws: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    """One annual S0 path per draw, central draw plus ``n_draws - 1`` sampled draws.

    Reuses `src.montecarlo.sample_draw`/`central_draw`/`parameters_for_draw`/
    `inputs_for_draw`/`load_context` and `src.macro.run_corner` exactly as
    `src.montecarlo.evaluate_draw` does, but keeps the full annual frame (that
    function trims to the four published horizon years before returning) and
    evaluates only the ``default`` variant's S0 scenario at ``central``
    persistence multipliers (irrelevant for S0, whose package gap is zero).
    """
    context = load_context(variants=["default"])
    d3 = _yaml(DEFAULT_PATHS["d3"])
    frf_rho_emerging = float(d3["fiscal_reaction"]["rho"]["proposed"])
    frf_rho_brazil = -0.037  # docs/debt_models_review.md: Brazil's own 2000-2024 OLS estimate (opposite sign to the panel)
    nl_threshold = float(d3["debt_and_feedback"]["historical_p95_debt_pct_gdp"])
    nl_k = 0.12  # choice: reaches a 300bp premium 50pp of GDP above the threshold (the linear C5
    # default caps at 250bp for a 50pp deviation), then the PREMIUM_CAP_BP ceiling takes over

    base_year = context["base_year"]
    target_years = context["target_years"]
    steps = max(target_years) - base_year
    rng = np.random.default_rng(seed)
    sfa_rng_brazil = np.random.default_rng([seed, STREAM_INDEX])
    sfa_rng_emerging = np.random.default_rng([seed, STREAM_INDEX, 1])

    rows = []
    for index in range(n_draws):
        draw = central_draw(context["parameters"], context["inputs"]) if index == 0 else sample_draw(
            rng, context["parameters"], context["inputs"]
        )
        draw["draw"] = index
        annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
        draw_parameters = parameters_for_draw(context["parameters"], draw)
        draw_inputs = inputs_for_draw(context["inputs"], draw)
        corner = run_corner(
            annual, context["population"], context["variant_configs"]["default"],
            draw_parameters, draw_inputs, "central", "transitory",
        )
        s0 = corner.loc[corner["scenario"].eq("S0")].copy()

        sfa_brazil = sfa_source_path(sfa_rng_brazil, steps, "brazil", d3)
        sfa_emerging = sfa_source_path(sfa_rng_emerging, steps, "emerging", d3)
        sfa_by_year_brazil = {base_year + step: value for step, value in sfa_brazil.items()}
        sfa_by_year_emerging = {base_year + step: value for step, value in sfa_emerging.items()}
        # sfa_adjustment_by_year takes D2's own SFA sign convention (positive =
        # observed debt grew more than the identity implies); run_corner flips
        # the sign internally before subtracting it from debt_adjustment_pp,
        # exactly as src.montecarlo.run() passes draw["sfa_debt_adjustment_by_year"].
        s0_sfa_brazil = run_corner(
            annual, context["population"], context["variant_configs"]["default"],
            draw_parameters, draw_inputs, "central", "transitory",
            sfa_adjustment_by_year=sfa_by_year_brazil,
        ).pipe(lambda f: f.loc[f["scenario"].eq("S0")])
        s0_sfa_emerging = run_corner(
            annual, context["population"], context["variant_configs"]["default"],
            draw_parameters, draw_inputs, "central", "transitory",
            sfa_adjustment_by_year=sfa_by_year_emerging,
        ).pipe(lambda f: f.loc[f["scenario"].eq("S0")])

        r_minus_g = implied_r_minus_g(s0)
        prior_debt = s0.sort_values("year").set_index("year")["debt_gdp"].shift(1)
        stabilising_pb = stabilising_primary_balance_pp(prior_debt, r_minus_g)
        actual_pb = s0.sort_values("year").set_index("year")["primary_balance_gdp"]
        fiscal_gap = stabilising_pb - actual_pb

        frf_emerging = fiscal_reaction_debt_path(s0, frf_rho_emerging, base_year)
        frf_brazil = fiscal_reaction_debt_path(s0, frf_rho_brazil, base_year)
        nonlinear = nonlinear_premium_debt_path(s0, base_year, nl_threshold, nl_k)

        s0_indexed = s0.sort_values("year").set_index("year")
        for year in target_years:
            rows.append({
                "draw": index,
                "year": int(year),
                "horizon": int(year) - base_year,
                "debt_gdp_s0": float(s0_indexed.loc[year, "debt_gdp"]),
                "debt_gdp_s0_sfa_brazil": float(s0_sfa_brazil.set_index("year").loc[year, "debt_gdp"]),
                "debt_gdp_s0_sfa_emerging": float(s0_sfa_emerging.set_index("year").loc[year, "debt_gdp"]),
                "debt_gdp_frf_emerging": float(frf_emerging.loc[year]),
                "debt_gdp_frf_brazil_robustness": float(frf_brazil.loc[year]),
                "debt_gdp_premium_nonlinear": float(nonlinear.loc[year]),
                "r_minus_g_implied_pct": float(r_minus_g.loc[year]) * 100.0,
                "primary_balance_gdp_actual": float(actual_pb.loc[year]),
                "stabilising_primary_balance_pp": float(stabilising_pb.loc[year]) if year in stabilising_pb.index and pd.notna(stabilising_pb.loc[year]) else float("nan"),
                "fiscal_gap_pp": float(fiscal_gap.loc[year]) if year in fiscal_gap.index and pd.notna(fiscal_gap.loc[year]) else float("nan"),
            })
    return pd.DataFrame(rows)


def summarise(draws: pd.DataFrame) -> pd.DataFrame:
    """Percentiles and breach probabilities by horizon, across draws (draw 0 excluded from percentiles: it is the central draw, kept only for documentation)."""
    sampled = draws.loc[draws["draw"] > 0]
    value_columns = [
        "debt_gdp_s0", "debt_gdp_s0_sfa_brazil", "debt_gdp_s0_sfa_emerging",
        "debt_gdp_frf_emerging", "debt_gdp_frf_brazil_robustness", "debt_gdp_premium_nonlinear",
        "stabilising_primary_balance_pp", "fiscal_gap_pp",
    ]
    records = []
    for horizon, group in sampled.groupby("horizon"):
        record = {"horizon": int(horizon)}
        for column in value_columns:
            record[f"{column}_p10"] = float(np.nanpercentile(group[column], 10))
            record[f"{column}_p50"] = float(np.nanpercentile(group[column], 50))
            record[f"{column}_p90"] = float(np.nanpercentile(group[column], 90))
        for threshold in BREACH_THRESHOLDS_PCT_GDP:
            record[f"p_breach_{int(threshold)}_no_sfa"] = float((group["debt_gdp_s0"] > threshold).mean())
            record[f"p_breach_{int(threshold)}_sfa_brazil"] = float((group["debt_gdp_s0_sfa_brazil"] > threshold).mean())
            record[f"p_breach_{int(threshold)}_sfa_emerging"] = float((group["debt_gdp_s0_sfa_emerging"] > threshold).mean())
        records.append(record)
    return pd.DataFrame(records).sort_values("horizon").reset_index(drop=True)


def render_report(draws: pd.DataFrame, summary: pd.DataFrame, n_draws: int, seed: int) -> str:
    lines = [
        "# D4 debt-level diagnostics (follow-up to the D2 gate)", "",
        "**This is a diagnostic layer about the S0 baseline's debt level, not a policy-comparison "
        "scenario and not a new validated forecast.** `outputs/backtest.md`'s Tier 2 (debt/GDP levels) "
        "verdict is unchanged and remains FAIL; nothing here makes a point debt forecast more "
        "trustworthy. It answers, with ranges, the questions `outputs/debt_panel.md`'s "
        "\"Implications for a lead-developer decision\" raised and left unimplemented.", "",
        f"Draws: {n_draws} (seed {seed}, central draw plus {n_draws - 1} sampled; independent stream, "
        "cannot perturb any `src.montecarlo` output). Every coefficient used here is already in "
        "`config/d3_proposed.yaml` or `config/parameters.yaml`, or is an explicitly labelled choice; "
        "nothing is re-estimated.", "",
        "## Probability of breaching stated debt/GDP thresholds, S0", "",
        "EC/IFI-style risk statement instead of a bare median path. `no_sfa` uses the plain debt "
        "identity; `sfa_brazil` is today's default stochastic stock-flow-adjustment term (Brazil's own "
        "2011-2024 history, block-bootstrapped); `sfa_emerging` substitutes the cross-country emerging-"
        "panel moments for comparison.", "",
        "| Horizon | P(>90%) no SFA | P(>90%) SFA (Brazil) | P(>90%) SFA (emerging) | P(>100%) SFA (Brazil) | P(>120%) SFA (Brazil) |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.horizon} | {row.p_breach_90_no_sfa * 100:.1f}% | {row.p_breach_90_sfa_brazil * 100:.1f}% | "
            f"{row.p_breach_90_sfa_emerging * 100:.1f}% | {row.p_breach_100_sfa_brazil * 100:.1f}% | "
            f"{row.p_breach_120_sfa_brazil * 100:.1f}% |"
        )
    lines += [
        "", "## Debt/GDP levels under the Brazil-own vs. emerging-panel SFA prior (p10/p50/p90, % GDP)", "",
        "| Horizon | Brazil-own SFA (default) | Emerging-panel SFA (alternative) |",
        "|---:|---|---|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.horizon} | {row.debt_gdp_s0_sfa_brazil_p50:.1f} [{row.debt_gdp_s0_sfa_brazil_p10:.1f}, {row.debt_gdp_s0_sfa_brazil_p90:.1f}] | "
            f"{row.debt_gdp_s0_sfa_emerging_p50:.1f} [{row.debt_gdp_s0_sfa_emerging_p10:.1f}, {row.debt_gdp_s0_sfa_emerging_p90:.1f}] |"
        )
    lines += [
        "", "## Stabilising primary balance and fiscal gap, S0 (pp of GDP)", "",
        "The primary balance that would hold debt flat at each year's own implied (1+i)/(1+g), against "
        "S0's actual projected primary balance. A positive fiscal gap is the further adjustment still "
        "needed to stabilise debt at that year's own rates; this is a point-in-time, EC S1/S2-style "
        "statement, not a forecast of what adjustment will occur.", "",
        "| Horizon | Stabilising primary balance (p50 [p10, p90]) | S0 actual primary balance (p50 [p10, p90]) | Fiscal gap (p50 [p10, p90]) |",
        "|---:|---|---|---|",
    ]
    sampled = draws.loc[draws["draw"] > 0]
    for row in summary.itertuples(index=False):
        actual = sampled.loc[sampled["horizon"].eq(row.horizon), "primary_balance_gdp_actual"]
        lines.append(
            f"| {row.horizon} | {row.stabilising_primary_balance_pp_p50:+.2f} [{row.stabilising_primary_balance_pp_p10:+.2f}, {row.stabilising_primary_balance_pp_p90:+.2f}] | "
            f"{actual.quantile(0.5):+.2f} [{actual.quantile(0.1):+.2f}, {actual.quantile(0.9):+.2f}] | "
            f"{row.fiscal_gap_pp_p50:+.2f} [{row.fiscal_gap_pp_p10:+.2f}, {row.fiscal_gap_pp_p90:+.2f}] |"
        )
    lines += [
        "", "## S0 diagnostic variants: fiscal-reaction-function and nonlinear risk premium", "",
        "These are **diagnostics about the no-reaction S0 baseline, not policy-comparison scenarios**: "
        "they are never differenced against S0 the way R/E scenarios are, and they do not appear in "
        "`outputs/runs/summary_percentiles.csv`.", "",
        "`frf_emerging` recomputes S0's primary balance each year as "
        "`pb_t = pb_S0,t + rho*(debt_{t-1} - debt_2025)` using the emerging-economy panel's estimated "
        "long-run response (`config/d3_proposed.yaml fiscal_reaction.rho`). "
        "**Robustness note:** Brazil's own 2000-2024 estimated response has the opposite sign "
        "(`docs/debt_models_review.md`: -0.037, n=22) -- Brazil's history argues for *less* reaction "
        "than S0 already assumes (none), not more, so `frf_emerging` should be read as \"what a "
        "typical emerging economy's historical behaviour would imply here,\" never as \"the realistic "
        "path.\" `frf_brazil_robustness` applies Brazil's own estimate instead, and (being negative) "
        "widens the debt path further than plain S0, consistent with that finding.", "",
        "`premium_nonlinear` replaces the linear, capped C5 sovereign-risk premium (unchanged for every "
        "other scenario) with a fiscal-fatigue-style shape for this diagnostic only: zero below the D3 "
        "cross-country historical P95 debt level "
        f"({float(_yaml(DEFAULT_PATHS['d3'])['debt_and_feedback']['historical_p95_debt_pct_gdp']):.1f}% of GDP), "
        "rising with the square of the excess above it. This is an explicitly labelled modelling choice "
        "(no identified equation), not a new estimated ceiling.", "",
        "| Horizon | Plain S0 | frf_emerging | frf_brazil_robustness | premium_nonlinear |",
        "|---:|---|---|---|---|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.horizon} | {row.debt_gdp_s0_p50:.1f} | {row.debt_gdp_frf_emerging_p50:.1f} "
            f"[{row.debt_gdp_frf_emerging_p10:.1f}, {row.debt_gdp_frf_emerging_p90:.1f}] | "
            f"{row.debt_gdp_frf_brazil_robustness_p50:.1f} [{row.debt_gdp_frf_brazil_robustness_p10:.1f}, {row.debt_gdp_frf_brazil_robustness_p90:.1f}] | "
            f"{row.debt_gdp_premium_nonlinear_p50:.1f} [{row.debt_gdp_premium_nonlinear_p10:.1f}, {row.debt_gdp_premium_nonlinear_p90:.1f}] |"
        )
    lines += [
        "", "## Limitations", "",
        "- `frf_emerging`/`frf_brazil_robustness` hold S0's own (1+i)/(1+g) path fixed and change only "
        "the primary balance; they do not re-run the GDP/multiplier chain a genuinely different fiscal "
        "stance would also affect.",
        "- `premium_nonlinear` adds its premium directly to the effective (1+i)/(1+g) ratio rather than "
        "decomposing and reinflating i and g separately; adequate for a diagnostic, not a replacement "
        "for the C5 channel.",
        "- `sfa_emerging` is sampled i.i.d. per year from the cross-country panel's summary moments, not "
        "block-bootstrapped from an observed sequence (none is checked into this repository): it "
        "therefore has no cross-year persistence, unlike `sfa_brazil`.",
        "- All of the above are differences about **S0 alone**. They are never compared against the "
        "policy scenarios (R_mod, R_amb, E_mod, ...), and no existing Monte Carlo output changes.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=N_DRAWS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--data", type=Path, default=DEFAULT_PATHS["data"])
    parser.add_argument("--report", type=Path, default=DEFAULT_PATHS["report"])
    args = parser.parse_args(argv)
    draws = run_s0_draws(args.draws, args.seed)
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
