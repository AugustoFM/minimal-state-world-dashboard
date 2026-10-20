# Minimal State World Dashboard

Classify every country by how close it is to a "minimal state" and explore it against development outcomes (GDP, GDP per capita, unemployment, HDI, access to health, civil rights, wealth and inequality).

Companion to the report "O Estado Mínimo: conceito, história e peso da iniciativa privada".

## Quick start
```
pip install pandas requests
python scripts/fetch_worldbank.py      # World Bank indicators -> data/raw/worldbank_long.csv
python scripts/build_dataset.py        # merge everything -> data/processed/countries.csv
python scripts/build_score.py          # minimal-state score -> data/processed/countries_scored.csv
```
Then open `dashboard/` (see PLAN.md, task T6). See `PLAN.md` for the full task list and `AGENTS.md` for rules for Codex.
