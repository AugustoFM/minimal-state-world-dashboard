"""IY1: interest-income and inflation-tax distribution diagnostic.

An independent review of this project's academic paper
(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`) argued the household
microsimulation (`src.micro`) omits two regressive channels a sustained,
debt-financed expansion would plausibly trigger: (1) higher government
interest expense accrues disproportionately to bondholders, who are
concentrated in the top income centiles, and (2) an inflation tax falls
hardest on poor households' largely non-indexed cash transfers. Both are
real gaps: `src.micro.INCOME_COLUMNS` has no capital/interest-income field
(PNAD's survey design does not collect it well), and no channel previously
eroded transfer income by extra inflation.

This diagnostic wires both channels as off-by-default, optional arguments to
`src.micro.simulate_household_incomes` (defaults reproduce the exact prior
behaviour; see that function's IY1 docstring section), then runs them here
as a standalone, additive Monte Carlo diagnostic -- it never calls
`src.montecarlo.run()`/`evaluate_draw()` and cannot change any published
output.

**Data source for the capital-income incidence curve.** PNAD has no
capital-income field, so the top-1%/top-10% concentration of capital income
used to allocate the interest-expense windfall is read from Receita Federal's
declared-income tax centiles (`data/brazil/micro/tax_centiles_2024.csv`,
Table V, already used in aggregate by `src.micro.tax_data_context` for RB4),
summing four declared capital/financial-income line items by centile:
financial-investment income, capital gains, interest-on-equity and exempt
dividends. This is tax-declarant data, not the PNAD survey population, and
Brazilian tax declarants are themselves concentrated in the upper part of the
income distribution -- so the resulting top-1%/top-10% shares are a
reasonable proxy for "how concentrated is capital income among the rich" but
are not survey-consistent population shares, a limitation stated plainly
rather than smoothed over.

**Government interest expense.** `src.macro`/`src.external` do not expose a
standalone "interest paid" column, so it is derived directly from the debt
identity's own definition: interest expense (% GDP) in year t is the
previous year's `debt_gdp_with_external` times the year's nominal interest
rate (`src.macro.nominal_rate_from_real` applied to
`real_interest_rate_for_year` and that year's `inflation_with_external_pct`)
-- the standard national-accounts "rate times stock" quantity that becomes
private interest income, not the debt identity's own (interest-growth)
net-of-dilution term (which is a different, growth-adjusted concept).

**Inflation-tax erosion.** Modelled as a fraction of each household's
baseline (survey-observed) Bolsa Familia amount -- not its policy-driven
delta -- lost to a scenario's cumulative *extra* (above-baseline) inflation
since the base year, via `src.external`'s own `external_extra_inflation_pp`
path. This is a stylised within-year erosion, not a claim that Bolsa Familia
is never adjusted; see the method note for the exact formula and its
limitations.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from src import external
from src import macro
from src import micro
from src.baseline import read_yaml
from src.macro import run_corner
from src.montecarlo import (
    central_draw,
    inputs_for_draw,
    load_context,
    parameters_for_draw,
    sample_draw,
    scenario_package_gaps,
)

DEFAULT_PATHS = {
    "tax_centiles": Path("data/brazil/micro/tax_centiles_2024.csv"),
    "data": Path("data/brazil/iy1_interest_income_distribution.csv"),
    "report": Path("outputs/iy1_interest_income_distribution.md"),
}
N_DRAWS = 300
SEED = 20261026
STREAM_INDEX = 13  # unused by run()'s streams (1-9), D4's (10), CYC1's (11), DC1's (12)
# E_mod/E_amb (debt-financed expansions), not R_mod/R_amb: the reviewer's "expansion reduces
# the Gini coefficient... is probably biased in favour of expansion" claim is specifically about
# the debt-financed expansion scenarios, not the fiscal-reduction ones CYC1/DC1 test.
SCENARIOS = ("E_mod", "E_amb")
CAPITAL_INCOME_COLUMN_SUBSTRINGS = (
    "Aplicações Financeiras",
    "na Alienação de Bens",
    "Capital Próprio",
    "Lucros e dividendos",
)


def capital_income_shares(path: str | Path = DEFAULT_PATHS["tax_centiles"]) -> dict[str, float]:
    """Top-1%/top-10% declarant shares of four declared capital/financial-income
    line items (Table V, Receita Federal), summed by centile. See module docstring
    for why this is a tax-declarant, not a survey-population, concentration curve."""
    data = pd.read_csv(path, encoding="utf-8")
    columns = [c for c in data.columns if any(sub in c for sub in CAPITAL_INCOME_COLUMN_SUBSTRINGS)]
    if len(columns) != len(CAPITAL_INCOME_COLUMN_SUBSTRINGS):
        raise ValueError(
            f"Expected {len(CAPITAL_INCOME_COLUMN_SUBSTRINGS)} capital-income columns, found {columns}"
        )
    partition = data.loc[(data["table"] == "V") & data["partition"].astype(str).str.lower().eq("true")]
    capital_income = partition[columns].sum(axis=1)
    total = float(capital_income.sum())
    p_low = partition["p_low"]
    return {
        "top_1_share_pct": 100.0 * float(capital_income.loc[p_low >= 99].sum()) / total,
        "top_10_share_pct": 100.0 * float(capital_income.loc[p_low >= 90].sum()) / total,
    }


def _micro_setup() -> dict:
    inputs = read_yaml("config/c3_inputs_proposed.yaml")
    persons_path = "data/processed/brazil/microdata/pnadc_2025_c3_input.csv"
    prepared = micro.prepare_microdata(pd.read_csv(persons_path, low_memory=False))
    lines = {name: float(entry["value"]) for name, entry in inputs["poverty_lines_brl_month_per_capita"].items()}
    return {
        "prepared": prepared, "inputs": inputs, "lines": lines,
        "nominal_gdp_brl": float(inputs["nominal_gdp_brl_million"]["value"]) * 1e6,
        "minimum_wage_brl": float(inputs["minimum_wage_brl_month"]["value"]),
        "consumption_like_exponent": float(inputs["defaults"]["consumption_like_exponent"]),
    }


def _nominal_rate_path(frame: pd.DataFrame, draw_inputs: Mapping, variant: str = "central") -> pd.Series:
    """Nominal interest rate (%) by year, from this scenario's own inflation path."""
    rates = {
        int(row.year): macro.nominal_rate_from_real(
            macro.real_interest_rate_for_year(draw_inputs, variant, int(row.year)),
            float(row.inflation_with_external_pct),
        )
        for row in frame.itertuples()
    }
    return frame["year"].map(rates)


