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

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EPISODES = ROOT / "data/brazil/episodes.csv"
WB_SPENDING = ROOT / "data/raw/brazil/worldbank_expense_1990_2025.json"
BASELINE = ROOT / "data/brazil/baseline.csv"
OUTPUT = ROOT / "data/brazil/b1_calibration.csv"
SPIKE_PP = 3.0
BREAK_PP = 10.0
PERCENTILES = (0.05, 0.10, 0.25, 0.50)


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


def spike_starts(series: pd.DataFrame) -> pd.DataFrame:
    prior = series.groupby("iso3")["value"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=2).mean()
    )
    flagged = series.assign(spike=(series["value"] - prior) > SPIKE_PP)
    return flagged.loc[:, ["iso3", "year", "spike"]]


def break_windows(series: pd.DataFrame, episodes: pd.DataFrame) -> pd.Series:
    """True where a year-on-year jump above BREAK_PP falls inside the episode."""
    jumps = series.assign(
        jump=series.groupby("iso3")["value"].diff().abs().gt(BREAK_PP)
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


def episode_percentiles() -> pd.DataFrame:
    episodes = pd.read_csv(EPISODES)
    middle = episodes.loc[episodes["sample_group"].eq("middle_income")]
    series = annual_series()
    middle = middle.merge(
        spike_starts(series),
        left_on=["iso3", "start_year"],
        right_on=["iso3", "year"],
        how="left",
    ).drop(columns="year")
    middle["series_break"] = break_windows(series, middle)
    rows = []
    for (horizon, sample), group in [
        ((h, "all"), g) for h, g in middle.groupby("horizon_years")
    ] + [
        ((h, "screened"), g.loc[g["spike"].ne(True) & ~g["series_break"]])
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


def main() -> int:
    percentiles = episode_percentiles()
    drift = drift_by_horizon()
    calibration = percentiles.merge(
        drift.add_prefix("drift_").reset_index(), on="horizon_years", how="left"
    )
    for variant in ("low", "central", "high"):
        calibration[f"cap_below_s0_{variant}"] = (
            calibration[f"drift_{variant}"] - calibration["cw_p10"]
        )
    calibration["government_scope"] = "central government only (WDI GC.XPN.TOTL.GD.ZS); proxy"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    calibration.to_csv(OUTPUT, index=False, float_format="%.4f")
    print(calibration.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
