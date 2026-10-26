"""JMC1: a jointly-integrated Monte Carlo, validated against 2000-2024 history.

The 8-task reviewer-response plan (RV0, IEQ1, PCY1, CYC1, DC1, IY1, MR1, FX1) built every new
channel -- state-dependent multiplier, Taylor-rule Selic, FX-linked debt revaluation,
endogenous FX, interest-income distribution -- as a standalone diagnostic that perturbs a
*copy* of the already-computed baseline path once, post-hoc, then reports its own median
effect. The paper combines those separately-run medians by simple addition, and says so
explicitly: "a simple addition of two separately-run statistics, not a single re-integrated
Monte Carlo."

A strict reading of the independent review's ask implies more than that: these channels should
interact *within* each draw and compound year over year -- higher debt stress raises Selic
(MR1), which plausibly widens the sovereign spread and weakens the currency (FX1), which
revalues the FX-linked debt tranche (DC1), which raises interest expense, which (via IY1) feeds
disproportionately to the top of the income distribution, and a widening Gini feeds back into
growth (IEQ1) -- not five independent, held-fixed recomputations summed at the end.

**Design.** A brand-new per-scenario, per-year recursion, mirroring `src.external.apply_external`'s
own debt loop exactly (same nominal-GDP and `debt_step` structure) but substituting, every year:

1. CYC1's state-dependent multiplier -- rescales that year's GDP gap by a sampled ratio in
   recession years, classified the same way CYC1 classifies them (a real-time trailing-mean
   proxy on the externally-shocked S0 path). Broadened here to all four scenarios (R_mod, R_amb,
   E_mod, E_amb), not just the two reduction scenarios CYC1's own standalone diagnostic tests --
   state-dependence in the literature cuts both ways, not only for contractions.
2. MR1's Taylor rule -- the real rate reacts to *that year's* rescaled gap and inflation, in
   place of the fixed `real_interest_rate_for_year` lookup.
3. A *running*, compounding sovereign-risk premium -- deviation of the *previous* year's own
   debt stock (not the baseline, external-only path) from the initial debt/GDP, the same
   bp-per-deviation-pp formula and cap `src.feedback.sovereign_risk_premium_path` already uses,
   inlined here because this loop determines each year sequentially and the premium for year t
   must be knowable before year t's rate is set (a lagged, not simultaneous, causal convention).
   This is the one deliberate departure from FX1's own standalone design, which uses the
   baseline debt path specifically *to avoid* a new compounding loop -- compounding it is the
   entire point of this module.
4. FX1's elasticity turns that premium into extra depreciation; DC1's exact FX-linked-tranche
   formula revalues the *running* debt stock by it, additive to the already-external-adjusted
   corner's own bootstrapped FX path, not a replacement for it.
5. IY1's capital-income allocation, applied only at this model's own `target_years` milestones
   (matching IY1's own established resolution, not every single year -- see "Scope" below),
   produces a Gini deviation from that year's own endogenous interest expense; its cumulative
   growth effect (via `src.feedback.inequality_log_output_effect`, reused as a pure function, not
   a modification of that module) multiplies into subsequent years' GDP level.

**Timing convention (the one genuinely new design decision, with no precedent elsewhere in this
repo to anchor it).** Selic for year t reacts to year t's own realized inflation and output gap
-- contemporaneous, the standard Taylor (1993) convention -- not a lag. Stated here as a
documented assumption, not derived from data.

**Scope: why the inequality/Gini closure is two-pass and milestone-resolution, not every-year.**
Closing IY1's loop fully would require a Gini value, from a full household microsimulation pass,
for every single projection year of every draw -- a genuine simultaneous fixed point, since each
year's Gini depends on that year's own interest expense, which depends on the prior years'
compounded inequality-growth feedback. The published model's own IEQ1 channel does not solve
that fixed point either: it uses a one-pass, pre-feedback Gini path as an approximation
(`src.montecarlo.evaluate_draw`'s own comment: "a pre-feedback C3 pass supplies the Gini path").
This module mirrors that exact, already-accepted approximation -- a first macro-only pass
produces the debt/rate/FX path with no inequality feedback; IY1's Gini deviations are computed
from *that* pass at `target_years` only (the same milestone years IY1's own standalone diagnostic
already uses); a second pass re-runs the full recursion with the resulting cumulative log-effect
now multiplying into the GDP level. Between target years the Gini deviation is held at its last
computed value (a documented discretization, not an estimate).

This module never imports or modifies `src.macro.run_corner`, `src.external.apply_external`, or
`src.feedback.apply_feedback`/`_evaluate` -- it reuses `run_corner`/`apply_external` unchanged to
build the externally-shocked corner, and reuses `sovereign_risk_premium_path`'s formula and
`inequality_log_output_effect` as pure, already-tested arithmetic, never calling
`src.montecarlo.run()`/`evaluate_draw()` and unable to change any published output.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from src import external
from src import micro
from src.cyc1_state_dependent_multiplier import classify_recession_years
from src.feedback import inequality_log_output_effect
from src.iy1_interest_income_distribution import _micro_setup, capital_income_shares
from src.macro import debt_step, macro_input, nominal_rate_from_real, real_interest_rate_for_year, run_corner
from src.montecarlo import (
    central_draw,
    inputs_for_draw,
    load_context,
    parameters_for_draw,
    sample_draw,
    scenario_package_gaps,
)
from src.mr1_taylor_rule import TAYLOR_1993_COEFFICIENT, taylor_real_rate

DEFAULT_PATHS = {
    "data": Path("data/brazil/jmc1_engine.csv"),
    "report": Path("outputs/jmc1_engine.md"),
}
N_DRAWS = 300
SEED = 20261026
STREAM_INDEX = 16  # unused by run()'s streams (1-9), D4's (10), CYC1's (11), DC1's (12), IY1's (13), MR1's (14), FX1's (15)
SCENARIOS = ("R_mod", "R_amb", "E_mod", "E_amb")
RISK_PREMIUM_CAP_PP = 50.0  # same out-of-sample guard already used by src.feedback and FX1
INEQUALITY_GROWTH_PP_PER_GINI = -0.1  # config/parameters.yaml inequality_to_growth.central (IEQ1's own coefficient)


def _joint_debt_path(
    frame: pd.DataFrame,
    draw_inputs: Mapping,
    variant: str,
    recession_years: pd.Series,
    ratio: float,
    inflation_target_pct: float,
    phi_pi: float,
    phi_y: float,
    elasticity: float,
    premium_bp: float,
    fx_share_pct: float,
    inequality_log_effect: pd.Series | None = None,
) -> pd.DataFrame:
    """Run the five-channel joint per-year recursion for every scenario in `frame`.

    `frame` is `external.apply_external`'s own output (all years, all scenarios); this function
    never mutates it. With `ratio=1.0`, `phi_pi=phi_y=0.0`, `elasticity=0.0` (or `premium_bp=0.0`)
    and `inequality_log_effect=None`, the resulting `debt_gdp_joint` column reproduces
    `debt_gdp_with_external` exactly -- see `tests/test_jmc1_engine.py`.
    """
    start_year = int(frame["year"].min())
    initial_debt = macro_input(draw_inputs, "initial_debt_gdp", variant) / 100.0
    initial_debt_gdp_pp = initial_debt * 100.0
    out_debt: dict[tuple[int, str], float] = {}
    out_rate: dict[tuple[int, str], float] = {}
    out_gap: dict[tuple[int, str], float] = {}
    out_fx: dict[tuple[int, str], float] = {}
    out_interest_expense: dict[tuple[int, str], float] = {}
    for scenario, group in frame.groupby("scenario", sort=False):
        ordered = group.sort_values("year")
        previous_debt, previous_nominal, price = initial_debt, None, 1.0
        for row in ordered.itertuples():
            year = int(row.year)
            key = (year, str(scenario))
            base_gap = float(row.gdp_level_vs_s0_pct)
            if inequality_log_effect is not None:
                factor = math.exp(float(inequality_log_effect.loc[row.Index]))
                effective_gap = ((1.0 + base_gap / 100.0) * factor - 1.0) * 100.0
            else:
                effective_gap = base_gap
            is_recession = bool(recession_years.get(year, False))
            rescaled_gap = effective_gap * ratio if is_recession else effective_gap
            if year > start_year:
                price *= 1.0 + row.inflation_with_external_pct / 100.0
            nominal = (
                row.real_gdp * price * (1 + rescaled_gap / 100.0) * (1 + row.external_gdp_level_pct / 100.0)
            )
            if year == start_year:
                out_debt[key] = initial_debt_gdp_pp
                out_rate[key] = float("nan")
                out_gap[key] = rescaled_gap
                out_fx[key] = 0.0
                out_interest_expense[key] = 0.0
                previous_nominal = nominal
                continue
            deviation_pp = previous_debt * 100.0 - initial_debt_gdp_pp
            deviation_pp = max(-RISK_PREMIUM_CAP_PP, min(RISK_PREMIUM_CAP_PP, deviation_pp))
            premium_pp = premium_bp / 10_000.0 * deviation_pp
            extra_fx_pct = elasticity * premium_pp
            base_real_rate = real_interest_rate_for_year(draw_inputs, variant, year)
            real_rate = taylor_real_rate(
                base_real_rate, float(row.inflation_with_external_pct), rescaled_gap,
                inflation_target_pct, phi_pi, phi_y,
            )
            nominal_interest = nominal_rate_from_real(real_rate, row.inflation_with_external_pct) / 100.0
            interest_expense_pp_gdp = previous_debt * 100.0 * nominal_interest
            new_debt = debt_step(
                previous_debt, nominal_interest, nominal / previous_nominal - 1.0,
                (row.primary_balance_gdp + float(getattr(row, "external_revenue_pp_gdp", 0.0))) / 100.0,
            )
            new_debt -= float(getattr(row, "debt_adjustment_pp", 0.0)) / 100.0
            fx_revaluation_pp = fx_share_pct / 100.0 * (previous_debt * 100.0) * (extra_fx_pct / 100.0)
            new_debt += fx_revaluation_pp / 100.0
            out_debt[key] = new_debt * 100.0
            out_rate[key] = nominal_interest * 100.0
            out_gap[key] = rescaled_gap
            out_fx[key] = extra_fx_pct
            out_interest_expense[key] = interest_expense_pp_gdp
            previous_debt = new_debt
            previous_nominal = nominal
    idx = list(zip(frame["year"].astype(int), frame["scenario"].astype(str)))
    return pd.DataFrame(
        {
            "debt_gdp_joint": [out_debt[k] for k in idx],
            "nominal_rate_joint_pct": [out_rate[k] for k in idx],
            "rescaled_gdp_gap_pct": [out_gap[k] for k in idx],
            "extra_fx_pct": [out_fx[k] for k in idx],
            "interest_expense_pp_gdp": [out_interest_expense[k] for k in idx],
        },
        index=frame.index,
    )


def _capital_income_gini_effect(
    frame: pd.DataFrame,
    pass1: pd.DataFrame,
    target_years: list[int],
    base_year: int,
    draw: Mapping,
    variant_scenarios: Mapping,
    micro_setup: Mapping,
    shares: Mapping,
) -> pd.Series:
    """IY1's Gini deviation at each target year, from pass 1's own endogenous interest expense,
    held constant between target years; returns a per-row Gini-change-vs-S0 (points) Series
    indexed like `frame`, ready for `inequality_log_output_effect`."""
    joined = frame[["year", "scenario"]].copy()
    joined["interest_expense_pp_gdp"] = pass1["interest_expense_pp_gdp"].to_numpy()
    s0_interest = (
        joined.loc[joined["scenario"].eq("S0")].set_index("year")["interest_expense_pp_gdp"]
    )
    gini_by_key: dict[tuple[int, str], float] = {}
    s0_gini_by_year: dict[int, float] = {}
    for year in target_years:
        if year not in s0_interest.index:
            continue
        horizon = int(year) - base_year
        s0_gaps = scenario_package_gaps(variant_scenarios, "S0", horizon, 0.0)
        households_s0 = micro.simulate_household_incomes(
            micro_setup["prepared"],
            gdp_level_vs_s0_pct=0.0, unemployment_change_pp=0.0, package_gaps_pp_gdp=s0_gaps,
            revenue_change_pp=0.0, nominal_gdp_brl=micro_setup["nominal_gdp_brl"],
            minimum_wage_brl=micro_setup["minimum_wage_brl"],
            pension_variant=draw["micro_pension_variant"], labour_variant=draw["micro_labour_variant"],
            tax_variant=draw["micro_tax_variant"],
            consumption_like_exponent=micro_setup["consumption_like_exponent"],
            random_seed=int(draw.get("draw", 0)),
        )
        s0_gini_by_year[int(year)] = micro.calculate_indicators(households_s0, micro_setup["lines"])["gini"]

    for scenario in SCENARIOS:
        scen = joined.loc[joined["scenario"].eq(scenario)].set_index("year")
        row_lookup = frame.loc[frame["scenario"].eq(scenario)].set_index("year")
        last_value = 0.0
        for year in sorted(scen.index):
            if year in target_years and year in s0_gini_by_year:
                delta_interest_pp_gdp = float(scen.loc[year, "interest_expense_pp_gdp"] - s0_interest.loc[year])
                windfall_monthly_brl = delta_interest_pp_gdp / 100.0 * micro_setup["nominal_gdp_brl"] / 12.0
                horizon = int(year) - base_year
                gap_below_s0_pp = float(row_lookup.loc[year, "gap_below_s0_pp"])
                gaps = scenario_package_gaps(variant_scenarios, scenario, horizon, gap_below_s0_pp)
                revenue = float(row_lookup.loc[year].get("revenue_change_pp", 0.0))
                households = micro.simulate_household_incomes(
                    micro_setup["prepared"],
                    gdp_level_vs_s0_pct=float(row_lookup.loc[year, "gdp_level_vs_s0_pct"]),
                    unemployment_change_pp=float(row_lookup.loc[year, "unemployment_change_pp"]),
                    package_gaps_pp_gdp=gaps, revenue_change_pp=revenue,
                    nominal_gdp_brl=micro_setup["nominal_gdp_brl"], minimum_wage_brl=micro_setup["minimum_wage_brl"],
                    pension_variant=draw["micro_pension_variant"], labour_variant=draw["micro_labour_variant"],
                    tax_variant=draw["micro_tax_variant"],
                    consumption_like_exponent=micro_setup["consumption_like_exponent"],
                    random_seed=int(draw.get("draw", 0)),
                    capital_income_windfall_brl_monthly=windfall_monthly_brl,
                    capital_income_top1_share_pct=shares["top_1_share_pct"],
                    capital_income_top10_share_pct=shares["top_10_share_pct"],
                )
                ind = micro.calculate_indicators(households, micro_setup["lines"])
                last_value = 100.0 * (ind["gini"] - s0_gini_by_year[int(year)])
            gini_by_key[(int(year), scenario)] = last_value
    return pd.Series(
        [gini_by_key.get((int(y), s), 0.0) for y, s in zip(frame["year"], frame["scenario"])], index=frame.index,
    )


def run_draws(n_draws: int = N_DRAWS, seed: int = SEED, close_inequality_loop: bool = True) -> pd.DataFrame:
    context = load_context(variants=["default"])
    params = context["parameters"]
    variant_scenarios = context["variant_configs"]["default"]
    ratio_cfg = params["multiplier_state_dependence_ratio"]
    discount_cfg = params["mr1_taylor_rule"]["discount_vs_taylor_1993"]
    elasticity_cfg = params["fx1_endogenous_fx"]["spread_to_depreciation_elasticity_pct_per_premium_pp"]
    premium_cfg = params["long_run_feedback"]["sovereign_risk_premium"]
    fx_share_cfg = params["debt_composition_fx"]["fx_linked_share_pct_of_dpf"]
    base_year = context["base_year"]
    target_years = list(context["target_years"])
    steps = max(target_years) - base_year
    shares = capital_income_shares()
    micro_setup = _micro_setup() if close_inequality_loop else None
    rng = np.random.default_rng(seed)
    ratio_rng = np.random.default_rng([seed, STREAM_INDEX])
    discount_rng = np.random.default_rng([seed, STREAM_INDEX, 1])
    elasticity_rng = np.random.default_rng([seed, STREAM_INDEX, 2])
    premium_rng = np.random.default_rng([seed, STREAM_INDEX, 3])
    fx_share_rng = np.random.default_rng([seed, STREAM_INDEX, 4])
    external_rng = np.random.default_rng([seed, STREAM_INDEX, 5])
    changes = external.historical_changes()

    rows: list[dict] = []
    for index in range(n_draws):
        draw = (
            central_draw(params, context["inputs"]) if index == 0 else sample_draw(rng, params, context["inputs"])
        )
        ratio = float(ratio_cfg["central"]) if index == 0 else float(ratio_rng.uniform(ratio_cfg["low"], ratio_cfg["high"]))
        discount = (
            float(discount_cfg["central"]) if index == 0 else float(discount_rng.uniform(discount_cfg["low"], discount_cfg["high"]))
        )
        phi_pi = phi_y = TAYLOR_1993_COEFFICIENT * discount
        elasticity = (
            float(elasticity_cfg["central"]) if index == 0 else float(elasticity_rng.uniform(elasticity_cfg["low"], elasticity_cfg["high"]))
        )
        premium_bp = (
            float(premium_cfg["central"]) if index == 0 else float(premium_rng.uniform(premium_cfg["low"], premium_cfg["high"]))
        )
        fx_share_pct = (
            float(fx_share_cfg["central"]) if index == 0 else float(fx_share_rng.uniform(fx_share_cfg["low"], fx_share_cfg["high"]))
        )
        annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
        draw_parameters = parameters_for_draw(params, draw)
        draw_inputs = inputs_for_draw(context["inputs"], draw)
        corner = run_corner(
            annual, context["population"], variant_scenarios, draw_parameters, draw_inputs, "central", "transitory",
        )
        bootstrapped = external.bootstrap_path(external_rng, changes, steps)
        effects = external.gdp_and_inflation_effects(bootstrapped, params)
        corner = external.apply_external(corner, effects, draw_inputs)
        inflation_target_pct = macro_input(draw_inputs, "gdp_deflator_growth", "central")

        s0 = corner.loc[corner["scenario"].eq("S0")].sort_values("year").set_index("year")
        effective_level_s0 = s0["real_gdp"] * (1.0 + s0["external_gdp_level_pct"] / 100.0)
        recession_years = classify_recession_years(effective_level_s0)

        pass1 = _joint_debt_path(
            corner, draw_inputs, "central", recession_years, ratio, inflation_target_pct, phi_pi, phi_y,
            elasticity, premium_bp, fx_share_pct, inequality_log_effect=None,
        )
        inequality_log_effect = None
        if close_inequality_loop:
            gini_change = _capital_income_gini_effect(
                corner, pass1, target_years, base_year, draw, variant_scenarios, micro_setup, shares,
            )
            inequality_log_effect = inequality_log_output_effect(corner, gini_change, INEQUALITY_GROWTH_PP_PER_GINI)
        pass2 = _joint_debt_path(
            corner, draw_inputs, "central", recession_years, ratio, inflation_target_pct, phi_pi, phi_y,
            elasticity, premium_bp, fx_share_pct, inequality_log_effect=inequality_log_effect,
        )

        corner = corner.assign(debt_gdp_pass1=pass1["debt_gdp_joint"], debt_gdp_joint=pass2["debt_gdp_joint"])
        s0_joint = corner.loc[corner["scenario"].eq("S0")].sort_values("year").set_index("year")
        for scenario in SCENARIOS:
            scen = corner.loc[corner["scenario"].eq(scenario)].sort_values("year").set_index("year")
            for year in target_years:
                if year not in scen.index:
                    continue
                row = scen.loc[year]
                s0_row = s0_joint.loc[year]
                rows.append(
                    {
                        "draw": index, "scenario": scenario, "year": int(year), "horizon": int(year) - base_year,
                        "ratio_sampled": ratio, "phi_pi_sampled": phi_pi, "elasticity_sampled": elasticity,
                        "premium_bp_sampled": premium_bp, "fx_share_pct_sampled": fx_share_pct,
                        "debt_gdp_baseline": float(row.debt_gdp_with_external - s0_row.debt_gdp_with_external),
                        "debt_gdp_joint_vs_s0_pp": float(row.debt_gdp_joint - s0_row.debt_gdp_joint),
                        "incremental_debt_gdp_from_joint_pp": float(
                            (row.debt_gdp_joint - s0_row.debt_gdp_joint)
                            - (row.debt_gdp_with_external - s0_row.debt_gdp_with_external)
                        ),
                    }
                )
    return pd.DataFrame(rows)


def summarise(draws: pd.DataFrame) -> pd.DataFrame:
    sampled = draws.loc[draws["draw"] > 0]
    records = []
    for (scenario, horizon), group in sampled.groupby(["scenario", "horizon"], sort=False):
        record = {"scenario": scenario, "horizon": int(horizon)}
        for column in ("debt_gdp_baseline", "debt_gdp_joint_vs_s0_pp", "incremental_debt_gdp_from_joint_pp"):
            record[f"{column}_p10"] = float(np.nanpercentile(group[column], 10))
            record[f"{column}_p50"] = float(np.nanpercentile(group[column], 50))
            record[f"{column}_p90"] = float(np.nanpercentile(group[column], 90))
        records.append(record)
    return pd.DataFrame(records).sort_values(["scenario", "horizon"]).reset_index(drop=True)


def render_report(draws: pd.DataFrame, summary: pd.DataFrame, n_draws: int, seed: int) -> str:
    lines = [
        "# JMC1: a jointly-integrated Monte Carlo",
        "",
        "Built in response to the question of whether CYC1/MR1/FX1/DC1/IY1 should interact "
        "within each draw and compound year over year, rather than be computed independently "
        "and summed afterward (the paper's existing framing for the 8-task reviewer-response "
        "plan). This is a second, fully separate Monte Carlo -- it never modifies `run_corner`, "
        "`apply_external`, or `src.montecarlo.run()`/`evaluate_draw()` and cannot change any "
        "published output. See the module docstring for the exact per-year recursion and the "
        "two-pass approximation used to close the IY1/inequality feedback loop.",
        "",
        f"Draws: {n_draws} (seed {seed}, central draw plus {n_draws - 1} sampled).",
        "",
        "## Debt/GDP vs S0: baseline (external-only) vs the joint, compounding engine",
        "",
        "| Scenario | Horizon | Baseline (pp, p50 [p10,p90]) | Joint engine (pp, p50 [p10,p90]) | "
        "Incremental from joint integration (pp, p50 [p10,p90]) |",
        "|---|---:|---|---|---|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.horizon} | "
            f"{row.debt_gdp_baseline_p50:+.3f} [{row.debt_gdp_baseline_p10:+.3f}, {row.debt_gdp_baseline_p90:+.3f}] | "
            f"{row.debt_gdp_joint_vs_s0_pp_p50:+.3f} [{row.debt_gdp_joint_vs_s0_pp_p10:+.3f}, "
            f"{row.debt_gdp_joint_vs_s0_pp_p90:+.3f}] | "
            f"{row.incremental_debt_gdp_from_joint_pp_p50:+.3f} "
            f"[{row.incremental_debt_gdp_from_joint_pp_p10:+.3f}, {row.incremental_debt_gdp_from_joint_pp_p90:+.3f}] |"
        )
    lines += [
        "",
        "## Limitations",
        "",
        "- Selic reacts contemporaneously to that year's own realized inflation/output gap "
        "(standard Taylor 1993 convention) -- a documented assumption, not derived from data; "
        "no interest-rate smoothing/gradualism term.",
        "- The sovereign-risk premium and FX-linked revaluation compound on the *running* debt "
        "path (unlike FX1's standalone diagnostic, which deliberately avoids this to stay a "
        "first-order effect) -- this is intentional here, but means JMC1's errors can compound "
        "across years in a way none of the standalone diagnostics do.",
        "- The IY1/inequality-growth loop is closed via a two-pass approximation (a pre-feedback "
        "pass supplies the Gini path, mirroring IEQ1's own already-published method), evaluated "
        "only at `target_years` milestones and held constant between them, not every year.",
        "- Does not independently validate against history; see `docs/jmc1_validation.md` and "
        "`src/backtest_jmc1.py` for the actual go/no-go test against 2000-2024 observed data.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=N_DRAWS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--data", type=Path, default=DEFAULT_PATHS["data"])
    parser.add_argument("--report", type=Path, default=DEFAULT_PATHS["report"])
    parser.add_argument("--no-inequality-loop", action="store_true")
    args = parser.parse_args(argv)
    draws = run_draws(args.draws, args.seed, close_inequality_loop=not args.no_inequality_loop)
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
