# Task status board (Codex: update this file after each task; Claude reads it to review)

| ID | Status (todo / in progress / PR open / done) | Branch / PR | Notes, problems, data gaps |
|---|---|---|---|
| A1 | done | `codex/brazil-a1-a4` | Consolidated Tesouro GFSM 2014 total and primary expenditure, annual 2010–2026 Q2. 2026 is partial; Q4 rolling-12-month % GDP used for completed years (latest quarter for partial year). Mandatory/discretionary split unavailable in this source. |
| A2 | done | `codex/brazil-a1-a4` | IBGE 2024 revision, Brazil by single age/sex, 2000–2070. UN WPP cross-check remains a data gap. |
| A3 | in progress | `codex/brazil-a1-a4` | PNAD list expanded with official per-capita income candidate (`VD5002`), source-income candidates, and household size computed using a temporary key dropped before output. Official PNAD layout files and POF documentation/read programs are saved; source-benefit codes and all POF mappings still need exact dictionary transcription/review. Loader supports temporary grouping but no survey microdata has been downloaded. Raw microdata paths are git-ignored. |
| A4 | done (fallback) | `codex/brazil-a1-a4` | Refetched WDI `GC.XPN.TOTL.GD.ZS` for 1990–2025 and rebuilt exact endpoint episodes. Central-government expense only, **not general-government expenditure**; no interpolation. Middle-income sample now has 598 15-year and 386 20-year episodes. Brazil itself has no exact 15/20-year pairs in the returned series (Brazil observations begin in 2010). |
| B1 | done | `task/b1` | Precedent cap below S0 (conservative/central): 3.9/4.9/6.1/7.0 and 4.2/5.5/7.3/8.5 pp at 5/10/15/20y; robust to threshold grid, leave-one-country-out and country bootstrap (b1_sensitivity.csv). R_mod inside everywhere; R_amb 20y capped 8 -> 7.0; optional R_max added. Implementability: federal discretionary is only 1.6% GDP (IFI RAF 101), so from 10y on both R paths need mandatory-rule changes (lower bounds reported); the LC 200/2023 25% withholding limit is a one-year tool and is not used as a multi-year allowance. Reviewed by Codex. Proxy: central-government episodes. |
| B2 | done | `task/b2` (merged) | Multipliers (Sanches et al. 2026), Gini effects (Ball et al. 2013) and infant-mortality elasticity (Szklo et al. 2024) checked in full text; ranges are spread across specifications, not CIs. Reviewed by Codex. Gaps: schooling and physician elasticities (C4 limited to mortality/life expectancy). |
| C1 | done | `task/c1` (merged) | Codex revision moved all runtime C1 inputs and source notes into `config/parameters.yaml` and changed the default builder path; removed the duplicate proposed-parameter file. C1 uses reproducible NTA profiles (ages 0–90+, 2003/2018) and 2024 COFOG shares; bounds are sensitivity envelopes, RGPS is a labelled proxy for RPPS-inclusive pensions, and 2024 shares carry to 2025. |
| C2 | done | `task/c2` (merged) | Multiplier GDP effects (transitory/persistent), debt dynamics on the Tesouro GFSM primary balance with same-year Fisher-adjusted implicit rates, PWT 10.01 growth accounting with dynamic 2000-2019 backcast. Central S0 potential growth ~0.9%/yr at 10y (IMF 2.5%: gap from PWT's negative TFP trend); central S0 debt 145% GDP at 10y vs IFI ~125% (gap mostly r-g). R paths read from scenarios.yaml by_year (R_amb 20y = 7.0 after B1). Built by Codex over five review rounds; sources archived and verified by Claude. Inputs consolidated into config/parameters.yaml (task/c2-registry). |
| C3 | todo | | |
| C4 | done | `task/c4` (merged) | Social block produces 5/10/15/20y sensitivity envelopes for S0, S1, R_mod, R_amb and optional R_max from C1 health shares and C2 GDP per capita; reviewed and committed by Claude (Codex run ended at usage limit after outputs were complete); IMR and LE anchors are read from raw files, S0 has no assumed trend, and every configured gap is emitted as `not_modelled`. LE uses its central-only elasticity; bound combinations are recorded. `40 passed`; CLI wrote 660 rows. No upstream-file change requested. |
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
