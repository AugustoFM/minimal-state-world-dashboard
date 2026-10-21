"""Brazil interest-rate history, expectations, associations, and S0 proposal.

All inputs are archived raw files.  The module uses only numpy/pandas for
estimation and deterministically rebuilds the eight outputs fixed in I1.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from src.macro import read_bcb_debt_history, read_general_government_fiscal_workbook


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/brazil/rates"
PATHS = {
    "monthly": ROOT / "data/brazil/rates_monthly.csv",
    "estimates": ROOT / "data/brazil/rates_estimates.csv",
    "events": ROOT / "data/brazil/rates_events.csv",
    "report": ROOT / "outputs/rates.md",
    "docs": ROOT / "docs/rates.md",
    "config": ROOT / "config/i1_proposed.yaml",
}
FOCUS_FILES = {
    "selic": "bcb_focus_annual_selic.json",
    "ipca": "bcb_focus_annual_ipca.json",
    "primary": "bcb_focus_annual_resultado_primario.json",
    "dlsp": "bcb_focus_annual_divida_liquida_sp.json",
    "dbgg": "bcb_focus_annual_divida_bruta_gg.json",
}
Z95 = 1.959963984540054


def fisher_real_rate(nominal_pct: float | np.ndarray, inflation_pct: float | np.ndarray):
    """Return the exact Fisher real rate, in percentage points."""
    nominal = np.asarray(nominal_pct, dtype=float)
    inflation = np.asarray(inflation_pct, dtype=float)
    result = ((1.0 + nominal / 100.0) / (1.0 + inflation / 100.0) - 1.0) * 100.0
    return float(result) if result.ndim == 0 else result


def select_focus_month_end(frame: pd.DataFrame) -> pd.DataFrame:
    """Select each target year's last survey observation in every month."""
    required = {"Data", "DataReferencia", "Mediana"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Focus data lacks {sorted(required - set(frame.columns))}")
    out = frame.copy()
    out["survey_date"] = pd.to_datetime(out["Data"], errors="raise")
    out["month"] = out["survey_date"].dt.to_period("M").dt.to_timestamp()
    out["reference_year"] = pd.to_numeric(out["DataReferencia"], errors="raise").astype(int)
    out["median"] = pd.to_numeric(out["Mediana"], errors="coerce")
    out = out.dropna(subset=["median"]).sort_values("survey_date")
    out = out.groupby(["month", "reference_year"], as_index=False).tail(1)
    return out[["month", "reference_year", "survey_date", "median"]].sort_values(
        ["month", "reference_year"], ignore_index=True
    )


def align_focus_horizon(frame: pd.DataFrame, horizon: int) -> pd.Series:
    """Select observations whose reference year equals survey year + horizon."""
    expected = frame["month"].dt.year + int(horizon)
    selected = frame.loc[frame["reference_year"].eq(expected)].copy()
    return selected.set_index("month")["median"].sort_index()


def _read_json(path: Path):
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path}")


def read_sgs(path: str | Path) -> pd.Series:
    """Read an untouched SGS JSON list as a dated numeric series."""
    rows = _read_json(Path(path))
    frame = pd.DataFrame(rows)
    dates = pd.to_datetime(frame["data"], format="%d/%m/%Y", errors="raise")
    values = pd.to_numeric(frame["valor"], errors="coerce")
    return pd.Series(values.to_numpy(), index=dates, name=Path(path).stem).sort_index()


def read_focus(path: str | Path) -> pd.DataFrame:
    """Read one Focus annual-expectations archive and take month-end surveys."""
    obj = _read_json(Path(path))
    rows = obj.get("value", obj) if isinstance(obj, dict) else obj
    return select_focus_month_end(pd.DataFrame(rows))


