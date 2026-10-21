"""Build the fixed-protocol D3 cross-country public-debt panel.

The module is deliberately offline: every input is an archived raw file.  It
implements the accounting decomposition, trajectory windows, fiscal-reaction
regressions, r-g summaries, debt episodes, and ageing regressions with numpy
and pandas.  Running ``python -m src.debt_panel`` rewrites every D3 output.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/debt_panel"
ADVANCED = "USA JPN DEU GBR FRA ITA CAN AUS KOR ESP NLD CHE SWE BEL AUT NOR DNK FIN IRL PRT GRC NZL ISR ISL".split()
EMERGING = "BRA ARG MEX CHL COL PER URY CRI PAN DOM PRY BOL ECU VEN TUR ZAF IND IDN PHL THA MYS PAK CHN RUS POL MAR".split()
COUNTRIES = ADVANCED + EMERGING
GROUP = {iso: "advanced" if iso in ADVANCED else "emerging" for iso in COUNTRIES}
YEARS = range(1975, 2025)
Z90 = 1.6448536269514722

PATHS = {
    "panel": ROOT / "data/debt_panel/panel.csv",
    "decomposition": ROOT / "data/debt_panel/decomposition.csv",
    "windows": ROOT / "data/debt_panel/windows.csv",
    "frf": ROOT / "data/debt_panel/frf_estimates.csv",
    "episodes": ROOT / "data/debt_panel/episodes.csv",
    "r_minus_g": ROOT / "data/debt_panel/r_minus_g.csv",
    "report": ROOT / "outputs/debt_panel.md",
    "docs": ROOT / "docs/debt_panel.md",
    "config": ROOT / "config/d3_proposed.yaml",
}


def load_imf(path: str | Path, indicator: str) -> pd.DataFrame:
    """Read an IMF DataMapper country/year mapping into tidy rows."""
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    values = payload.get("values", {}).get(indicator, {})
    rows = [
        (iso, int(year), float(value))
        for iso, observations in values.items()
        if iso in COUNTRIES
        for year, value in observations.items()
        if value is not None and str(year).isdigit() and int(year) in YEARS
    ]
    return pd.DataFrame(rows, columns=["iso3", "year", indicator])


def load_wdi(path: str | Path, name: str) -> pd.DataFrame:
    """Read an archived WDI list of observation records."""
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = []
    for record in payload:
        iso, year, value = record.get("countryiso3code"), record.get("date"), record.get("value")
        if iso in COUNTRIES and value is not None and str(year).isdigit() and int(year) in YEARS:
            rows.append((iso, int(year), float(value)))
    frame = pd.DataFrame(rows, columns=["iso3", "year", name])
    return frame.drop_duplicates(["iso3", "year"], keep="last")


def _merge_series(base: pd.DataFrame, addition: pd.DataFrame) -> pd.DataFrame:
    return base.merge(addition, on=["iso3", "year"], how="left", validate="one_to_one")


def hp_gap(growth: pd.Series, years: pd.Series, smoothing: float = 100.0) -> pd.Series:
    """Return log-output deviations from an HP trend for consecutive segments.

    A level index is reconstructed only from observed real-growth rates.  Each
    uninterrupted segment is independently normalised; no missing year is
    interpolated. Segments shorter than five observations are left missing.
    """
    answer = pd.Series(np.nan, index=growth.index, dtype=float)
    valid = growth.notna()
    segment = ((years.diff().ne(1)) | (~valid) | (~valid.shift(fill_value=False))).cumsum()
    for _, idx in growth[valid].groupby(segment[valid]).groups.items():
        idx = list(idx)
        if len(idx) < 5:
            continue
        rates = growth.loc[idx].to_numpy(dtype=float)
        log_level = np.cumsum(np.log1p(rates / 100.0))
        n = len(log_level)
        second_difference = np.zeros((n - 2, n))
        for row in range(n - 2):
            second_difference[row, row:row + 3] = (1.0, -2.0, 1.0)
        trend = np.linalg.solve(
            np.eye(n) + smoothing * second_difference.T @ second_difference,
            log_level,
        )
        answer.loc[idx] = log_level - trend
    return answer


def build_panel() -> pd.DataFrame:
    """Assemble the 50-country 1975-2024 unbalanced panel."""
    panel = pd.MultiIndex.from_product([COUNTRIES, YEARS], names=["iso3", "year"]).to_frame(index=False)
    imf = {
        "d": ("imf_d.json", "d"),
        "pb": ("imf_pb.json", "pb"),
        "ie": ("imf_ie.json", "ie"),
        "prim_exp": ("imf_prim_exp.json", "prim_exp"),
        "debt_weo": ("imf_GGXWDG_NGDP.json", "GGXWDG_NGDP"),
        "debt_hpdd": ("imf_DEBT1.json", "DEBT1"),
        "debt_gdd": ("imf_GG_DEBT_GDP.json", "GG_DEBT_GDP"),
    }
    for column, (filename, indicator) in imf.items():
        data = load_imf(RAW / filename, indicator).rename(columns={indicator: column})
        panel = _merge_series(panel, data)
    wdi = {
        "real_growth": "wdi_NY.GDP.MKTP.KD.ZG.json",
        "deflator_inflation": "wdi_NY.GDP.DEFL.KD.ZG.json",
        "age65_share": "wdi_SP.POP.65UP.TO.ZS.json",
        "old_age_dependency": "wdi_SP.POP.DPND.OL.json",
    }
    for column, filename in wdi.items():
        panel = _merge_series(panel, load_wdi(RAW / filename, column))
    panel["group"] = panel["iso3"].map(GROUP)
    panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)
    panel["output_gap"] = panel.groupby("iso3", group_keys=False).apply(
        lambda x: hp_gap(x["real_growth"], x["year"]), include_groups=False
    ).reset_index(level=0, drop=True)
    return panel[[
        "iso3", "group", "year", "d", "pb", "ie", "prim_exp", "real_growth",
        "deflator_inflation", "age65_share", "old_age_dependency", "output_gap",
        "debt_weo", "debt_hpdd", "debt_gdd",
    ]]


def decomposition_row(
    debt: float,
    lagged_debt: float,
    primary_balance: float,
    interest: float,
    real_growth: float,
    inflation: float,
) -> dict[str, float]:
    """Apply the fixed D3 debt-accounting formulas to one observation."""
    g, pi = real_growth / 100.0, inflation / 100.0
    gamma = (1.0 + g) * (1.0 + pi) - 1.0
    primary = -primary_balance
    growth = -g / (1.0 + gamma) * lagged_debt
    inflation_contribution = -(gamma - g) / (1.0 + gamma) * lagged_debt
    change = debt - lagged_debt
    sfa = change - primary - interest - growth - inflation_contribution
    nominal_rate = math.nan if lagged_debt < 5.0 else interest * (1.0 + gamma) / lagged_debt
    r_minus_g = math.nan if lagged_debt < 5.0 else (nominal_rate - gamma) / (1.0 + gamma) * 100.0
    return {
        "delta_d": change,
        "primary_deficit_contribution": primary,
        "interest_contribution": interest,
        "real_growth_contribution": growth,
        "inflation_contribution": inflation_contribution,
        "sfa": sfa,
        "nominal_growth_pct": gamma * 100.0,
        "effective_nominal_rate_pct": nominal_rate * 100.0 if math.isfinite(nominal_rate) else math.nan,
        "r_minus_g_pct": r_minus_g,
    }


def decompose_panel(panel: pd.DataFrame) -> pd.DataFrame:
    """Decompose observations having all fixed-protocol inputs and an annual lag."""
    data = panel.sort_values(["iso3", "year"]).copy()
    data["lagged_debt"] = data.groupby("iso3")["d"].shift()
    data["lag_year"] = data.groupby("iso3")["year"].shift()
    needed = ["d", "lagged_debt", "pb", "ie", "real_growth", "deflator_inflation"]
    use = data.dropna(subset=needed).loc[lambda x: x["year"] - x["lag_year"] == 1].copy()
    calculated = pd.DataFrame([
        decomposition_row(row.d, row.lagged_debt, row.pb, row.ie, row.real_growth, row.deflator_inflation)
        for row in use.itertuples(index=False)
    ], index=use.index)
    out = pd.concat([use[["iso3", "group", "year", "d", "lagged_debt", "pb", "ie", "real_growth", "deflator_inflation"]], calculated], axis=1)
    out["large_sfa_flag"] = out["sfa"].abs() > 10.0
    return out.reset_index(drop=True)


def longest_increase_run(years: Sequence[int], debt: Sequence[float]) -> int:
    """Longest count of consecutive annual debt increases (transition count)."""
    best = current = 0
    for position in range(1, len(years)):
        if years[position] == years[position - 1] + 1 and debt[position] > debt[position - 1]:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def find_local_peaks(data: pd.DataFrame, radius: int = 5) -> pd.DataFrame:
    """Find debt maxima with complete +/- ``radius`` annual neighborhoods."""
    rows = []
    for iso, country in data.dropna(subset=["d"]).groupby("iso3"):
        values = country.set_index("year")["d"].sort_index()
        for year, value in values.items():
            expected = list(range(int(year) - radius, int(year) + radius + 1))
            if not set(expected).issubset(values.index):
                continue
            neighborhood = values.loc[expected]
            if value == neighborhood.max() and (neighborhood < value).any():
                rows.append({"iso3": iso, "peak_year": int(year), "peak_debt": float(value)})
    return pd.DataFrame(rows, columns=["iso3", "peak_year", "peak_debt"])


def build_windows(panel: pd.DataFrame, decomposition: pd.DataFrame) -> pd.DataFrame:
    """Build all exact-endpoint 20-year windows, peaks, and coverage summaries."""
    records: list[dict] = []
    dec_index = decomposition.set_index(["iso3", "year"])
    for iso, country in panel.groupby("iso3"):
        country = country.sort_values("year")
        indexed = country.set_index("year")
        observed = country.dropna(subset=["d"])
        years, debts = observed["year"].astype(int).tolist(), observed["d"].tolist()
        records.append({
            "row_type": "country_summary", "iso3": iso, "group": GROUP[iso],
            "start_year": min(years) if years else np.nan, "end_year": max(years) if years else np.nan,
            "debt_observations": len(years), "longest_increase_run": longest_increase_run(years, debts),
            "pb_observations": int(country["pb"].notna().sum()),
            "interest_observations": int(country["ie"].notna().sum()),
            "growth_observations": int(country["real_growth"].notna().sum()),
            "inflation_observations": int(country["deflator_inflation"].notna().sum()),
            "decomposition_observations": int((decomposition["iso3"] == iso).sum()),
        })
        for start in YEARS:
            end = start + 20
            if end > 2024 or start not in indexed.index or end not in indexed.index:
                continue
            if pd.isna(indexed.at[start, "d"]) or pd.isna(indexed.at[end, "d"]):
                continue
            span = indexed.loc[start + 1:end]
            row = {
                "row_type": "20_year", "iso3": iso, "group": GROUP[iso],
                "start_year": start, "end_year": end, "start_debt": indexed.at[start, "d"],
                "end_debt": indexed.at[end, "d"], "debt_change": indexed.at[end, "d"] - indexed.at[start, "d"],
                "cumulative_pb": span["pb"].sum(min_count=1), "pb_observations": span["pb"].notna().sum(),
                "end_pb": indexed.at[end, "pb"], "start_age65": indexed.at[start, "age65_share"],
                "end_age65": indexed.at[end, "age65_share"], "start_prim_exp": indexed.at[start, "prim_exp"],
                "end_prim_exp": indexed.at[end, "prim_exp"], "start_pb": indexed.at[start, "pb"],
            }
            row["age65_change"] = row["end_age65"] - row["start_age65"]
            row["prim_exp_change"] = row["end_prim_exp"] - row["start_prim_exp"]
            row["pb_change"] = row["end_pb"] - row["start_pb"]
            try:
                dec = dec_index.loc[(iso, slice(start + 1, end)), :]
            except KeyError:
                dec = decomposition.iloc[0:0]
            row["decomposition_observations"] = len(dec)
            for column in ["primary_deficit_contribution", "interest_contribution", "real_growth_contribution", "inflation_contribution", "sfa"]:
                row[column] = dec[column].sum(min_count=1) if len(dec) else np.nan
            records.append(row)
    peaks = find_local_peaks(panel)
    debt_lookup = panel.set_index(["iso3", "year"])["d"]
    for peak in peaks.itertuples(index=False):
        row = {
            "row_type": "peak", "iso3": peak.iso3, "group": GROUP[peak.iso3],
            "start_year": peak.peak_year, "start_debt": peak.peak_debt,
        }
        for horizon in (5, 10):
            value = debt_lookup.get((peak.iso3, peak.peak_year + horizon), np.nan)
            row[f"debt_after_{horizon}y"] = value
            row[f"change_after_{horizon}y"] = value - peak.peak_debt if pd.notna(value) else np.nan
        records.append(row)
    return pd.DataFrame(records)


def _ols_covariance(
    y: np.ndarray,
    x: np.ndarray,
    *,
    clusters: np.ndarray | None = None,
    hac_lags: int | None = None,
) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    """OLS with country-clustered or Bartlett Newey-West covariance."""
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - x @ beta
    bread = np.linalg.pinv(x.T @ x)
    n, k = x.shape
    if clusters is not None:
        unique = pd.unique(clusters)
        meat = np.zeros((k, k))
        for cluster in unique:
            score = x[clusters == cluster].T @ residual[clusters == cluster]
            meat += np.outer(score, score)
        correction = len(unique) / (len(unique) - 1) * (n - 1) / (n - k) if len(unique) > 1 and n > k else 1.0
        covariance = correction * bread @ meat @ bread
    elif hac_lags is not None:
        scores = x * residual[:, None]
        meat = scores.T @ scores
        for lag in range(1, min(hac_lags, n - 1) + 1):
            weight = 1.0 - lag / (hac_lags + 1.0)
            cross = scores[lag:].T @ scores[:-lag]
            meat += weight * (cross + cross.T)
        covariance = (n / (n - k) if n > k else 1.0) * bread @ meat @ bread
    else:
        covariance = bread * float(residual @ residual) / max(n - k, 1)
    total = float(((y - y.mean()) ** 2).sum())
    r2 = math.nan if total == 0 else 1.0 - float(residual @ residual) / total
    return beta, np.sqrt(np.maximum(np.diag(covariance), 0.0)), r2, residual


def _frf_data(panel: pd.DataFrame, sample: Iterable[str], start_year: int = 1975) -> pd.DataFrame:
    data = panel[panel["iso3"].isin(sample) & (panel["year"] >= start_year)].sort_values(["iso3", "year"]).copy()
    data["debt_lag"] = data.groupby("iso3")["d"].shift()
    data["pb_lag"] = data.groupby("iso3")["pb"].shift()
    data["year_lag"] = data.groupby("iso3")["year"].shift()
    return data.loc[data["year"] - data["year_lag"] == 1]


def estimate_frf(
    panel: pd.DataFrame,
    sample: Sequence[str],
    *,
    cubic: bool = False,
    lagged_pb: bool = True,
    start_year: int = 1975,
    end_year: int = 2024,
    low_inflation_only: bool = False,
    brazil_hac_lags: int = 2,
) -> dict:
    """Estimate the fixed-effects FRF, or Brazil OLS with HAC covariance."""
    data = _frf_data(panel, sample, start_year)
    data = data[data["year"] <= end_year]
    if low_inflation_only:
        data = data[data["deflator_inflation"] < 15.0]
    terms = ["debt_lag", "output_gap"] + (["pb_lag"] if lagged_pb else [])
    if cubic:
        data["debt_lag_sq"] = data["debt_lag"] ** 2
        data["debt_lag_cu"] = data["debt_lag"] ** 3
        terms = ["debt_lag", "debt_lag_sq", "debt_lag_cu", "output_gap"] + (["pb_lag"] if lagged_pb else [])
    data = data.dropna(subset=["pb", *terms]).copy()
    brazil = list(sample) == ["BRA"]
    if brazil:
        names = ["intercept", *terms]
        x = np.column_stack([np.ones(len(data)), data[terms].to_numpy(dtype=float)])
        y = data["pb"].to_numpy(dtype=float)
        beta, se, r2, _ = _ols_covariance(y, x, hac_lags=brazil_hac_lags)
    else:
        names = terms
        demean = data.groupby("iso3")[["pb", *terms]].transform(lambda value: value - value.mean())
        y, x = demean["pb"].to_numpy(dtype=float), demean[terms].to_numpy(dtype=float)
        beta, se, r2, _ = _ols_covariance(y, x, clusters=data["iso3"].to_numpy())
    result = {
        "names": names, "beta": beta, "se": se, "r2": r2, "nobs": len(data),
        "countries": data["iso3"].nunique(), "data": data,
    }
    coefficient = dict(zip(names, beta))
    if "pb_lag" in coefficient:
        denominator = 1.0 - coefficient["pb_lag"]
        result["long_run"] = coefficient["debt_lag"] / denominator if abs(denominator) > 1e-10 else math.nan
        # Delta-method covariance is intentionally omitted from the output: the
        # fixed protocol asks for the response, not a confidence interval.
    else:
        result["long_run"] = coefficient["debt_lag"]
    return result


def _regression_rows(name: str, sample_name: str, model: Mapping) -> list[dict]:
    rows = []
    for term, estimate, se in zip(model["names"], model["beta"], model["se"]):
        rows.append({
            "analysis": "fiscal_reaction", "specification": name, "sample": sample_name,
            "term": term, "estimate": estimate, "standard_error": se,
            "ci90_low": estimate - Z90 * se, "ci90_high": estimate + Z90 * se,
            "nobs": model["nobs"], "countries": model["countries"], "r2": model["r2"],
        })
    rows.append({
        "analysis": "fiscal_reaction", "specification": name, "sample": sample_name,
        "term": "long_run_debt_response", "estimate": model["long_run"],
        "nobs": model["nobs"], "countries": model["countries"], "r2": model["r2"],
    })
    if "debt_lag_sq" in model["names"]:
        coefficients = dict(zip(model["names"], model["beta"]))
        roots = np.roots([3 * coefficients["debt_lag_cu"], 2 * coefficients["debt_lag_sq"], coefficients["debt_lag"]])
        observed = model["data"]["debt_lag"]
        feasible = sorted(float(root.real) for root in roots if abs(root.imag) < 1e-8 and observed.min() <= root.real <= observed.max())
        rows.append({
            "analysis": "fiscal_reaction", "specification": name, "sample": sample_name,
            "term": "fiscal_fatigue_zero_marginal_response", "estimate": feasible[0] if feasible else np.nan,
            "nobs": model["nobs"], "countries": model["countries"], "r2": model["r2"],
            "note": "lowest real root within the estimation sample debt range",
        })
    return rows


def load_brazil_official_primary_balance() -> pd.DataFrame:
    """Load the BCB NFSP series and convert deficits to primary-balance signs."""
    data = pd.read_csv(ROOT / "data/brazil/backtest_observed.csv")
    data = data[data["indicator"] == "primary_result_pct_gdp"][["year", "value"]].copy()
    data["official_pb"] = -pd.to_numeric(data["value"], errors="coerce")
    return data[["year", "official_pb"]].dropna().sort_values("year").reset_index(drop=True)


def brazil_primary_balance_comparison(
    panel: pd.DataFrame,
    official: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Align FPP and official BCB primary balances without filling missing years."""
    fpp = panel.loc[panel["iso3"] == "BRA", ["year", "pb"]].rename(columns={"pb": "fpp_pb"})
    if official is None:
        official = load_brazil_official_primary_balance()
    comparison = fpp.merge(official, on="year", how="inner")
    comparison = comparison.dropna(subset=["fpp_pb", "official_pb"]).copy()
    comparison["fpp_minus_official_gap"] = comparison["fpp_pb"] - comparison["official_pb"]
    return comparison.sort_values("year").reset_index(drop=True)


