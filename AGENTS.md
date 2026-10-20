# Instructions for Codex
- Read PLAN.md first; take only tasks marked [Codex]; one branch per task, small PRs.
- Python 3.11+, pandas, requests. No API keys needed. Keep scripts idempotent and runnable from repo root.
- ISO3 country codes are the key. Exclude World Bank aggregates (regions/income groups).
- Save raw downloads untouched in `data/raw/`; derived data in `data/processed/`.
- Record source URL, download date and licence in `data/raw/SOURCES.md`.
- Never invent or interpolate data; keep value-year pairs.

## Brazil scenario work
- Read PLAN_BRAZIL.md, then take tasks marked Codex from `tasks/`. Claude reviews PRs.
- Model parameters come only from `config/parameters.yaml` (each with a source); scenario sizes from `config/scenarios.yaml`.
- Outputs are ranges (p10/p50/p90). Never present a single path as a forecast.