def ols_newey_west(
    y: Sequence[float], x: Sequence[Sequence[float]], lag: int = 6
) -> dict[str, np.ndarray | float | int]:
    """OLS with Bartlett Newey-West covariance and no small-sample correction."""
    yv = np.asarray(y, dtype=float)
    xv = np.asarray(x, dtype=float)
    if yv.ndim != 1 or xv.ndim != 2 or len(yv) != len(xv):
        raise ValueError("y must be 1D and x 2D with equal row counts")
    if not np.isfinite(yv).all() or not np.isfinite(xv).all():
        raise ValueError("OLS inputs must be finite")
    nobs, nvars = xv.shape
    if nobs <= nvars or np.linalg.matrix_rank(xv) < nvars:
        raise ValueError("OLS design is rank deficient or lacks residual degrees of freedom")
    beta = np.linalg.lstsq(xv, yv, rcond=None)[0]
    residual = yv - xv @ beta
    scores = xv * residual[:, None]
    meat = scores.T @ scores
    for ell in range(1, min(int(lag), nobs - 1) + 1):
        weight = 1.0 - ell / (int(lag) + 1.0)
        gamma = scores[ell:].T @ scores[:-ell]
        meat += weight * (gamma + gamma.T)
    bread = np.linalg.inv(xv.T @ xv)
    covariance = bread @ meat @ bread
    se = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    tss = float(np.sum((yv - yv.mean()) ** 2))
    r2 = math.nan if tss == 0 else 1.0 - float(residual @ residual) / tss
    return {"beta": beta, "se": se, "covariance": covariance, "residual": residual,
            "r2": r2, "nobs": nobs}


def estimate_pass_through(frame: pd.DataFrame) -> dict[str, float | int | np.ndarray]:
    """Regress the implicit nominal debt rate on current and lagged Selic."""
    sample = frame[["implicit_nominal_rate_pct", "selic_annual_avg_pct"]].copy()
    sample["selic_lag"] = sample["selic_annual_avg_pct"].shift(1)
    sample = sample.dropna()
    x = np.column_stack([np.ones(len(sample)), sample["selic_annual_avg_pct"], sample["selic_lag"]])
    result = ols_newey_west(sample["implicit_nominal_rate_pct"].to_numpy(), x, lag=1)
    beta = np.asarray(result["beta"])
    covariance = np.asarray(result["covariance"])
    long_run = float(beta[1] + beta[2])
    long_run_se = float(np.sqrt(max(covariance[1, 1] + covariance[2, 2] + 2 * covariance[1, 2], 0)))
    result.update({
        "current": float(beta[1]), "lagged": float(beta[2]), "long_run": long_run,
        "long_run_se": long_run_se,
        "year1_share": math.nan if long_run == 0 else float(beta[1] / long_run),
        "years": sample.index.astype(int).tolist(),
    })
    return result


def _monthly_last(series: pd.Series) -> pd.Series:
    return series.resample("MS").last()


def _monthly_mean(series: pd.Series) -> pd.Series:
    return series.resample("MS").mean()


def _focus_pair_real(first: pd.DataFrame, second: pd.DataFrame, horizon: int) -> pd.Series:
    joined = pd.concat(
        [align_focus_horizon(first, horizon).rename("nominal"),
         align_focus_horizon(second, horizon).rename("inflation")], axis=1
    ).dropna()
    return pd.Series(
        fisher_real_rate(joined["nominal"].to_numpy(), joined["inflation"].to_numpy()),
        index=joined.index,
    )


def _longest_common_real(selic: pd.DataFrame, ipca: pd.DataFrame) -> pd.Series:
    rows: list[dict[str, float | pd.Timestamp]] = []
    months = sorted(set(selic["month"]) & set(ipca["month"]))
    for month in months:
        s = selic[selic["month"].eq(month)].set_index("reference_year")["median"]
        i = ipca[ipca["month"].eq(month)].set_index("reference_year")["median"]
        common = sorted(set(s.index) & set(i.index))
        if common:
            year = common[-1]
            rows.append({"month": month, "value": fisher_real_rate(s.loc[year], i.loc[year])})
    return pd.DataFrame(rows).set_index("month")["value"]