def restricted_distribution(
    decomposition: pd.DataFrame,
    value: str,
) -> pd.DataFrame:
    """Summarise low-inflation observations for fixed review periods and groups."""
    records: list[dict] = []
    periods = (("1975-2024", 1975), ("2000-2024", 2000), ("2010-2024", 2010))
    low = decomposition[decomposition["deflator_inflation"] < 15.0]
    for period, start in periods:
        period_data = low[low["year"].between(start, 2024)]
        samples = {
            "advanced": period_data[period_data["group"] == "advanced"],
            "emerging": period_data[period_data["group"] == "emerging"],
            "Brazil": period_data[period_data["iso3"] == "BRA"],
        }
        for sample, data in samples.items():
            values = data[value].dropna()
            records.append({
                "metric": value, "period": period, "sample": sample, "n": len(values),
                "mean": values.mean(), "median": values.median(),
                "p10": values.quantile(.1), "p90": values.quantile(.9),
            })
    return pd.DataFrame(records)


def stabilisation_comparison(estimates: pd.DataFrame, decomposition: pd.DataFrame) -> pd.DataFrame:
    """Compare FRF long-run responses with three debt-stabilising responses."""
    low_2000 = decomposition[
        decomposition["year"].between(2000, 2024)
        & (decomposition["deflator_inflation"] < 15.0)
    ]
    brazil_rg = low_2000.loc[low_2000["iso3"] == "BRA", "r_minus_g_pct"].mean()
    emerging_rg = low_2000.loc[low_2000["group"] == "emerging", "r_minus_g_pct"].median()
    scenarios = [
        ("S0 central 2045", 4.9, 0.5),
        ("Brazil low-inflation 2000-2024 mean", brazil_rg, 2.0),
        ("Emerging low-inflation 2000-2024 median", emerging_rg, 2.0),
    ]
    specifications = {
        "primary", "low_inflation_robustness", "2000_2024_robustness",
        "low_inflation_2000_2024_calibration",
        "brazil_official_pb_2000_2024", "brazil_fpp_pb_2000_2024",
    }
    responses = estimates[
        estimates["specification"].isin(specifications)
        & (estimates["term"] == "long_run_debt_response")
    ]
    records = []
    for response in responses.itertuples(index=False):
        for scenario, rg, growth in scenarios:
            needed = (rg / 100.0) / (1.0 + growth / 100.0)
            records.append({
                "sample": response.sample, "specification": response.specification,
                "long_run_response": response.estimate, "benchmark": scenario,
                "r_minus_g_pct": rg, "g_pct": growth,
                "response_needed": needed,
                "stabilises": "yes" if response.estimate >= needed else "no",
            })
    return pd.DataFrame(records)


