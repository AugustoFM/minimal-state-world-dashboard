# Brazil scenarios: reducing vs keeping the size of the state

Full literature review (20 papers), methods comparison and rationale: Claude Doc "Brazil: state-size reform scenarios - literature review and execution plan".

## Question
Compare, for 5, 10, 15 and 20 years, (S0) status-quo policy with population ageing, (S1) constant state size, and (R5/R10/R15/R20) gradual reductions in the state, on GDP per capita, debt, unemployment, Gini, top income shares, poverty, wealth concentration, and social indicators (health, education, HDI components).

## Default design (v1, applied 2026-10-20; see `config/scenarios.yaml`)
- State = general-government primary spending, % GDP. Compare S0 (status quo, ageing drift) with R_mod (0.2 pp GDP/yr below S0) and R_amb (0.4 pp/yr, capped by B1); S1 constant size is an optional reference.
- Reductions are measured against S0 because ageing raises pension/health spending on its own.
- Package: 40% pension/indexation, 25% subsidies/tax expenditures, 20% efficiency, 15% other; public investment and means-tested transfers protected.
- Validate the 10-year case first.

## Principles
- Ranges, not point forecasts; every output shows 10th/50th/90th percentile.
- Composition of the reduction matters more than size: test pension-first, subsidies-first, investment cut, efficiency gains, privatisation, compensating transfers.
- "Realistic reduction" is calibrated from observed episodes (B1), not from opinion. Pace and package shares are v1 defaults until B1.
- Cutting and keeping the state are held to the same evidence standard.

## Chain
demographics (A2) -> fiscal baseline (C1) -> macro (C2) -> microsimulation (C3) + social (C4) -> long-run feedback (C5) + external environment (C6) -> Monte Carlo (D1) -> back-tests (D2) -> dashboard/report (E).

## Tasks (details in `tasks/<ID>.md`)
| ID | Task | Owner | Depends on | Output |
|---|---|---|---|---|
| A1 | Rebuild a consolidated general-government spending series for Brazil | Codex (download/clean), Claude (definitions) | - | `data/brazil/fiscal.csv` |
| A2 | Population projections by age to 2070 | Codex | - | `data/brazil/population.csv` |
| A3 | Household microdata and top-income data | Codex | - | `data/brazil/micro/` |
| A4 | Cross-country episodes of state-size change | Codex | A1 | `data/brazil/episodes.csv` |
| B1 | Calibrate the 'realistic reduction' per horizon | Claude + Codex | A1, A4 | `config/scenarios.yaml` |
| B2 | Parameter ranges from the 20 papers | Claude | - | `config/parameters.yaml` |
| C1 | Demographic and pension spending baseline (S0, S1) | Codex builds, Claude reviews | A1, A2 | `src/baseline.py` |
| C2 | Macro block | Codex builds, Claude reviews | B2, C1 | `src/macro.py` |
| C3 | Microsimulation | Codex builds, Claude reviews | A3, C2 | `src/micro.py` |
| C4 | Social outcomes block | Claude specifies, Codex builds | B2 | `src/social.py` |
| C5 | Long-run feedback: human capital, health, public capital, risk premium, inequality | Claude sources, Codex builds | C2, C4 (C3) | `src/feedback.py` |
| C6 | External block: terms of trade, exchange rate, pass-through | Claude sources, Codex builds | C2 (C5) | `src/external.py` |
| P1 | 2026 runoff programme scenarios (Lula, Flávio Bolsonaro) with shared machinery | Claude maps, Codex builds | C1-C6, D1, D2 gate | `config/programs_2026.yaml`, `src/programs.py` |
| F1 | Fiscal delivery ratio: LDO primary targets vs outturns 1999-2025, by government and pooled | Claude sources, Codex assembles | - | `data/brazil/fiscal_delivery.csv` |
| D1 | Monte Carlo runs | Codex | C1-C4 | `outputs/runs/` |
| D2 | Back-tests | Codex runs, Claude interprets | C1-C3, C6 | `outputs/backtest.md` |
| E1 | Brazil dashboard | Claude | D1 | `dashboard/brazil.html` |
| E2 | Written report | Claude | D1, D2 | `report` |

## Gate before dashboard/report
Back-test errors within a stated tolerance; every output a range; every parameter traceable to `config/parameters.yaml`.
