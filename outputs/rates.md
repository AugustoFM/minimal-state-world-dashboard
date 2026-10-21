# Brazil interest rates and an evidence-based S0 proposal

## Current position

On 21 October 2026 the Selic target was 13.75%. Paired with the latest available 12-month IPCA (4.58%, September), the Fisher ex-post real rate was 8.77%. This snapshot was at the 71.7th percentile of monthly observations since 2000 and the 89.6th percentile since 2010. The mixed-date snapshot is shown explicitly; the monthly CSV leaves October ex-post real Selic missing until October inflation exists.

The primary medium-term market measure is the Focus expectation for Selic relative to IPCA for calendar year t+3. The CSV also reports t+2 and the longest common Focus horizon as labelled robustness measures.

## Fiscal-expectations association

In the fixed monthly first-difference specification through September 2026 (n=200), a one-percentage-point improvement in the expected primary balance was associated with -3.61 basis points in the t+3 expected real rate (95% interval -15.01 to 7.78). A one-point increase in expected DLSP was associated with 0.16 basis points (95% interval -2.50 to 2.82). These are market associations, not causal effects.

All primary and robustness coefficients, including levels with trend, the 2017 start, DBGG from 2018, and EMBI through June 2024, are in `data/brazil/rates_estimates.csv`. Robustness results are labelled and do not replace the fixed primary specification.

## Descriptive event windows

Changes run from the month before the event to two months after. The October 2026 window is partial and ends at the last archived observation. These windows describe co-movement and do not isolate event effects.

| event | from_month | to_month | partial_window | change_medium_real_t3_pct | change_primary_balance_t2_pct_gdp | change_dlsp_t3_pct_gdp |
| --- | --- | --- | --- | --- | --- | --- |
| EC 95 spending cap | 2016-11-01 | 2017-02-01 | False | -0.603 | 0.500 | 3.440 |
| Pension reform final approval | 2019-09-01 | 2019-12-01 | False | -0.483 | 0.070 | 0.000 |
| PEC da Transicao | 2022-11-01 | 2023-02-01 | False | -0.276 | -0.050 | 0.800 |
| LC 200 approval | 2023-07-01 | 2023-10-01 | False | 0.000 | 0.000 | -0.050 |
| Fiscal package (Nov-Dec 2024) | 2024-10-01 | 2025-01-01 | False | 0.479 | 0.042 | 4.500 |
| 2026 first round | 2026-09-01 | 2026-10-01 | True | 0.000 | 0.090 | 0.055 |

## Pass-through to the debt

The annual regression uses 2010-2025 fiscal observations and has 15 usable rows after the lag. The long-run pass-through is 0.429 points of the implicit nominal debt rate per one-point Selic change. The current-year coefficient is 0.405, or 94.2% of the long-run response. This is a small annual sample and the coefficients are imprecise.

The implicit rate divides general-government interest payable by the average of current and prior December DBGG, as fixed in I1. Annual source-derived inputs are not separately written because they are intermediate calculations.

## Proposed S0 real-rate path

The 2025 implicit real debt-rate anchor is 8.63%. Focus determines 2026-2029; the real policy rate then converges in five annual steps to 5.0%. Before the fiscal term, the proposed implicit real debt rate is 7.88% in 2026, 7.14% in 2030, and 6.70% in 2045, versus the current fixed 5.05% assumption.

The fiscal term is the primary DLSP coefficient multiplied by scenario expected debt minus the 2025 S0 debt anchor, with the same equation for every scenario. It is not included in the table below because I1 does not prescribe scenario debt paths and model files may not be changed. The DLSP-estimation/DBGG-scenario concept mismatch is a data limitation; the DBGG estimate is retained as robustness.

| year | real_policy_rate_pct | implicit_real_debt_rate_pct | difference_from_fixed_5_05_pp |
| --- | --- | --- | --- |
| 2026 | 7.633 | 7.878 | 2.828 |
| 2027 | 7.361 | 7.716 | 2.666 |
| 2028 | 6.506 | 7.363 | 2.313 |
| 2029 | 6.280 | 7.251 | 2.201 |
| 2030 | 6.024 | 7.141 | 2.091 |
| 2034 | 5.000 | 6.702 | 1.652 |
| 2035 | 5.000 | 6.695 | 1.645 |
| 2045 | 5.000 | 6.695 | 1.645 |

## Data problems and interpretation

Focus begins in 2010, and DBGG expectations begin only in 2018. October 2026 is incomplete (last Focus survey 16 October); observed inflation and debt stocks end in September and August respectively. EMBI ends in June 2024. US yields use the last available daily observation in each month. The event design uses overlapping macro news and cannot identify effects. Expected DLSP and scenario DBGG are different debt concepts. The pass-through regression has only 15 usable observations. No missing value is interpolated.