def _ageing_regression_rows(windows: pd.DataFrame) -> list[dict]:
    rows = []
    source = windows[windows["row_type"] == "20_year"].copy()
    for dependent in ("prim_exp_change", "pb_change"):
        data = source.dropna(subset=[dependent, "age65_change", "group"])
        x = np.column_stack([
            np.ones(len(data)), data["age65_change"].to_numpy(),
            (data["group"] == "advanced").astype(float).to_numpy(),
        ])
        beta, se, r2, _ = _ols_covariance(data[dependent].to_numpy(), x, clusters=data["iso3"].to_numpy())
        for term, estimate, error in zip(["intercept", "age65_change", "advanced_dummy"], beta, se):
            rows.append({
                "analysis": "ageing", "specification": "all_20_year_windows", "sample": "full",
                "outcome": dependent, "term": term, "estimate": estimate, "standard_error": error,
                "ci90_low": estimate - Z90 * error, "ci90_high": estimate + Z90 * error,
                "nobs": len(data), "countries": data["iso3"].nunique(), "r2": r2,
            })
    # Fixed 1995-2024 long difference (29 years because endpoints are fixed).
    panel_rows = []
    for iso, data in source.groupby("iso3"):
        original = data[(data["start_year"] == 1995) & (data["end_year"] == 2015)]
        # Replaced below in build_estimates using panel data; keep no accidental alternative.
        if len(original):
            pass
    return rows


