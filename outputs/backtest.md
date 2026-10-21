# D2 historical back-tests

**Overall proposed gate: FAIL.** Legacy aggregate retained for downstream report compatibility; use the two tier verdicts below for publication decisions.

**Tier 1 - differences vs S0: PASS.** This is the gate for publishing scenario effects.

**Tier 2 - debt/GDP levels: FAIL.** The verdict uses the out-of-sample recursion with the pre-2018 mean SFA; the zero-SFA result is reported alongside it.

No coefficient was tuned to improve these results. Calculations are offline and use checked-in observations and fixed model parameters.

## Gate v2

| Tier | Test | Statistic | Tolerance / benchmark | Verdict |
|---|---|---:|---:|---|
| 1: differences vs S0 | Debt engine, one step ahead (2011-2024) | MAE 2.054 pp | <= 2.5 pp | PASS |
| 1: differences vs S0 | Growth block (2006-2019) | absolute mean error 0.165 pp/yr | <= 0.5 pp/yr | PASS |
| 1: differences vs S0 | C7 channel A OOS (2015-2024) | RMSE 3.004 pp | naive RMSE 3.881 pp; must be lower | PASS |
| 2: levels | 2017-anchor zero-SFA recursion, 2024 | error +16.061 pp | absolute error <= 5 pp | FAIL (reported only) |
| 2: levels | 2017-anchor with-SFA recursion, 2024 | error +12.472 pp | absolute error <= 5 pp | FAIL |

All gate rules are lead-developer decisions dated 2026-10-21 in `config/d2_inputs_proposed.yaml`. C7 audit rows are read from `data/brazil/c7_backtest.csv`, not re-estimated.

The level tolerance is absolute 2024 debt error <= 5 pp of GDP.

## All annual test statistics

| Block | Mean error | MAE | RMSE | Correlation | Final error | Verdict |
|---|---:|---:|---:|---:|---:|---|
| debt_engine | 4.879 | 7.129 | 9.322 | 0.953 | 18.571 | FAIL |
| debt_engine_one_step | 1.358 | 2.054 | 2.390 | 0.991 | 0.707 | PASS |
| debt_engine_zero_sfa_oos | 8.825 | 8.825 | 10.312 | 0.610 | 16.061 | FAIL |
| debt_engine_with_sfa_oos | 7.071 | 7.071 | 8.223 | 0.701 | 12.472 | FAIL |
| growth_block | 0.165 | 1.734 | 2.238 | 0.772 | 0.952 | PASS |
| multiplier_total | -0.044 | 2.619 | 3.466 | -0.108 | -4.651 | not_rated |
| multiplier_categories | 0.115 | 3.681 | 4.570 | -0.161 | -5.518 | not_rated |
| inflation_pass_through | -0.890 | 1.751 | 2.047 | 0.505 | -1.270 | not_rated |
| c7_channel_a_oos | 1.745 | 2.449 | 3.004 | 0.597 | -1.849 | PASS |

## Debt engine

The original cumulative recursion starts from observed 2010 gross debt. The Tesouro workbook has no 2006-2009 interest-payable observations, so no earlier implicit-rate series is invented.

| Year | Observed debt | Simulated debt | Simulated - observed |
|---:|---:|---:|---:|
| 2024 | 76.27 | 94.84 | +18.57 |
| 2023 | 73.83 | 91.05 | +17.22 |
| 2022 | 71.68 | 86.96 | +15.28 |

The one-step-ahead mean error is +1.36 pp/year and MAE is 2.05 pp. Re-anchoring each year separates equation error from accumulation.

The textbook identity omits stock-flow adjustments, valuation/reclassification effects and repo effects. Tesouro GFS interest and BCB primary-result/gross-debt series also differ in institutional coverage and timing.

## Stock-flow adjustment

SFA is observed debt minus the one-step prediction. The 2011-2017 mean is -0.500 pp of GDP/year and the sample SD is 2.420 pp. Only these seven years estimate the constant applied after the observed 2017 anchor.

| Year | Implied SFA (pp GDP) | Documented context (not fitted) |
|---:|---:|---|
| 2011 | +1.705 | Treasury loans to BNDES |
| 2012 | +2.929 | Treasury loans to BNDES |
| 2013 | -1.832 |  |
| 2014 | +0.025 |  |
| 2015 | +0.213 |  |
| 2016 | -3.823 | BNDES early repayments and BCB result transfers |
| 2017 | -2.717 | BNDES early repayments and BCB result transfers |
| 2018 | -2.626 | BNDES early repayments and BCB result transfers |
| 2019 | -3.910 | BNDES early repayments and BCB result transfers |
| 2020 | -0.925 | BNDES early repayments and BCB result transfers |
| 2021 | -2.359 | BNDES early repayments and BCB result transfers |
| 2022 | -3.366 | BNDES early repayments and BCB result transfers |
| 2023 | -1.622 |  |
| 2024 | -0.707 |  |

