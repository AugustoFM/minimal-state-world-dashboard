"""Build exact-window spending episodes from the existing World Bank series.

The fallback indicator GC.XPN.TOTL.GD.ZS is central-government expense (% GDP),
not general-government expense. Country scope is limited to current World Bank
lower-middle and upper-middle income economies, plus Brazil for a separate
Brazil distribution. Only exact observed endpoint pairs are used; no gaps are
interpolated.
"""
from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WDI = ROOT / "data/raw/worldbank_long.csv"
CLASSIFICATIONS = ROOT / "data/raw/brazil/worldbank_country_metadata.json"
EPISODES = ROOT / "data/brazil/episodes.csv"
SUMMARY = ROOT / "data/brazil/episodes_summary.csv"
INDICATOR = "GC.XPN.TOTL.GD.ZS"
HORIZONS = (5, 10, 15, 20)


def eligible_countries() -> pd.DataFrame:
    # World Bank API pagination envelope is [metadata, country records].
    records = json.loads(CLASSIFICATIONS.read_text(encoding="utf-8"))[1]
    countries = pd.DataFrame(records)
    countries["income_group"] = countries["incomeLevel"].map(lambda item: item.get("id"))
    countries["region_code"] = countries["region"].map(lambda item: item.get("id"))
    return countries.loc[
        countries["income_group"].isin(["LMC", "UMC"])
        & countries["region_code"].notna()
        & countries["region_code"].ne("NA"),
        ["id", "income_group"],
    ].rename(columns={"id": "iso3"})


def make_episodes() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(WDI)
    values = raw.loc[raw["indicator"].eq("gov_expense_pct_gdp"),
                     ["iso3", "country", "year", "value"]].copy()
    values["year"] = pd.to_numeric(values["year"], errors="coerce")
    values["value"] = pd.to_numeric(values["value"], errors="coerce")
    values = values.dropna(subset=["iso3", "year", "value"])
    values["year"] = values["year"].astype(int)
    classes = eligible_countries()
    income = values.merge(classes, on="iso3", how="inner")
    # Keep only ISO3 country records. Aggregates are not present in the World
    # Bank country metadata's non-aggregate region codes and are excluded above.
    groups = [("middle_income", income)]
    brazil = values.loc[values["iso3"].eq("BRA")].copy()
    if not brazil.empty:
        brazil["income_group"] = "UMC"
        groups.append(("brazil", brazil))

    rows = []
    for group_name, group in groups:
        lookup = {(r.iso3, int(r.year)): (r.country, float(r.value), r.income_group)
                  for r in group.itertuples(index=False)}
        for (iso3, year0), (country, value0, income_group) in lookup.items():
            for horizon in HORIZONS:
                year1 = year0 + horizon
                endpoint = lookup.get((iso3, year1))
                if endpoint is None:
                    continue
                end_country, value1, _ = endpoint
                rows.append({
                    "sample_group": group_name,
                    "iso3": iso3,
                    "country": country or end_country,
                    "income_group_current": income_group,
                    "horizon_years": horizon,
                    "start_year": year0,
                    "start_spending_pct_gdp": value0,
                    "end_year": year1,
                    "end_spending_pct_gdp": value1,
                    "change_percentage_points": value1 - value0,
                    "series_code": INDICATOR,
                    "government_scope": "central government only; not general government",
                    "income_classification_basis": "current World Bank classification (2026 API snapshot)",
                    "source": "World Bank WDI series already in data/raw/worldbank_long.csv",
                })
    episodes = pd.DataFrame(rows)
    if episodes.empty:
        summary = pd.DataFrame(columns=["sample_group", "horizon_years", "n_episodes", "p10", "p50", "p90"])
        return episodes, summary
    summary = episodes.groupby(["sample_group", "horizon_years"]).agg(
        n_episodes=("change_percentage_points", "size"),
        p10=("change_percentage_points", lambda s: s.quantile(.10)),
        p50=("change_percentage_points", "median"),
        p90=("change_percentage_points", lambda s: s.quantile(.90)),
    )
    index = pd.MultiIndex.from_product(
        [["middle_income", "brazil"], HORIZONS],
        names=["sample_group", "horizon_years"],
    )
    summary = summary.reindex(index).reset_index()
    summary["n_episodes"] = summary["n_episodes"].fillna(0).astype(int)
    summary["series_code"] = INDICATOR
    summary["government_scope"] = "central government only; not general government"
    summary["income_classification_basis"] = "current World Bank classification (2026 API snapshot)"
    return episodes, summary


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    episodes, summary = make_episodes()
    EPISODES.parent.mkdir(parents=True, exist_ok=True)
    episodes.to_csv(EPISODES, index=False)
    summary.to_csv(SUMMARY, index=False)
    return episodes, summary


if __name__ == "__main__":
    episode_data, summaries = build()
    print(f"Wrote {len(episode_data)} episodes and {len(summaries)} summary rows")
    print(f"Scope: central-government only ({INDICATOR}); no interpolation")
