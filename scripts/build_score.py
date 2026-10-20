"""Minimal-state score v2. 0-100, 100 = most minimal. Run from repo root.

Dimensions (each 0-100, higher = smaller state), following the report's three-part definition:
  dim_budget    Fiscal burden: mean(Fraser 1A gov. consumption, Fraser 1D top tax rate) x10;
                fallback (no Fraser data): mean(Heritage Government Spending, Heritage Tax Burden)
  dim_footprint Economic footprint: Fraser 1E state ownership of assets x10
  dim_scope     Reach beyond core functions: mean(Fraser 1B transfers & subsidies, 1C gov. investment) x10
Confidence: high = 3 dimensions, medium = 2, low = 1 (typically Heritage-only countries).
World Bank spending/GDP is shown as context but NOT scored: it rewards fragile low-capacity and oil states.
"""
import pandas as pd
df = pd.read_csv("data/processed/countries.csv")
f = df[["efw_1a_consumption", "efw_1d_tax"]].mean(axis=1) * 10
fb = df[["heritage_gov_spending", "heritage_tax_burden"]].mean(axis=1)
df["dim_budget"] = f.fillna(fb)
df["dim_footprint"] = df["efw_1e_state_ownership"] * 10
df["dim_scope"] = df[["efw_1b_transfers", "efw_1c_investment"]].mean(axis=1) * 10
d = ["dim_budget", "dim_footprint", "dim_scope"]
df["dims_used"] = df[d].notna().sum(axis=1)
df["minimal_state_score"] = df[d].mean(axis=1).where(df["dims_used"] >= 1)
df["confidence"] = df["dims_used"].map({3: "high", 2: "medium", 1: "low"})
df.to_csv("data/processed/countries_scored.csv", index=False)
print(df["confidence"].value_counts(dropna=False).to_string())
