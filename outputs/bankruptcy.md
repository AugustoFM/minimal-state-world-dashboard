# Firm distress, exits and interest rates in Brazil

The estimates below describe historical associations. They are not causal estimates or forecasts, and the proposed channel is applied identically to every scenario.

## Main estimates

The cumulative monthly NPL response is **0.460 pp per 1 pp of the ex-ante real rate** (95% CI 0.256 to 0.664; n=156). This is the sum of coefficients at 0, 6, 12 and 18 months, conditional on 12-month IBC-Br growth.

In the 14-year IBGE firm sample, the current annual real-rate coefficient for the exit rate is **0.713 pp per 1 pp** (95% CI -0.085 to 1.512; n=14). The sample is small and the interval is imprecise.

### Monthly robustness

| specification | estimate | ci95 low | ci95 high | nobs |
|---|---|---|---|---|
| primary_real_rate | 0.460 | 0.256 | 0.664 | 156 |
| robust_selic | 0.304 | 0.237 | 0.370 | 156 |
| robust_lending_rate | 0.275 | 0.221 | 0.329 | 156 |
| robust_exclude_pandemic | 0.409 | 0.160 | 0.658 | 134 |

## Serasa 2024-2026

Counts below are CNPJs. 2024 and 2025 are full years; 2026 covers January-May only. The Selic monthly average reached 15% in July 2025 and remained at 15% through February 2026 in the archived I1 series. These short descriptive series do not identify a rate effect.

| year | serasa rj requested cnpjs | serasa bankruptcy requested cnpjs |
|---|---|---|
| 2024 | 2193 | 867 |
| 2025 | 2621 | 745 |
| 2026 | 878 | 277 |

RJ requests by sector:

| period | commerce | industry | services | agriculture |
|---|---|---|---|---|
| 2024 | 524 | 440 | 647 | 582 |
| 2025 | 563 | 479 | 770 | 809 |
| 2026 Jan-May | 174 | 152 | 308 | 244 |

The workbook has no firm-size breakdown, so a size summary is unavailable rather than estimated. It distinguishes requests from decrees/grants/approvals; the table uses requests consistently.

### Sparse annual press-release observations

| year | serasa bankruptcy requested annual | serasa rj requested annual | serasa method |
|---|---|---|---|
| 2011 | 1737 | NA | old method (unit not stated) |
| 2012 | 1929 | NA | old method (unit not stated) |
| 2013 | 1758 | NA | old method (unit not stated) |
| 2019 | 1417 | 1387 | old method (unit not stated) |
| 2020 | 972 | 1179 | old method (unit not stated) |
| 2021 | 950 | 891 | old method (unit not stated) |
| 2022 | 866 | 833 | old method (unit not stated) |
| 2024 | 949 | 2273 | old method (unit not stated) |
| 2025 | 698 | 2466 | new method: CNPJs (977 processes for RJ); preliminary |

The old and relaunched methods are shown with their flags and are not used in a regression. For 2025, the later workbook monthly total (2,621 RJ-requesting CNPJs) differs from the preliminary annual press-release point (2,466); the vintages are retained separately and not reconciled.

## Annual exit-rate scatter table

| year | firm exit rate pct | annual mean ex post real selic pct | annual mean ex post real selic lag1 pct | real gdp growth pct |
|---|---|---|---|---|
| 2008.000 | 17.655 | 6.410 | 8.121 | 5.094 |
| 2009.000 | 17.690 | 5.009 | 6.410 | -0.126 |
| 2010.000 | 16.255 | 4.626 | 5.009 | 7.528 |
| 2011.000 | 19.039 | 4.803 | 4.626 | 3.974 |
| 2012.000 | 17.383 | 3.065 | 4.803 | 1.921 |
| 2013.000 | 14.570 | 1.961 | 3.065 | 3.005 |
| 2014.000 | 20.713 | 4.355 | 1.961 | 0.504 |
| 2015.000 | 15.676 | 4.088 | 4.355 | -3.546 |
| 2016.000 | 16.056 | 4.985 | 4.088 | -3.276 |
| 2017.000 | 15.686 | 6.478 | 4.985 | 1.323 |
| 2018.000 | 17.368 | 2.822 | 6.478 | 1.784 |
| 2019.000 | 14.014 | 2.219 | 2.822 | 1.221 |
| 2020.000 | 13.012 | -0.304 | 2.219 | -3.277 |
| 2021.000 | 11.660 | -3.473 | -0.304 | 4.763 |

## Interpretation and proposed channel

Higher real rates can coincide with higher debt-service burdens, weaker refinancing conditions and later loan distress or exit. The historical specifications cannot isolate this channel from common macroeconomic shocks, policy responses, borrower composition or legal/measurement changes.

`config/bk_proposed.yaml` stores a proposal only: the scenario real rate is the base real rate plus the I1 offset where used plus the C5 risk premium. The NPL equation uses the monthly cumulative association; the exit-rate index uses the annual current-rate association and is normalized to 100 in the base year. Because no scenario output-gap coefficient is identified here, it is an explicit zero placeholder pending separate estimation. Future integration must propagate parameter uncertainty and show p10/p50/p90, never a single forecast path.

Full definitions, assumptions and limitations are in `docs/bankruptcy.md`.
