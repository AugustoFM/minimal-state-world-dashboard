"""C7 external block v2: fixed annual regressions and honest back-tests.

The module is deliberately self-contained (numpy/pandas only for estimation),
offline, and deterministic.  The primary specifications and windows are fixed
in ``tasks/C7.md``; robustness results never select a model.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from src.external import gdp_and_inflation_effects
from src.macro import read_general_government_fiscal_workbook


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = {
    "external": ROOT / "data/brazil/external_observed.csv",
    "backtest": ROOT / "data/brazil/backtest_observed.csv",
    "fiscal_workbook": ROOT / "data/raw/brazil/demonstrativos-governo-geral.xlsx",
    "parameters": ROOT / "config/parameters.yaml",
    "estimates": ROOT / "data/brazil/c7_estimates.csv",
    "backtest_output": ROOT / "data/brazil/c7_backtest.csv",
    "config": ROOT / "config/c7_proposed.yaml",
    "report": ROOT / "outputs/c7_backtest.md",
    "docs": ROOT / "docs/c7_external_v2.md",
}
Z90 = 1.6448536269514722


PRIMARY_SPECS = {
    "A_output": {
        "dependent": "gdp_growth_pct", "regressors": ["dlnP", "dlnP_lag", "world_gdp_growth_pct"],
        "constant": True, "fit": (2000, 2014), "test": (2015, 2024), "key": "dlnP", "sign": 1,
    },
    "B1_spread": {
        "dependent": "dEMBI", "regressors": ["dlnP", "dUS"],
        "constant": True, "fit": (2000, 2014), "test": (2015, 2024), "key": "dlnP", "sign": -1,
    },
    "B2_real_rate": {
        "dependent": "dr", "regressors": ["dEMBI_per_100"],
        "constant": True, "fit": (2000, 2014), "test": (2015, 2024), "key": "dEMBI_per_100", "sign": 1,
    },
    "B3_debt_rate": {
        "dependent": "dimplicit", "regressors": ["dr", "dr_lag"],
        "constant": False, "fit": (2011, 2017), "test": (2018, 2024), "key": "dr", "sign": 1,
    },
    "C_investment": {
        "dependent": "dinvestment_rate", "regressors": ["dlnP", "dlnP_lag"],
        "constant": True, "fit": (2000, 2014), "test": (2015, 2024), "key": "dlnP", "sign": 1,
    },
    "D_revenue": {
        "dependent": "commodity_revenue_pct_gdp", "regressors": ["lnP"],
        "constant": True, "fit": (2010, 2017), "test": (2018, 2024), "key": "lnP", "sign": 1,
    },
    "D_dividends": {
        "dependent": "dividends_pct_gdp", "regressors": ["lnP"],
        "constant": True, "fit": (2010, 2017), "test": (2018, 2024), "key": "lnP", "sign": 1,
    },
    "D_concessions": {
        "dependent": "concessions_pct_gdp", "regressors": ["lnP"],
        "constant": True, "fit": (2010, 2017), "test": (2018, 2024), "key": "lnP", "sign": 1,
    },
}

ROBUSTNESS_SPECS = {
    "A_output_CTOT": {
        **PRIMARY_SPECS["A_output"], "regressors": ["dlnCTOT", "dlnCTOT_lag", "world_gdp_growth_pct"], "key": "dlnCTOT",
    },
    "A_output_china": {
        **PRIMARY_SPECS["A_output"], "regressors": ["dlnP", "dlnP_lag", "world_gdp_growth_pct", "china_gdp_growth_pct"],
    },
    "B1_spread_fed_funds": {
        **PRIMARY_SPECS["B1_spread"], "regressors": ["dlnP", "dFed"],
    },
    "A_output_reverse": {
        **PRIMARY_SPECS["A_output"], "fit": (2010, 2024), "test": (2000, 2009),
    },
    "B1_spread_reverse": {
        **PRIMARY_SPECS["B1_spread"], "fit": (2010, 2024), "test": (2000, 2009),
    },
    "C_investment_reverse": {
        **PRIMARY_SPECS["C_investment"], "fit": (2010, 2024), "test": (2000, 2009),
    },
}


def _long_to_wide(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    needed = {"year", "indicator", "value"}
    if not needed.issubset(frame.columns):
        raise ValueError(f"{path} lacks {sorted(needed - set(frame.columns))}")
    if frame.duplicated(["year", "indicator"]).any():
        raise ValueError(f"{path} has duplicate year/indicator rows")
    return frame.pivot(index="year", columns="indicator", values="value").sort_index()


def read_commodity_revenue(path: str | Path = DEFAULT_PATHS["fiscal_workbook"]) -> pd.DataFrame:
    """Read exact GFS codes 1412 and 1415 from annual sheet 3.2.a."""
    frame = pd.read_excel(path, sheet_name="3.2.a", header=None)
    codes = pd.to_numeric(frame.iloc[:, 0], errors="coerce")
    matches = {code: frame.loc[codes.eq(code)] for code in (1412, 1415)}
    if any(len(rows) != 1 for rows in matches.values()):
        raise ValueError("Expected exactly one row each for GFS codes 1412 and 1415")
    records = []
    for column in range(frame.shape[1]):
        year = pd.to_numeric(pd.Series([frame.iloc[3, column]]), errors="coerce").iloc[0]
        if pd.isna(year) or not 2010 <= int(year) <= 2024:
            continue
        dividend = float(matches[1412].iloc[0, column]) * 100.0
        concession = float(matches[1415].iloc[0, column]) * 100.0
        records.append({
            "year": int(year), "dividends_pct_gdp": dividend,
            "concessions_pct_gdp": concession,
            "commodity_revenue_pct_gdp": dividend + concession,
        })
    return pd.DataFrame(records).set_index("year").sort_index()


def load_prepare_data(
    external_path: str | Path = DEFAULT_PATHS["external"],
    backtest_path: str | Path = DEFAULT_PATHS["backtest"],
    workbook_path: str | Path = DEFAULT_PATHS["fiscal_workbook"],
) -> pd.DataFrame:
    """Load checked-in observations and create only the fixed transformations."""
    external = _long_to_wide(external_path)
    observed = _long_to_wide(backtest_path)
    data = external.join(observed, how="outer").join(read_commodity_revenue(workbook_path), how="outer")
    data.index = data.index.astype(int)
    data.index.name = "year"
    data["lnP"] = np.log(data["commodity_export_price_index"])
    data["dlnP"] = data["lnP"].diff() * 100.0
    data["dlnP_lag"] = data["dlnP"].shift(1)
    data["lnCTOT"] = np.log(data["commodity_tot_index"])
    data["dlnCTOT"] = data["lnCTOT"].diff() * 100.0
    data["dlnCTOT_lag"] = data["dlnCTOT"].shift(1)
    data["dUS"] = data["us_10y_yield_pct"].diff()
    data["dFed"] = data["us_fed_funds_pct"].diff()
    data["dEMBI"] = data["embi_brazil_spread_bp"].diff()
    data["dEMBI_per_100"] = data["dEMBI"] / 100.0
    data["real_policy_rate"] = data["selic_pct"] - data["ipca_12m_pct"]
    data["dr"] = data["real_policy_rate"].diff()
    data["dr_lag"] = data["dr"].shift(1)
    data["dinvestment_rate"] = data["investment_rate_pct_gdp"].diff()

    debt = data["gross_general_government_debt_pct_gdp"]
    implicit = pd.Series(index=data.index, dtype=float)
    for year in range(2011, 2025):
        fiscal = read_general_government_fiscal_workbook(workbook_path, year)
        implicit.loc[year] = float(fiscal["interest_payable_gdp"]) / float(debt.loc[year - 1]) * 100.0
    data["implicit_interest_pct"] = implicit
    data["dimplicit"] = data["implicit_interest_pct"].diff()
    return data.sort_index()


def ols_newey_west(y: Sequence[float], x: Sequence[Sequence[float]], lag: int = 1) -> dict:
    """OLS with Bartlett Newey-West covariance (no finite-sample correction)."""
    yv = np.asarray(y, dtype=float)
    xv = np.asarray(x, dtype=float)
    if xv.ndim != 2 or yv.ndim != 1 or len(yv) != len(xv):
        raise ValueError("y must be 1D and x 2D with the same row count")
    if not np.isfinite(yv).all() or not np.isfinite(xv).all():
        raise ValueError("OLS input contains non-finite values")
    n, k = xv.shape
    if n <= k or np.linalg.matrix_rank(xv) < k:
        raise ValueError("OLS design is rank deficient or has no residual degrees of freedom")
    beta = np.linalg.lstsq(xv, yv, rcond=None)[0]
    residual = yv - xv @ beta
    meat = np.zeros((k, k), dtype=float)
    scores = xv * residual[:, None]
    meat += scores.T @ scores
    for ell in range(1, min(int(lag), n - 1) + 1):
        weight = 1.0 - ell / (lag + 1.0)
        gamma = scores[ell:].T @ scores[:-ell]
        meat += weight * (gamma + gamma.T)
    bread = np.linalg.inv(xv.T @ xv)
    covariance = bread @ meat @ bread
    se = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    centered = yv - yv.mean()
    tss = float(centered @ centered)
    r2 = math.nan if tss == 0 else 1.0 - float(residual @ residual) / tss
    return {"beta": beta, "se": se, "covariance": covariance, "residual": residual, "r2": r2, "nobs": n}


def _estimate_one(data: pd.DataFrame, name: str, spec: Mapping) -> dict:
    columns = [spec["dependent"], *spec["regressors"]]
    sample = data.loc[spec["fit"][0]:spec["fit"][1], columns].dropna()
    x = sample[list(spec["regressors"])].to_numpy(dtype=float)
    names = list(spec["regressors"])
    if spec["constant"]:
        x = np.column_stack([np.ones(len(sample)), x])
        names = ["constant", *names]
    result = ols_newey_west(sample[spec["dependent"]].to_numpy(dtype=float), x, lag=1)
    coefficients = {term: float(value) for term, value in zip(names, result["beta"])}
    standard_errors = {term: float(value) for term, value in zip(names, result["se"])}
    return {
        "name": name, "dependent": spec["dependent"], "regressors": list(spec["regressors"]),
        "constant": bool(spec["constant"]), "coefficients": coefficients,
        "standard_errors": standard_errors, "r2": float(result["r2"]), "nobs": int(result["nobs"]),
        "fit_window": [int(spec["fit"][0]), int(spec["fit"][1])],
        "test_window": [int(spec["test"][0]), int(spec["test"][1])],
        "estimation_years": [int(year) for year in sample.index],
        "dependent_fit_mean": float(sample[spec["dependent"]].mean()),
        "regressor_fit_means": {column: float(sample[column].mean()) for column in spec["regressors"]},
        "key_coefficient": str(spec["key"]), "expected_sign": int(spec["sign"]),
    }


def estimate_channels(window: str = "primary", data: pd.DataFrame | None = None) -> dict[str, dict]:
    """Estimate primary, robustness, or all fixed specifications."""
    source = load_prepare_data() if data is None else data
    if window == "primary":
        specs = PRIMARY_SPECS
    elif window in {"robustness", "reverse"}:
        specs = ROBUSTNESS_SPECS if window == "robustness" else {k: v for k, v in ROBUSTNESS_SPECS.items() if k.endswith("_reverse")}
    elif window == "all":
        specs = {**PRIMARY_SPECS, **ROBUSTNESS_SPECS}
    else:
        raise ValueError("window must be 'primary', 'robustness', 'reverse', or 'all'")
    return {name: _estimate_one(source, name, spec) for name, spec in specs.items()}


def predict(data: pd.DataFrame, model: Mapping) -> pd.Series:
    """Predict one estimated model, preserving the supplied frame's index."""
    out = pd.Series(0.0, index=data.index, dtype=float)
    coefficients = model["coefficients"]
    if model.get("constant", "constant" in coefficients):
        out += float(coefficients.get("constant", 0.0))
    for regressor in model["regressors"]:
        out += data[regressor].astype(float) * float(coefficients[regressor])
    required = data[list(model["regressors"])].notna().all(axis=1)
    return out.where(required)


