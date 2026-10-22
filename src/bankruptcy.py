"""Firm distress, firm exits, and interest-rate associations for Brazil.

The command ``python -m src.bankruptcy`` rebuilds every BK output from archived
inputs.  Estimation uses NumPy OLS and the Bartlett Newey-West implementation
in :mod:`src.rates`; no network access or model wiring is required.
"""

from __future__ import annotations

import json
import math
import unicodedata
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import yaml

from src.rates import Z95, ols_newey_west


ROOT = Path(__file__).resolve().parents[1]
RAW_BK = ROOT / "data/raw/brazil/bankruptcy"
RAW_FIRMS = ROOT / "data/raw/brazil/firms"
PATHS = {
    "monthly": ROOT / "data/brazil/firm_distress_monthly.csv",
    "annual": ROOT / "data/brazil/firm_distress_annual.csv",
    "estimates": ROOT / "data/brazil/bankruptcy_estimates.csv",
    "config": ROOT / "config/bk_proposed.yaml",
    "report": ROOT / "outputs/bankruptcy.md",
    "docs": ROOT / "docs/bankruptcy.md",
}
IPEA_FILES = {
    "firm_npl_total_pct": "ipeadata_BM12_CINPJ12.json",
    "firm_npl_free_pct": "ipeadata_BM12_CRLINPJ12.json",
    "firm_lending_rate_total_pct": "ipeadata_BM12_CTJPJ12.json",
    "firm_lending_rate_free_pct": "ipeadata_BM12_CRLTJPJ12.json",
    "firm_spread_total_pp": "ipeadata_BM12_CSDPJ12.json",
    "firm_spread_free_pp": "ipeadata_BM12_CRLSDPJ12.json",
    "ibc_br_sa_index": "ipeadata_SGS12_IBCBRDESSAZ12.json",
}
PANDEMIC_START = pd.Timestamp("2020-03-01")
PANDEMIC_END = pd.Timestamp("2021-12-01")


def read_ipeadata(path: str | Path, name: str | None = None) -> pd.Series:
    """Parse an untouched Ipeadata OData JSON into a monthly numeric series."""
    obj = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    rows = obj.get("value", obj) if isinstance(obj, dict) else obj
    frame = pd.DataFrame(rows)
    if not {"VALDATA", "VALVALOR"}.issubset(frame.columns):
        raise ValueError("Ipeadata input must contain VALDATA and VALVALOR")
    dates = pd.to_datetime(frame["VALDATA"], utc=True, errors="raise").dt.tz_convert(None)
    dates = dates.dt.to_period("M").dt.to_timestamp()
    values = pd.to_numeric(frame["VALVALOR"], errors="coerce")
    result = pd.Series(values.to_numpy(), index=dates, name=name or Path(path).stem)
    return result.groupby(level=0).last().sort_index()


def _plain(value: object) -> str:
    text = str(value).strip().lower()
    return "".join(
        char for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )


def read_sidra_events(path: str | Path) -> pd.DataFrame:
    """Parse SIDRA v3 event series; columns are normalized event labels."""
    obj = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    variables = obj if isinstance(obj, list) else [obj]
    rows: list[dict[str, object]] = []
    for variable in variables:
        for result in variable.get("resultados", []):
            categories: list[str] = []
            for classification in result.get("classificacoes", []):
                categories.extend(str(v) for v in classification.get("categoria", {}).values())
            event = categories[0] if categories else "unknown"
            for series in result.get("series", []):
                for year, value in series.get("serie", {}).items():
                    rows.append({"year": int(year), "event": event, "value": pd.to_numeric(value, errors="coerce")})
    if not rows:
        raise ValueError(f"No SIDRA event rows in {path}")
    long = pd.DataFrame(rows)
    long["event_key"] = long["event"].map(_plain)
    out = long.pivot_table(index="year", columns="event_key", values="value", aggfunc="first")
    out.columns.name = None
    return out.sort_index()


