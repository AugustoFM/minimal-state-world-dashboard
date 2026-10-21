# I1 interest-rate method

`python -m src.rates` reads archived files only and deterministically rebuilds the monthly data, estimates, event table, report, method note, and proposal YAML.

## Transformations

The monthly Selic is the calendar-month average of daily target observations. Twelve-month IPCA is SGS 13522. Real rates use the exact Fisher formula `((1+n/100)/(1+pi/100)-1)*100`. For every Focus indicator/reference-year pair, the observation with the latest survey date in the month is retained. Horizons are calendar-year alignments: t+h means reference year equals survey year plus h. No value is carried or interpolated.

The primary medium-term expected real rate pairs t+3 Selic and IPCA. The t+2 and longest common reference year are robustness measures. The next-calendar-year pair is the ex-ante one-year measure. Daily US 10-year and EMBI data use the last non-missing observation in each month because the regressions compare end-of-month Focus snapshots.

## Estimation

The fixed primary regression uses monthly first differences from January 2010 through September 2026 and an intercept. Regressors are t+2 expected primary balance, t+3 expected DLSP, and the US 10-year yield. OLS and Bartlett Newey-West covariance with six lags are implemented in numpy without a finite-sample correction. Robustness specifications use levels plus a linear trend, a 2017 start, DBGG from 2018, and EMBI through June 2024. Coefficients are associations, not causal estimates.

The event table subtracts the month-before value from the two-month-after value. The fiscal-package event is dated November 2024, so its fixed window is October 2024 to January 2025. The October 2026 event is explicitly partial and ends at the last available month.

Annual implicit nominal interest equals interest payable as a share of GDP divided by average current/prior December DBGG. It is regressed on current and lagged calendar-year average Selic for 2010-2025. Long-run pass-through is the sum of the two slopes; year-one share is the current slope divided by that sum. Newey-West uses one lag. Annual IPCA compounds the 12 monthly SGS 433 changes, and the 2025 implicit real anchor uses Fisher.

## Proposal

The proposed real-policy path uses the latest archived Focus medians for 2026-2029, five equal annual steps from the 2029 value to the 5% neutral rate in 2034, and 5% thereafter. Starting from the observed 2025 implicit real debt rate, each annual change applies the estimated current and lagged coefficients to current and lagged real-policy-rate changes; 2026 therefore uses the observed 2024-2025 lagged change. The YAML preserves the neutral range 4.5-6.0 and the primary fiscal coefficient with its confidence interval. The fiscal term is formula-only because scenario debt paths are outside I1.

## Limitations

Focus coverage begins in 2010 and DBGG expectations in 2018. October 2026 is partial. EMBI stops in June 2024. Expected DLSP is not the same concept as scenario DBGG. First differences can be noisy; the regressions are short and observational. Pass-through uses only 15 lag-complete annual observations and may combine maturity, composition, inflation, and valuation effects. The neutral-rate range comes from the separate review, not these regressions. Event windows contain all contemporaneous news and support no causal attribution.