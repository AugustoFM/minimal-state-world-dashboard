# D2 historical back-tests

**Overall proposed gate: FAIL.** Only the two supplied numerical tolerances are rated. The multiplier and inflation exercises remain diagnostics, not validation tests.

No coefficient was tuned to improve these results. All calculations are offline and use the checked-in observations, C2 central parameters and unchanged C2/C6 equations.

## Results and proposed tolerances

| Block | Mean error (pp) | MAE (pp) | RMSE (pp) | Correlation | Final error (pp) | Verdict |
|---|---:|---:|---:|---:|---:|---|
| debt_engine | 4.879 | 7.129 | 9.322 | 0.953 | 18.571 | FAIL |
| debt_engine_one_step | 1.358 | 2.054 | 2.390 | 0.991 | 0.707 | not_rated |
| growth_block | 0.165 | 1.734 | 2.238 | 0.772 | 0.952 | PASS |
| multiplier_total | -0.044 | 2.619 | 3.466 | -0.108 | -4.651 | not_rated |
| multiplier_categories | 0.115 | 3.681 | 4.570 | -0.161 | -5.518 | not_rated |
| inflation_pass_through | -0.890 | 1.751 | 2.047 | 0.505 | -1.270 | not_rated |

Rated tolerances proposed for lead-developer approval: absolute 2024 debt error <= 5 pp of GDP; absolute growth mean error <= 0.5 pp/year over 2006-2019. `not_rated` means no tolerance was supplied, not a pass.

## Debt engine

The recursion starts from observed 2010 gross debt. A 2006 run is not possible from the supplied inputs: the Tesouro GFS workbook has no 2006-2009 interest-payable observations. Substituting Selic would not be an observed implicit debt rate, so no series was invented.

The largest absolute misses are:

| Year | Observed debt | Simulated debt | Simulated - observed |
|---:|---:|---:|---:|
| 2024 | 76.27 | 94.84 | +18.57 |
| 2023 | 73.83 | 91.05 | +17.22 |
| 2022 | 71.68 | 86.96 | +15.28 |

**One-step-ahead diagnostic (added in lead-developer review).** Re-anchoring each year on observed lagged debt isolates the recursion from accumulation. Its mean error is +1.36 pp/year (MAE 2.05); the implied stock-flow adjustment (observed minus one-step prediction) is positive in 2011-2012, when the Treasury lent to BNDES, and negative in 2016-2022, the years of BNDES early repayments to the Treasury and BCB result transfers used to redeem debt. The cumulative miss is therefore mostly the sum of these operations, which the textbook identity omits by construction. The diagnostic is not rated and does not change the gate verdict. Projections set future stock-flow adjustments to zero, identical across scenarios, so they largely cancel in paired differences vs S0 but not in debt levels.

These residuals are not hidden adjustments. The textbook identity omits stock-flow adjustments and valuation/reclassification effects; BCB gross debt is also affected by repo operations. In addition, Tesouro GFS interest and the BCB consolidated-public-sector primary result/gross-debt series have different institutional coverage and timing. Those concept differences accumulate when a simulated level is not re-anchored each year.

## Growth accounting plus external block

Observed PWT investment-derived capital accumulation, human capital and employment are used each year. TFP is held at the C2 central 2000-2019 rate. The C6 terms-of-trade coefficient, permanent/cyclical split and decay are unchanged.

| Episode | Actual cumulative growth | Fixed-TFP factor model | C6 ToT addition | Model total | Model - actual | Model / actual |
|---|---:|---:|---:|---:|---:|---:|
| commodity boom (2005 base to 2010; 2003-04 unavailable because ToT starts in 2005) | 24.46% | 13.49% | +0.78 pp | 14.27% | -10.18 pp | 58.4% |
| recession (2014-2016) | -6.24% | 3.62% | -0.40 pp | 3.22% | +9.46 pp | -51.7% |

The boom row begins with the 2005 level and measures the 2006-2010 transitions. The repository has no terms-of-trade observation before 2005, so the requested 2003-2004 external decomposition cannot be produced honestly.

Largest annual growth residuals:

| Year | Observed | Model | C6 contribution | Model - observed |
|---:|---:|---:|---:|---:|
| 2007 | 6.07 | 1.81 | +0.10 | -4.26 |
| 2015 | -3.55 | 0.60 | -0.41 | +4.14 |
| 2016 | -3.28 | -0.14 | +0.14 | +3.13 |

**External-block warning:** C6 adds only +0.78 pp to cumulative 2006-2010 growth. It therefore explains little of the boom and should not be presented as a sufficient external-history model. Missing channels include capital inflows/FDI, commodity-linked fiscal revenue, exchange-rate effects on inflation and interest rates, and FX-linked debt.

## Multiplier diagnostic

The benchmark is observed annual real GDP growth minus its 2010-2024 arithmetic mean (1.707%). The spending input is the annual change in Tesouro general-government primary spending/GDP. This is a weak test: observed spending changes are endogenous, annual data do not identify fiscal shocks, and the aggregate series cannot reveal which category actually changed.

- `multiplier_total`: correlation -0.108; signs agree in 64.3% of 2011-2024 years and 2/3 recession years (2014-2016).
- `multiplier_categories`: correlation -0.161; signs agree in 42.9% of 2011-2024 years and 1/3 recession years (2014-2016).

## Inflation pass-through diagnostic

Predicted extra inflation from observed BRL/USD changes is compared with IPCA minus the CMN target. Mean error is -0.890 pp, RMSE 2.047 pp and correlation 0.505. The target path is in `config/d2_inputs_proposed.yaml`, labelled **transcribed without a network check**. This is not a complete inflation model: it omits expectations, inertia, slack, commodity prices and administered prices.

## Publication implications

The proposed D2 gate fails. No failing block should be called validated and scenario results should not be published as model-validated projections.

Changes needed are structural rather than parameter retuning: add an explicit debt stock-flow/reconciliation layer with aligned fiscal concepts; extend C6 with the omitted external channels; identify fiscal shocks and category composition for a credible multiplier test; and embed pass-through in a broader inflation equation. Re-estimate or change parameters only with new sourced evidence and an out-of-sample protocol.

The annual audit rows are in `data/brazil/backtest_results.csv` (one row per year/test; residual = predicted minus observed).
