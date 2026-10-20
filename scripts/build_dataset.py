"""TODO [Codex T4]: merge data/raw/* into data/processed/countries.csv (one row per ISO3, value + year per indicator).
Starter: latest non-null WB value per country/indicator."""
import pandas as pd
df = pd.read_csv("data/raw/worldbank_long.csv").sort_values("year")
last = df.groupby(["iso3", "country", "indicator"]).tail(1)
wide = last.pivot(index=["iso3", "country"], columns="indicator", values=["value", "year"])
wide.columns = [f"{b}_{a}" if a == "year" else b for a, b in wide.columns]
wide.reset_index().to_csv("data/processed/countries.csv", index=False)