def historical_changes_v2(
    external_path: str | Path = DEFAULT_PATHS["external"],
    backtest_path: str | Path = DEFAULT_PATHS["backtest"],
    workbook_path: str | Path = DEFAULT_PATHS["fiscal_workbook"],
) -> pd.DataFrame:
    """Joint observed changes for block bootstrap, 2000-2024, no interpolation."""
    data = load_prepare_data(external_path, backtest_path, workbook_path)
    out = data.loc[2000:2024, ["dlnP", "dUS", "world_gdp_growth_pct"]].copy()
    if out.isna().any().any() or list(out.index) != list(range(2000, 2025)):
        raise ValueError("Historical v2 changes must be complete for 2000-2024")
    return out


def effects_from_path(path: pd.DataFrame, coefficients: Mapping[str, Mapping]) -> pd.DataFrame:
    """Translate an external path into annual model effects, without global state.

    ``path`` requires dlnP and dUS; world growth is optional and defaults to its
    A fit-window mean (therefore zero output effect).  Intercepts are excluded:
    effects are deviations from a no-shock path.  Annual A growth deviations
    and C investment-rate changes are accumulated into levels.
    """
    required = {"dlnP", "dUS"}
    if not required.issubset(path.columns):
        raise ValueError(f"Path lacks {sorted(required - set(path.columns))}")
    models = coefficients
    a, b1, b2, b3, c, d = (models[key] for key in (
        "A_output", "B1_spread", "B2_real_rate", "B3_debt_rate", "C_investment", "D_revenue"
    ))
    dlnp = path["dlnP"].to_numpy(dtype=float)
    dus = path["dUS"].to_numpy(dtype=float)
    world_mean = float(a["regressor_fit_means"]["world_gdp_growth_pct"])
    world_input = path.get("world_gdp_growth_pct", pd.Series(world_mean, index=path.index)).to_numpy(dtype=float)
    # A literal all-zero path is the public no-shock convention. World growth
    # is a level regressor, so zero here means its fit-window mean. Non-zero
    # supplied paths are interpreted as observed world-growth levels.
    world = np.full(len(path), world_mean) if np.all(world_input == 0.0) else world_input
    lag_price = np.r_[0.0, dlnp[:-1]]
    growth_effect = (
        float(a["coefficients"]["dlnP"]) * dlnp
        + float(a["coefficients"]["dlnP_lag"]) * lag_price
        + float(a["coefficients"]["world_gdp_growth_pct"]) * (world - world_mean)
    )
    gdp_level = (np.cumprod(1.0 + growth_effect / 100.0) - 1.0) * 100.0
    embi = float(b1["coefficients"]["dlnP"]) * dlnp + float(b1["coefficients"]["dUS"]) * dus
    real_rate = float(b2["coefficients"]["dEMBI_per_100"]) * embi / 100.0
    lag_real = np.r_[0.0, real_rate[:-1]]
    debt_rate = float(b3["coefficients"]["dr"]) * real_rate + float(b3["coefficients"]["dr_lag"]) * lag_real
    investment_flow = float(c["coefficients"]["dlnP"]) * dlnp + float(c["coefficients"]["dlnP_lag"]) * lag_price
    investment_level = np.cumsum(investment_flow)
    cumulative_log_price = np.cumsum(dlnp) / 100.0
    revenue = float(d["coefficients"]["lnP"]) * cumulative_log_price
    return pd.DataFrame({
        "gdp_level_pct": gdp_level, "embi_change_bp": embi,
        "real_rate_change_pp": real_rate, "debt_rate_change_pp": debt_rate,
        "revenue_change_pp_gdp": revenue, "investment_rate_change_pp": investment_level,
    }, index=path.index)