def build_monthly() -> tuple[pd.DataFrame, Mapping[str, pd.DataFrame]]:
    """Build monthly history and all end-of-month Focus transformations."""
    focus = {name: read_focus(RAW / filename) for name, filename in FOCUS_FILES.items()}
    daily_target = read_sgs(RAW / "bcb_sgs_432_selic_target_daily.json")
    ipca12 = read_sgs(RAW / "bcb_sgs_13522_ipca_12m.json")
    index = pd.date_range("2000-01-01", "2026-10-01", freq="MS")
    out = pd.DataFrame(index=index)
    out.index.name = "month"
    out["selic_target_monthly_avg_pct"] = _monthly_mean(daily_target).reindex(index)
    out["ipca_12m_pct"] = _monthly_last(ipca12).reindex(index)
    out["ex_post_real_selic_pct"] = fisher_real_rate(
        out["selic_target_monthly_avg_pct"], out["ipca_12m_pct"]
    )
    for horizon, name in [(1, "ex_ante_real_t1_pct"), (2, "medium_real_t2_pct"),
                          (3, "medium_real_t3_pct")]:
        out[name] = _focus_pair_real(focus["selic"], focus["ipca"], horizon).reindex(index)
    out["medium_real_longest_pct"] = _longest_common_real(
        focus["selic"], focus["ipca"]
    ).reindex(index)
    out["primary_balance_t2_pct_gdp"] = align_focus_horizon(focus["primary"], 2).reindex(index)
    out["dlsp_t3_pct_gdp"] = align_focus_horizon(focus["dlsp"], 3).reindex(index)
    out["dbgg_t3_pct_gdp"] = align_focus_horizon(focus["dbgg"], 3).reindex(index)
    dgs = pd.read_csv(ROOT / "data/raw/brazil/external/fred_DGS10.csv")
    dgs["observation_date"] = pd.to_datetime(dgs["observation_date"])
    dgs["DGS10"] = pd.to_numeric(dgs["DGS10"], errors="coerce")
    out["us_10y_pct"] = _monthly_last(dgs.set_index("observation_date")["DGS10"]).reindex(index)
    embi_obj = _read_json(ROOT / "data/raw/brazil/external/ipeadata_JPM366_EMBI366.json")
    embi = pd.DataFrame(embi_obj["value"])
    embi["date"] = pd.to_datetime(embi["VALDATA"], utc=True).dt.tz_convert(None)
    embi["value"] = pd.to_numeric(embi["VALVALOR"], errors="coerce")
    out["embi_brazil_bp"] = _monthly_last(embi.set_index("date")["value"]).reindex(index)
    return out.reset_index(), focus


def _estimate_model(
    data: pd.DataFrame, specification: str, dependent: str, regressors: list[str],
    start: str, end: str, differences: bool, trend: bool = False, lag: int = 6,
) -> list[dict[str, object]]:
    columns = [dependent, *regressors]
    sample = data.set_index("month").loc[start:end, columns].copy()
    if differences:
        sample = sample.diff()
    sample = sample.dropna()
    xparts = [np.ones(len(sample))]
    terms = ["constant"]
    if trend:
        xparts.append(np.arange(len(sample), dtype=float))
        terms.append("trend")
    xparts.extend(sample[column].to_numpy() for column in regressors)
    terms.extend(regressors)
    x = np.column_stack(xparts)
    result = ols_newey_west(sample[dependent].to_numpy(), x, lag=lag)
    rows = []
    for term, estimate, se in zip(terms, result["beta"], result["se"]):
        rows.append({
            "analysis": "fiscal_expectations", "specification": specification,
            "term": term, "estimate": float(estimate), "std_error": float(se),
            "ci95_low": float(estimate - Z95 * se), "ci95_high": float(estimate + Z95 * se),
            "unit": "percentage points per percentage point",
            "nobs": int(result["nobs"]), "r2": float(result["r2"]),
            "start": sample.index.min().date().isoformat(),
            "end": sample.index.max().date().isoformat(), "nw_lags": lag,
        })
    return rows