def build_estimates(panel: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    samples = {"full": COUNTRIES, "advanced": ADVANCED, "emerging": EMERGING, "brazil": ["BRA"]}
    for sample_name, countries in samples.items():
        rows += _regression_rows("primary", sample_name, estimate_frf(panel, countries))
        rows += _regression_rows("cubic_robustness", sample_name, estimate_frf(panel, countries, cubic=True))
        rows += _regression_rows("no_lagged_pb_robustness", sample_name, estimate_frf(panel, countries, lagged_pb=False))
        rows += _regression_rows("1990_2024_robustness", sample_name, estimate_frf(panel, countries, start_year=1990))
    for sample_name, countries in {"full": COUNTRIES, "emerging": EMERGING}.items():
        rows += _regression_rows(
            "low_inflation_robustness", sample_name,
            estimate_frf(panel, countries, low_inflation_only=True),
        )
        rows += _regression_rows(
            "2000_2024_robustness", sample_name,
            estimate_frf(panel, countries, start_year=2000),
        )
        rows += _regression_rows(
            "low_inflation_2000_2024_calibration", sample_name,
            estimate_frf(panel, countries, start_year=2000, low_inflation_only=True),
        )
    brazil_official = panel.copy()
    official = load_brazil_official_primary_balance()
    brazil_official = brazil_official.merge(official, on="year", how="left", validate="many_to_one")
    brazil_official.loc[brazil_official["iso3"] == "BRA", "pb"] = brazil_official.loc[
        brazil_official["iso3"] == "BRA", "official_pb"
    ]
    rows += _regression_rows(
        "brazil_official_pb_2000_2024", "brazil",
        estimate_frf(brazil_official, ["BRA"], start_year=2000),
    )
    rows += _regression_rows(
        "brazil_fpp_pb_2000_2024", "brazil",
        estimate_frf(panel, ["BRA"], start_year=2000),
    )
    rows += _ageing_regression_rows(windows)
    long_rows = []
    indexed = panel.set_index(["iso3", "year"])
    for iso in COUNTRIES:
        try:
            first, last = indexed.loc[(iso, 1995)], indexed.loc[(iso, 2024)]
        except KeyError:
            continue
        long_rows.append({
            "iso3": iso, "group": GROUP[iso],
            "age65_change": last.age65_share - first.age65_share,
            "prim_exp_change": last.prim_exp - first.prim_exp,
            "pb_change": last.pb - first.pb,
        })
    long_data = pd.DataFrame(long_rows)
    for dependent in ("prim_exp_change", "pb_change"):
        data = long_data.dropna(subset=[dependent, "age65_change"])
        x = np.column_stack([np.ones(len(data)), data["age65_change"], (data["group"] == "advanced").astype(float)])
        beta, se, r2, _ = _ols_covariance(data[dependent].to_numpy(), x)
        for term, estimate, error in zip(["intercept", "age65_change", "advanced_dummy"], beta, se):
            rows.append({
                "analysis": "ageing", "specification": "1995_2024_long_difference", "sample": "full",
                "outcome": dependent, "term": term, "estimate": estimate, "standard_error": error,
                "ci90_low": estimate - Z90 * error, "ci90_high": estimate + Z90 * error,
                "nobs": len(data), "countries": data["iso3"].nunique(), "r2": r2,
            })
    return pd.DataFrame(rows)


def detect_episodes(panel: pd.DataFrame, decomposition: pd.DataFrame) -> pd.DataFrame:
    """Detect fixed-threshold reduction and increase episodes within ten years."""
    records = []
    peaks = find_local_peaks(panel)
    debt = panel.set_index(["iso3", "year"])["d"]
    candidates: list[tuple[str, str, int, int, float, float]] = []
    for peak in peaks.itertuples(index=False):
        future = [(year, debt.get((peak.iso3, year), np.nan)) for year in range(peak.peak_year + 1, min(peak.peak_year + 10, 2024) + 1)]
        future = [(year, value) for year, value in future if pd.notna(value)]
        if future:
            end, end_debt = min(future, key=lambda pair: pair[1])
            if peak.peak_debt - end_debt >= 15.0:
                candidates.append(("reduction", peak.iso3, peak.peak_year, end, peak.peak_debt, end_debt))
    for iso, country in panel.dropna(subset=["d"]).groupby("iso3"):
        values = country.set_index("year")["d"]
        for start, start_debt in values.items():
            future = [(year, values.get(year, np.nan)) for year in range(int(start) + 1, min(int(start) + 10, 2024) + 1)]
            future = [(year, value) for year, value in future if pd.notna(value)]
            if future:
                end, end_debt = max(future, key=lambda pair: pair[1])
                if end_debt - start_debt >= 30.0:
                    candidates.append(("increase", iso, int(start), end, float(start_debt), float(end_debt)))
    dec = decomposition.set_index(["iso3", "year"])
    for kind, iso, start, end, start_debt, end_debt in candidates:
        try:
            period = dec.loc[(iso, slice(start + 1, end)), :]
        except KeyError:
            period = decomposition.iloc[0:0]
        row = {
            "episode_type": kind, "iso3": iso, "group": GROUP[iso], "start_year": start,
            "end_year": end, "years": end - start, "start_debt": start_debt, "end_debt": end_debt,
            "debt_change": end_debt - start_debt, "decomposition_observations": len(period),
        }
        for column in ["primary_deficit_contribution", "interest_contribution", "real_growth_contribution", "inflation_contribution", "sfa"]:
            row[column] = period[column].sum(min_count=1) if len(period) else np.nan
        records.append(row)
    return pd.DataFrame(records).sort_values(["episode_type", "iso3", "start_year"]).reset_index(drop=True)


def _ar1(values: pd.DataFrame) -> tuple[float, float, int]:
    data = values.sort_values("year").copy()
    data["lag"] = data["r_minus_g_pct"].shift()
    data["lag_year"] = data["year"].shift()
    data = data.dropna(subset=["r_minus_g_pct", "lag"])
    data = data[data["year"] - data["lag_year"] == 1]
    if len(data) < 4:
        return math.nan, math.nan, len(data)
    x = np.column_stack([np.ones(len(data)), data["lag"]])
    beta, se, _, _ = _ols_covariance(data["r_minus_g_pct"].to_numpy(), x)
    return float(beta[1]), float(se[1]), len(data)


def build_r_minus_g(decomposition: pd.DataFrame) -> pd.DataFrame:
    """Return observations plus group/decade, persistence, FE, and JST rows."""
    observations = decomposition.dropna(subset=["r_minus_g_pct"])[["iso3", "group", "year", "lagged_debt", "r_minus_g_pct"]].copy()
    observations.insert(0, "row_type", "observation")
    observations["decade"] = observations["year"] // 10 * 10
    rows = [observations]
    summary = observations.groupby(["group", "decade"])["r_minus_g_pct"].agg(["count", "mean", "median", "std", lambda x: x.quantile(.1), lambda x: x.quantile(.9)]).reset_index()
    summary.columns = ["group", "decade", "nobs", "mean", "median", "std", "p10", "p90"]
    summary.insert(0, "row_type", "group_decade_summary")
    rows.append(summary)
    persistence = []
    for iso, data in observations.groupby("iso3"):
        estimate, se, nobs = _ar1(data)
        persistence.append({"row_type": "country_ar1", "iso3": iso, "group": GROUP[iso], "estimate": estimate, "standard_error": se, "nobs": nobs})
    rows.append(pd.DataFrame(persistence))
    fe_data = observations.dropna(subset=["lagged_debt"]).copy()
    demean = fe_data.groupby("iso3")[["r_minus_g_pct", "lagged_debt"]].transform(lambda x: x - x.mean())
    beta, se, r2, _ = _ols_covariance(demean["r_minus_g_pct"].to_numpy(), demean[["lagged_debt"]].to_numpy(), clusters=fe_data["iso3"].to_numpy())
    rows.append(pd.DataFrame([{"row_type": "debt_fe_slope", "estimate": beta[0], "standard_error": se[0], "nobs": len(fe_data), "countries": fe_data.iso3.nunique(), "r2": r2}]))
    calibration_fe = decomposition[
        decomposition["year"].between(2000, 2024)
        & (decomposition["deflator_inflation"] < 15.0)
    ].dropna(subset=["r_minus_g_pct", "lagged_debt"])
    calibration_demean = calibration_fe.groupby("iso3")[["r_minus_g_pct", "lagged_debt"]].transform(lambda x: x - x.mean())
    calibration_beta, calibration_se, calibration_r2, _ = _ols_covariance(
        calibration_demean["r_minus_g_pct"].to_numpy(),
        calibration_demean[["lagged_debt"]].to_numpy(),
        clusters=calibration_fe["iso3"].to_numpy(),
    )
    rows.append(pd.DataFrame([{
        "row_type": "debt_fe_slope_low_inflation_2000_2024",
        "estimate": calibration_beta[0], "standard_error": calibration_se[0],
        "nobs": len(calibration_fe), "countries": calibration_fe.iso3.nunique(), "r2": calibration_r2,
    }]))
    country = observations.groupby(["iso3", "group"])["r_minus_g_pct"].agg(["count", "mean"]).reset_index()
    country["rank_descending"] = country["mean"].rank(ascending=False, method="min")
    country.insert(0, "row_type", "country_summary")
    rows.append(country.rename(columns={"count": "nobs"}))
    brazil_decade = observations[observations["iso3"] == "BRA"].groupby("decade")["r_minus_g_pct"].agg(["count", "mean"]).reset_index()
    brazil_decade.insert(0, "row_type", "brazil_decade_summary")
    rows.append(brazil_decade.rename(columns={"count": "nobs"}))
    try:
        jst = pd.read_stata(RAW / "JSTdatasetR6.xlsx", columns=["year", "iso", "ltrate", "gdp"])
        jst = jst[jst["year"].between(1950, 2020)].sort_values(["iso", "year"])
        jst["nominal_gdp_growth_pct"] = jst.groupby("iso")["gdp"].pct_change(fill_method=None) * 100.0
        jst["r_minus_g_pct"] = (jst["ltrate"] / 100.0 - jst["nominal_gdp_growth_pct"] / 100.0) / (1.0 + jst["nominal_gdp_growth_pct"] / 100.0) * 100.0
        jst = jst.replace([np.inf, -np.inf], np.nan).dropna(subset=["r_minus_g_pct"])
        jst_rows = jst.rename(columns={"iso": "iso3"})[["iso3", "year", "ltrate", "nominal_gdp_growth_pct", "r_minus_g_pct"]]
        jst_rows.insert(0, "row_type", "jst_observation")
        rows.append(jst_rows)
    except (ValueError, OSError):
        rows.append(pd.DataFrame([{"row_type": "jst_unavailable", "note": "Archived JST file could not be parsed"}]))
    return pd.concat(rows, ignore_index=True, sort=False)


def _s0_values() -> dict:
    data = pd.read_csv(ROOT / "outputs/runs/summary_percentiles.csv")
    selected = data[(data["variant"] == "compensating_transfers") & (data["persistence"] == "persistent") & (data["scenario"] == "S0")]
    values = {(row.indicator, int(row.year)): float(row.p50) for row in selected.itertuples()}
    population = pd.read_csv(ROOT / "data/brazil/population.csv")
    population = population[(population["sex"] == "Ambos") & (population["location"] == "Brasil")].copy()
    population["age_number"] = pd.to_numeric(population["age"].astype(str).str.extract(r"(\d+)")[0])
    shares = {}
    for year in (2025, 2045):
        year_data = population[population["year"] == year]
        shares[year] = year_data.loc[year_data["age_number"] >= 65, "population"].sum() / year_data["population"].sum() * 100.0
    values[("age65_share", 2025)], values[("age65_share", 2045)] = shares[2025], shares[2045]
    values[("ageing_spending_ratio", 2045)] = (values[("spending_pct_gdp", 2045)] - 40.0) / (shares[2045] - shares[2025])
    return values


def _fmt(value: float, digits: int = 2) -> str:
    return "NA" if pd.isna(value) else f"{float(value):.{digits}f}"


def _markdown(frame: pd.DataFrame, digits: int = 2) -> list[str]:
    headers = list(frame.columns)
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for values in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(_fmt(value, digits) if isinstance(value, (float, np.floating)) else str(value) for value in values) + " |")
    return lines