def _c6_growth(data: pd.DataFrame, parameters_path: str | Path) -> pd.Series:
    with Path(parameters_path).open(encoding="utf-8") as handle:
        parameters = yaml.safe_load(handle)
    tot = data.loc[2005:2024, "net_barter_terms_of_trade"]
    changes = np.log(tot).diff().dropna() * 100.0
    path = pd.DataFrame({"step": range(1, len(changes) + 1), "tot_change_pct": changes.to_numpy(), "fx_change_pct": 0.0})
    levels = gdp_and_inflation_effects(path, parameters).set_index("step")["external_gdp_level_pct"]
    level_by_year = pd.Series([0.0, *levels.to_list()], index=range(2005, 2025))
    growth = ((1.0 + level_by_year / 100.0) / (1.0 + level_by_year.shift(1) / 100.0) - 1.0) * 100.0
    return growth.dropna()


def _metrics(frame: pd.DataFrame, predicted: str) -> dict[str, float]:
    valid = frame[["observed", predicted]].dropna()
    residual = valid[predicted] - valid["observed"]
    return {
        "mean_error": float(residual.mean()),
        "rmse": float(np.sqrt(np.mean(np.square(residual)))),
        "sign_agreement": float((np.sign(valid[predicted]) == np.sign(valid["observed"])).mean()),
        "nobs": int(len(valid)),
    }