def _annual_pass_through_data(monthly: pd.DataFrame) -> pd.DataFrame:
    daily = read_sgs(RAW / "bcb_sgs_432_selic_target_daily.json")
    selic = daily.groupby(daily.index.year).mean()
    debt_path = RAW / "bcb_sgs_13762_dbgg_pct_gdp.json"
    debt = read_bcb_debt_history(debt_path, range(2009, 2026))
    records = []
    workbook = ROOT / "data/raw/brazil/demonstrativos-governo-geral.xlsx"
    ipca = read_sgs(RAW / "bcb_sgs_433_ipca_monthly.json")
    for year in range(2010, 2026):
        interest = float(read_general_government_fiscal_workbook(workbook, year)["interest_payable_gdp"])
        average_debt = (debt[year - 1] + debt[year]) / 2.0
        nominal = interest / average_debt * 100.0
        inflation_values = ipca[ipca.index.year == year].dropna()
        annual_ipca = (np.prod(1.0 + inflation_values.to_numpy() / 100.0) - 1.0) * 100.0
        records.append({"year": year, "interest_payable_pct_gdp": interest,
                        "average_debt_pct_gdp": average_debt,
                        "implicit_nominal_rate_pct": nominal,
                        "annual_ipca_pct": annual_ipca,
                        "implicit_real_rate_pct": fisher_real_rate(nominal, annual_ipca),
                        "selic_annual_avg_pct": float(selic.loc[year])})
    return pd.DataFrame(records).set_index("year")