def render_report(panel: pd.DataFrame, decomposition: pd.DataFrame, windows: pd.DataFrame, estimates: pd.DataFrame, episodes: pd.DataFrame, rg: pd.DataFrame) -> str:
    """Render the evidence-first D3 report exclusively from computed tables."""
    s0 = _s0_values()
    twenty = windows[windows["row_type"] == "20_year"].copy()
    change = s0[("debt_gdp", 2045)] - 78.6
    pb_2045 = s0[("primary_balance_gdp", 2045)]
    percentile = lambda series, value: float((series.dropna() <= value).mean() * 100.0)
    all_debt_pct = percentile(twenty["debt_change"], change)
    em_debt_pct = percentile(twenty.loc[twenty.group == "emerging", "debt_change"], change)
    all_pb_pct = percentile(panel["pb"], pb_2045)
    em_pb_pct = percentile(panel.loc[panel.group == "emerging", "pb"], pb_2045)
    joint = twenty[(twenty["debt_change"] >= change) & (twenty["end_pb"] <= pb_2045)]
    if joint.empty:
        joint_text = "No observed window jointly matched both thresholds."
    else:
        labels = ", ".join(f"{r.iso3} {int(r.start_year)}-{int(r.end_year)}" for r in joint.itertuples())
        first = joint.iloc[0]
        joint_text = (
            f"{len(joint)} observed windows jointly had debt rise by at least {_fmt(change)} points and ended "
            f"with a primary balance at or below {_fmt(pb_2045)}% of GDP: {labels}. The qualifying window is not "
            f"a close analogue of smooth S0 drift: its summed inflation contribution is {_fmt(first['inflation_contribution'])} "
            f"points and SFA is {_fmt(first['sfa'])} points, indicating extreme nominal dynamics and accounting/source residuals."
        )
    primary = estimates[(estimates.analysis == "fiscal_reaction") & (estimates.specification == "primary")]
    frf = primary[primary.term.isin(["debt_lag", "pb_lag", "long_run_debt_response"])].pivot(index="sample", columns="term", values="estimate").reset_index()
    brazil_rg = rg[(rg.row_type == "country_summary") & (rg.iso3 == "BRA")].iloc[0]
    rg_group = decomposition.dropna(subset=["r_minus_g_pct"]).groupby("group")["r_minus_g_pct"].agg(["count", "mean", "median", "std"]).reset_index()
    rg_low = restricted_distribution(decomposition, "r_minus_g_pct")
    sfa_low = restricted_distribution(decomposition, "sfa")
    calibration_rg = rg_low[(rg_low["period"] == "2000-2024") & (rg_low["sample"].isin(["advanced", "emerging", "Brazil"]))]
    low_2000 = decomposition[
        decomposition["year"].between(2000, 2024)
        & (decomposition["deflator_inflation"] < 15.0)
    ]
    emerging_country_rg = low_2000[low_2000["group"] == "emerging"].groupby("iso3")["r_minus_g_pct"].mean().dropna()
    brazil_low_rank = int(emerging_country_rg.rank(ascending=False, method="min").loc["BRA"])
    brazil_period_rg = pd.DataFrame([
        {
            "period": label, "n": values.notna().sum(), "mean": values.mean(),
            "median": values.median(), "p10": values.quantile(.1), "p90": values.quantile(.9),
        }
        for label, start, end in (("2000-2014", 2000, 2014), ("2015-2019", 2015, 2019), ("2020-2024", 2020, 2024))
        for values in [decomposition.loc[
            (decomposition["iso3"] == "BRA") & decomposition["year"].between(start, end),
            "r_minus_g_pct",
        ]]
    ])
    pb_comparison = brazil_primary_balance_comparison(panel)
    pb_mean_gap = pb_comparison["fpp_minus_official_gap"].mean()
    review_specs = estimates[
        estimates["specification"].isin([
            "low_inflation_robustness", "2000_2024_robustness",
            "low_inflation_2000_2024_calibration",
            "brazil_official_pb_2000_2024", "brazil_fpp_pb_2000_2024",
        ])
        & estimates["term"].isin(["debt_lag", "pb_lag", "long_run_debt_response"])
    ]
    review_frf = review_specs.pivot(index=["sample", "specification"], columns="term", values="estimate").reset_index()
    review_nobs = review_specs.groupby(["sample", "specification"], as_index=False)["nobs"].first()
    review_frf = review_frf.merge(review_nobs, on=["sample", "specification"])
    stabilisation = stabilisation_comparison(estimates, decomposition)
    debt_quantiles = pd.DataFrame([
        {"sample": "full panel", "p95": panel["d"].quantile(.95), "p99": panel["d"].quantile(.99)},
        {"sample": "emerging", "p95": panel.loc[panel["group"] == "emerging", "d"].quantile(.95), "p99": panel.loc[panel["group"] == "emerging", "d"].quantile(.99)},
    ])
    rg_decade = rg[rg.row_type == "group_decade_summary"][["group", "decade", "nobs", "mean", "median", "p10", "p90"]]
    jst = rg[rg.row_type == "jst_observation"]
    top_increases = twenty.nlargest(10, "debt_change")[["iso3", "start_year", "end_year", "debt_change", "primary_deficit_contribution", "interest_contribution", "real_growth_contribution", "inflation_contribution", "sfa"]]
    episode_summary = episodes.groupby(["episode_type", "group"]).agg(episodes=("iso3", "size"), median_debt_change=("debt_change", "median"), median_primary=("primary_deficit_contribution", "median"), median_growth=("real_growth_contribution", "median"), median_inflation=("inflation_contribution", "median"), median_interest=("interest_contribution", "median"), median_sfa=("sfa", "median")).reset_index()
    age = estimates[(estimates.analysis == "ageing") & (estimates.term == "age65_change")][["specification", "outcome", "estimate", "standard_error", "nobs"]]
    sfa = decomposition["sfa"].agg(["count", "mean", "std", "median"])
    large_sfa = decomposition[decomposition["large_sfa_flag"]].sort_values(["iso3", "year"])
    coverage = windows[windows.row_type == "country_summary"][["iso3", "group", "start_year", "end_year", "debt_observations", "pb_observations", "interest_observations", "growth_observations", "inflation_observations", "decomposition_observations", "longest_increase_run"]]
    peaks = windows[windows.row_type == "peak"]
    peak_summary = pd.DataFrame([
        {"horizon": horizon, "nobs": peaks[f"change_after_{horizon}y"].notna().sum(),
         "mean_change": peaks[f"change_after_{horizon}y"].mean(), "median_change": peaks[f"change_after_{horizon}y"].median(),
         "p10_change": peaks[f"change_after_{horizon}y"].quantile(.1), "p90_change": peaks[f"change_after_{horizon}y"].quantile(.9)}
        for horizon in (5, 10)
    ])
    lines = [
        "# D3 cross-country debt trajectories", "",
        "## Findings for the S0 comparison", "",
        f"S0's median debt increase from 78.6% of GDP in 2025 to {_fmt(s0[('debt_gdp', 2045)])}% in 2045 is {_fmt(change)} percentage points; with the C5 feedback it reaches {_fmt(s0[('debt_gdp_with_feedback', 2045)])}%. The no-feedback change is at the {_fmt(all_debt_pct, 1)}th percentile of the {len(twenty)} observed 20-year changes and the {_fmt(em_debt_pct, 1)}th percentile among emerging-economy windows. The 2045 primary balance of {_fmt(pb_2045)}% of GDP is at the {_fmt(all_pb_pct, 1)}th percentile overall and {_fmt(em_pb_pct, 1)}th percentile among emerging observations (lower means a larger deficit).",
        "",
        joint_text,
        "",
        "The primary fiscal-reaction estimates below are percentage points of primary balance per one-point lagged-debt change. The long-run response is rho/(1-phi). Brazil is time-series OLS with two-lag Newey-West uncertainty; the panel estimates use country fixed effects and country-clustered uncertainty.", "",
        *_markdown(frf, 4), "",
        f"In the calibration-relevant low-inflation 2000-2024 sample, r-g averaged {_fmt(calibration_rg.loc[calibration_rg['sample'] == 'advanced', 'mean'].iloc[0])}% for advanced economies and {_fmt(calibration_rg.loc[calibration_rg['sample'] == 'emerging', 'mean'].iloc[0])}% for emerging economies; Brazil averaged {_fmt(calibration_rg.loc[calibration_rg['sample'] == 'Brazil', 'mean'].iloc[0])}%. Full-sample results are reported only in the lead-review robustness section because high-inflation accounting contaminates both r-g and SFA.", "",
        "r-g by group and decade:", "", *_markdown(rg_decade, 2), "",
        f"The JST robustness sample contains {len(jst)} country-years in 1950-2020 and has mean r-g {_fmt(jst['r_minus_g_pct'].mean())}% (long-term rate minus nominal GDP growth, using the exact ratio formula).", "",
        "## Largest 20-year debt increases", "",
        "Contributions are summed annual percentage points for years with a complete decomposition; SFA closes each annual identity.", "",
        *_markdown(top_increases, 2), "",
        "## Large reductions and increases", "",
        "A reduction starts at a complete-neighborhood local peak and reaches a fall of at least 15 points within ten years. An increase is every observed start year from which debt reaches at least 30 points higher within ten years; overlapping starts are retained, as the fixed protocol does not prescribe de-duplication.", "",
        *_markdown(episode_summary, 2), "",
        "The signs in this table identify accounting associations, not causal effects. Positive primary-deficit, interest, or SFA contributions raise debt; negative real-growth and inflation contributions reduce the debt ratio.", "",
        "Debt after local peaks:", "", *_markdown(peak_summary, 2), "",
        "## Ageing and primary spending", "",
        *_markdown(age, 4), "",
        f"S0's implied spending slope is {_fmt(s0[('ageing_spending_ratio', 2045)], 4)} points of GDP per one-point increase in the 65+ share: spending rises from 40.00% to {_fmt(s0[('spending_pct_gdp', 2045)])}% while the IBGE share rises from {_fmt(s0[('age65_share', 2025)])}% to {_fmt(s0[('age65_share', 2045)])}%. In the historical 20-year windows, faster ageing was associated with primary-balance deterioration (the slope shown above is negative), qualitatively like S0, but not with a debt-and-deficit combination as extreme as S0 except the jointly qualifying window identified above. Overlapping windows and common shocks prevent a causal interpretation.", "",
        "## Brazil and IFI comparison", "",
        f"Brazil has {int(panel[(panel.iso3 == 'BRA') & panel.d.notna()].shape[0])} debt observations in 1975-2024 and {int(decomposition[decomposition.iso3 == 'BRA'].shape[0])} complete annual decompositions. S0 reaches {_fmt(s0[('debt_gdp', 2035)])}% in 2035, versus IFI RAF 113's 111.6% base case, 80.9% optimistic case, and 148.1% pessimistic case. S0's 2035 primary balance is {_fmt(s0[('primary_balance_gdp', 2035)])}% of GDP, compared with the report's primary deficit near 1% of GDP.", "",
        "## Lead-review robustness (2026-10-21)", "",
        "### High-inflation contamination and calibration samples", "",
        f"The unrestricted means are r-g {_fmt(rg_group.loc[rg_group.group == 'emerging', 'mean'].iloc[0])}% for emerging economies and {_fmt(brazil_rg['mean'])}% for Brazil. The unrestricted emerging SFA mean is {_fmt(decomposition.loc[decomposition.group == 'emerging', 'sfa'].mean())} points. These full-sample values are not suitable for calibration: in high-inflation years the FPP interest series behaves like a real/operational-interest measure while the inflation correction is left in SFA (Brazil 1976-1986 is the clearest case). Low inflation means GDP-deflator inflation below 15% in the observation year.", "",
        "Low-inflation r-g distribution (%):", "", *_markdown(rg_low[["period", "sample", "n", "mean", "median", "p10", "p90"]], 2), "",
        "Low-inflation SFA distribution (percentage points of GDP):", "", *_markdown(sfa_low[["period", "sample", "n", "mean", "median", "p10", "p90"]], 2), "",
        f"On country-average r-g in the low-inflation 2000-2024 sample, Brazil ranks {brazil_low_rank} of {len(emerging_country_rg)} emerging economies from highest to lowest.", "",
        "Brazil r-g by period (all available observations, %):", "", *_markdown(brazil_period_rg, 2), "",
        "### Brazil primary-balance check", "",
        "The official series uses the BCB NFSP convention, in which positive values are deficits; the table converts it to primary balance by multiplying by -1. The gap is FPP minus official, in percentage points of GDP.", "",
        *_markdown(pb_comparison, 2), "",
        f"Across the {len(pb_comparison)} overlapping years, the mean FPP-minus-official gap is {_fmt(pb_mean_gap)} points. Brazil-specific fiscal-reaction analysis should use the official BCB balance with FPP debt; the FPP-balance regression is retained only as a comparison.", "",
        "### Fiscal-reaction robustness", "",
        "The low-inflation panel restriction applies to the current observation year. All specifications retain the same debt, output-gap, and lagged-primary-balance regressors; Brazil uses OLS with Newey-West covariance at two lags. Long-run response is rho/(1-phi).", "",
        *_markdown(review_frf, 4), "",
        "Small-sample warning: the Brazil estimates have only one short time series, and the official-balance regression loses its first available observation to the lag.", "",
        "### Stabilisation arithmetic", "",
        "The response needed per point of debt is `(r-g)/(1+g)`, with rates expressed as decimals. The emerging-median benchmark uses the same 2% growth assumption as the Brazil historical benchmark. A `yes` only means the estimated long-run response is at least this arithmetic threshold; it is not a forecast or a model change.", "",
        *_markdown(stabilisation, 4), "",
        "### Historical debt distribution", "",
        *_markdown(debt_quantiles, 2), "",
        "The data contain no default/restructuring flag, so the maximum debt reached by an emerging economy without such a flag cannot be identified defensibly. The emerging p95 and p99 are reported instead. `historical_p99_debt_pct_gdp` in the proposed YAML replaces the former diagnostic-ceiling name; it remains descriptive, not a sustainability limit.", "",
        "## Accounting diagnostics and coverage", "",
        f"The decomposition has {int(sfa['count'])} observations. SFA has mean {_fmt(sfa['mean'])}, standard deviation {_fmt(sfa['std'])}, and median {_fmt(sfa['median'])} percentage points; {int(decomposition.large_sfa_flag.sum())} observations exceed 10 points in absolute value. These large residuals can reflect defaults, bank support, valuation changes, perimeter/definition changes, or mismatched source concepts and should not be assigned a cause from these data alone.", "",
        "All observations with absolute SFA above 10 points:", "",
        *_markdown(large_sfa[["iso3", "year", "delta_d", "sfa"]], 2), "",
        "Country debt coverage and longest annual increase runs:", "",
        *_markdown(coverage, 0), "",
        "## Implications for a lead-developer decision", "",
        "- Test an S0 robustness variant with the estimated emerging-economy fiscal response, while retaining uncertainty and reporting ranges.",
        "- Calibrate r-g and SFA from the emerging distribution and show Brazil separately; do not treat either residual accounting term as a policy effect.",
        "- Keep inflation as an explicit debt-ratio channel. Historical inflation contributions can be large, but the evidence does not imply that inflation is a costless adjustment mechanism.",
        "- The within-country r-g/debt slope is evidence about feedback, not a structural risk-premium estimate. The proposed YAML therefore labels any debt ceiling as a diagnostic bound rather than an estimated sustainability limit.", "",
        "## Limitations", "",
        "The fiscal data are IMF historical reconstructions and can mix government perimeters across countries and time. WDI deflator inflation and real growth do not always match the fiscal-series denominator, so SFA also absorbs source mismatch. Dynamic fixed effects are biased in short panels; Brazil's sample is small; HP output gaps are end-point sensitive. Overlapping 20-year windows are dependent observations. Peaks require all 11 annual debt observations in the +/-5-year neighborhood. No missing value is interpolated, and JST is a robustness dataset for advanced economies only.", "",
    ]
    return "\n".join(lines)