def build_backtests(data: pd.DataFrame, models: Mapping[str, Mapping], parameters_path: str | Path = DEFAULT_PATHS["parameters"]) -> tuple[pd.DataFrame, dict]:
    rows, summaries = [], {}
    c6 = _c6_growth(data, parameters_path)
    for name, spec in PRIMARY_SPECS.items():
        model = models[name]
        test = data.loc[spec["test"][0]:spec["test"][1]].copy()
        predicted = predict(test, model)
        naive = pd.Series(model["dependent_fit_mean"], index=test.index)
        c6_values = c6.reindex(test.index) if name == "A_output" else pd.Series(np.nan, index=test.index)
        for year in test.index:
            observed = test.loc[year, spec["dependent"]]
            if pd.isna(observed) or pd.isna(predicted.loc[year]):
                continue
            rows.append({
                "channel": name, "year": int(year), "observed": float(observed),
                "predicted": float(predicted.loc[year]), "residual": float(predicted.loc[year] - observed),
                "naive": float(naive.loc[year]),
                "c6": float(c6_values.loc[year]) if pd.notna(c6_values.loc[year]) else math.nan,
                "is_2020": int(year == 2020),
                "embi_2024_partial": int(name == "B1_spread" and year == 2024),
            })
        channel = pd.DataFrame([row for row in rows if row["channel"] == name])
        metrics = _metrics(channel, "predicted")
        naive_metrics = _metrics(channel, "naive")
        no_2020 = channel.loc[channel["year"].ne(2020)]
        without_2020 = _metrics(no_2020, "predicted")
        naive_without_2020 = _metrics(no_2020, "naive")
        c6_metrics = _metrics(channel, "c6") if name == "A_output" else None
        c6_without_2020 = _metrics(no_2020, "c6") if name == "A_output" else None
        sign_ok = float(model["coefficients"][model["key_coefficient"]]) * int(model["expected_sign"]) > 0
        verdict = "supported" if metrics["rmse"] < naive_metrics["rmse"] and sign_ok else "not supported"
        model["verdict"] = verdict
        summaries[name] = {
            "model": metrics, "naive": naive_metrics, "without_2020": without_2020,
            "naive_without_2020": naive_without_2020, "c6": c6_metrics,
            "c6_without_2020": c6_without_2020,
            "sign_consistent": bool(sign_ok), "verdict": verdict,
        }
    return pd.DataFrame(rows), summaries


