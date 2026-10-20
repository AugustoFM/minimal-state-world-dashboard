"""Calibrate the 'realistic reduction' per horizon (task B1).

Upper percentile of observed declines: country-weighted 10th percentile of the
change in spending/GDP over each horizon among middle-income countries
(data/brazil/episodes.csv, A4). Episodes that start on a spike (start value more
than SPIKE_PP above the mean of the up-to-three prior observed years) are
dropped, because their declines are mean reversion rather than policy. Each
country gets equal weight per horizon so long series do not dominate. Episodes
whose window contains a year-on-year jump above BREAK_PP are also dropped as
likely series breaks or crises (e.g. Nicaragua 1990-94).

Reductions in config/scenarios.yaml are measured against S0, which drifts up with
ageing (C1, data/brazil/baseline.csv). A reduction R below S0 changes spending
from today by drift - R, so the largest reduction consistent with observed
experience is cap = drift + |p10|.

Proxy warning: A4 uses central-government expense (WDI GC.XPN.TOTL.GD.ZS), not
general-government primary spending.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
EPISODES = ROOT / "data/brazil/episodes.csv"
WB_SPENDING = ROOT / "data/raw/brazil/worldbank_expense_1990_2025.json"
BASELINE = ROOT / "data/brazil/baseline.csv"
SCENARIOS = ROOT / "config/scenarios.yaml"
OUTPUT = ROOT / "data/brazil/b1_calibration.csv"
SENSITIVITY = ROOT / "data/brazil/b1_sensitivity.csv"
# Screening thresholds and the percentile are method choices, not estimates;
# b1_sensitivity.csv reports how the cap moves when each is varied.
SPIKE_PP = 3.0
BREAK_PP = 10.0
PERCENTILES = (0.05, 0.10, 0.25, 0.50)
SPIKE_GRID = (2.0, 3.0, 5.0, None)
BREAK_GRID = (5.0, 10.0, 15.0, None)
PERCENTILE_GRID = (0.05, 0.10, 0.25)
BOOTSTRAP_DRAWS = 1000
BOOTSTRAP_SEED = 20261020
# Federal discretionary spending was 1.6% of GDP in 2024 (IFI RAF 101, Table 6).
# A reduction larger than all of it cannot come from discretionary spending alone,
# so the excess is a lower bound on the part that must change mandatory-spending
# rules (federal only, 2024 level). Within a single year the executive may also
# withhold up to 25% of authorised discretionary spending (LC 200/2023 art. 7
# para 2); that is a one-year budget-execution tool and is never subtracted from
# multi-year reductions.
DISCRETIONARY_PCT_GDP = 1.6
DISCRETIONARY_MAX_WITHHELD = 0.25


def mandatory_lower_bound(reduction: float) -> float:
    """Minimum part of a reduction (pp GDP) that must come from mandatory rules."""
    return max(0.0, reduction - DISCRETIONARY_PCT_GDP)


def annual_series() -> pd.DataFrame:
    # World Bank API pagination envelope is [metadata, observations].
    records = json.loads(WB_SPENDING.read_text(encoding="utf-8"))[1]
    data = pd.DataFrame(
        {
            "iso3": [r["countryiso3code"] for r in records],
            "year": [int(r["date"]) for r in records],
            "value": [r["value"] for r in records],
        }
    ).dropna(subset=["value"])
    return data.sort_values(["iso3", "year"])


def spike_starts(series: pd.DataFrame, spike_pp: float | None = SPIKE_PP) -> pd.DataFrame:
    prior = series.groupby("iso3")["value"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=2).mean()
    )
    if spike_pp is None:
        return series.assign(spike=False).loc[:, ["iso3", "year", "spike"]]
    flagged = series.assign(spike=(series["value"] - prior) > spike_pp)
    return flagged.loc[:, ["iso3", "year", "spike"]]


def break_windows(
    series: pd.DataFrame, episodes: pd.DataFrame, break_pp: float | None = BREAK_PP
) -> pd.Series:
    """True where a year-on-year jump above break_pp falls inside the episode."""
    if break_pp is None:
        return pd.Series(False, index=episodes.index)
    jumps = series.assign(
        jump=series.groupby("iso3")["value"].diff().abs().gt(break_pp)
    )
    jump_years = jumps.loc[jumps["jump"], ["iso3", "year"]].rename(
        columns={"year": "jump_year"}
    )
    flagged = (
        episodes.loc[:, ["iso3", "start_year", "end_year"]]
        .assign(episode=episodes.index)
        .merge(jump_years, on="iso3", how="left")
    )
    inside = flagged["jump_year"].gt(flagged["start_year"]) & flagged["jump_year"].le(
        flagged["end_year"]
    )
    return inside.groupby(flagged["episode"]).any().reindex(episodes.index, fill_value=False)


def weighted_quantile(changes: pd.Series, countries: pd.Series, p: float) -> float:
    frame = pd.DataFrame({"change": changes, "iso3": countries})
    frame["weight"] = 1 / frame.groupby("iso3")["iso3"].transform("size")
    frame = frame.sort_values("change")
    cumulative = frame["weight"].cumsum() / frame["weight"].sum()
    return float(frame.loc[cumulative >= p, "change"].iloc[0])


def screened_episodes(
    series: pd.DataFrame,
    spike_pp: float | None = SPIKE_PP,
    break_pp: float | None = BREAK_PP,
) -> pd.DataFrame:
    episodes = pd.read_csv(EPISODES)
    middle = episodes.loc[episodes["sample_group"].eq("middle_income")]
    middle = middle.merge(
        spike_starts(series, spike_pp),
        left_on=["iso3", "start_year"],
        right_on=["iso3", "year"],
        how="left",
    ).drop(columns="year")
    middle["series_break"] = break_windows(series, middle, break_pp)
    return middle


def keep(middle: pd.DataFrame) -> pd.DataFrame:
    return middle.loc[middle["spike"].ne(True) & ~middle["series_break"]]


def episode_percentiles(series: pd.DataFrame) -> pd.DataFrame:
    middle = screened_episodes(series)
    rows = []
    for (horizon, sample), group in [
        ((h, "all"), g) for h, g in middle.groupby("horizon_years")
    ] + [
        ((h, "screened"), keep(g))
        for h, g in middle.groupby("horizon_years")
    ]:
        row = {
            "horizon_years": horizon,
            "sample": sample,
            "n_episodes": len(group),
            "n_countries": group["iso3"].nunique(),
        }
        for p in PERCENTILES:
            row[f"cw_p{int(p * 100)}"] = weighted_quantile(
                group["change_percentage_points"], group["iso3"], p
            )
        rows.append(row)
    return pd.DataFrame(rows)


def drift_by_horizon() -> pd.DataFrame:
    baseline = pd.read_csv(BASELINE)
    base_year = int(baseline["year"].min())
    total = baseline.loc[
        baseline["scenario"].eq("S0") & baseline["category"].eq("total"),
        ["year", "variant", "drift_pct_gdp"],
    ]
    total = total.assign(horizon_years=total["year"] - base_year)
    return total.pivot(index="horizon_years", columns="variant", values="drift_pct_gdp")


def sensitivity(series: pd.DataFrame) -> pd.DataFrame:
    """p10 under the threshold grid, a country bootstrap and leave-one-country-out."""
    rows = []
    for spike_pp in SPIKE_GRID:
        for break_pp in BREAK_GRID:
            kept = keep(screened_episodes(series, spike_pp, break_pp))
            for horizon, group in kept.groupby("horizon_years"):
                for p in PERCENTILE_GRID:
                    rows.append({
                        "horizon_years": horizon,
                        "method": "grid",
                        "spike_pp": spike_pp,
                        "break_pp": break_pp,
                        "percentile": p,
                        "value": weighted_quantile(
                            group["change_percentage_points"], group["iso3"], p
                        ),
                    })
    kept = keep(screened_episodes(series))
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    for horizon, group in kept.groupby("horizon_years"):
        countries = group["iso3"].unique()
        by_country = {iso3: g for iso3, g in group.groupby("iso3")}
        for draw in range(BOOTSTRAP_DRAWS):
            picks = rng.choice(countries, size=len(countries), replace=True)
            # A country drawn twice counts as two countries for the weighting.
            sample = pd.concat(
                [by_country[iso3].assign(iso3=f"{iso3}#{i}") for i, iso3 in enumerate(picks)]
            )
            rows.append({
                "horizon_years": horizon,
                "method": "bootstrap",
                "draw": draw,
                "percentile": 0.10,
                "value": weighted_quantile(
                    sample["change_percentage_points"], sample["iso3"], 0.10
                ),
            })
        for iso3 in countries:
            sample = group.loc[group["iso3"].ne(iso3)]
            rows.append({
                "horizon_years": horizon,
                "method": "leave_one_out",
                "omitted": iso3,
                "percentile": 0.10,
                "value": weighted_quantile(
                    sample["change_percentage_points"], sample["iso3"], 0.10
                ),
            })
    return pd.DataFrame(rows)


def classify(reduction: float, conservative: float, central: float) -> str:
    if reduction <= conservative:
        return "inside"
    if reduction <= central:
        return "borderline"
    return "outside"


def main() -> int:
    series = annual_series()
    percentiles = episode_percentiles(series)
    drift = drift_by_horizon()
    calibration = percentiles.merge(
        drift.add_prefix("drift_").reset_index(), on="horizon_years", how="left"
    )
    for variant in ("low", "central", "high"):
        calibration[f"cap_below_s0_{variant}"] = (
            calibration[f"drift_{variant}"] - calibration["cw_p10"]
        )
    sens = sensitivity(series)
    boot = sens.loc[sens["method"].eq("bootstrap")].groupby("horizon_years")["value"]
    loo = sens.loc[sens["method"].eq("leave_one_out")].groupby("horizon_years")["value"]
    grid = sens.loc[
        sens["method"].eq("grid") & sens["percentile"].eq(0.10)
    ].groupby("horizon_years")["value"]
    robustness = pd.DataFrame({
        "p10_bootstrap_q10": boot.quantile(0.10),
        "p10_bootstrap_q90": boot.quantile(0.90),
        "p10_loo_min": loo.min(),
        "p10_loo_max": loo.max(),
        "p10_grid_min": grid.min(),
        "p10_grid_max": grid.max(),
    }).reset_index()
    calibration = calibration.merge(robustness, on="horizon_years", how="left")
    screened = calibration["sample"].eq("screened")
    # Precedent bound. Conservative uses the least negative p10 that 90% of country
    # resamples stay below, so a path inside it survives sample composition.
    calibration["precedent_cap_conservative"] = (
        calibration["drift_low"] - calibration["p10_bootstrap_q90"]
    ).where(screened)
    calibration["precedent_cap_central"] = calibration["cap_below_s0_low"].where(screened)
    calibration["federal_discretionary_2024_pct_gdp"] = DISCRETIONARY_PCT_GDP
    calibration["one_year_max_withholding_pp"] = DISCRETIONARY_PCT_GDP * DISCRETIONARY_MAX_WITHHELD
    with SCENARIOS.open(encoding="utf-8") as handle:
        scenarios = yaml.safe_load(handle)["scenarios"]
    for name in ("R_mod", "R_amb"):
        sizes = calibration["horizon_years"].map(scenarios[name]["by_year"])
        calibration[f"{name}_pp"] = sizes
        calibration[f"{name}_precedent"] = [
            classify(r, c, m) if s else None
            for r, c, m, s in zip(
                sizes,
                calibration["precedent_cap_conservative"],
                calibration["precedent_cap_central"],
                screened,
            )
        ]
        calibration[f"{name}_mandatory_min_pp"] = sizes.map(mandatory_lower_bound)
    calibration["government_scope"] = "central government only (WDI GC.XPN.TOTL.GD.ZS); proxy"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    calibration.to_csv(OUTPUT, index=False, float_format="%.4f")
    sens.to_csv(SENSITIVITY, index=False, float_format="%.4f")
    view = calibration.loc[screened, [
        "horizon_years", "cw_p10", "p10_bootstrap_q10", "p10_bootstrap_q90",
        "p10_loo_min", "p10_loo_max", "p10_grid_min", "p10_grid_max", "drift_low",
        "precedent_cap_conservative", "precedent_cap_central",
        "R_mod_pp", "R_mod_precedent", "R_amb_pp", "R_amb_precedent",
        "R_mod_mandatory_min_pp", "R_amb_mandatory_min_pp",
    ]]
    print(view.T.to_string(float_format=lambda v: f"{v:.2f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
