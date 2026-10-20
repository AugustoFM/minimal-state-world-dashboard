# Task status board (Codex: update this file after each task; Claude reads it to review)

| ID | Status (todo / in progress / PR open / done) | Branch / PR | Notes, problems, data gaps |
|---|---|---|---|
| A1 | done | `codex/brazil-a1-a4` | Consolidated Tesouro GFSM 2014 total and primary expenditure, annual 2010–2026 Q2. 2026 is partial; Q4 rolling-12-month % GDP used for completed years (latest quarter for partial year). Mandatory/discretionary split unavailable in this source. |
| A2 | done | `codex/brazil-a1-a4` | IBGE 2024 revision, Brazil by single age/sex, 2000–2070. UN WPP cross-check remains a data gap. |
| A3 | in progress | `codex/brazil-a1-a4` | PNAD list expanded with official per-capita income candidate (`VD5002`), source-income candidates, and household size computed using a temporary key dropped before output. Official PNAD layout files and POF documentation/read programs are saved; source-benefit codes and all POF mappings still need exact dictionary transcription/review. Loader supports temporary grouping but no survey microdata has been downloaded. Raw microdata paths are git-ignored. |
| A4 | done (fallback) | `codex/brazil-a1-a4` | Refetched WDI `GC.XPN.TOTL.GD.ZS` for 1990–2025 and rebuilt exact endpoint episodes. Central-government expense only, **not general-government expenditure**; no interpolation. Middle-income sample now has 598 15-year and 386 20-year episodes. Brazil itself has no exact 15/20-year pairs in the returned series (Brazil observations begin in 2010). |
| B1 | todo | | |
| B2 | done | `task/b2` (merged) | Multipliers (Sanches et al. 2026), Gini effects (Ball et al. 2013) and infant-mortality elasticity (Szklo et al. 2024) checked in full text; ranges are spread across specifications, not CIs. Reviewed by Codex. Gaps: schooling and physician elasticities (C4 limited to mortality/life expectancy). |
| C1 | done | `task/c1` (merged) | Revised to reproducible NTA single-age profiles (ages 0–90+, 2003/2018) and exact 2024 COFOG shares/cells. Bounds envelope sourced profile vintage and pension-indexation combinations; RGPS remains a labelled proxy for RPPS-inclusive pensions, and 2024 shares are carried to 2025. Committed by Claude after review. |
| C2 | PR open | `task/c2` | Lead-review debt-rate fix applied: 2021-25 nominal implicit rates are Fisher-converted with same-year IBGE GDP-deflator inflation (13.0/8.6/5.2/3.8/5.73%). Real-rate history is -2.0422/2.3877/5.0501/7.1968/6.9379%, range -2.0422/5.0501/7.1968%; projected nominal corners are 0.8966/8.2016/11.2703%. Old nominal behavior is behind an explicit false-by-default legacy flag. Central S0 potential growth is 1.122/0.936/0.659/0.348% and debt is 104.46/145.49/207.48/298.94% at 5/10/15/20 years. The 10-year 66.85 pp rise decomposes into 25.97 pp primary (including C1 ageing) and 40.88 pp interest-growth; the latter explains most of the remaining 20.49 pp gap above the secondary ~125% IFI benchmark. IBGE SIDRA sources for 2025 GDP and 2021-2025 deflators archived and checked by Claude (2025 deflator derived 5.71 vs 5.73 used, rounding). CLI writes 504 rows. Exact pytest command: 27 passed. Reviewed and committed by Claude. |
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
- A4 was later refetched from the World Bank API for 1990–2025 into `data/raw/brazil/worldbank_expense_1990_2025.json`; summary episode files were rebuilt from that response.
- A3 downloads are documentation/layout files only. Full PNAD and POF microdata remain deferred until the exact source mappings are reviewed.