def _compound(values: pd.Series) -> float:
    return (float(np.prod(1.0 + values.to_numpy(dtype=float) / 100.0)) - 1.0) * 100.0


def episode_table(data: pd.DataFrame, models: Mapping[str, Mapping], parameters_path: str | Path = DEFAULT_PATHS["parameters"]) -> pd.DataFrame:
    a_predictions = predict(data, models["A_output"])
    c6 = _c6_growth(data, parameters_path)
    rows = []
    for label, first, last in (("commodity boom", 2006, 2010), ("domestic recession", 2014, 2016)):
        rows.append({
            "episode": label, "period": f"{first}-{last}",
            "observed_cumulative_growth_pct": _compound(data.loc[first:last, "gdp_growth_pct"]),
            "A_cumulative_growth_pct": _compound(a_predictions.loc[first:last]),
            "C6_cumulative_growth_pct": _compound(c6.loc[first:last]),
        })
    return pd.DataFrame(rows)


def estimates_table(models: Mapping[str, Mapping]) -> pd.DataFrame:
    rows = []
    for name, model in models.items():
        for coefficient, value in model["coefficients"].items():
            se = float(model["standard_errors"][coefficient])
            rows.append({
                "channel": name, "coefficient": coefficient, "estimate": float(value), "newey_west_se": se,
                "ci90_low": float(value) - Z90 * se, "ci90_high": float(value) + Z90 * se,
                "nobs": model["nobs"], "r2": model["r2"],
                "fit_start": model["fit_window"][0], "fit_end": model["fit_window"][1],
                "actual_fit_years": ";".join(map(str, model["estimation_years"])),
                "test_start": model["test_window"][0], "test_end": model["test_window"][1],
                "verdict": model.get("verdict", "robustness only"),
            })
    return pd.DataFrame(rows)


def _fmt(value: float) -> str:
    return "NA" if value is None or not math.isfinite(float(value)) else f"{float(value):.3f}"


