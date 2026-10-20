"""Minimal-state score v1 (see PLAN.md). 100 = most minimal. Needs >=2 dimensions.
TODO [Codex T5]: add SOE and EFW/Heritage dimensions once raw files exist."""
import pandas as pd
df = pd.read_csv("data/processed/countries.csv")
def inv_pct(s): return (1 - s.rank(pct=True)) * 100   # lower value -> higher score
dims = {"dim_budget": inv_pct(df["gov_expense_pct_gdp"])}
for k, v in dims.items(): df[k] = v
d = list(dims)
df["dims_used"] = df[d].notna().sum(axis=1)
df["minimal_state_score"] = df[d].mean(axis=1).where(df["dims_used"] >= 1)  # raise to 2 when more dims exist
df.to_csv("data/processed/countries_scored.csv", index=False)
