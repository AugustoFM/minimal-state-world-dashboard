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
    "c7_backtest": ROOT / "data/brazil/c7_backtest.csv",
    "c7_estimates": ROOT / "data/brazil/c7_estimates.csv",
    "external_observed": ROOT / "data/brazil/external_observed.csv",
    "results": ROOT / "data/brazil/backtest_results.csv",
    "report": ROOT / "outputs/backtest.md",
}

PERIOD_WINDOWS = [
    ("Dilma I", 2011, 2014, False),
    ("2015-2016", 2015, 2016, False),
    ("Temer", 2017, 2018, False),
    ("Bolsonaro", 2019, 2022, False),
    ("Lula III (data end 2024)", 2023, 2024, False),
    ("2023-2025", 2023, 2025, True),
]
IBGE_2025_GROWTH = 2.3
IBGE_2025_GROWTH_SOURCE = "IBGE, released 2026-03-03; hand-entered"

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


def sfa_out_of_sample(
    inputs: pd.DataFrame,
    estimate_start: int = 2011,
    estimate_end: int = 2017,
    anchor_year: int = 2017,
) -> tuple[pd.DataFrame, dict]:
    """Estimate a constant SFA in 2011-2017 and test it after the 2017 anchor.

    SFA is observed debt minus the one-step textbook prediction, in percentage
    points of GDP.  The standard deviation is the sample standard deviation.
    """
    data = inputs.sort_values("year").reset_index(drop=True).copy()
    one_step = debt_one_step(data)
    one_step["sfa_pp"] = -one_step["residual_pp"]
    estimation = one_step.loc[one_step["year"].between(estimate_start, estimate_end)]
    expected_years = list(range(estimate_start, estimate_end + 1))
    if estimation["year"].astype(int).tolist() != expected_years:
        raise ValueError(f"SFA estimation requires exactly {expected_years}")
    mean_sfa = float(estimation["sfa_pp"].mean())
    sd_sfa = float(estimation["sfa_pp"].std(ddof=1))

    indexed = data.set_index("year")
    if anchor_year not in indexed.index:
        raise ValueError(f"SFA recursion lacks anchor year {anchor_year}")
    years = list(range(anchor_year, int(data["year"].max()) + 1))
    zero = [float(indexed.loc[anchor_year, "observed_debt_gdp"])]
    with_sfa = zero.copy()
    for year in years[1:]:
        row = indexed.loc[year]
        args = (
            float(row["implicit_interest_pct"]) / 100.0,
            float(row["nominal_gdp_growth_pct"]) / 100.0,
            float(row["primary_balance_gdp"]) / 100.0,
        )
        zero.append(debt_step(zero[-1] / 100.0, *args) * 100.0)
        with_sfa.append(debt_step(with_sfa[-1] / 100.0, *args) * 100.0 + mean_sfa)
    recursion = pd.DataFrame({
        "year": years,
        "observed_debt_gdp": indexed.loc[years, "observed_debt_gdp"].to_numpy(dtype=float),
        "zero_sfa_debt_gdp": zero,
        "with_sfa_debt_gdp": with_sfa,
    })
    recursion["zero_sfa_residual_pp"] = recursion["zero_sfa_debt_gdp"] - recursion["observed_debt_gdp"]
    recursion["with_sfa_residual_pp"] = recursion["with_sfa_debt_gdp"] - recursion["observed_debt_gdp"]
    summary = {
        "estimation_years": expected_years,
        "mean_2011_2017": mean_sfa,
        "sd_2011_2017": sd_sfa,
        "values_by_year": {
            int(row.year): float(row.sfa_pp) for row in one_step.itertuples(index=False)
        },
    }
    return recursion, summary


def debt_test_inputs(wide: pd.DataFrame, workbook: str | Path, nominal_path: str | Path) -> pd.DataFrame:
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
    return pd.DataFrame(rows)