def _markdown_table(frame: pd.DataFrame, formats: Mapping[str, str] | None = None) -> list[str]:
    formats = formats or {}
    headers = list(frame.columns)
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in frame.itertuples(index=False, name=None):
        values = []
        for column, value in zip(headers, row):
            if pd.isna(value):
                values.append("NA")
            elif column in formats:
                values.append(format(value, formats[column]))
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def render_report(data: pd.DataFrame, models: Mapping[str, Mapping], summaries: Mapping, episodes: pd.DataFrame) -> str:
    primary = estimates_table({k: models[k] for k in PRIMARY_SPECS})
    coefficient_view = primary[["channel", "coefficient", "estimate", "newey_west_se", "ci90_low", "ci90_high", "nobs", "r2"]]
    summary_rows = []
    for name in PRIMARY_SPECS:
        summary = summaries[name]
        summary_rows.append({
            "channel": name, "RMSE": summary["model"]["rmse"], "naive RMSE": summary["naive"]["rmse"],
            "mean error": summary["model"]["mean_error"], "sign agreement": summary["model"]["sign_agreement"],
            "RMSE excl. 2020": summary["without_2020"]["rmse"],
            "naive excl. 2020": summary["naive_without_2020"]["rmse"],
            "C6 RMSE": summary["c6"]["rmse"] if summary["c6"] else math.nan, "verdict": summary["verdict"],
        })
    summary_frame = pd.DataFrame(summary_rows)
    robust_rows = []
    for name, spec in ROBUSTNESS_SPECS.items():
        model = models[name]
        test = data.loc[spec["test"][0]:spec["test"][1]]
        diagnostic = pd.DataFrame({
            "observed": test[spec["dependent"]], "predicted": predict(test, model),
            "naive": model["dependent_fit_mean"],
        }).dropna()
        metric = _metrics(diagnostic, "predicted")
        naive_metric = _metrics(diagnostic, "naive")
        key = model["key_coefficient"]
        robust_rows.append({
            "channel": name, "coefficient": key, "estimate": model["coefficients"][key],
            "newey_west_se": model["standard_errors"][key], "nobs fit": model["nobs"],
            "test RMSE": metric["rmse"], "naive RMSE": naive_metric["rmse"],
            "sign agreement": metric["sign_agreement"],
        })
    robust_keys = pd.DataFrame(robust_rows)
    h = models["B3_debt_rate"]["coefficients"]
    lines = [
        "# C7 external block v2: fixed-protocol back-test", "",
        "The primary specifications were fixed before estimation. No specification was selected after seeing 2015-2024 outcomes. "
        "The main 2000-2014 fits contain only 15 annual observations; B3 is smaller still (six usable differences, 2012-2017). "
        "OLS uncertainty is Newey-West with one lag, and 90% intervals are normal approximations.", "",
        "## Primary estimates", "",
        *_markdown_table(coefficient_view, {"estimate": ".4f", "newey_west_se": ".4f", "ci90_low": ".4f", "ci90_high": ".4f", "r2": ".3f"}), "",
        f"B3 pass-through of a one percentage-point policy real-rate change is {h['dr']:.3f} pp in year 1 and {h['dr'] + h['dr_lag']:.3f} pp cumulatively by year 2.", "",
        "## Out-of-sample results", "",
        "Residual and mean error are predicted minus observed. Sign agreement is the fraction of years with equal observed/predicted signs. "
        "The D regressions are levels, so their sign agreement is mechanically uninformative. The C6 column is the standalone C6 external growth contribution, not a complete GDP forecast.", "",
        *_markdown_table(summary_frame, {"RMSE": ".3f", "naive RMSE": ".3f", "mean error": "+.3f", "sign agreement": ".1%", "RMSE excl. 2020": ".3f", "naive excl. 2020": ".3f", "C6 RMSE": ".3f"}), "",
        "A verdict is `supported` only when the fixed model's test RMSE beats the fit-window-mean naive benchmark and its key coefficient has the prespecified literature-consistent sign. "
        "Dividends and concessions are reported separately but do not create extra searched specifications.", "",
        "The rule produces two knife-edge cases: B2 beats naive RMSE by only "
        f"{summaries['B2_real_rate']['naive']['rmse'] - summaries['B2_real_rate']['model']['rmse']:.3f} pp and its key 90% interval includes zero; "
        f"total D misses naive by only {summaries['D_revenue']['model']['rmse'] - summaries['D_revenue']['naive']['rmse']:.4f} pp. "
        "A is supported against naive but its annual RMSE is slightly above the standalone C6 contribution. These labels apply the prespecified rule, not a claim of strong validation.", "",
        "## Episodes", "",
        *_markdown_table(episodes, {"observed_cumulative_growth_pct": ".2f", "A_cumulative_growth_pct": ".2f", "C6_cumulative_growth_pct": ".2f"}), "",
        "Channel A is a full conditional growth equation. C6 is only its external GDP-level contribution; the comparison is therefore diagnostic rather than like-for-like.", "",
        "## Fixed robustness checks (not selected)", "",
        *_markdown_table(robust_keys, {"estimate": ".4f", "newey_west_se": ".4f", "test RMSE": ".3f", "naive RMSE": ".3f", "sign agreement": ".1%"}), "",
        "These alternatives are reported without changing any primary verdict: CTOT for Pcx; China growth added to A; federal funds replacing the US 10-year yield in B1; and the prespecified 2010-2024 fit / 2000-2009 reverse tests for A, B1 and C.", "",
        "## Literature reference points", "",
        "Céspedes-Velasco (2012) reports that a roughly 60% commodity-price rise is associated with about +1% output relative to trend and +3.5 pp in the investment rate. "
        f"For the comparable one-off log price change, the fixed C7 coefficients imply about {((1 + (models['A_output']['coefficients']['dlnP'] * math.log(1.6) * 100) / 100) * (1 + (models['A_output']['coefficients']['dlnP_lag'] * math.log(1.6) * 100) / 100) - 1) * 100:.2f}% GDP after two years and "
        f"{(models['C_investment']['coefficients']['dlnP'] + models['C_investment']['coefficients']['dlnP_lag']) * math.log(1.6) * 100:.2f} pp in the investment rate, holding world growth at its fit mean. "
        "These are scale references, not targets imposed on estimation. Uribe-Yue (2006) attributes roughly 20% and 12% of activity variance to US-rate and spread shocks respectively; that variance decomposition is qualitative context and is not directly comparable with these annual equations. "
        "Notably, C7's B1 US-rate coefficient is negative, contrary to the usual positive spread response, and B1 fails its OOS benchmark.", "",
        "## Limits and data warnings", "",
        "- Annual samples are tiny and the models are intentionally parsimonious. HAC intervals are especially fragile for B3's six fit observations.",
        "- EMBI and Selic are endogenous to Brazilian activity and policy; coefficients are predictive associations, not identified causal effects.",
        "- Pcx is a commodity export price index, not an export-volume measure.",
        "- The 2020 pandemic lies in the test window; RMSE is shown both with and without 2020, but the primary verdict uses the fixed full window.",
        "- The 2024 EMBI observation is only an annual mean through July. Its B1 prediction/residual is retained and explicitly flagged in the CSV.",
        "- The fiscal-workbook concessions line includes oil royalties and special participations but is broader than a pure commodity-revenue measure.",
        "- B3 cannot estimate a 2011 difference because the requested implicit-rate series starts in 2011; its actual fit observations are 2012-2017.",
        "- The 2014-2016 collapse contains large domestic political, corruption-investigation and monetary shocks that these external regressors do not explain.", "",
    ]
    return "\n".join(lines)


