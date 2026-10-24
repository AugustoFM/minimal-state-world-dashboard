# Firm distress and interest rates: method

## Definitions and construction

The monthly panel runs from March 2011 through August 2026. Ipeadata/BCB series are aligned to calendar months. The primary outcome is the 12-month change in the non-performing-loan (NPL) rate for firms using free-market credit. The primary rate variable is the 12-month change in the one-year-ahead ex-ante real rate already constructed by I1. IBC-Br enters as 100 times its 12-month log change, an activity-growth control. No gaps are interpolated.

IBGE firm birth, entry and exit rates equal the relevant event count divided by active firms in that year, times 100. Employer birth and death rates use active employer firms as denominator. These ratios are descriptive accounting rates, not hazards for a fixed cohort. Annual real rates use the calendar-year mean ex-post real Selic so the fixed 2008-2021 sample is complete; the previous-year term is computed from 2007 before restricting the table to 2008-2025. Real GDP growth is the archived World Bank series in `data/brazil/backtest_observed.csv`.

Serasa monthly CNPJ totals and sectors use the non-cumulative workbook sheets. The archived workbook contains four sectors (commerce, industry, services and agriculture), but no firm-size field. Size results are therefore reported as unavailable; none are inferred. Sparse annual press-release observations retain the supplied `method` flag. Old-method counts and the relaunched 2025 CNPJ method are never spliced into a regression.

## Estimation assumptions

The primary regression is OLS of the 12-month NPL change on 12-month ex-ante-real-rate changes at lags 0, 6, 12 and 18 months, plus 12-month log IBC-Br growth and an intercept. The cumulative response is the sum of the four rate slopes. Its variance is the sum of every element in their covariance submatrix. Bartlett Newey-West standard errors use 18 lags, no finite-sample correction, and normal 95% confidence intervals, matching `src/rates.py`.

Robustness replaces the real rate with the Selic target or the free-credit firm lending rate, and separately removes March 2020-December 2021. Local projections shift the same 12-month NPL-change outcome forward by horizons 0-24 while retaining the four real-rate-change terms and activity control. They are sensitivity estimates, not a structural impulse response.

Annual regressions use an intercept, current and prior calendar-year mean ex-post real Selic, real GDP growth, and Newey-West uncertainty with one lag. The firm sample has 14 years (2008-2021); the employer sample has eight (2015-2022). These very small samples make estimates and confidence intervals imprecise.

## Limitations

All estimates are associations, not causal effects. Rate changes may respond to the same macroeconomic conditions that affect distress, and controls are incomplete. NPLs cover bank credit rather than all firm finance and can be affected by portfolio composition, recognition rules and write-offs. IBC-Br is an activity proxy, not a model-consistent output gap. Pandemic credit programmes and moratoria can change both measured arrears and exits; the exclusion check does not remove every pandemic-related effect.

The public Serasa series is short, observations may be revised, one process can contain multiple CNPJs, and the 2025 relaunch creates a method break. Legal requests, decrees, grants and approvals are different stages and are not interchangeable. IBGE exit and employer-death definitions differ from bankruptcy and judicial recovery. The proposed YAML is not wired into model files; any later use must apply the same equation to every scenario and propagate uncertainty into p10/p50/p90 ranges.
