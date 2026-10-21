"""Offline historical back-tests for the Brazil scenario model blocks (D2).

The module deliberately evaluates the checked-in C2/C6 equations and central
parameters.  It does not estimate or tune parameters against the test period.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
import yaml

from src.external import gdp_and_inflation_effects
from src.macro import (
    debt_step,
    multiplier_by_package,
    multiplier_level_effect,
    pwt_implied_investment_rates,
    read_general_government_fiscal_workbook,
    read_pwt_brazil_growth,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = {
    "observed": ROOT / "data/brazil/backtest_observed.csv",
    "fiscal": ROOT / "data/brazil/fiscal.csv",
    "workbook": ROOT / "data/raw/brazil/demonstrativos-governo-geral.xlsx",
    "nominal_gdp": ROOT / "data/raw/brazil/macro/ibge_sidra_1846_gdp_current_1996_2025.json",
    "pwt": ROOT / "data/raw/brazil/macro/pwt1001.dta",
    "parameters": ROOT / "config/parameters.yaml",
    "scenarios": ROOT / "config/scenarios.yaml",
    "d2": ROOT / "config/d2_inputs_proposed.yaml",
    "results": ROOT / "data/brazil/backtest_results.csv",
    "report": ROOT / "outputs/backtest.md",
}

RESULT_COLUMNS = [
    "test", "year", "observed_value", "predicted_value", "residual",
    "baseline_prediction", "external_contribution", "input_change",
    "unit", "note",
]


def _yaml(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return value


def observed_wide(path: str | Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    required = {"year", "indicator", "value"}
    if not required.issubset(data.columns):
        raise ValueError(f"Observed file lacks {sorted(required - set(data.columns))}")
    if data.duplicated(["year", "indicator"]).any():
        raise ValueError("Observed input has duplicate year/indicator rows")
    return data.pivot(index="year", columns="indicator", values="value").sort_index()


def annual_nominal_gdp(path: str | Path) -> pd.Series:
    """Read annual current-price GDP by summing untouched SIDRA quarters."""
    with Path(path).open(encoding="utf-8") as handle:
        rows = json.load(handle)
    records = []
    for row in rows[1:]:
        quarter = str(row.get("D3C", ""))
        value = str(row.get("V", ""))
        if len(quarter) == 6 and quarter.isdigit() and value not in {"", "...", "-"}:
            records.append((int(quarter[:4]), float(value)))
    frame = pd.DataFrame(records, columns=["year", "value"])
    counts = frame.groupby("year").size()
    if (counts != 4).any():
        raise ValueError("Nominal GDP input must contain four quarters per year")
    return frame.groupby("year")["value"].sum().sort_index()


def debt_backtest(inputs: pd.DataFrame) -> pd.DataFrame:
    """Run the textbook debt recursion from the first observed debt anchor.

    Required rates and balances are percentages. A positive primary balance is
    a surplus, matching :func:`src.macro.debt_step`.
    """
    needed = {
        "year", "observed_debt_gdp", "primary_balance_gdp",
        "implicit_interest_pct", "nominal_gdp_growth_pct",
    }
    missing = needed - set(inputs.columns)
    if missing:
        raise ValueError(f"Debt back-test lacks {sorted(missing)}")
    data = inputs.sort_values("year").reset_index(drop=True).copy()
    years = data["year"].astype(int).tolist()
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError("Debt back-test requires consecutive years")
    predicted = [float(data.loc[0, "observed_debt_gdp"])]
    for row in data.iloc[1:].itertuples(index=False):
        predicted.append(
            debt_step(
                predicted[-1] / 100.0,
                float(row.implicit_interest_pct) / 100.0,
                float(row.nominal_gdp_growth_pct) / 100.0,
                float(row.primary_balance_gdp) / 100.0,
            ) * 100.0
        )
    data["predicted_debt_gdp"] = predicted
    data["residual_pp"] = data["predicted_debt_gdp"] - data["observed_debt_gdp"]
    return data


def debt_one_step(inputs: pd.DataFrame) -> pd.DataFrame:
    """Re-anchor each year on observed lagged debt; the residual is the implied stock-flow adjustment."""
    data = inputs.sort_values("year").reset_index(drop=True).copy()
    lagged = data["observed_debt_gdp"].shift(1)
    data["predicted_debt_gdp"] = [
        math.nan if pd.isna(previous) else debt_step(
            previous / 100.0,
            float(row.implicit_interest_pct) / 100.0,
            float(row.nominal_gdp_growth_pct) / 100.0,
            float(row.primary_balance_gdp) / 100.0,
        ) * 100.0
        for previous, row in zip(lagged, data.itertuples(index=False))
    ]
    data["residual_pp"] = data["predicted_debt_gdp"] - data["observed_debt_gdp"]
    return data.iloc[1:].reset_index(drop=True)


def build_debt_test(wide: pd.DataFrame, workbook: str | Path, nominal_path: str | Path) -> pd.DataFrame:
    years = list(range(2010, 2025))
    nominal = annual_nominal_gdp(nominal_path)
    debt = wide["gross_general_government_debt_pct_gdp"]
    primary = -wide["primary_result_pct_gdp"]  # source convention: negative is surplus
    rows = []
    for year in years:
        fiscal = read_general_government_fiscal_workbook(workbook, year)
        interest = math.nan if year == years[0] else float(fiscal["interest_payable_gdp"]) / float(debt.loc[year - 1]) * 100.0
        rows.append({
            "year": year,
            "observed_debt_gdp": float(debt.loc[year]),
            "primary_balance_gdp": float(primary.loc[year]),
            "implicit_interest_pct": interest,
            "nominal_gdp_growth_pct": math.nan if year == years[0] else (float(nominal.loc[year] / nominal.loc[year - 1]) - 1.0) * 100.0,
        })
    inputs = pd.DataFrame(rows)
    frames = []
    for test, out, note in [
        ("debt_engine", debt_backtest(inputs), "input_change is primary surplus (+) / deficit (-), pp GDP"),
        ("debt_engine_one_step", debt_one_step(inputs),
         "re-anchored on observed lagged debt; -residual is the implied stock-flow adjustment, pp GDP"),
    ]:
        frames.append(pd.DataFrame({
            "test": test,
            "year": out["year"],
            "observed_value": out["observed_debt_gdp"],
            "predicted_value": out["predicted_debt_gdp"],
            "residual": out["residual_pp"],
            "baseline_prediction": np.nan,
            "external_contribution": np.nan,
            "input_change": out["primary_balance_gdp"],
            "unit": "percent_of_gdp",
            "note": note,
        }))
    return pd.concat(frames, ignore_index=True)


def growth_backtest_pwt(
    pwt: pd.DataFrame,
    start_year: int = 2000,
    end_year: int = 2019,
    *,
    tfp_growth_pct: float | None = None,
) -> pd.DataFrame:
    """C2 dynamic growth backcast with observed factors and optional fixed TFP."""
    # C2's all-observed validation anchors K in ``start_year`` and evaluates
    # the following transitions.  A fixed-TFP test needs the prior-year anchor
    # so that ``start_year`` itself is an evaluated transition.
    first = (
        start_year - 1
        if tfp_growth_pct is not None and start_year > int(pwt["year"].min())
        else start_year
    )
    data = pwt.loc[pwt["year"].between(first, end_year)].set_index("year")
    expected = list(range(first, end_year + 1))
    if list(data.index) != expected:
        raise ValueError("PWT growth back-test requires a complete annual span")
    rates = pwt_implied_investment_rates(pwt).set_index("year")
    projected_capital = float(data.loc[first, "rnna"])
    records = []
    for year in expected[1:]:
        prior, current = data.loc[year - 1], data.loc[year]
        old_capital = projected_capital
        projected_capital = (
            (1.0 - float(current["delta"])) * old_capital
            + float(rates.loc[year, "implied_investment_rate"]) * float(current["rgdpna"])
        )
        capital_factor = projected_capital / old_capital
        alpha = 1.0 - float((prior["labsh"] + current["labsh"]) / 2.0)
        tfp_factor = (
            float(current["rtfpna"] / prior["rtfpna"])
            if tfp_growth_pct is None
            else 1.0 + float(tfp_growth_pct) / 100.0
        )
        factor = (
            tfp_factor
            * capital_factor ** alpha
            * float((current["hc"] * current["emp"]) / (prior["hc"] * prior["emp"])) ** (1.0 - alpha)
        )
        records.append({
            "year": year,
            "predicted_growth_pct": (factor - 1.0) * 100.0,
            "pwt_observed_growth_pct": (float(current["rgdpna"] / prior["rgdpna"]) - 1.0) * 100.0,
        })
    return pd.DataFrame(records).loc[lambda x: x["year"].between(start_year, end_year)].reset_index(drop=True)


def build_growth_test(wide: pd.DataFrame, parameters: Mapping, pwt_path: str | Path) -> pd.DataFrame:
    pwt = read_pwt_brazil_growth(pwt_path)
    start, end = 2006, 2019
    tfp_start, tfp_end = (int(x) for x in parameters["growth_calibration"]["tfp_periods"]["central"])
    tfp = pwt.set_index("year")["rtfpna"]
    tfp_central = ((float(tfp.loc[tfp_end]) / float(tfp.loc[tfp_start])) ** (1.0 / (tfp_end - tfp_start)) - 1.0) * 100.0
    base = growth_backtest_pwt(pwt, start, end, tfp_growth_pct=tfp_central)

    tot = wide["net_barter_terms_of_trade"].loc[start - 1:end]
    changes = np.log(tot).diff().dropna() * 100.0
    path = pd.DataFrame({"step": range(1, len(changes) + 1), "tot_change_pct": changes.to_numpy(), "fx_change_pct": 0.0})
    effects = gdp_and_inflation_effects(path, parameters).set_index("step")
    levels = pd.Series([0.0] + effects["external_gdp_level_pct"].tolist(), index=range(start - 1, end + 1))
    ext_growth = ((1.0 + levels.loc[start:end] / 100.0).to_numpy() / (1.0 + levels.loc[start - 1:end - 1] / 100.0).to_numpy() - 1.0) * 100.0
    predicted = ((1.0 + base["predicted_growth_pct"].to_numpy() / 100.0) * (1.0 + ext_growth / 100.0) - 1.0) * 100.0
    observed = wide.loc[start:end, "gdp_growth_pct"].to_numpy()
    return pd.DataFrame({
        "test": "growth_block",
        "year": base["year"],
        "observed_value": observed,
        "predicted_value": predicted,
        "residual": predicted - observed,
        "baseline_prediction": base["predicted_growth_pct"],
        "external_contribution": predicted - base["predicted_growth_pct"].to_numpy(),
        "input_change": changes.to_numpy(),
        "unit": "percentage_points_per_year",
        "note": "fixed C2 central TFP; input_change is observed ToT log change (%)",
    })


def _growth_from_level_effect(level: pd.Series) -> pd.Series:
    previous = level.shift(1).fillna(0.0)
    return ((1.0 + level / 100.0) / (1.0 + previous / 100.0) - 1.0) * 100.0


def build_multiplier_tests(
    wide: pd.DataFrame,
    fiscal_path: str | Path,
    parameters: Mapping,
    scenarios: Mapping,
) -> pd.DataFrame:
    fiscal = pd.read_csv(fiscal_path).loc[lambda x: x["year"].between(2010, 2024)].copy()
    years = fiscal["year"].astype(int).tolist()
    spending = fiscal.set_index("year")["primary_spending_pct_gdp"]
    level_change = spending - float(spending.loc[2010])
    trend = float(wide.loc[2010:2024, "gdp_growth_pct"].mean())
    observed_gap = wide.loc[years, "gdp_growth_pct"] - trend
    central = multiplier_by_package(parameters, "central")

    specifications: dict[str, tuple[pd.DataFrame, dict]] = {}
    total_gaps = pd.DataFrame({
        "year": years, "scenario": "history", "package": "total_expenditure",
        "gap_below_s0_pp": -level_change.to_numpy(),
    })
    total_entry = parameters["fiscal_multipliers_brazil"]["accumulated"]["total_expenditure"]
    specifications["multiplier_total"] = (total_gaps, {"total_expenditure": {"multiplier": float(total_entry["central"]), "horizon_months": float(total_entry["horizon_months"])}})

    category_rows = []
    for year in years:
        for package, share in scenarios["package_shares"].items():
            category_rows.append({"year": year, "scenario": "history", "package": package, "gap_below_s0_pp": -float(level_change.loc[year]) * float(share)})
    specifications["multiplier_categories"] = (pd.DataFrame(category_rows), central)

    frames = []
    annual_change = spending.diff()
    for name, (gaps, multipliers) in specifications.items():
        level = multiplier_level_effect(gaps, multipliers, "transitory").set_index("year")["gdp_level_vs_s0_pct"].loc[years]
        contribution = _growth_from_level_effect(level)
        frames.append(pd.DataFrame({
            "test": name,
            "year": years,
            "observed_value": observed_gap.to_numpy(),
            "predicted_value": contribution.to_numpy(),
            "residual": contribution.to_numpy() - observed_gap.to_numpy(),
            "baseline_prediction": trend,
            "external_contribution": np.nan,
            "input_change": annual_change.loc[years].to_numpy(),
            "unit": "percentage_points_per_year",
            "note": "observed is growth minus 2010-2024 mean; input is annual primary-spending/GDP change",
        }))
    return pd.concat(frames, ignore_index=True)


def build_inflation_test(wide: pd.DataFrame, parameters: Mapping, d2: Mapping) -> pd.DataFrame:
    years = list(range(2005, 2025))
    fx = wide["brl_per_usd"].loc[2004:2024]
    changes = np.log(fx).diff().dropna() * 100.0
    path = pd.DataFrame({"step": range(1, len(years) + 1), "tot_change_pct": 0.0, "fx_change_pct": changes.to_numpy()})
    predicted = gdp_and_inflation_effects(path, parameters)["external_extra_inflation_pp"].to_numpy()
    targets = pd.Series({int(k): float(v) for k, v in d2["inflation_target_pct"]["by_year"].items()})
    observed_gap = wide.loc[years, "ipca_12m_pct"] - targets.loc[years]
    return pd.DataFrame({
        "test": "inflation_pass_through",
        "year": years,
        "observed_value": observed_gap.to_numpy(),
        "predicted_value": predicted,
        "residual": predicted - observed_gap.to_numpy(),
        "baseline_prediction": targets.loc[years].to_numpy(),
        "external_contribution": np.nan,
        "input_change": changes.to_numpy(),
        "unit": "percentage_points",
        "note": "observed is IPCA minus CMN target; input is BRL/USD log change (%)",
    })


def statistics_table(results: pd.DataFrame, d2: Mapping) -> pd.DataFrame:
    records = []
    for test, data in results.groupby("test", sort=False):
        residual = data["residual"].astype(float)
        correlation = float(data[["observed_value", "predicted_value"]].corr().iloc[0, 1])
        record = {
            "test": test,
            "mean_error": float(residual.mean()),
            "mae": float(residual.abs().mean()),
            "rmse": float(np.sqrt(np.mean(np.square(residual)))),
            "correlation": correlation,
            "final_error": float(residual.iloc[-1]),
            "status": "not_rated",
        }
        if test == "debt_engine":
            tol = float(d2["tolerances"]["debt_final_year_absolute_error_pp_gdp"]["value"])
            record["status"] = "PASS" if abs(record["final_error"]) <= tol else "FAIL"
        elif test == "growth_block":
            tol = float(d2["tolerances"]["growth_absolute_mean_error_pp_per_year"]["value"])
            record["status"] = "PASS" if abs(record["mean_error"]) <= tol else "FAIL"
        records.append(record)
    return pd.DataFrame(records)


def _compound(values: pd.Series) -> float:
    return (float(np.prod(1.0 + values.to_numpy(dtype=float) / 100.0)) - 1.0) * 100.0


def episode_table(growth: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for episode, start, end, label in [
        ("commodity boom", 2006, 2010, "2005 base to 2010; 2003-04 unavailable because ToT starts in 2005"),
        ("recession", 2014, 2016, "2014-2016"),
    ]:
        data = growth.loc[growth["year"].between(start, end)]
        actual = _compound(data["observed_value"])
        base = _compound(data["baseline_prediction"])
        model = _compound(data["predicted_value"])
        rows.append({
            "episode": episode, "period": label, "actual": actual,
            "base": base, "external": model - base, "model": model,
            "residual": model - actual,
            "share_explained": model / actual * 100.0 if actual != 0 else math.nan,
        })
    return pd.DataFrame(rows)


def render_report(results: pd.DataFrame, stats: pd.DataFrame, d2: Mapping) -> str:
    lookup = stats.set_index("test")
    rated = lookup.loc[["debt_engine", "growth_block"], "status"]
    verdict = "PASS" if rated.eq("PASS").all() else "FAIL"
    growth = results.loc[results["test"].eq("growth_block")]
    episodes = episode_table(growth)
    debt = results.loc[results["test"].eq("debt_engine")]
    largest_debt = debt.loc[debt["residual"].abs().nlargest(3).index]
    largest_growth = growth.loc[growth["residual"].abs().nlargest(3).index]

    lines = [
        "# D2 historical back-tests", "",
        f"**Overall proposed gate: {verdict}.** Only the two supplied numerical tolerances are rated. "
        "The multiplier and inflation exercises remain diagnostics, not validation tests.", "",
        "No coefficient was tuned to improve these results. All calculations are offline and use the checked-in observations, C2 central parameters and unchanged C2/C6 equations.", "",
        "## Results and proposed tolerances", "",
        "| Block | Mean error (pp) | MAE (pp) | RMSE (pp) | Correlation | Final error (pp) | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in stats.itertuples(index=False):
        lines.append(f"| {row.test} | {row.mean_error:.3f} | {row.mae:.3f} | {row.rmse:.3f} | {row.correlation:.3f} | {row.final_error:.3f} | {row.status} |")
    debt_tol = d2["tolerances"]["debt_final_year_absolute_error_pp_gdp"]["value"]
    growth_tol = d2["tolerances"]["growth_absolute_mean_error_pp_per_year"]["value"]
    lines += [
        "",
        f"Rated tolerances proposed for lead-developer approval: absolute 2024 debt error <= {debt_tol:g} pp of GDP; absolute growth mean error <= {growth_tol:g} pp/year over 2006-2019. `not_rated` means no tolerance was supplied, not a pass.", "",
        "## Debt engine", "",
        "The recursion starts from observed 2010 gross debt. A 2006 run is not possible from the supplied inputs: the Tesouro GFS workbook has no 2006-2009 interest-payable observations. Substituting Selic would not be an observed implicit debt rate, so no series was invented.", "",
        "The largest absolute misses are:", "",
        "| Year | Observed debt | Simulated debt | Simulated - observed |",
        "|---:|---:|---:|---:|",
    ]
    for row in largest_debt.itertuples(index=False):
        lines.append(f"| {row.year} | {row.observed_value:.2f} | {row.predicted_value:.2f} | {row.residual:+.2f} |")
    lines += [
        "",
        "**One-step-ahead diagnostic (added in lead-developer review).** Re-anchoring each year on observed lagged debt isolates the recursion from accumulation. "
        f"Its mean error is {lookup.loc['debt_engine_one_step', 'mean_error']:+.2f} pp/year (MAE {lookup.loc['debt_engine_one_step', 'mae']:.2f}); "
        "the implied stock-flow adjustment (observed minus one-step prediction) is positive in 2011-2012, when the Treasury lent to BNDES, and negative in 2016-2022, "
        "the years of BNDES early repayments to the Treasury and BCB result transfers used to redeem debt. The cumulative miss is therefore mostly the sum of these operations, "
        "which the textbook identity omits by construction. The diagnostic is not rated and does not change the gate verdict. "
        "Projections set future stock-flow adjustments to zero, identical across scenarios, so they largely cancel in paired differences vs S0 but not in debt levels.", "",
        "These residuals are not hidden adjustments. The textbook identity omits stock-flow adjustments and valuation/reclassification effects; BCB gross debt is also affected by repo operations. In addition, Tesouro GFS interest and the BCB consolidated-public-sector primary result/gross-debt series have different institutional coverage and timing. Those concept differences accumulate when a simulated level is not re-anchored each year.", "",
        "## Growth accounting plus external block", "",
        "Observed PWT investment-derived capital accumulation, human capital and employment are used each year. TFP is held at the C2 central 2000-2019 rate. The C6 terms-of-trade coefficient, permanent/cyclical split and decay are unchanged.", "",
        "| Episode | Actual cumulative growth | Fixed-TFP factor model | C6 ToT addition | Model total | Model - actual | Model / actual |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in episodes.itertuples(index=False):
        lines.append(f"| {row.episode} ({row.period}) | {row.actual:.2f}% | {row.base:.2f}% | {row.external:+.2f} pp | {row.model:.2f}% | {row.residual:+.2f} pp | {row.share_explained:.1f}% |")
    lines += [
        "",
        "The boom row begins with the 2005 level and measures the 2006-2010 transitions. The repository has no terms-of-trade observation before 2005, so the requested 2003-2004 external decomposition cannot be produced honestly.", "",
        "Largest annual growth residuals:", "",
        "| Year | Observed | Model | C6 contribution | Model - observed |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in largest_growth.itertuples(index=False):
        lines.append(f"| {row.year} | {row.observed_value:.2f} | {row.predicted_value:.2f} | {row.external_contribution:+.2f} | {row.residual:+.2f} |")
    boom = episodes.loc[episodes["episode"].eq("commodity boom")].iloc[0]
    lines += [
        "",
        f"**External-block warning:** C6 adds only {boom.external:+.2f} pp to cumulative 2006-2010 growth. It therefore explains little of the boom and should not be presented as a sufficient external-history model. Missing channels include capital inflows/FDI, commodity-linked fiscal revenue, exchange-rate effects on inflation and interest rates, and FX-linked debt.", "",
        "## Multiplier diagnostic", "",
        f"The benchmark is observed annual real GDP growth minus its 2010-2024 arithmetic mean ({float(results.loc[results.test.eq('multiplier_total'), 'baseline_prediction'].iloc[0]):.3f}%). The spending input is the annual change in Tesouro general-government primary spending/GDP. This is a weak test: observed spending changes are endogenous, annual data do not identify fiscal shocks, and the aggregate series cannot reveal which category actually changed.", "",
    ]
    for name in ("multiplier_total", "multiplier_categories"):
        data = results.loc[results["test"].eq(name) & results["year"].gt(2010)]
        sign = float((np.sign(data["predicted_value"]) == np.sign(data["observed_value"])).mean() * 100.0)
        recession = data.loc[data["year"].between(2014, 2016)]
        recession_sign = int((np.sign(recession["predicted_value"]) == np.sign(recession["observed_value"])).sum())
        lines.append(f"- `{name}`: correlation {lookup.loc[name, 'correlation']:.3f}; signs agree in {sign:.1f}% of 2011-2024 years and {recession_sign}/3 recession years (2014-2016).")
    inflation = lookup.loc["inflation_pass_through"]
    lines += [
        "",
        "## Inflation pass-through diagnostic", "",
        f"Predicted extra inflation from observed BRL/USD changes is compared with IPCA minus the CMN target. Mean error is {inflation['mean_error']:+.3f} pp, RMSE {inflation['rmse']:.3f} pp and correlation {inflation['correlation']:.3f}. The target path is in `config/d2_inputs_proposed.yaml`, labelled **transcribed without a network check**. This is not a complete inflation model: it omits expectations, inertia, slack, commodity prices and administered prices.", "",
        "## Publication implications", "",
    ]
    if verdict == "FAIL":
        lines.append("The proposed D2 gate fails. No failing block should be called validated and scenario results should not be published as model-validated projections.")
    else:
        lines.append("The two proposed numerical gates pass, but the unrated weak diagnostics and stated model omissions remain publication caveats; passing is not proof of causal validity.")
    lines += [
        "",
        "Changes needed are structural rather than parameter retuning: add an explicit debt stock-flow/reconciliation layer with aligned fiscal concepts; extend C6 with the omitted external channels; identify fiscal shocks and category composition for a credible multiplier test; and embed pass-through in a broader inflation equation. Re-estimate or change parameters only with new sourced evidence and an out-of-sample protocol.", "",
        "The annual audit rows are in `data/brazil/backtest_results.csv` (one row per year/test; residual = predicted minus observed).",
    ]
    return "\n".join(lines) + "\n"


def run_backtests(paths: Mapping[str, str | Path] = DEFAULT_PATHS) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    parameters = _yaml(paths["parameters"])
    scenarios = _yaml(paths["scenarios"])
    d2 = _yaml(paths["d2"])
    wide = observed_wide(paths["observed"])
    results = pd.concat([
        build_debt_test(wide, paths["workbook"], paths["nominal_gdp"]),
        build_growth_test(wide, parameters, paths["pwt"]),
        build_multiplier_tests(wide, paths["fiscal"], parameters, scenarios),
        build_inflation_test(wide, parameters, d2),
    ], ignore_index=True)[RESULT_COLUMNS]
    if results.duplicated(["test", "year"]).any():
        raise RuntimeError("Back-test output must have one row per test/year")
    stats = statistics_table(results, d2)
    return results, stats, render_report(results, stats, d2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT_PATHS["results"])
    parser.add_argument("--report", type=Path, default=DEFAULT_PATHS["report"])
    args = parser.parse_args(argv)
    results, stats, report = run_backtests()
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.results, index=False, float_format="%.10f")
    args.report.write_text(report, encoding="utf-8")
    print(stats.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"Wrote {len(results)} annual rows to {args.results} and {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