def build_debt_test(wide: pd.DataFrame, workbook: str | Path, nominal_path: str | Path) -> pd.DataFrame:
    inputs = debt_test_inputs(wide, workbook, nominal_path)
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
    recursion, summary = sfa_out_of_sample(inputs)
    for test, prediction, residual, note in [
        (
            "debt_engine_zero_sfa_oos", "zero_sfa_debt_gdp", "zero_sfa_residual_pp",
            "recursion from observed 2017 debt; zero stock-flow adjustment",
        ),
        (
            "debt_engine_with_sfa_oos", "with_sfa_debt_gdp", "with_sfa_residual_pp",
            f"recursion from observed 2017 debt; constant 2011-2017 mean SFA ({summary['mean_2011_2017']:+.6f} pp/year)",
        ),
    ]:
        frames.append(pd.DataFrame({
            "test": test,
            "year": recursion["year"],
            "observed_value": recursion["observed_debt_gdp"],
            "predicted_value": recursion[prediction],
            "residual": recursion[residual],
            "baseline_prediction": np.nan,
            "external_contribution": np.nan,
            "input_change": np.nan,
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


def _tfp_window_cagr(pwt: pd.DataFrame, parameters: Mapping, window_key: str) -> float:
    tfp_start, tfp_end = (int(x) for x in parameters["growth_calibration"]["tfp_periods"][window_key])
    tfp = pwt.set_index("year")["rtfpna"]
    return ((float(tfp.loc[tfp_end]) / float(tfp.loc[tfp_start])) ** (1.0 / (tfp_end - tfp_start)) - 1.0) * 100.0


def build_growth_test(wide: pd.DataFrame, parameters: Mapping, pwt_path: str | Path) -> pd.DataFrame:
    """Two growth-block checks over the same 2006-2019 window.

    ``growth_block`` fixes TFP at the C2 central rate (PWT 2000-2019 CAGR), a
    window that contains the test period: it is an in-sample consistency
    check, kept for the episode narrative in the report, and is not what the
    Tier 1 gate is keyed on. ``growth_block_oos`` fixes TFP at a window ending
    in 2005, strictly before the test period starts, and is the statistic
    ``gate_verdicts`` actually rates (see the 2026-10-23 lead-developer review
    noting the original check was not genuinely held out).
    """
    pwt = read_pwt_brazil_growth(pwt_path)
    start, end = 2006, 2019

    tot = wide["net_barter_terms_of_trade"].loc[start - 1:end]
    changes = np.log(tot).diff().dropna() * 100.0
    path = pd.DataFrame({"step": range(1, len(changes) + 1), "tot_change_pct": changes.to_numpy(), "fx_change_pct": 0.0})
    effects = gdp_and_inflation_effects(path, parameters).set_index("step")
    levels = pd.Series([0.0] + effects["external_gdp_level_pct"].tolist(), index=range(start - 1, end + 1))
    ext_growth = ((1.0 + levels.loc[start:end] / 100.0).to_numpy() / (1.0 + levels.loc[start - 1:end - 1] / 100.0).to_numpy() - 1.0) * 100.0
    observed = wide.loc[start:end, "gdp_growth_pct"].to_numpy()

    def _frame(test_name: str, tfp_growth_pct: float, note: str) -> pd.DataFrame:
        base = growth_backtest_pwt(pwt, start, end, tfp_growth_pct=tfp_growth_pct)
        predicted = ((1.0 + base["predicted_growth_pct"].to_numpy() / 100.0) * (1.0 + ext_growth / 100.0) - 1.0) * 100.0
        return pd.DataFrame({
            "test": test_name,
            "year": base["year"],
            "observed_value": observed,
            "predicted_value": predicted,
            "residual": predicted - observed,
            "baseline_prediction": base["predicted_growth_pct"],
            "external_contribution": predicted - base["predicted_growth_pct"].to_numpy(),
            "input_change": changes.to_numpy(),
            "unit": "percentage_points_per_year",
            "note": note,
        })

    in_sample = _frame(
        "growth_block",
        _tfp_window_cagr(pwt, parameters, "central"),
        "fixed C2 central TFP (2000-2019; overlaps the 2006-2019 test window, so this is an "
        "in-sample consistency check, not the Tier 1 gated statistic); input_change is observed ToT log change (%)",
    )
    out_of_sample = _frame(
        "growth_block_oos",
        _tfp_window_cagr(pwt, parameters, "pre_2006_backtest_oos"),
        "fixed TFP from a window ending in 2005, strictly before the 2006-2019 test period "
        "(genuinely held out; this is the statistic gate_verdicts rates for Tier 1); input_change is observed ToT log change (%)",
    )
    return pd.concat([in_sample, out_of_sample], ignore_index=True)


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


def build_c7_gate_test(path: str | Path) -> pd.DataFrame:
    """Load, without re-estimation, the fixed C7 channel-A OOS audit rows."""
    data = pd.read_csv(path).loc[lambda x: x["channel"].eq("A_output")].copy()
    if data["year"].astype(int).tolist() != list(range(2015, 2025)):
        raise ValueError("C7 channel A gate requires the checked-in 2015-2024 rows")
    return pd.DataFrame({
        "test": "c7_channel_a_oos",
        "year": data["year"].astype(int),
        "observed_value": data["observed"].astype(float),
        "predicted_value": data["predicted"].astype(float),
        "residual": data["predicted"].astype(float) - data["observed"].astype(float),
        "baseline_prediction": data["naive"].astype(float),
        "external_contribution": data["c6"].astype(float),
        "input_change": np.nan,
        "unit": "percentage_points_per_year",
        "note": "loaded from data/brazil/c7_backtest.csv; fixed 2015-2024 channel A OOS test, not re-estimated",
    })


def read_general_government_revenue(path: str | Path) -> pd.Series:
    """Read code 1 annual general-government revenue/GDP from sheet 3.2.a."""
    sheet = pd.read_excel(path, sheet_name="3.2.a", header=None)
    years = pd.to_numeric(sheet.iloc[3], errors="coerce")
    code = sheet.iloc[:, 0].astype(str).str.strip()
    rows = sheet.loc[code.eq("1")]
    if len(rows) != 1:
        raise ValueError("Expected exactly one code row '1' in workbook sheet 3.2.a")
    values = pd.to_numeric(rows.iloc[0], errors="coerce")
    result = {
        int(year): float(values.iloc[column]) * 100.0
        for column, year in enumerate(years)
        if pd.notna(year) and pd.notna(values.iloc[column])
    }
    return pd.Series(result, name="revenue_pct_gdp").sort_index()


def _endpoint_change(series: pd.Series, start: int, end: int) -> tuple[float, float, float]:
    """Change over a period measured from the last year before it (the inherited level) to its end."""
    base = start - 1
    if base not in series.index or end not in series.index:
        return math.nan, math.nan, math.nan
    first, last = float(series.loc[base]), float(series.loc[end])
    return first, last, last - first


def period_diagnostic(
    wide: pd.DataFrame,
    fiscal_path: str | Path,
    workbook_path: str | Path,
    external_path: str | Path,
    estimates_path: str | Path,
    parameters: Mapping,
) -> pd.DataFrame:
    """Build neutral calendar-period summaries from observed input columns."""
    fiscal = pd.read_csv(fiscal_path).set_index("year")
    spending = fiscal["primary_spending_pct_gdp"].astype(float)
    revenue = read_general_government_revenue(workbook_path)
    primary = -wide["primary_result_pct_gdp"].astype(float)
    debt = wide["gross_general_government_debt_pct_gdp"].astype(float)

    external_long = pd.read_csv(external_path)
    external = external_long.pivot(index="year", columns="indicator", values="value").sort_index()
    price = external["commodity_export_price_index"].astype(float)
    dlnp = np.log(price).diff() * 100.0
    regressors = pd.DataFrame({
        "dlnP": dlnp,
        "dlnP_lag": dlnp.shift(1),
        "world_gdp_growth_pct": external["world_gdp_growth_pct"].astype(float),
    })
    estimates = pd.read_csv(estimates_path)
    reverse = estimates.loc[estimates["channel"].eq("A_output_reverse")]
    coefficients = reverse.set_index("coefficient")["estimate"].astype(float)
    needed = {"dlnP", "dlnP_lag", "world_gdp_growth_pct"}
    if not needed.issubset(coefficients.index):
        raise ValueError(f"C7 reverse estimates lack {sorted(needed - set(coefficients.index))}")
    # Lead review fix: the reverse fit's own fitted values (constant included), so the trend and the world
    # growth level enter as estimated; the constant is reported as `trend_proxy_pct`.
    trend = float(coefficients.loc["constant"])
    c7_fitted = trend + sum(regressors[name] * coefficients.loc[name] for name in sorted(needed))
    multiplier = float(parameters["fiscal_multipliers_brazil"]["accumulated"]["total_expenditure"]["central"])
    spending_effect = spending.diff() * multiplier
    implied = c7_fitted + spending_effect

    growth = wide["gdp_growth_pct"].astype(float).copy()
    growth.loc[2025] = IBGE_2025_GROWTH
    rows = []
    for label, start, end, separately_flagged in PERIOD_WINDOWS:
        gdp_window = growth.loc[start:end]
        s0, s1, ds = _endpoint_change(spending, start, end)
        r0, r1, dr = _endpoint_change(revenue, start, end)
        p0, p1, dp = _endpoint_change(primary, start, end)
        d0, d1, dd = _endpoint_change(debt, start, end)
        if start - 1 in price.index and end in price.index:
            commodity_change = float((math.log(float(price.loc[end])) - math.log(float(price.loc[start - 1]))) * 100.0)
        else:
            commodity_change = math.nan
        model_window = implied.loc[start:end]
        model_complete = len(model_window) == end - start + 1 and model_window.notna().all()
        implied_mean = float(model_window.mean()) if model_complete else math.nan
        observed_mean = float(gdp_window.mean())
        rows.append({
            "period": label,
            "start_year": start,
            "end_year": end,
            "separately_flagged": separately_flagged,
            "average_real_gdp_growth_pct": observed_mean,
            "growth_years": ";".join(str(year) for year in gdp_window.index),
            "growth_source": IBGE_2025_GROWTH_SOURCE if end == 2025 else "data/brazil/backtest_observed.csv:gdp_growth_pct",
            "primary_spending_start_pct_gdp": s0,
            "primary_spending_end_pct_gdp": s1,
            "primary_spending_change_pp": ds,
            "revenue_start_pct_gdp": r0,
            "revenue_end_pct_gdp": r1,
            "revenue_change_pp": dr,
            "primary_balance_start_pct_gdp": p0,
            "primary_balance_end_pct_gdp": p1,
            "primary_balance_change_pp": dp,
            "gross_debt_start_pct_gdp": d0,
            "gross_debt_end_pct_gdp": d1,
            "gross_debt_change_pp": dd,
            "commodity_price_log_change_pct": commodity_change,
            "model_implied_growth_pct": implied_mean,
            "model_residual_pp": implied_mean - observed_mean if model_complete else math.nan,
            "model_years": f"{start}-{end}" if model_complete else "unavailable: 2025 C7 inputs absent",
            "trend_proxy_pct": trend,
            "spending_multiplier": multiplier,
        })
    return pd.DataFrame(rows)


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
            "naive_rmse": math.nan,
            "status": "not_rated",
        }
        if test == "debt_engine":
            tol = float(d2["tolerances"]["debt_final_year_absolute_error_pp_gdp"]["value"])
            record["status"] = "PASS" if abs(record["final_error"]) <= tol else "FAIL"
        elif test == "growth_block":
            record["status"] = "not_rated"
        elif test == "growth_block_oos":
            tol = float(d2["tolerances"]["growth_absolute_mean_error_pp_per_year"]["value"])
            record["status"] = "PASS" if abs(record["mean_error"]) <= tol else "FAIL"
        elif test == "debt_engine_one_step":
            tol = float(d2["tolerances"]["debt_one_step_mae_pp_gdp"]["value"])
            record["status"] = "PASS" if record["mae"] <= tol else "FAIL"
        elif test in {"debt_engine_zero_sfa_oos", "debt_engine_with_sfa_oos"}:
            tol = float(d2["tolerances"]["debt_final_year_absolute_error_pp_gdp"]["value"])
            record["status"] = "PASS" if abs(record["final_error"]) <= tol else "FAIL"
        elif test == "c7_channel_a_oos":
            naive_residual = data["baseline_prediction"].astype(float) - data["observed_value"].astype(float)
            record["naive_rmse"] = float(np.sqrt(np.mean(np.square(naive_residual))))
            record["status"] = "PASS" if record["rmse"] < record["naive_rmse"] else "FAIL"
        records.append(record)
    return pd.DataFrame(records)


def gate_verdicts(stats: pd.DataFrame, d2: Mapping) -> dict[str, str]:
    """Apply the lead-developer's two-tier publication gate."""
    lookup = stats.set_index("test")
    one_step_tol = float(d2["tolerances"]["debt_one_step_mae_pp_gdp"]["value"])
    growth_tol = float(d2["tolerances"]["growth_absolute_mean_error_pp_per_year"]["value"])
    debt_tol = float(d2["tolerances"]["debt_final_year_absolute_error_pp_gdp"]["value"])
    tier1_checks = [
        float(lookup.loc["debt_engine_one_step", "mae"]) <= one_step_tol,
        abs(float(lookup.loc["growth_block_oos", "mean_error"])) <= growth_tol,
        float(lookup.loc["c7_channel_a_oos", "rmse"]) < float(lookup.loc["c7_channel_a_oos", "naive_rmse"]),
    ]
    tier2_pass = abs(float(lookup.loc["debt_engine_with_sfa_oos", "final_error"])) <= debt_tol
    return {
        "tier_1_differences_vs_s0": "PASS" if all(tier1_checks) else "FAIL",
        "tier_2_levels": "PASS" if tier2_pass else "FAIL",
    }


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


def _render_report_v1(results: pd.DataFrame, stats: pd.DataFrame, d2: Mapping) -> str:
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


def render_report(
    results: pd.DataFrame,
    stats: pd.DataFrame,
    d2: Mapping,
    sfa_summary: Mapping,
    periods: pd.DataFrame,
) -> str:
    lookup = stats.set_index("test")
    gates = gate_verdicts(stats, d2)
    growth = results.loc[results["test"].eq("growth_block")]
    debt = results.loc[results["test"].eq("debt_engine")]
    episodes = episode_table(growth)

    lines = [
        "# D2 historical back-tests", "",
        f"**Overall proposed gate: {'PASS' if all(value == 'PASS' for value in gates.values()) else 'FAIL'}.** Legacy aggregate retained for downstream report compatibility; use the two tier verdicts below for publication decisions.", "",
        f"**Tier 1 - differences vs S0: {gates['tier_1_differences_vs_s0']}.** This is the gate for publishing scenario effects.", "",
        f"**Tier 2 - debt/GDP levels: {gates['tier_2_levels']}.** The verdict uses the out-of-sample recursion with the pre-2018 mean SFA; the zero-SFA result is reported alongside it.", "",
        "No coefficient was tuned to improve these results. Calculations are offline and use checked-in observations and fixed model parameters.", "",
        "**Debt-level context (diagnostic, not a point forecast).** Tier 2 is expected to keep failing: its "
        "dominant residual is discretionary Treasury/BNDES/BCB stock-flow operations with no macro antecedent "
        "(see the Stock-flow adjustment section below). Rather than chase a point fix, `python -m "
        "src.debt_level_diagnostics` (`outputs/debt_level_diagnostics.md`) reports, with ranges: the probability "
        "of S0 breaching stated debt/GDP thresholds; the primary balance that would stabilise debt at each "
        "horizon's own rates and the gap to S0's actual projected balance; debt-level bands under Brazil's own "
        "stock-flow-adjustment history versus a cross-country emerging-panel alternative; and two off-to-the-side "
        "diagnostic variants of S0 itself (an estimated fiscal-reaction-function path, a nonlinear risk-premium "
        "path) -- never mixed into the R/E-vs-S0 policy grid. This does not and cannot make Tier 2 pass; it "
        "answers `outputs/debt_panel.md`'s \"Implications for a lead-developer decision\" with evidence instead "
        "of leaving them unimplemented.", "",
        "## Gate v2", "",
        "| Tier | Test | Statistic | Tolerance / benchmark | Verdict |",
        "|---|---|---:|---:|---|",
        f"| 1: differences vs S0 | Debt engine, one step ahead (2011-2024) | MAE {lookup.loc['debt_engine_one_step', 'mae']:.3f} pp | <= {d2['tolerances']['debt_one_step_mae_pp_gdp']['value']:g} pp | {lookup.loc['debt_engine_one_step', 'status']} |",
        f"| 1: differences vs S0 | Growth block, genuinely out-of-sample (2006-2019, TFP from 1996-2005) | absolute mean error {abs(lookup.loc['growth_block_oos', 'mean_error']):.3f} pp/yr | <= {d2['tolerances']['growth_absolute_mean_error_pp_per_year']['value']:g} pp/yr | {lookup.loc['growth_block_oos', 'status']} |",
        f"| 1: differences vs S0 | C7 channel A OOS (2015-2024) | RMSE {lookup.loc['c7_channel_a_oos', 'rmse']:.3f} pp | naive RMSE {lookup.loc['c7_channel_a_oos', 'naive_rmse']:.3f} pp; must be lower | {lookup.loc['c7_channel_a_oos', 'status']} |",
        f"| 2: levels | 2017-anchor zero-SFA recursion, 2024 | error {lookup.loc['debt_engine_zero_sfa_oos', 'final_error']:+.3f} pp | absolute error <= {d2['tolerances']['debt_final_year_absolute_error_pp_gdp']['value']:g} pp | {lookup.loc['debt_engine_zero_sfa_oos', 'status']} (reported only) |",
        f"| 2: levels | 2017-anchor with-SFA recursion, 2024 | error {lookup.loc['debt_engine_with_sfa_oos', 'final_error']:+.3f} pp | absolute error <= {d2['tolerances']['debt_final_year_absolute_error_pp_gdp']['value']:g} pp | {lookup.loc['debt_engine_with_sfa_oos', 'status']} |",
        "",
        "All gate rules are lead-developer decisions dated 2026-10-21 in `config/d2_inputs_proposed.yaml`. C7 audit rows are read from `data/brazil/c7_backtest.csv`, not re-estimated.", "",
        "**Claude review (2026-10-23), fixed 2026-10-24:** the original growth-block Tier 1 check was not held out: its fixed TFP growth rate was the PWT CAGR over 2000-2019 (`config/parameters.yaml`), a window that fully contains the 2006-2019 test period, so a PASS there demonstrated internal consistency, not held-out predictive skill. That check is kept in the statistics table below as `growth_block` (`not_rated`, used only for the episode narrative), and the Tier 1 gate now rates a second statistic, `growth_block_oos`, which fixes TFP at the 1996-2005 window instead: the same equations, the same test period, but a TFP input estimated entirely before it, matching the debt one-step check (an accounting identity, no fitted parameter) and the C7 channel-A OOS check (fit 2000-2014, tested 2015-2024) in being genuinely held out.", "",
        f"The level tolerance is absolute 2024 debt error <= {d2['tolerances']['debt_final_year_absolute_error_pp_gdp']['value']:g} pp of GDP.", "",
        "## All annual test statistics", "",
        "| Block | Mean error | MAE | RMSE | Correlation | Final error | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in stats.itertuples(index=False):
        lines.append(f"| {row.test} | {row.mean_error:.3f} | {row.mae:.3f} | {row.rmse:.3f} | {row.correlation:.3f} | {row.final_error:.3f} | {row.status} |")

    largest_debt = debt.loc[debt["residual"].abs().nlargest(3).index]
    lines += [
        "", "## Debt engine", "",
        "The original cumulative recursion starts from observed 2010 gross debt. The Tesouro workbook has no 2006-2009 interest-payable observations, so no earlier implicit-rate series is invented.", "",
        "| Year | Observed debt | Simulated debt | Simulated - observed |",
        "|---:|---:|---:|---:|",
    ]
    for row in largest_debt.itertuples(index=False):
        lines.append(f"| {row.year} | {row.observed_value:.2f} | {row.predicted_value:.2f} | {row.residual:+.2f} |")
    lines += [
        "",
        f"The one-step-ahead mean error is {lookup.loc['debt_engine_one_step', 'mean_error']:+.2f} pp/year and MAE is {lookup.loc['debt_engine_one_step', 'mae']:.2f} pp. Re-anchoring each year separates equation error from accumulation.", "",
        "The textbook identity omits stock-flow adjustments, valuation/reclassification effects and repo effects. Tesouro GFS interest and BCB primary-result/gross-debt series also differ in institutional coverage and timing.", "",
        "## Stock-flow adjustment", "",
        f"SFA is observed debt minus the one-step prediction. The 2011-2017 mean is {sfa_summary['mean_2011_2017']:+.3f} pp of GDP/year and the sample SD is {sfa_summary['sd_2011_2017']:.3f} pp. Only these seven years estimate the constant applied after the observed 2017 anchor.", "",
        "| Year | Implied SFA (pp GDP) | Documented context (not fitted) |",
        "|---:|---:|---|",
    ]
    for year, value in sfa_summary["values_by_year"].items():
        context = "Treasury loans to BNDES" if year in {2011, 2012} else ("BNDES early repayments and BCB result transfers" if 2016 <= year <= 2022 else "")
        lines.append(f"| {year} | {value:+.3f} | {context} |")
    lines += [
        "",
        "The operation labels provide balance-sheet context; they are not fitted annual values. The OOS comparison recursively applies zero SFA or the fixed 2011-2017 mean during 2018-2024.", "",
        "## Growth accounting plus external block", "",
        "Observed PWT investment-derived capital accumulation, human capital and employment are used each year. TFP is fixed at the C2 central 2000-2019 rate and C6 is unchanged. This is the `growth_block` row (in-sample consistency check, `not_rated`); the episode and annual-residual tables below use it because it matches the central C2 projection. The Tier 1 gate above is rated on the separate, genuinely out-of-sample `growth_block_oos` row (TFP fixed at the pre-2006 1996-2005 window) in the statistics table that follows.", "",
        "| Episode | Actual cumulative growth | Fixed-TFP factor model | C6 addition | Model total | Model - actual |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in episodes.itertuples(index=False):
        lines.append(f"| {row.episode} ({row.period}) | {row.actual:.2f}% | {row.base:.2f}% | {row.external:+.2f} pp | {row.model:.2f}% | {row.residual:+.2f} pp |")
    largest_growth = growth.loc[growth["residual"].abs().nlargest(3).index]
    lines += ["", "The boom row measures the 2006-2010 transitions from the 2005 level; earlier ToT observations are unavailable in the D2 input.", "", "Largest annual growth residuals:", "", "| Year | Observed | Model | C6 contribution | Model - observed |", "|---:|---:|---:|---:|---:|"]
    for row in largest_growth.itertuples(index=False):
        lines.append(f"| {row.year} | {row.observed_value:.2f} | {row.predicted_value:.2f} | {row.external_contribution:+.2f} | {row.residual:+.2f} |")

    def fmt(value: float, suffix: str = "") -> str:
        return "NA" if pd.isna(value) else f"{value:+.2f}{suffix}"

    lines += [
        "", "## Period diagnostic", "",
        "Every calendar window is treated identically. Changes are end-year minus start-year values within the window; commodity prices use 100 x ln(end/start). Primary balance is sign-flipped, so positive means surplus. This is descriptive, not a causal attribution or ranking.", "",
        "| Period | Avg GDP growth | Spending/GDP change | Revenue/GDP change | Primary-balance change | Gross-debt change | Commodity log change | Implied growth | Residual |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in periods.itertuples(index=False):
        flag = " [separately flagged]" if row.separately_flagged else ""
        lines.append(
            f"| {row.period}{flag} | {fmt(row.average_real_gdp_growth_pct, '%')} | {fmt(row.primary_spending_change_pp)} pp | "
            f"{fmt(row.revenue_change_pp)} pp | {fmt(row.primary_balance_change_pp)} pp | {fmt(row.gross_debt_change_pp)} pp | "
            f"{fmt(row.commodity_price_log_change_pct, '%')} | {fmt(row.model_implied_growth_pct, '%')} | {fmt(row.model_residual_pp)} pp |"
        )
    lines += [
        "",
        "Inputs are observed annual GDP growth; Q4 general-government primary spending/GDP; revenue/GDP from workbook sheet 3.2.a code `1`; sign-flipped consolidated primary balance; gross debt; and commodity export prices. The 2019 revenue figure includes the one-off transfer-of-rights auction in concessions code 1415.", "",
        f"The flagged 2023-2025 row uses 2025 GDP growth {IBGE_2025_GROWTH:.1f}% ({IBGE_2025_GROWTH_SOURCE}) and complete 2025 spending/revenue. Debt, primary balance, commodity price, implied growth and residual are `NA` because those checked-in series stop in 2024; no value is carried forward.", "",
        "Level changes run from the last year before each period (the inherited level) to the period's last year. "
        f"Model-implied growth is the C7 `A_output_reverse` fitted value (constant {periods['trend_proxy_pct'].iloc[0]:.3f} included, world growth as a level, as estimated), plus the C2 central total-expenditure multiplier ({periods['spending_multiplier'].iloc[0]:.2f}) times annual primary-spending/GDP change. The reverse coefficients were fitted on 2010-2024, so all 2011-2024 windows are in-sample for that fit.", "",
        "Residuals mix domestic policy, credit, politics, omitted shocks and measurement. They are not attributed to governments and must not be read as rankings.", "",
        "## Multiplier diagnostic", "",
        f"The benchmark is growth minus its 2010-2024 mean ({float(results.loc[results.test.eq('multiplier_total'), 'baseline_prediction'].iloc[0]):.3f}%). Spending changes are endogenous and do not identify fiscal shocks, so this remains unrated.", "",
    ]
    for name in ("multiplier_total", "multiplier_categories"):
        lines.append(f"- `{name}`: correlation {lookup.loc[name, 'correlation']:.3f}, RMSE {lookup.loc[name, 'rmse']:.3f} pp.")
    inflation = lookup.loc["inflation_pass_through"]
    lines += [
        "", "## Inflation pass-through diagnostic", "",
        f"Observed BRL/USD pass-through is compared with IPCA minus target. Mean error is {inflation['mean_error']:+.3f} pp, RMSE {inflation['rmse']:.3f} pp and correlation {inflation['correlation']:.3f}. This incomplete one-variable diagnostic remains unrated.", "",
        "## Publication implications", "",
        "Tier 1 passes, so paired scenario differences vs S0 clear the numerical gate; this is not proof of causal validity." if gates["tier_1_differences_vs_s0"] == "PASS" else "Tier 1 fails, so scenario differences vs S0 do not clear the publication gate.",
        "Tier 2 passes with the pre-specified SFA OOS run, so debt/GDP levels clear the numerical gate subject to the documented concept limitations." if gates["tier_2_levels"] == "PASS" else "Tier 2 fails, so debt/GDP paths should not be published as model-validated levels.", "",
        "The annual audit rows are in `data/brazil/backtest_results.csv` (residual = predicted minus observed).",
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
        build_c7_gate_test(paths["c7_backtest"]),
    ], ignore_index=True)[RESULT_COLUMNS]
    if results.duplicated(["test", "year"]).any():
        raise RuntimeError("Back-test output must have one row per test/year")
    stats = statistics_table(results, d2)
    debt_inputs = debt_test_inputs(wide, paths["workbook"], paths["nominal_gdp"])
    _, sfa_summary = sfa_out_of_sample(debt_inputs)
    periods = period_diagnostic(
        wide, paths["fiscal"], paths["workbook"], paths["external_observed"],
        paths["c7_estimates"], parameters,
    )
    return results, stats, render_report(results, stats, d2, sfa_summary, periods)


def write_sfa_summary(path: str | Path, summary: Mapping) -> None:
    """Idempotently persist the reproducible SFA block for later Monte Carlo use."""
    config = _yaml(path)
    config["sfa_summary"] = {
        "definition": "observed debt minus one-step debt-engine prediction, pp GDP",
        "estimation_years": [2011, 2017],
        "mean_2011_2017": float(summary["mean_2011_2017"]),
        "sd_2011_2017": float(summary["sd_2011_2017"]),
        "sd_definition": "sample standard deviation (ddof=1)",
        "values_by_year": {int(year): float(value) for year, value in summary["values_by_year"].items()},
    }
    Path(path).write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")


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
    wide = observed_wide(DEFAULT_PATHS["observed"])
    debt_inputs = debt_test_inputs(wide, DEFAULT_PATHS["workbook"], DEFAULT_PATHS["nominal_gdp"])
    _, sfa_summary = sfa_out_of_sample(debt_inputs)
    write_sfa_summary(DEFAULT_PATHS["d2"], sfa_summary)
    print(stats.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"Wrote {len(results)} annual rows to {args.results} and {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