def render_docs() -> str:
    return "\n".join([
        "# D3 debt-panel method", "",
        "`python -m src.debt_panel` reads only archived files and deterministically rebuilds the six CSVs, report, method note, and proposed-calibration YAML.", "",
        "## Data and panel", "",
        "The sample is the fixed list of 24 advanced and 26 emerging economies for 1975-2024. IMF Public Finances in Modern History supplies debt, primary balance, interest and primary expenditure. WEO, HPDD and GDD debt fields are cross-check columns only. WDI supplies real growth, GDP-deflator inflation and ageing measures. Rows with missing observations remain missing; nothing is interpolated. The archived JST file has an `.xlsx` suffix but Stata 118 content, so it is read with `pandas.read_stata`.", "",
        "## Accounting", "",
        "For exact annual lags, nominal growth is `(1+g)(1+pi)-1`. Contributions follow the formulas fixed in `tasks/D3.md`; SFA is the residual that makes their sum equal the observed debt change. Effective interest and r-g are missing when lagged debt is below 5% of GDP. Large SFA means absolute SFA above 10 points. Calibration summaries restrict the sample to years with GDP-deflator inflation below 15% and to 2000-2024 because the FPP interest/SFA split is not comparable in high-inflation years.", "",
        "## Trajectories and episodes", "",
        "A 20-year window requires observed debt at both exact endpoints. Cumulative primary balance and decomposition contributions report their observation counts and are never gap-filled. Local peaks require a complete +/-5-year debt neighborhood. Reductions use the lowest subsequent debt within ten years from a peak and require a 15-point fall. Increases retain every start year whose maximum debt within ten years is at least 30 points higher; overlaps are intentionally visible.", "",
        "## Estimation", "",
        "The output gap is the log real-GDP index reconstructed from WDI growth minus an HP trend (lambda 100) within uninterrupted segments. Panel FRFs use within-country demeaning and country-clustered covariance with finite-sample correction. Brazil uses OLS with an intercept and Bartlett Newey-West covariance with two lags. Robustness rows add debt squared/cubed, omit lagged primary balance, start in 1990, restrict current observations to inflation below 15%, or restrict the period to 2000-2024. Long-run response is rho/(1-phi). Cubic fatigue is the lowest real zero of the marginal debt response inside the observed estimation range.", "",
        "For the Brazil 2000-2024 robustness, the BCB primary-result series is converted from NFSP signs (positive is a deficit) to primary-balance signs and paired with FPP debt. The FPP primary-balance version is retained as a direct comparison. No balance observation is interpolated. Stabilisation thresholds are arithmetic comparisons of long-run FRF responses with `(r-g)/(1+g)` and do not alter the debt model.", "",
        "The ageing regressions use all exact-endpoint 20-year windows with an advanced-economy dummy and country-clustered uncertainty. A fixed 1995-2024 long difference is labelled robustness. These regressions are descriptive because ageing, spending and fiscal balances respond to common shocks and institutions.", "",
        "## Important limitations", "",
        "Country definitions and fiscal perimeters can change. WDI macro series need not share the fiscal data denominator, making SFA partly a source-alignment residual. Fixed-effects dynamic-panel estimates may have Nickell bias. Cluster inference has only 24 or 26 clusters in group estimates, and Brazil HAC inference is small-sample. HP gaps are endpoint-sensitive. The panel has no default/restructuring flag, so it cannot identify a maximum non-default debt observation. Overlapping windows and episodes are not independent. JST long rates are market yields, whereas the main panel uses an effective debt-service rate.", "",
    ])


