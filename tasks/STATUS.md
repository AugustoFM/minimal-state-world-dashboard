# Task status board (Codex: update this file after each task; Claude reads it to review)

| ID | Status (todo / in progress / PR open / done) | Branch / PR | Notes, problems, data gaps |
|---|---|---|---|
| A1 | done | `codex/brazil-a1-a4` | Consolidated Tesouro GFSM 2014 total and primary expenditure, annual 2010–2026 Q2. 2026 is partial; Q4 rolling-12-month % GDP used for completed years (latest quarter for partial year). Mandatory/discretionary split unavailable in this source. |
| A2 | done | `codex/brazil-a1-a4` | IBGE 2024 revision, Brazil by single age/sex, 2000–2070. UN WPP cross-check remains a data gap. |
| A3 | in progress | `codex/brazil-a1-a4` | Added PNAD Contínua/POF ingestion contract, loader and proposed dictionary. No full microdata downloaded. Exact POF field mappings and final variable shortlist require agreement against official year-specific reading layouts. |
| A4 | done (fallback) | `codex/brazil-a1-a4` | IMF DataMapper API and OECD SDMX returned HTTP 403. Used existing World Bank `GC.XPN.TOTL.GD.ZS`; it is central-government expense, **not general-government expenditure**. Current WB income classification snapshot used; no interpolation. 15/20-year windows have zero exact endpoint pairs in the available series. |
| B1 | todo | | |
| B2 | todo | | |
| C1 | todo | | |
| C2 | todo | | |
| C3 | todo | | |
| C4 | todo | | |
| D1 | todo | | |
| D2 | todo | | |
| E1 | todo | | |
| E2 | todo | | |

## Branch consolidation notes

- The A1 and A2 commits are combined on `codex/brazil-a1-a4` so both outputs and raw sources are present together.
- Concurrent Claude edits to `AGENTS.md`, `PLAN_BRAZIL.md`, and `config/scenarios.yaml` were present in the checkout when work resumed and are preserved unchanged here.
- IMF October 2026 WEO workbook and DataMapper API, and the OECD SDMX API, each returned HTTP 403 from this environment. A4 therefore uses the existing World Bank indicator and labels its central-government-only scope in the output files.