The operation labels provide balance-sheet context; they are not fitted annual values. The OOS comparison recursively applies zero SFA or the fixed 2011-2017 mean during 2018-2024.

## Growth accounting plus external block

Observed PWT investment-derived capital accumulation, human capital and employment are used each year. TFP is fixed at the C2 central 2000-2019 rate and C6 is unchanged.

| Episode | Actual cumulative growth | Fixed-TFP factor model | C6 addition | Model total | Model - actual |
|---|---:|---:|---:|---:|---:|
| commodity boom (2005 base to 2010; 2003-04 unavailable because ToT starts in 2005) | 24.46% | 13.49% | +0.78 pp | 14.27% | -10.18 pp |
| recession (2014-2016) | -6.24% | 3.62% | -0.40 pp | 3.22% | +9.46 pp |

The boom row measures the 2006-2010 transitions from the 2005 level; earlier ToT observations are unavailable in the D2 input.

Largest annual growth residuals:

| Year | Observed | Model | C6 contribution | Model - observed |
|---:|---:|---:|---:|---:|
| 2007 | 6.07 | 1.81 | +0.10 | -4.26 |
| 2015 | -3.55 | 0.60 | -0.41 | +4.14 |
| 2016 | -3.28 | -0.14 | +0.14 | +3.13 |

## Period diagnostic

Every calendar window is treated identically. Changes are end-year minus start-year values within the window; commodity prices use 100 x ln(end/start). Primary balance is sign-flipped, so positive means surplus. This is descriptive, not a causal attribution or ranking.

| Period | Avg GDP growth | Spending/GDP change | Revenue/GDP change | Primary-balance change | Gross-debt change | Commodity log change | Implied growth | Residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dilma I | +2.35% | +1.42 pp | -0.79 pp | -3.18 pp | +4.51 pp | -7.23% | +2.13% | -0.22 pp |
| 2015-2016 | -3.41% | +3.49 pp | +2.36 pp | -1.92 pp | +13.56 pp | -27.68% | -0.12% | +3.29 pp |
| Temer | +1.55% | -1.09 pp | -0.42 pp | +0.93 pp | +5.43 pp | +5.81% | +2.28% | +0.73 pp |
| Bolsonaro | +1.43% | -0.37 pp | +2.36 pp | +2.80 pp | -3.59 pp | +29.04% | +2.24% | +0.81 pp |
| Lula III (data end 2024) | +3.33% | +1.46 pp | -0.05 pp | -1.65 pp | +4.59 pp | -14.37% | +1.05% | -2.28 pp |
| 2023-2025 [separately flagged] | +2.99% | +1.94 pp | +0.21 pp | NA pp | NA pp | NA | NA | NA pp |

Inputs are observed annual GDP growth; Q4 general-government primary spending/GDP; revenue/GDP from workbook sheet 3.2.a code `1`; sign-flipped consolidated primary balance; gross debt; and commodity export prices. The 2019 revenue figure includes the one-off transfer-of-rights auction in concessions code 1415.

The flagged 2023-2025 row uses 2025 GDP growth 2.3% (IBGE, released 2026-03-03; hand-entered) and complete 2025 spending/revenue. Debt, primary balance, commodity price, implied growth and residual are `NA` because those checked-in series stop in 2024; no value is carried forward.

Level changes run from the last year before each period (the inherited level) to the period's last year. Model-implied growth is the C7 `A_output_reverse` fitted value (constant -0.662 included, world growth as a level, as estimated), plus the C2 central total-expenditure multiplier (0.50) times annual primary-spending/GDP change. The reverse coefficients were fitted on 2010-2024, so all 2011-2024 windows are in-sample for that fit.

Residuals mix domestic policy, credit, politics, omitted shocks and measurement. They are not attributed to governments and must not be read as rankings.

## Multiplier diagnostic

The benchmark is growth minus its 2010-2024 mean (1.707%). Spending changes are endogenous and do not identify fiscal shocks, so this remains unrated.

- `multiplier_total`: correlation -0.108, RMSE 3.466 pp.
- `multiplier_categories`: correlation -0.161, RMSE 4.570 pp.

## Inflation pass-through diagnostic

Observed BRL/USD pass-through is compared with IPCA minus target. Mean error is -0.890 pp, RMSE 2.047 pp and correlation 0.505. This incomplete one-variable diagnostic remains unrated.

## Publication implications

Tier 1 passes, so paired scenario differences vs S0 clear the numerical gate; this is not proof of causal validity.
Tier 2 fails, so debt/GDP paths should not be published as model-validated levels.

The annual audit rows are in `data/brazil/backtest_results.csv` (residual = predicted minus observed).