def build_estimates(monthly: pd.DataFrame) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Estimate the fixed fiscal-expectations and pass-through specifications."""
    primary_regs = ["primary_balance_t2_pct_gdp", "dlsp_t3_pct_gdp", "us_10y_pct"]
    rows = _estimate_model(monthly, "primary_differences_2010_2026m09",
                           "medium_real_t3_pct", primary_regs,
                           "2010-01-01", "2026-09-01", True)
    rows += _estimate_model(monthly, "robustness_levels_trend",
                            "medium_real_t3_pct", primary_regs,
                            "2010-01-01", "2026-09-01", False, trend=True)
    rows += _estimate_model(monthly, "robustness_differences_2017_2026m09",
                            "medium_real_t3_pct", primary_regs,
                            "2017-01-01", "2026-09-01", True)
    rows += _estimate_model(monthly, "robustness_dbgg_differences_2018_2026m09",
                            "medium_real_t3_pct",
                            ["primary_balance_t2_pct_gdp", "dbgg_t3_pct_gdp", "us_10y_pct"],
                            "2018-01-01", "2026-09-01", True)
    rows += _estimate_model(monthly, "robustness_embi_differences_to_2024m06",
                            "medium_real_t3_pct", [*primary_regs, "embi_brazil_bp"],
                            "2010-01-01", "2024-06-01", True)
    annual = _annual_pass_through_data(monthly)
    passthrough = estimate_pass_through(annual)
    beta = np.asarray(passthrough["beta"])
    se = np.asarray(passthrough["se"])
    for term, estimate, stderr in zip(["constant", "selic_current", "selic_lag"], beta, se):
        rows.append({"analysis": "debt_pass_through", "specification": "primary_2010_2025",
                     "term": term, "estimate": float(estimate), "std_error": float(stderr),
                     "ci95_low": float(estimate - Z95 * stderr),
                     "ci95_high": float(estimate + Z95 * stderr),
                     "unit": "percentage points per percentage point", "nobs": int(passthrough["nobs"]),
                     "r2": float(passthrough["r2"]), "start": "2010", "end": "2025", "nw_lags": 1})
    for term, estimate, stderr, unit in [
        ("long_run_pass_through", passthrough["long_run"], passthrough["long_run_se"],
         "percentage points per percentage point"),
        ("year1_share", passthrough["year1_share"], math.nan, "share of long-run pass-through"),
    ]:
        rows.append({"analysis": "debt_pass_through", "specification": "derived_2010_2025",
                     "term": term, "estimate": float(estimate), "std_error": float(stderr),
                     "ci95_low": float(estimate - Z95 * stderr) if math.isfinite(stderr) else math.nan,
                     "ci95_high": float(estimate + Z95 * stderr) if math.isfinite(stderr) else math.nan,
                     "unit": unit, "nobs": int(passthrough["nobs"]),
                     "r2": float(passthrough["r2"]), "start": "2010", "end": "2025", "nw_lags": 1})
    return pd.DataFrame(rows), passthrough, annual


EVENTS = [
    ("EC 95 spending cap", "2016-12-01"),
    ("Pension reform final approval", "2019-10-01"),
    ("PEC da Transicao", "2022-12-01"),
    ("LC 200 approval", "2023-08-01"),
    ("Fiscal package (Nov-Dec 2024)", "2024-11-01"),
    ("2026 first round", "2026-10-01"),
]


def build_events(monthly: pd.DataFrame) -> pd.DataFrame:
    """Compute fixed before-to-two-month-after descriptive event changes."""
    data = monthly.set_index("month")
    rows = []
    columns = ["medium_real_t3_pct", "primary_balance_t2_pct_gdp", "dlsp_t3_pct_gdp"]
    for label, date in EVENTS:
        event = pd.Timestamp(date)
        before = event - pd.offsets.MonthBegin(1)
        intended_after = event + pd.offsets.MonthBegin(2)
        available = data.index[data.index <= intended_after]
        after = available.max() if len(available) else pd.NaT
        partial = bool(after < intended_after)
        row: dict[str, object] = {"event": label, "event_month": event.date().isoformat(),
                                 "from_month": before.date().isoformat(),
                                 "to_month": after.date().isoformat(), "partial_window": partial}
        for column in columns:
            row[f"{column}_from"] = data.at[before, column]
            row[f"{column}_to"] = data.at[after, column]
            row[f"change_{column}"] = data.at[after, column] - data.at[before, column]
        rows.append(row)
    return pd.DataFrame(rows)


def _latest_focus_year(focus: Mapping[str, pd.DataFrame], name: str, year: int) -> float:
    frame = focus[name]
    rows = frame[frame["reference_year"].eq(year)].sort_values("survey_date")
    if rows.empty:
        raise ValueError(f"No latest Focus {name} value for {year}")
    return float(rows.iloc[-1]["median"])


def build_proposal(
    focus: Mapping[str, pd.DataFrame], estimates: pd.DataFrame,
    passthrough: Mapping[str, object], annual: pd.DataFrame,
) -> dict:
    """Construct the proposal-only 2026-2045 S0 rate path and fiscal formula."""
    policy: dict[int, float] = {}
    focus_inputs: dict[int, dict[str, float]] = {}
    for year in range(2026, 2030):
        selic = _latest_focus_year(focus, "selic", year)
        ipca = _latest_focus_year(focus, "ipca", year)
        policy[year] = fisher_real_rate(selic, ipca)
        focus_inputs[year] = {"selic_pct": selic, "ipca_pct": ipca,
                              "real_policy_pct": policy[year]}
    last = policy[2029]
    for step, year in enumerate(range(2030, 2035), start=1):
        policy[year] = last + (5.0 - last) * step / 5.0
    for year in range(2035, 2046):
        policy[year] = 5.0
    b0 = float(passthrough["current"])
    b1 = float(passthrough["lagged"])
    anchor = float(annual.loc[2025, "implicit_real_rate_pct"])
    policy_2025 = fisher_real_rate(float(annual.loc[2025, "selic_annual_avg_pct"]),
                                   float(annual.loc[2025, "annual_ipca_pct"]))
    policy_2024 = fisher_real_rate(float(annual.loc[2024, "selic_annual_avg_pct"]),
                                   float(annual.loc[2024, "annual_ipca_pct"]))
    implicit: dict[int, float] = {}
    previous_implicit = anchor
    previous_policy = policy_2025
    twice_previous_policy = policy_2024
    for year in range(2026, 2046):
        value = (previous_implicit + b0 * (policy[year] - previous_policy)
                 + b1 * (previous_policy - twice_previous_policy))
        implicit[year] = value
        previous_implicit = value
        twice_previous_policy = previous_policy
        previous_policy = policy[year]
    primary = estimates[(estimates["specification"] == "primary_differences_2010_2026m09") &
                        (estimates["term"] == "dlsp_t3_pct_gdp")].iloc[0]
    anchor_debt = float(read_bcb_debt_history(
        RAW / "bcb_sgs_13762_dbgg_pct_gdp.json", [2025]
    )[2025])
    return {
        "task": "I1", "status": "proposal_only_not_read_by_model",
        "long_run_real_policy_rate_pct": {"central": 5.0, "low": 4.5, "high": 6.0,
            "source": "BCB neutral-rate estimate and review range; see docs/interest_rates_review.md"},
        "focus_inputs_latest_survey": focus_inputs,
        "pass_through": {
            "current_year": b0, "lagged_year": b1,
            "long_run": float(passthrough["long_run"]),
            "year1_share": float(passthrough["year1_share"]),
            "sample": "2010-2025, n=15 after the Selic lag",
            "derivation": "implicit nominal rate = interest payable / average current-prior December DBGG; OLS on current and lagged annual-average Selic",
        },
        "anchors": {"year": 2025, "implicit_real_rate_pct": anchor,
                    "real_policy_rate_pct": policy_2025,
                    "prior_year_real_policy_rate_pct": policy_2024,
                    "s0_debt_pct_gdp": anchor_debt,
                    "fixed_model_comparator_pct": 5.05},
        "fiscal_term": {
            "coefficient_real_rate_pp_per_debt_pp": float(primary["estimate"]),
            "ci95_low": float(primary["ci95_low"]), "ci95_high": float(primary["ci95_high"]),
            "formula": "coefficient * (scenario_expected_debt_pct_gdp - 2025_S0_debt_pct_gdp)",
            "application": "identical equation and coefficient for every scenario; association, not causal",
            "debt_measure_note": "The estimated coefficient uses Focus expected DLSP because the fixed primary specification requires it, while the scenario anchor is DBGG; this concept mismatch is flagged and should be tested with the DBGG robustness estimate.",
        },
        "s0_path_before_fiscal_term": [
            {"year": year, "real_policy_rate_pct": policy[year],
             "implicit_real_debt_rate_pct": implicit[year],
             "difference_from_fixed_5_05_pp": implicit[year] - 5.05}
            for year in range(2026, 2046)
        ],
        "path_derivation": "2026-2029 latest Focus Fisher real rates; 2030-2034 five equal annual steps to 5%; thereafter 5%. Starting from the 2025 implicit real debt rate, annual changes apply current and lagged pass-through to current and lagged changes in the real-policy rate; the 2026 lag uses observed 2024-2025 rates.",
    }


def _fmt(value: float, digits: int = 2) -> str:
    return "NA" if pd.isna(value) else f"{value:.{digits}f}"


def _markdown(frame: pd.DataFrame, digits: int = 2) -> list[str]:
    show = frame.copy()
    for column in show.select_dtypes(include="number"):
        show[column] = show[column].map(lambda value: _fmt(value, digits))
    headers = [str(column) for column in show.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in show.itertuples(index=False, name=None))
    return lines


def render_report(monthly: pd.DataFrame, estimates: pd.DataFrame, events: pd.DataFrame,
                  proposal: Mapping, annual: pd.DataFrame) -> str:
    latest_target = float(read_sgs(RAW / "bcb_sgs_432_selic_target_daily.json").iloc[-1])
    latest_ipca = float(monthly["ipca_12m_pct"].dropna().iloc[-1])
    current_real = fisher_real_rate(latest_target, latest_ipca)
    history = monthly["ex_post_real_selic_pct"].dropna()
    p_all = float((history <= current_real).mean() * 100)
    p_2010 = float((history[history.index >= monthly.index[monthly["month"].eq(pd.Timestamp("2010-01-01"))][0]] <= current_real).mean() * 100)
    primary = estimates[estimates["specification"].eq("primary_differences_2010_2026m09")]
    pb = primary[primary["term"].eq("primary_balance_t2_pct_gdp")].iloc[0]
    debt = primary[primary["term"].eq("dlsp_t3_pct_gdp")].iloc[0]
    pt = estimates[(estimates["analysis"] == "debt_pass_through") &
                   estimates["term"].isin(["selic_current", "selic_lag", "long_run_pass_through", "year1_share"])]
    path = pd.DataFrame(proposal["s0_path_before_fiscal_term"])
    path["year"] = path["year"].astype(str)
    event_show = events[["event", "from_month", "to_month", "partial_window",
                         "change_medium_real_t3_pct", "change_primary_balance_t2_pct_gdp",
                         "change_dlsp_t3_pct_gdp"]].copy()
    lines = [
        "# Brazil interest rates and an evidence-based S0 proposal", "",
        "## Current position", "",
        f"On 21 October 2026 the Selic target was {_fmt(latest_target)}%. Paired with the latest available 12-month IPCA ({_fmt(latest_ipca)}%, September), the Fisher ex-post real rate was {_fmt(current_real)}%. This snapshot was at the {_fmt(p_all, 1)}th percentile of monthly observations since 2000 and the {_fmt(p_2010, 1)}th percentile since 2010. The mixed-date snapshot is shown explicitly; the monthly CSV leaves October ex-post real Selic missing until October inflation exists.", "",
        "The primary medium-term market measure is the Focus expectation for Selic relative to IPCA for calendar year t+3. The CSV also reports t+2 and the longest common Focus horizon as labelled robustness measures.", "",
        "## Fiscal-expectations association", "",
        f"In the fixed monthly first-difference specification through September 2026 (n={int(pb['nobs'])}), a one-percentage-point improvement in the expected primary balance was associated with {_fmt(pb['estimate'] * 100)} basis points in the t+3 expected real rate (95% interval {_fmt(pb['ci95_low'] * 100)} to {_fmt(pb['ci95_high'] * 100)}). A one-point increase in expected DLSP was associated with {_fmt(debt['estimate'] * 100)} basis points (95% interval {_fmt(debt['ci95_low'] * 100)} to {_fmt(debt['ci95_high'] * 100)}). These are market associations, not causal effects.", "",
        "All primary and robustness coefficients, including levels with trend, the 2017 start, DBGG from 2018, and EMBI through June 2024, are in `data/brazil/rates_estimates.csv`. Robustness results are labelled and do not replace the fixed primary specification.", "",
        "## Descriptive event windows", "",
        "Changes run from the month before the event to two months after. The October 2026 window is partial and ends at the last archived observation. These windows describe co-movement and do not isolate event effects.", "",
        *_markdown(event_show, 3), "",
        "## Pass-through to the debt", "",
        f"The annual regression uses 2010-2025 fiscal observations and has {int(pt.iloc[0]['nobs'])} usable rows after the lag. The long-run pass-through is {_fmt(float(pt.loc[pt.term.eq('long_run_pass_through'), 'estimate'].iloc[0]), 3)} points of the implicit nominal debt rate per one-point Selic change. The current-year coefficient is {_fmt(float(pt.loc[pt.term.eq('selic_current'), 'estimate'].iloc[0]), 3)}, or {_fmt(float(pt.loc[pt.term.eq('year1_share'), 'estimate'].iloc[0]) * 100, 1)}% of the long-run response. This is a small annual sample and the coefficients are imprecise.", "",
        "The implicit rate divides general-government interest payable by the average of current and prior December DBGG, as fixed in I1. Annual source-derived inputs are not separately written because they are intermediate calculations.", "",
        "## Proposed S0 real-rate path", "",
        f"The 2025 implicit real debt-rate anchor is {_fmt(proposal['anchors']['implicit_real_rate_pct'])}%. Focus determines 2026-2029; the real policy rate then converges in five annual steps to 5.0%. Before the fiscal term, the proposed implicit real debt rate is {_fmt(path.iloc[0]['implicit_real_debt_rate_pct'])}% in 2026, {_fmt(path[path.year.eq('2030')].iloc[0]['implicit_real_debt_rate_pct'])}% in 2030, and {_fmt(path.iloc[-1]['implicit_real_debt_rate_pct'])}% in 2045, versus the current fixed 5.05% assumption.", "",
        "The fiscal term is the primary DLSP coefficient multiplied by scenario expected debt minus the 2025 S0 debt anchor, with the same equation for every scenario. It is not included in the table below because I1 does not prescribe scenario debt paths and model files may not be changed. The DLSP-estimation/DBGG-scenario concept mismatch is a data limitation; the DBGG estimate is retained as robustness.", "",
        *_markdown(path.loc[path.year.isin([str(year) for year in [2026, 2027, 2028, 2029, 2030, 2034, 2035, 2045]])], 3), "",
        "## Data problems and interpretation", "",
        "Focus begins in 2010, and DBGG expectations begin only in 2018. October 2026 is incomplete (last Focus survey 16 October); observed inflation and debt stocks end in September and August respectively. EMBI ends in June 2024. US yields use the last available daily observation in each month. The event design uses overlapping macro news and cannot identify effects. Expected DLSP and scenario DBGG are different debt concepts. The pass-through regression has only 15 usable observations. No missing value is interpolated.",
    ]
    return "\n".join(lines)


def render_docs() -> str:
    return "\n".join([
        "# I1 interest-rate method", "",
        "`python -m src.rates` reads archived files only and deterministically rebuilds the monthly data, estimates, event table, report, method note, and proposal YAML.", "",
        "## Transformations", "",
        "The monthly Selic is the calendar-month average of daily target observations. Twelve-month IPCA is SGS 13522. Real rates use the exact Fisher formula `((1+n/100)/(1+pi/100)-1)*100`. For every Focus indicator/reference-year pair, the observation with the latest survey date in the month is retained. Horizons are calendar-year alignments: t+h means reference year equals survey year plus h. No value is carried or interpolated.", "",
        "The primary medium-term expected real rate pairs t+3 Selic and IPCA. The t+2 and longest common reference year are robustness measures. The next-calendar-year pair is the ex-ante one-year measure. Daily US 10-year and EMBI data use the last non-missing observation in each month because the regressions compare end-of-month Focus snapshots.", "",
        "## Estimation", "",
        "The fixed primary regression uses monthly first differences from January 2010 through September 2026 and an intercept. Regressors are t+2 expected primary balance, t+3 expected DLSP, and the US 10-year yield. OLS and Bartlett Newey-West covariance with six lags are implemented in numpy without a finite-sample correction. Robustness specifications use levels plus a linear trend, a 2017 start, DBGG from 2018, and EMBI through June 2024. Coefficients are associations, not causal estimates.", "",
        "The event table subtracts the month-before value from the two-month-after value. The fiscal-package event is dated November 2024, so its fixed window is October 2024 to January 2025. The October 2026 event is explicitly partial and ends at the last available month.", "",
        "Annual implicit nominal interest equals interest payable as a share of GDP divided by average current/prior December DBGG. It is regressed on current and lagged calendar-year average Selic for 2010-2025. Long-run pass-through is the sum of the two slopes; year-one share is the current slope divided by that sum. Newey-West uses one lag. Annual IPCA compounds the 12 monthly SGS 433 changes, and the 2025 implicit real anchor uses Fisher.", "",
        "## Proposal", "",
        "The proposed real-policy path uses the latest archived Focus medians for 2026-2029, five equal annual steps from the 2029 value to the 5% neutral rate in 2034, and 5% thereafter. Starting from the observed 2025 implicit real debt rate, each annual change applies the estimated current and lagged coefficients to current and lagged real-policy-rate changes; 2026 therefore uses the observed 2024-2025 lagged change. The YAML preserves the neutral range 4.5-6.0 and the primary fiscal coefficient with its confidence interval. The fiscal term is formula-only because scenario debt paths are outside I1.", "",
        "## Limitations", "",
        "Focus coverage begins in 2010 and DBGG expectations in 2018. October 2026 is partial. EMBI stops in June 2024. Expected DLSP is not the same concept as scenario DBGG. First differences can be noisy; the regressions are short and observational. Pass-through uses only 15 lag-complete annual observations and may combine maturity, composition, inflation, and valuation effects. The neutral-rate range comes from the separate review, not these regressions. Event windows contain all contemporaneous news and support no causal attribution.",
    ])


def run() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str, dict]:
    monthly, focus = build_monthly()
    estimates, passthrough, annual = build_estimates(monthly)
    events = build_events(monthly)
    proposal = build_proposal(focus, estimates, passthrough, annual)
    report = render_report(monthly, estimates, events, proposal, annual)
    return monthly, estimates, events, report, render_docs(), proposal


def main() -> int:
    monthly, estimates, events, report, docs, proposal = run()
    for key, frame in [("monthly", monthly), ("estimates", estimates), ("events", events)]:
        PATHS[key].parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(PATHS[key], index=False, float_format="%.10f")
    PATHS["report"].write_text(report, encoding="utf-8")
    PATHS["docs"].write_text(docs, encoding="utf-8")
    with PATHS["config"].open("w", encoding="utf-8", newline="\n") as handle:
        yaml.safe_dump(proposal, handle, sort_keys=False, allow_unicode=True)
    print(f"Wrote {len(monthly)} months, {len(estimates)} estimates, and {len(events)} events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