def render_docs(models: Mapping[str, Mapping], summaries: Mapping) -> str:
    supported = [name for name, value in summaries.items() if value["verdict"] == "supported"]
    return "\n".join([
        "# C7 external block v2", "",
        "`src.external_v2` estimates the prespecified annual Brazilian external-channel equations using only checked-in files. It has no network path and no global estimated state.", "",
        "## Public API", "",
        "- `load_prepare_data()` reads and transforms Pcx, CTOT, US rates, EMBI, macro outcomes, GFS revenue codes 1412/1415, and the GFS implicit interest rate.",
        "- `estimate_channels(window)` returns coefficients, Newey-West standard errors, fit statistics, exact estimation years and fit means for `primary`, `robustness`, `reverse`, or `all`.",
        "- `predict(data, model)` applies one returned model.",
        "- `historical_changes_v2()` returns the complete observed 2000-2024 joint path of `dlnP`, `dUS`, and world GDP growth for a later block bootstrap.",
        "- `effects_from_path(path, coefficients)` returns GDP-level, EMBI, real-rate, debt-rate, commodity-revenue and investment-rate effects. It removes intercepts and centers world growth on A's fit mean, so a zero path produces zero effects.", "",
        "## Units and dynamics", "",
        "`dlnP` is a percent log change, `dUS` is a percentage-point change, and `dEMBI` is basis points. B2 receives `dEMBI / 100`. A's annual growth deviations compound to a GDP-level deviation. C's predicted annual changes cumulate to the investment-rate level. D is evaluated relative to the projection base-year Pcx level. B3 applies contemporaneous and lagged real-rate changes.", "",
        "## Estimation and wiring boundary", "",
        "The point estimates are proposals, not runtime parameters: `config/parameters.yaml` is untouched. The lead developer should wire only mechanically supported channels. Current supported primary equations: " + (", ".join(supported) if supported else "none") + ". See `config/c7_proposed.yaml` for exact proposed mappings and `outputs/c7_backtest.md` for the full limitations and robustness table.", "",
        "The prediction equations are associations. In particular, EMBI and Selic endogeneity prevents a causal reading, and no Monte Carlo integration is performed in C7.", "",
    ])


