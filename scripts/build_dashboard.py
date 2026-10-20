"""Write dashboard/data.js from data/processed/countries_scored.csv. Run from repo root, then open dashboard/index.html."""
import json, pandas as pd, numpy as np
df = pd.read_csv("data/processed/countries_scored.csv")
cols = [c for c in df.columns if not c.endswith("_year") or c in ("hdi_year",)]
df = df[cols].replace({np.nan: None})
recs = []
for r in df.to_dict("records"):
    recs.append({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
open("dashboard/data.js", "w", encoding="utf-8").write("window.DATA=" + json.dumps(recs, ensure_ascii=False) + ";")
print(len(recs), "countries -> dashboard/data.js")