def twelve_month_changes(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Add exact 12-row changes, preserving monthly alignment and missingness."""
    out = frame.copy()
    for column in columns:
        out[f"d12_{column}"] = out[column] - out[column].shift(12)
    return out


def exclude_pandemic(frame: pd.DataFrame, date_column: str = "month") -> pd.DataFrame:
    """Exclude March 2020 through December 2021, inclusive."""
    dates = pd.to_datetime(frame[date_column]) if date_column in frame else pd.to_datetime(frame.index)
    keep = ~((dates >= PANDEMIC_START) & (dates <= PANDEMIC_END))
    return frame.loc[np.asarray(keep)].copy()


def cumulative_response(
    beta: Sequence[float], covariance: Sequence[Sequence[float]], indices: Sequence[int]
) -> tuple[float, float, float, float]:
    """Return a coefficient sum, its delta-method SE, and normal 95% CI."""
    coefficients = np.asarray(beta, dtype=float)
    cov = np.asarray(covariance, dtype=float)
    idx = np.asarray(indices, dtype=int)
    estimate = float(coefficients[idx].sum())
    variance = float(cov[np.ix_(idx, idx)].sum())
    se = math.sqrt(max(variance, 0.0))
    return estimate, se, estimate - Z95 * se, estimate + Z95 * se


def read_serasa(path: str | Path) -> pd.DataFrame:
    """Read monthly CNPJ totals and sector detail from the Serasa workbook."""
    total = pd.read_excel(path, sheet_name="Total de CNPJs", header=None)
    total = total.iloc[5:, :7].copy()
    total.columns = [
        "month", "serasa_bankruptcy_requested_cnpjs", "serasa_bankruptcy_decreed_cnpjs",
        "serasa_rj_requested_cnpjs", "serasa_rj_granted_cnpjs",
        "serasa_rj_approved_cnpjs", "serasa_re_requested_cnpjs",
    ]
    total["month"] = pd.to_datetime(total["month"], errors="coerce")
    total = total.dropna(subset=["month"])
    for column in total.columns[1:]:
        total[column] = pd.to_numeric(total[column], errors="coerce")

    sector = pd.read_excel(path, sheet_name="Total de CNPJs Setor", header=None)
    sector = sector.iloc[5:, :27].copy()
    sector[0] = pd.to_datetime(sector[0], errors="coerce")
    sector = sector.dropna(subset=[0]).set_index(0)
    sectors = ["commerce", "industry", "services", "agriculture"]
    # The workbook groups four sectors plus a total for each legal event.
    groups = {
        "bankruptcy_requested": 1,
        "bankruptcy_decreed": 6,
        "rj_requested": 11,
        "rj_granted": 16,
        "rj_approved": 21,
    }
    details = pd.DataFrame(index=sector.index)
    for event, start in groups.items():
        for offset, label in enumerate(sectors):
            details[f"serasa_{event}_{label}_cnpjs"] = pd.to_numeric(
                sector[start + offset], errors="coerce"
            )
    return total.set_index("month").join(details, how="left").reset_index()


def read_serasa_annual(path: str | Path) -> pd.DataFrame:
    """Read sparse annual Serasa observations without altering method flags."""
    frame = pd.read_csv(path)
    required = {"year", "falencias_requeridas", "rj_requeridas", "basis", "source_url"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Annual Serasa input lacks {sorted(required - set(frame.columns))}")
    return frame.rename(columns={
        "falencias_requeridas": "serasa_bankruptcy_requested_annual",
        "rj_requeridas": "serasa_rj_requested_annual", "basis": "serasa_method",
        "source_url": "serasa_source_url",
    })


def build_monthly() -> pd.DataFrame:
    """Build the complete monthly distress panel, March 2011-August 2026."""
    series = {
        name: read_ipeadata(RAW_BK / filename, name)
        for name, filename in IPEA_FILES.items()
    }
    index = pd.date_range("2011-03-01", "2026-08-01", freq="MS")
    out = pd.DataFrame(index=index)
    out.index.name = "month"
    for name, values in series.items():
        out[name] = values.reindex(index)

    rates = pd.read_csv(ROOT / "data/brazil/rates_monthly.csv", parse_dates=["month"])
    rates = rates.set_index("month")
    rate_columns = [
        "selic_target_monthly_avg_pct", "ex_post_real_selic_pct", "ex_ante_real_t1_pct"
    ]
    out = out.join(rates[rate_columns], how="left")
    out["log_ibc_br_sa_x100"] = np.log(out["ibc_br_sa_index"]) * 100.0
    change_columns = [
        "firm_npl_total_pct", "firm_npl_free_pct", "firm_lending_rate_free_pct",
        "selic_target_monthly_avg_pct", "ex_ante_real_t1_pct", "log_ibc_br_sa_x100",
    ]
    out = twelve_month_changes(out, change_columns)
    serasa = read_serasa(RAW_BK / "serasa_falencias-e-recuperacoes-mai26.xlsx").set_index("month")
    out = out.join(serasa, how="left")
    return out.reset_index()


def _event_column(frame: pd.DataFrame, words: Sequence[str]) -> str:
    matches = [column for column in frame if all(word in column for word in words)]
    if len(words) == 1 and words[0] in matches:
        return words[0]
    if len(matches) != 1:
        raise ValueError(f"Expected one SIDRA column containing {words}; found {matches}")
    return matches[0]


def _gdp_growth() -> pd.Series:
    observed = pd.read_csv(ROOT / "data/brazil/backtest_observed.csv")
    rows = observed.loc[observed["indicator"].eq("gdp_growth_pct"), ["year", "value"]]
    return rows.set_index("year")["value"].astype(float)


def build_annual(monthly: pd.DataFrame) -> pd.DataFrame:
    """Build 2008-2025 firm-event, credit, rate, activity, and Serasa panel."""
    firms = read_sidra_events(RAW_FIRMS / "ibge_sidra_2718_firm_events_BR.json")
    employers = read_sidra_events(RAW_FIRMS / "ibge_sidra_9924_employer_events_BR.json")
    firm_active = _event_column(firms, ["total de empresas ativas"])
    firm_birth = _event_column(firms, ["nascimento"])
    firm_entry = _event_column(firms, ["entrada"])
    firm_exit = _event_column(firms, ["saida"])
    employer_active = _event_column(employers, ["ativas"])
    employer_birth = _event_column(employers, ["nascimento"])
    employer_death = _event_column(employers, ["morte"])

    out = pd.DataFrame(index=pd.Index(range(2008, 2026), name="year"))
    out["active_firms"] = firms[firm_active]
    out["firm_births"] = firms[firm_birth]
    out["firm_entries"] = firms[firm_entry]
    out["firm_exits"] = firms[firm_exit]
    out["firm_birth_rate_pct"] = out["firm_births"] / out["active_firms"] * 100.0
    out["firm_entry_rate_pct"] = out["firm_entries"] / out["active_firms"] * 100.0
    out["firm_exit_rate_pct"] = out["firm_exits"] / out["active_firms"] * 100.0
    out["active_employer_firms"] = employers[employer_active]
    out["employer_births"] = employers[employer_birth]
    out["employer_deaths"] = employers[employer_death]
    out["employer_birth_rate_pct"] = out["employer_births"] / out["active_employer_firms"] * 100.0
    out["employer_death_rate_pct"] = out["employer_deaths"] / out["active_employer_firms"] * 100.0

    month = monthly.copy()
    month["year"] = pd.to_datetime(month["month"]).dt.year
    means = month.groupby("year")[[
        "firm_npl_total_pct", "firm_npl_free_pct", "ex_ante_real_t1_pct",
        "ex_post_real_selic_pct", "selic_target_monthly_avg_pct",
    ]].mean().add_prefix("annual_mean_")
    out = out.join(means)
    # Rate lags use all archived monthly observations so 2008 retains a 2007 lag.
    rates = pd.read_csv(ROOT / "data/brazil/rates_monthly.csv", parse_dates=["month"])
    rate_year = rates.groupby(rates["month"].dt.year)["ex_post_real_selic_pct"].mean()
    out["annual_mean_ex_post_real_selic_pct"] = out.index.map(rate_year)
    out["annual_mean_ex_post_real_selic_lag1_pct"] = out.index.map(rate_year.shift(1))
    out["real_gdp_growth_pct"] = _gdp_growth()

    serasa = read_serasa_annual(
        RAW_BK / "serasa_annual_press_releases_2026-10-22.csv"
    ).set_index("year")
    out = out.join(serasa)
    return out.reset_index()


def _row(
    analysis: str, specification: str, term: str, estimate: float, se: float,
    result: dict, sample: pd.DataFrame, unit: str, horizon: float = math.nan,
    note: str = "",
) -> dict[str, object]:
    return {
        "analysis": analysis, "specification": specification, "term": term,
        "horizon_months": horizon, "estimate": estimate, "std_error": se,
        "ci95_low": estimate - Z95 * se, "ci95_high": estimate + Z95 * se,
        "unit": unit, "nobs": int(result["nobs"]), "r2": float(result["r2"]),
        "start": pd.to_datetime(sample.index.min()).date().isoformat() if analysis != "annual" else int(sample.index.min()),
        "end": pd.to_datetime(sample.index.max()).date().isoformat() if analysis != "annual" else int(sample.index.max()),
        "nw_lags": 18 if analysis in {"monthly", "local_projection"} else 1,
        "note": note,
    }


def estimate_monthly(
    monthly: pd.DataFrame, rate_column: str = "d12_ex_ante_real_t1_pct",
    specification: str = "primary_real_rate", omit_pandemic: bool = False,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Estimate the fixed distributed-lag monthly NPL specification."""
    data = monthly.set_index("month").copy()
    rate_terms = []
    for lag in (0, 6, 12, 18):
        name = f"{rate_column}_lag{lag}"
        data[name] = data[rate_column].shift(lag)
        rate_terms.append(name)
    columns = ["d12_firm_npl_free_pct", *rate_terms, "d12_log_ibc_br_sa_x100"]
    sample = data[columns].dropna()
    if omit_pandemic:
        sample = exclude_pandemic(sample)
    x = np.column_stack([np.ones(len(sample)), *(sample[c].to_numpy() for c in columns[1:])])
    result = ols_newey_west(sample[columns[0]].to_numpy(), x, lag=18)
    terms = ["constant", *rate_terms, "d12_log_ibc_br_sa_x100"]
    unit = "percentage points of NPL per percentage point"
    rows = [
        _row("monthly", specification, term, float(b), float(se), result, sample,
             unit if term in rate_terms else "dependent-variable units per regressor unit")
        for term, b, se in zip(terms, result["beta"], result["se"])
    ]
    estimate, se, low, high = cumulative_response(result["beta"], result["covariance"], [1, 2, 3, 4])
    cumulative = _row("monthly", specification, "cumulative_rate_response", estimate, se,
                      result, sample, unit, note="sum of rate coefficients at lags 0, 6, 12, and 18 months")
    cumulative["ci95_low"], cumulative["ci95_high"] = low, high
    rows.append(cumulative)
    return rows, result


def estimate_local_projections(monthly: pd.DataFrame) -> list[dict[str, object]]:
    """Estimate h=0..24 projections of future 12-month NPL changes."""
    base = monthly.set_index("month").copy()
    rate = "d12_ex_ante_real_t1_pct"
    rate_terms = []
    for lag in (0, 6, 12, 18):
        name = f"{rate}_lag{lag}"
        base[name] = base[rate].shift(lag)
        rate_terms.append(name)
    rows: list[dict[str, object]] = []
    for horizon in range(25):
        dependent = f"npl_change_lead_{horizon}"
        base[dependent] = base["d12_firm_npl_free_pct"].shift(-horizon)
        columns = [dependent, *rate_terms, "d12_log_ibc_br_sa_x100"]
        sample = base[columns].dropna()
        x = np.column_stack([np.ones(len(sample)), *(sample[c].to_numpy() for c in columns[1:])])
        result = ols_newey_west(sample[dependent].to_numpy(), x, lag=18)
        estimate, se, low, high = cumulative_response(result["beta"], result["covariance"], [1, 2, 3, 4])
        row = _row("local_projection", "real_rate", "cumulative_rate_response", estimate, se,
                   result, sample, "percentage points of NPL per percentage point", horizon)
        row["ci95_low"], row["ci95_high"] = low, high
        rows.append(row)
    return rows


def estimate_annual(annual: pd.DataFrame) -> list[dict[str, object]]:
    """Estimate firm event-rate associations with current/lagged real rates."""
    data = annual.set_index("year")
    regressors = [
        "annual_mean_ex_post_real_selic_pct", "annual_mean_ex_post_real_selic_lag1_pct",
        "real_gdp_growth_pct",
    ]
    outcomes = {
        "firm_exit_rate": "firm_exit_rate_pct", "firm_birth_rate": "firm_birth_rate_pct",
        "employer_death_rate": "employer_death_rate_pct",
        "employer_birth_rate": "employer_birth_rate_pct",
    }
    rows: list[dict[str, object]] = []
    for specification, dependent in outcomes.items():
        sample = data[[dependent, *regressors]].dropna()
        x = np.column_stack([np.ones(len(sample)), *(sample[c].to_numpy() for c in regressors)])
        result = ols_newey_west(sample[dependent].to_numpy(), x, lag=1)
        for term, estimate, se in zip(["constant", *regressors], result["beta"], result["se"]):
            rows.append(_row(
                "annual", specification, term, float(estimate), float(se), result, sample,
                "percentage points of event rate per percentage point" if term != "constant" else "percentage points",
                note="small annual sample; confidence intervals are imprecise",
            ))
    return rows


def estimate_all(monthly: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    primary, _ = estimate_monthly(monthly)
    rows.extend(primary)
    for column, name in [
        ("d12_selic_target_monthly_avg_pct", "robust_selic"),
        ("d12_firm_lending_rate_free_pct", "robust_lending_rate"),
    ]:
        extra, _ = estimate_monthly(monthly, column, name)
        rows.extend(extra)
    extra, _ = estimate_monthly(monthly, specification="robust_exclude_pandemic", omit_pandemic=True)
    rows.extend(extra)
    rows.extend(estimate_local_projections(monthly))
    rows.extend(estimate_annual(annual))
    return pd.DataFrame(rows)


def _fmt(value: object, digits: int = 3) -> str:
    return "NA" if pd.isna(value) else f"{float(value):.{digits}f}"


def _table(frame: pd.DataFrame, columns: Sequence[str], digits: int = 2) -> list[str]:
    labels = [column.replace("_", " ") for column in columns]
    lines = ["| " + " | ".join(labels) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for _, row in frame.iterrows():
        values = [_fmt(row[c], digits) if isinstance(row[c], (float, np.floating)) else str(row[c]) for c in columns]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_config(estimates: pd.DataFrame) -> None:
    primary = estimates.query("analysis == 'monthly' and specification == 'primary_real_rate' and term == 'cumulative_rate_response'").iloc[0]
    exit_row = estimates.query("analysis == 'annual' and specification == 'firm_exit_rate' and term == 'annual_mean_ex_post_real_selic_pct'").iloc[0]
    config = {
        "status": "proposal_only_not_wired",
        "scope": "identical equation and parameters for every scenario",
        "scenario_real_rate_assumption": {
            "equation": "base real rate + I1 offset where used + C5 risk premium",
            "source": "tasks/BK.md step 5",
        },
        "output_gap_assumption": {
            "coefficient": 0.0,
            "reason": "monthly regression controls for observed 12-month log IBC-Br growth; it does not identify a scenario output-gap coefficient",
            "treatment": "retain as an explicit zero placeholder until separately estimated and reviewed",
        },
        "firm_npl_rate": {
            "equation": "delta12_npl_pp = cumulative_real_rate_response * delta12_scenario_real_rate_pp + activity_control",
            "coefficient_p50": float(primary.estimate), "coefficient_ci95_low": float(primary.ci95_low),
            "coefficient_ci95_high": float(primary.ci95_high),
            "unit": "pp of firm free-credit NPL rate per pp of ex-ante real rate",
            "source": "data/brazil/bankruptcy_estimates.csv primary_real_rate cumulative_rate_response",
        },
        "exit_rate_index": {
            "normalization": "100 in the scenario base year",
            "equation": "index change = current_real_rate_coefficient * scenario_real_rate_deviation_pp",
            "coefficient_p50": float(exit_row.estimate), "coefficient_ci95_low": float(exit_row.ci95_low),
            "coefficient_ci95_high": float(exit_row.ci95_high),
            "unit": "pp of firm exit rate per pp of annual mean ex-post real Selic",
            "source": "data/brazil/bankruptcy_estimates.csv firm_exit_rate current real-rate term",
        },
        "uncertainty_assumption": "A future integration must propagate coefficient uncertainty and report p10/p50/p90; no single path is a forecast.",
        "causal_status": "Associational coefficients; do not interpret as causal effects.",
    }
    PATHS["config"].write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")


def write_docs() -> None:
    text = """# Firm distress and interest rates: method

## Definitions and construction

The monthly panel runs from March 2011 through August 2026. Ipeadata/BCB series are aligned to calendar months. The primary outcome is the 12-month change in the non-performing-loan (NPL) rate for firms using free-market credit. The primary rate variable is the 12-month change in the one-year-ahead ex-ante real rate already constructed by I1. IBC-Br enters as 100 times its 12-month log change, an activity-growth control. No gaps are interpolated.

IBGE firm birth, entry and exit rates equal the relevant event count divided by active firms in that year, times 100. Employer birth and death rates use active employer firms as denominator. These ratios are descriptive accounting rates, not hazards for a fixed cohort. Annual real rates use the calendar-year mean ex-post real Selic so the fixed 2008-2021 sample is complete; the previous-year term is computed from 2007 before restricting the table to 2008-2025. Real GDP growth is the archived World Bank series in `data/brazil/backtest_observed.csv`.

Serasa monthly CNPJ totals and sectors use the non-cumulative workbook sheets. The archived workbook contains four sectors (commerce, industry, services and agriculture), but no firm-size field. Size results are therefore reported as unavailable; none are inferred. Sparse annual press-release observations retain the supplied `method` flag. Old-method counts and the relaunched 2025 CNPJ method are never spliced into a regression.

## Estimation assumptions

The primary regression is OLS of the 12-month NPL change on 12-month ex-ante-real-rate changes at lags 0, 6, 12 and 18 months, plus 12-month log IBC-Br growth and an intercept. The cumulative response is the sum of the four rate slopes. Its variance is the sum of every element in their covariance submatrix. Bartlett Newey-West standard errors use 18 lags, no finite-sample correction, and normal 95% confidence intervals, matching `src/rates.py`.

Robustness replaces the real rate with the Selic target or the free-credit firm lending rate, and separately removes March 2020-December 2021. Local projections shift the same 12-month NPL-change outcome forward by horizons 0-24 while retaining the four real-rate-change terms and activity control. They are sensitivity estimates, not a structural impulse response.

Annual regressions use an intercept, current and prior calendar-year mean ex-post real Selic, real GDP growth, and Newey-West uncertainty with one lag. The firm sample has 14 years (2008-2021); the employer sample has eight (2015-2022). These very small samples make estimates and confidence intervals imprecise.

## Limitations

All estimates are associations, not causal effects. Rate changes may respond to the same macroeconomic conditions that affect distress, and controls are incomplete. NPLs cover bank credit rather than all firm finance and can be affected by portfolio composition, recognition rules and write-offs. IBC-Br is an activity proxy, not a model-consistent output gap. Pandemic credit programmes and moratoria can change both measured arrears and exits; the exclusion check does not remove every pandemic-related effect.

The public Serasa series is short, observations may be revised, one process can contain multiple CNPJs, and the 2025 relaunch creates a method break. Legal requests, decrees, grants and approvals are different stages and are not interchangeable. IBGE exit and employer-death definitions differ from bankruptcy and judicial recovery. The proposed YAML is not wired into model files; any later use must apply the same equation to every scenario and propagate uncertainty into p10/p50/p90 ranges.
"""
    PATHS["docs"].write_text(text, encoding="utf-8")


def write_report(monthly: pd.DataFrame, annual: pd.DataFrame, estimates: pd.DataFrame) -> None:
    primary = estimates.query("analysis == 'monthly' and specification == 'primary_real_rate' and term == 'cumulative_rate_response'").iloc[0]
    exit_row = estimates.query("analysis == 'annual' and specification == 'firm_exit_rate' and term == 'annual_mean_ex_post_real_selic_pct'").iloc[0]
    robustness = estimates.query("analysis == 'monthly' and term == 'cumulative_rate_response'")[["specification", "estimate", "ci95_low", "ci95_high", "nobs"]]

    serasa_cols = ["serasa_rj_requested_cnpjs", "serasa_bankruptcy_requested_cnpjs"]
    serasa = monthly.dropna(subset=serasa_cols, how="all").copy()
    serasa["year"] = pd.to_datetime(serasa["month"]).dt.year
    yearly = serasa.groupby("year")[serasa_cols].sum(min_count=1).reset_index()
    sector_cols = [c for c in monthly if c.startswith("serasa_rj_requested_") and c.endswith("_cnpjs") and c != "serasa_rj_requested_cnpjs"]
    sector = serasa.assign(period=np.where(serasa["year"].eq(2026), "2026 Jan-May", serasa["year"].astype(str))).groupby("period")[sector_cols].sum(min_count=1).reset_index()
    sector = sector.rename(columns={c: c.removeprefix("serasa_rj_requested_").removesuffix("_cnpjs") for c in sector_cols})
    sparse = annual.dropna(subset=["serasa_bankruptcy_requested_annual", "serasa_rj_requested_annual"], how="all")[["year", "serasa_bankruptcy_requested_annual", "serasa_rj_requested_annual", "serasa_method"]]
    scatter = annual.dropna(subset=["firm_exit_rate_pct"])[["year", "firm_exit_rate_pct", "annual_mean_ex_post_real_selic_pct", "annual_mean_ex_post_real_selic_lag1_pct", "real_gdp_growth_pct"]]

    lines = [
        "# Firm distress, exits and interest rates in Brazil", "",
        "The estimates below describe historical associations. They are not causal estimates or forecasts, and the proposed channel is applied identically to every scenario.", "",
        "## Main estimates", "",
        f"The cumulative monthly NPL response is **{primary.estimate:.3f} pp per 1 pp of the ex-ante real rate** (95% CI {primary.ci95_low:.3f} to {primary.ci95_high:.3f}; n={int(primary.nobs)}). This is the sum of coefficients at 0, 6, 12 and 18 months, conditional on 12-month IBC-Br growth.", "",
        f"In the 14-year IBGE firm sample, the current annual real-rate coefficient for the exit rate is **{exit_row.estimate:.3f} pp per 1 pp** (95% CI {exit_row.ci95_low:.3f} to {exit_row.ci95_high:.3f}; n={int(exit_row.nobs)}). The sample is small and the interval is imprecise.", "",
        "### Monthly robustness", "", *_table(robustness, list(robustness.columns), 3), "",
        "## Serasa 2024-2026", "",
        "Counts below are CNPJs. 2024 and 2025 are full years; 2026 covers January-May only. The Selic monthly average reached 15% in July 2025 and remained at 15% through February 2026 in the archived I1 series. These short descriptive series do not identify a rate effect.", "",
        *_table(yearly, list(yearly.columns), 0), "",
        "RJ requests by sector:", "", *_table(sector, list(sector.columns), 0), "",
        "The workbook has no firm-size breakdown, so a size summary is unavailable rather than estimated. It distinguishes requests from decrees/grants/approvals; the table uses requests consistently.", "",
        "### Sparse annual press-release observations", "",
        *_table(sparse, list(sparse.columns), 0), "",
        "The old and relaunched methods are shown with their flags and are not used in a regression. For 2025, the later workbook monthly total (2,621 RJ-requesting CNPJs) differs from the preliminary annual press-release point (2,466); the vintages are retained separately and not reconciled.", "",
        "## Annual exit-rate scatter table", "",
        *_table(scatter, list(scatter.columns), 3), "",
        "## Interpretation and proposed channel", "",
        "Higher real rates can coincide with higher debt-service burdens, weaker refinancing conditions and later loan distress or exit. The historical specifications cannot isolate this channel from common macroeconomic shocks, policy responses, borrower composition or legal/measurement changes.", "",
        "`config/bk_proposed.yaml` stores a proposal only: the scenario real rate is the base real rate plus the I1 offset where used plus the C5 risk premium. The NPL equation uses the monthly cumulative association; the exit-rate index uses the annual current-rate association and is normalized to 100 in the base year. Because no scenario output-gap coefficient is identified here, it is an explicit zero placeholder pending separate estimation. Future integration must propagate parameter uncertainty and show p10/p50/p90, never a single forecast path.", "",
        "Full definitions, assumptions and limitations are in `docs/bankruptcy.md`.", "",
    ]
    PATHS["report"].write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    monthly = build_monthly()
    annual = build_annual(monthly)
    estimates = estimate_all(monthly, annual)
    monthly.to_csv(PATHS["monthly"], index=False, float_format="%.10f")
    annual.to_csv(PATHS["annual"], index=False, float_format="%.10f")
    estimates.to_csv(PATHS["estimates"], index=False, float_format="%.10f")
    write_config(estimates)
    write_docs()
    write_report(monthly, annual, estimates)
    print(f"Wrote {len(monthly)} monthly rows, {len(annual)} annual rows, and {len(estimates)} estimates.")


if __name__ == "__main__":
    main()
