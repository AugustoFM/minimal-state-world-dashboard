# Brazil scenarios: reducing vs keeping the size of the state

Full literature review (20 papers), methods comparison and rationale: Claude Doc "Brazil: state-size reform scenarios - literature review and execution plan".

## Question
Compare, for 5, 10, 15 and 20 years, (S0) status-quo policy with population ageing, (S1) constant state size, and (R5/R10/R15/R20) gradual reductions in the state, on GDP per capita, debt, unemployment, Gini, top income shares, poverty, wealth concentration, and social indicators (health, education, HDI components).

## Principles
- Ranges, not point forecasts; every output shows 10th/50th/90th percentile.
- Composition of the reduction matters more than size: test pension-first, subsidies-first, investment cut, efficiency gains, privatisation, compensating transfers.
- "Realistic reduction" is calibrated from observed episodes (B1), not from opinion. Reduction sizes in this repo before B1 are placeholders.
- Cutting and keeping the state are held to the same evidence standard.

## Chain
demographics (A2) -> fiscal baseline (C1) -> macro (C2) -> microsimulation (C3) + social (C4) -> Monte Carlo (D1) -> back-tests (D2) -> dashboard/report (E).

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
| D1 | Monte Carlo runs | Codex | C1-C4 | `outputs/runs/` |
| D2 | Back-tests | Codex runs, Claude interprets | C1-C3 | `outputs/backtest.md` |
| E1 | Brazil dashboard | Claude | D1 | `dashboard/brazil.html` |
| E2 | Written report | Claude | D1, D2 | `report` |

## Gate before dashboard/report
Back-test errors within a stated tolerance; every output a range; every parameter traceable to `config/parameters.yaml`.