def config_payload(models: Mapping[str, Mapping], summaries: Mapping) -> dict:
    estimates = {}
    for name, model in models.items():
        coefficients = {}
        for term, value in model["coefficients"].items():
            se = model["standard_errors"][term]
            coefficients[term] = {
                "estimate": float(value), "newey_west_se": float(se),
                "interval_90": [float(value) - Z90 * float(se), float(value) + Z90 * float(se)],
            }
        estimates[name] = {
            "fit_window": model["fit_window"], "test_window": model["test_window"],
            "actual_estimation_years": model["estimation_years"], "nobs": model["nobs"], "r2": model["r2"],
            "coefficients": coefficients, "verdict": model.get("verdict", "robustness only"),
        }
    supported = {name for name, summary in summaries.items() if summary["verdict"] == "supported"}
    proposals = [
        {"channel": "A_output", "output": "gdp_level_pct", "replaces": "C6 ToT-to-GDP beta and potential/cyclical split"},
        {"channel": "B1_spread+B2_real_rate+B3_debt_rate", "output": "debt_rate_change_pp", "replaces": "adds external interest-rate premium to C2/C5 debt recursion"},
        {"channel": "C_investment", "output": "investment_rate_change_pp", "replaces": "adds an external investment-rate path before C2 capital accumulation"},
        {"channel": "D_revenue", "output": "revenue_change_pp_gdp", "replaces": "adds revenue_by_year-like external commodity revenue"},
    ]
    for proposal in proposals:
        components = proposal["channel"].split("+")
        proposal["eligible"] = all(component in supported for component in components)
    return {
        "task": "C7 external block v2", "estimator": "OLS with Bartlett Newey-West SE, lag 1, no finite-sample correction",
        "interval": "90% normal approximation", "estimates": estimates,
        "wiring_proposal": proposals,
        "warning": "Proposals only. Do not wire equations marked ineligible; config/parameters.yaml is unchanged.",
    }


def run(paths: Mapping[str, str | Path] = DEFAULT_PATHS) -> tuple[pd.DataFrame, pd.DataFrame, str, str, dict]:
    data = load_prepare_data(paths["external"], paths["backtest"], paths["fiscal_workbook"])
    models = estimate_channels("all", data)
    backtests, summaries = build_backtests(data, models, paths["parameters"])
    episodes = episode_table(data, models, paths["parameters"])
    return estimates_table(models), backtests, render_report(data, models, summaries, episodes), render_docs(models, summaries), config_payload(models, summaries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    estimates, backtests, report, docs, config = run()
    for key in ("estimates", "backtest_output", "config", "report", "docs"):
        Path(DEFAULT_PATHS[key]).parent.mkdir(parents=True, exist_ok=True)
    estimates.to_csv(DEFAULT_PATHS["estimates"], index=False, float_format="%.10f")
    backtests.to_csv(DEFAULT_PATHS["backtest_output"], index=False, float_format="%.10f")
    Path(DEFAULT_PATHS["report"]).write_text(report, encoding="utf-8")
    Path(DEFAULT_PATHS["docs"]).write_text(docs, encoding="utf-8")
    with Path(DEFAULT_PATHS["config"]).open("w", encoding="utf-8", newline="\n") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
    print(f"Wrote {len(estimates)} coefficient rows and {len(backtests)} back-test rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