def proposed_config(panel: pd.DataFrame, decomposition: pd.DataFrame, estimates: pd.DataFrame, rg: pd.DataFrame) -> dict:
    full_primary = estimates[(estimates.analysis == "fiscal_reaction") & (estimates.specification == "primary") & (estimates["sample"] == "emerging")].set_index("term")
    primary = estimates[
        (estimates.analysis == "fiscal_reaction")
        & (estimates.specification == "low_inflation_2000_2024_calibration")
        & (estimates["sample"] == "emerging")
    ].set_index("term")
    calibration = decomposition[
        decomposition["year"].between(2000, 2024)
        & (decomposition["deflator_inflation"] < 15.0)
    ]
    emerging_rg = calibration.loc[calibration.group == "emerging", "r_minus_g_pct"].dropna()
    brazil_rg = calibration.loc[calibration.iso3 == "BRA", "r_minus_g_pct"].dropna()
    emerging_sfa = calibration.loc[calibration.group == "emerging", "sfa"].dropna()
    brazil_sfa = calibration.loc[calibration.iso3 == "BRA", "sfa"].dropna()
    full_emerging_rg = decomposition.loc[decomposition.group == "emerging", "r_minus_g_pct"].dropna()
    full_brazil_rg = decomposition.loc[decomposition.iso3 == "BRA", "r_minus_g_pct"].dropna()
    full_emerging_sfa = decomposition.loc[decomposition.group == "emerging", "sfa"].dropna()
    full_brazil_sfa = decomposition.loc[decomposition.iso3 == "BRA", "sfa"].dropna()
    full_slope = rg[rg.row_type == "debt_fe_slope"].iloc[0]
    slope = rg[rg.row_type == "debt_fe_slope_low_inflation_2000_2024"].iloc[0]
    summary = lambda values: {
        "n": int(values.count()), "mean": float(values.mean()),
        "median": float(values.median()), "sd": float(values.std(ddof=1)),
        "p10": float(values.quantile(.1)), "p90": float(values.quantile(.9)),
    }
    return {
        "task": "D3",
        "status": "proposals_only_not_read_by_model",
        "fiscal_reaction": {
            "sample_definition": "GDP-deflator inflation below 15% in that year, 2000-2024",
            "rho": {"proposed": float(primary.loc["debt_lag", "estimate"]), "derivation": "Emerging-country FE coefficient on lagged debt", "output": "data/debt_panel/frf_estimates.csv"},
            "phi": {"proposed": float(primary.loc["pb_lag", "estimate"]), "derivation": "Emerging-country FE coefficient on lagged primary balance", "output": "data/debt_panel/frf_estimates.csv"},
            "long_run": {"proposed": float(primary.loc["long_run_debt_response", "estimate"]), "derivation": "rho/(1-phi), emerging-country FE", "output": "data/debt_panel/frf_estimates.csv"},
        },
        "r_minus_g_pct": {
            "sample_definition": "GDP-deflator inflation below 15% in that year, 2000-2024",
            "emerging": {**summary(emerging_rg), "derivation": "Annual effective-rate r-g observations, emerging sample", "output": "data/debt_panel/r_minus_g.csv"},
            "brazil": {**summary(brazil_rg), "derivation": "Annual effective-rate r-g observations for Brazil", "output": "data/debt_panel/r_minus_g.csv"},
        },
        "stock_flow_adjustment_pp": {
            "sample_definition": "GDP-deflator inflation below 15% in that year, 2000-2024",
            "emerging": summary(emerging_sfa),
            "brazil": summary(brazil_sfa),
            "derivation": "Annual debt-decomposition residuals",
            "output": "data/debt_panel/decomposition.csv",
            "warning": "Heavy-tailed residual including crises, valuation changes, definition changes and cross-source mismatch; use robust sensitivity ranges.",
        },
        "full_sample_not_for_calibration": {
            "reason": "High-inflation observations combine an FPP interest series that behaves like real/operational interest with an inflation correction that lands in SFA, strongly biasing r-g and SFA.",
            "r_minus_g_pct": {
                "emerging": summary(full_emerging_rg),
                "brazil": summary(full_brazil_rg),
            },
            "stock_flow_adjustment_pp": {
                "emerging": summary(full_emerging_sfa),
                "brazil": summary(full_brazil_sfa),
            },
            "fiscal_reaction_emerging": {
                "rho": float(full_primary.loc["debt_lag", "estimate"]),
                "phi": float(full_primary.loc["pb_lag", "estimate"]),
                "long_run": float(full_primary.loc["long_run_debt_response", "estimate"]),
            },
            "r_minus_g_debt_feedback_per_debt_pp": float(full_slope["estimate"]),
        },
        "debt_and_feedback": {
            "historical_p99_debt_pct_gdp": float(panel["d"].quantile(.99)),
            "historical_p95_debt_pct_gdp": float(panel["d"].quantile(.95)),
            "derivation": "99th percentile of observed annual debt in the fixed 50-country panel; descriptive bound, not a sustainability threshold",
            "output": "data/debt_panel/panel.csv",
            "r_minus_g_debt_feedback_per_debt_pp": float(slope["estimate"]),
            "feedback_derivation": "Within-country FE slope of r-g on lagged debt, GDP-deflator inflation below 15%, 2000-2024",
            "feedback_output": "data/debt_panel/r_minus_g.csv",
            "warning": "Association is not an identified risk-premium equation; no evidence-based hard feedback ceiling is estimated.",
        },
    }


def run() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str, dict]:
    panel = build_panel()
    decomposition = decompose_panel(panel)
    windows = build_windows(panel, decomposition)
    estimates = build_estimates(panel, windows)
    episodes = detect_episodes(panel, decomposition)
    rg = build_r_minus_g(decomposition)
    report = render_report(panel, decomposition, windows, estimates, episodes, rg)
    return panel, decomposition, windows, estimates, episodes, rg, report, render_docs(), proposed_config(panel, decomposition, estimates, rg)


def main() -> int:
    panel, decomposition, windows, estimates, episodes, rg, report, docs, config = run()
    frames = {
        "panel": panel, "decomposition": decomposition, "windows": windows,
        "frf": estimates, "episodes": episodes, "r_minus_g": rg,
    }
    for name, frame in frames.items():
        PATHS[name].parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(PATHS[name], index=False, float_format="%.10f")
    PATHS["report"].write_text(report, encoding="utf-8")
    PATHS["docs"].write_text(docs, encoding="utf-8")
    with PATHS["config"].open("w", encoding="utf-8", newline="\n") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
    print(f"Wrote {len(panel)} panel rows, {len(decomposition)} decompositions, {len(windows)} windows, and {len(episodes)} episodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
