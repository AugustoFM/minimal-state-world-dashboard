# Minimal State World Dashboard

Classify every country by how close it is to a "minimal state" and explore it against development outcomes (GDP, GDP per capita, unemployment, HDI, access to health, civil rights, wealth and inequality).

Companion to the report "O Estado Mínimo: conceito, história e peso da iniciativa privada".

## Live dashboards

- [World dashboard](https://augustofm.github.io/minimal-state-world-dashboard/dashboard/index.html) — the cross-country minimal-state map and scores above.
- [Brazil fiscal-scenario dashboard](https://augustofm.github.io/minimal-state-world-dashboard/dashboard/brazil.html) — Monte Carlo comparison of reduction/expansion scenarios vs the status-quo baseline, with the back-test gate verdict attached.
- [Four Years to Decide](https://augustofm.github.io/minimal-state-world-dashboard/presidency-game/index.html) — decision-support simulation companion to the teaching case "The Vote: Brazil's 2026 Runoff," playing either runoff candidate's own filed programme one year at a time against the same published model. See `presidency-game/MANUAL.md`.

## Quick start
```
pip install pandas requests
pip install openpyxl pycountry
python scripts/fetch_worldbank.py      # World Bank WDI + WGI -> data/raw/worldbank_long.csv
python scripts/build_dataset.py        # merge all sources -> data/processed/countries.csv
python scripts/build_score.py          # minimal-state score -> data/processed/countries_scored.csv
python scripts/build_dashboard.py      # -> dashboard/data.js
```
Then open `dashboard/index.html` in a browser (Leaflet map; needs internet for the Leaflet library and map tiles). See `PLAN.md` for the full task list and `AGENTS.md` for rules for Codex.