def _interest_expense_pp_gdp(frame: pd.DataFrame, draw_inputs: Mapping) -> pd.Series:
    """Interest expense (% GDP) = previous year's debt/GDP times this year's nominal rate."""
    ordered = frame.sort_values("year")
    previous_debt = ordered["debt_gdp_with_external"].shift(1)
    rate = _nominal_rate_path(ordered, draw_inputs)
    expense = previous_debt / 100.0 * rate
    expense.iloc[0] = 0.0  # no prior-year stock inside this corner for the base year
    return expense.reindex(frame.index)


def _cumulative_extra_inflation(effects: pd.DataFrame, base_year: int, years: list[int]) -> dict[int, float]:
    steps = effects.set_index("step")["external_extra_inflation_pp"]
    cumulative = {base_year: 0.0}
    factor = 1.0
    for step in range(1, max(years) - base_year + 1):
        factor *= 1.0 + float(steps.get(step, 0.0)) / 100.0
        cumulative[base_year + step] = (factor - 1.0) * 100.0
    return cumulative


def run_draws(n_draws: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    context = load_context(variants=["default"])
    params = context["parameters"]
    variant_scenarios = context["variant_configs"]["default"]
    base_year = context["base_year"]
    target_years = context["target_years"]
    steps = max(target_years) - base_year
    shares = capital_income_shares()
    micro_setup = _micro_setup()
    rng = np.random.default_rng(seed)
    external_rng = np.random.default_rng([seed, STREAM_INDEX, 1])
    changes = external.historical_changes()

    rows: list[dict] = []
    for index in range(n_draws):
        draw = (
            central_draw(params, context["inputs"])
            if index == 0
            else sample_draw(rng, params, context["inputs"])
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
        cumulative_extra_inflation = _cumulative_extra_inflation(effects, base_year, list(target_years))

        s0 = corner.loc[corner["scenario"].eq("S0")].sort_values("year").set_index("year")
        s0_interest = _interest_expense_pp_gdp(s0.reset_index(), draw_inputs).set_axis(s0.index)

        for scenario in SCENARIOS:
            scen = corner.loc[corner["scenario"].eq(scenario)].sort_values("year").set_index("year")
            scen_interest = _interest_expense_pp_gdp(scen.reset_index(), draw_inputs).set_axis(scen.index)
            for year in target_years:
                if year not in scen.index:
                    continue
                row = scen.loc[year]
                delta_interest_pp_gdp = float(scen_interest.loc[year] - s0_interest.loc[year])
                windfall_monthly_brl = delta_interest_pp_gdp / 100.0 * micro_setup["nominal_gdp_brl"] / 12.0
                horizon = int(year) - base_year
                gaps = scenario_package_gaps(variant_scenarios, scenario, horizon, float(row.gap_below_s0_pp))
                revenue = float(getattr(row, "revenue_change_pp", 0.0))
                erosion_pct = cumulative_extra_inflation.get(int(year), 0.0)

                common_kwargs = dict(
                    gdp_level_vs_s0_pct=float(row.gdp_level_vs_s0_pct),
                    unemployment_change_pp=float(row.unemployment_change_pp), package_gaps_pp_gdp=gaps,
                    revenue_change_pp=revenue, nominal_gdp_brl=micro_setup["nominal_gdp_brl"],
                    minimum_wage_brl=micro_setup["minimum_wage_brl"],
                    pension_variant=draw["micro_pension_variant"], labour_variant=draw["micro_labour_variant"],
                    tax_variant=draw["micro_tax_variant"],
                    consumption_like_exponent=micro_setup["consumption_like_exponent"],
                    random_seed=int(draw.get("draw", index)),
                )
                households_without_iy1 = micro.simulate_household_incomes(micro_setup["prepared"], **common_kwargs)
                households_with_iy1 = micro.simulate_household_incomes(
                    micro_setup["prepared"], **common_kwargs,
                    capital_income_windfall_brl_monthly=windfall_monthly_brl,
                    capital_income_top1_share_pct=shares["top_1_share_pct"],
                    capital_income_top10_share_pct=shares["top_10_share_pct"],
                    transfer_inflation_erosion_pct=erosion_pct,
                )
                ind_without = micro.calculate_indicators(households_without_iy1, micro_setup["lines"])
                ind_with = micro.calculate_indicators(households_with_iy1, micro_setup["lines"])
                rows.append({
                    "draw": index, "scenario": scenario, "year": int(year), "horizon": horizon,
                    "delta_interest_pp_gdp": delta_interest_pp_gdp,
                    "windfall_monthly_brl": windfall_monthly_brl,
                    "cumulative_extra_inflation_pct": erosion_pct,
                    "gini_without_iy1": ind_without["gini"],
                    "gini_with_iy1": ind_with["gini"],
                    "gini_change_from_iy1_points": 100.0 * (ind_with["gini"] - ind_without["gini"]),
                    "poverty_218_without_iy1_pct": ind_without.get("poverty_headcount_bolsa_familia_pct"),
                    "poverty_218_with_iy1_pct": ind_with.get("poverty_headcount_bolsa_familia_pct"),
                })
    return pd.DataFrame(rows)


def summarise(draws: pd.DataFrame) -> pd.DataFrame:
    sampled = draws.loc[draws["draw"] > 0]
    records = []
    for (scenario, horizon), group in sampled.groupby(["scenario", "horizon"], sort=False):
        record = {"scenario": scenario, "horizon": int(horizon)}
        for column in (
            "gini_change_from_iy1_points", "poverty_218_with_iy1_pct", "poverty_218_without_iy1_pct",
        ):
            record[f"{column}_p10"] = float(np.nanpercentile(group[column], 10))
            record[f"{column}_p50"] = float(np.nanpercentile(group[column], 50))
            record[f"{column}_p90"] = float(np.nanpercentile(group[column], 90))
        records.append(record)
    return pd.DataFrame(records).sort_values(["scenario", "horizon"]).reset_index(drop=True)


def render_report(draws: pd.DataFrame, summary: pd.DataFrame, shares: Mapping, n_draws: int, seed: int) -> str:
    lines = [
        "# IY1: interest-income and inflation-tax distribution diagnostic",
        "",
        "Built in direct response to an independent review of this project's academic paper "
        "(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the microsimulation "
        "omits the regressive channels of (1) higher government interest expense accruing to "
        "bondholders concentrated at the top of the income distribution and (2) an inflation tax "
        "falling hardest on poor households' non-indexed transfers. Both are wired as off-by-"
        "default arguments to `src.micro.simulate_household_incomes` and run here as a standalone "
        "diagnostic comparing Gini/poverty with and without both channels switched on.",
        "",
        f"Capital-income concentration (Receita Federal declared capital/financial income, Table V, "
        f"2024): top 1% of declarants hold {shares['top_1_share_pct']:.1f}% of it, top 10% hold "
        f"{shares['top_10_share_pct']:.1f}%.",
        "",
        f"Draws: {n_draws} (seed {seed}, central draw plus {n_draws - 1} sampled).",
        "",
        "## Effect of switching both IY1 channels on, vs the published (channels-off) Gini/poverty",
        "",
        "| Scenario | Horizon | Gini change from IY1 (points, p50 [p10,p90]) | Poverty (R$218) with IY1 "
        "(p50 [p10,p90]) | Poverty (R$218) without IY1 (p50 [p10,p90]) |",
        "|---|---:|---|---|---|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.horizon} | "
            f"{row.gini_change_from_iy1_points_p50:+.3f} "
            f"[{row.gini_change_from_iy1_points_p10:+.3f}, {row.gini_change_from_iy1_points_p90:+.3f}] | "
            f"{row.poverty_218_with_iy1_pct_p50:.2f} "
            f"[{row.poverty_218_with_iy1_pct_p10:.2f}, {row.poverty_218_with_iy1_pct_p90:.2f}] | "
            f"{row.poverty_218_without_iy1_pct_p50:.2f} "
            f"[{row.poverty_218_without_iy1_pct_p10:.2f}, {row.poverty_218_without_iy1_pct_p90:.2f}] |"
        )
    lines += [
        "",
        "## Limitations",
        "",
        "- The capital-income concentration curve comes from Receita Federal tax declarants, not "
        "the PNAD survey population; declarants are themselves concentrated among higher earners, "
        "so this is a reasonable but not survey-consistent proxy for 'how concentrated is capital "
        "income among the rich'.",
        "- Government interest expense is derived from the debt identity's own rate-times-stock "
        "definition, not a separately estimated bond-holding-by-income-decile survey (no such "
        "survey exists for Brazil at this granularity).",
        "- The inflation-tax erosion applies only to the baseline Bolsa Familia amount for one "
        "scenario-year's worth of cumulative extra inflation; it does not model a household's full "
        "multi-year exposure or any policy catch-up adjustment beyond what the scenario already "
        "assumes.",
        "- Within-band allocation of the interest windfall is proportional to each household's own "
        "income, a documented choice, not an estimated incidence.",
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
    shares = capital_income_shares()
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    draws.to_csv(args.data, index=False, float_format="%.6f")
    args.report.write_text(render_report(draws, summary, shares, args.draws, args.seed), encoding="utf-8")
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print(f"Wrote {len(draws)} draw-horizon rows to {args.data} and {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
