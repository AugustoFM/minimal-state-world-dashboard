# D3 cross-country debt trajectories

## Findings for the S0 comparison

S0's median debt increase from 78.6% of GDP in 2025 to 244.44% in 2045 is 165.84 percentage points; with the C5 feedback it reaches 314.04%. The no-feedback change is at the 99.8th percentile of the 1400 observed 20-year changes and the 99.6th percentile among emerging-economy windows. The 2045 primary balance of -7.68% of GDP is at the 1.8th percentile overall and 1.8th percentile among emerging observations (lower means a larger deficit).

1 observed windows jointly had debt rise by at least 165.84 points and ended with a primary balance at or below -7.68% of GDP: VEN 1999-2019. The qualifying window is not a close analogue of smooth S0 drift: its summed inflation contribution is -736.34 points and SFA is 787.87 points, indicating extreme nominal dynamics and accounting/source residuals.

The primary fiscal-reaction estimates below are percentage points of primary balance per one-point lagged-debt change. The long-run response is rho/(1-phi). Brazil is time-series OLS with two-lag Newey-West uncertainty; the panel estimates use country fixed effects and country-clustered uncertainty.

| sample | debt_lag | long_run_debt_response | pb_lag |
|---|---|---|---|
| advanced | 0.0106 | 0.0352 | 0.6982 |
| brazil | -0.0149 | -0.0270 | 0.4504 |
| emerging | 0.0114 | 0.0377 | 0.6969 |
| full | 0.0108 | 0.0372 | 0.7091 |

In the calibration-relevant low-inflation 2000-2024 sample, r-g averaged -0.08% for advanced economies and -2.42% for emerging economies; Brazil averaged 2.83%. Full-sample results are reported only in the lead-review robustness section because high-inflation accounting contaminates both r-g and SFA.

r-g by group and decade:

| group | decade | nobs | mean | median | p10 | p90 |
|---|---|---|---|---|---|---|
| advanced | 1970.00 | 92.00 | -6.31 | -4.77 | -17.29 | 1.99 |
| advanced | 1980.00 | 236.00 | -1.46 | 0.11 | -8.94 | 6.12 |
| advanced | 1990.00 | 240.00 | 2.05 | 2.29 | -3.29 | 7.42 |
| advanced | 2000.00 | 240.00 | 1.11 | 0.70 | -2.90 | 5.49 |
| advanced | 2010.00 | 240.00 | -0.18 | -0.41 | -2.62 | 2.46 |
| advanced | 2020.00 | 120.00 | -2.70 | -3.42 | -8.18 | 4.09 |
| emerging | 1970.00 | 71.00 | -18.91 | -15.20 | -39.34 | -3.21 |
| emerging | 1980.00 | 183.00 | -19.15 | -12.86 | -47.85 | 0.53 |
| emerging | 1990.00 | 225.00 | -9.01 | -6.16 | -26.03 | 4.24 |
| emerging | 2000.00 | 258.00 | -4.61 | -3.79 | -14.08 | 3.43 |
| emerging | 2010.00 | 260.00 | -5.39 | -2.62 | -12.32 | 1.30 |
| emerging | 2020.00 | 130.00 | -7.13 | -3.58 | -18.68 | 8.87 |

The JST robustness sample contains 1260 country-years in 1950-2020 and has mean r-g -1.07% (long-term rate minus nominal GDP growth, using the exact ratio formula).

## Largest 20-year debt increases

Contributions are summed annual percentage points for years with a complete decomposition; SFA closes each annual identity.

| iso3 | start_year | end_year | debt_change | primary_deficit_contribution | interest_contribution | real_growth_contribution | inflation_contribution | sfa |
|---|---|---|---|---|---|---|---|---|
| VEN | 2000 | 2020.00 | 308.84 | 92.76 | 44.49 | 3.92 | -925.20 | 1092.88 |
| VEN | 2001 | 2021.00 | 223.51 | 96.10 | 42.39 | 4.61 | -1234.06 | 1314.47 |
| VEN | 1999 | 2019.00 | 176.43 | 80.33 | 45.84 | -1.27 | -736.34 | 787.87 |
| JPN | 1992 | 2012.00 | 159.33 | 64.57 | 55.06 | -20.35 | 28.46 | 31.59 |
| JPN | 1991 | 2011.00 | 156.78 | 54.74 | 56.12 | -17.29 | 25.65 | 37.55 |
| JPN | 1993 | 2013.00 | 156.61 | 70.88 | 53.97 | -25.13 | 29.25 | 27.64 |
| JPN | 1994 | 2014.00 | 148.92 | 73.83 | 52.88 | -26.44 | 25.54 | 23.11 |
| VEN | 1998 | 2018.00 | 144.66 | 65.79 | 48.70 | -0.04 | -568.18 | 598.39 |
| JPN | 1990 | 2010.00 | 142.65 | 43.04 | 57.17 | -19.73 | 20.53 | 41.65 |
| JPN | 1995 | 2015.00 | 135.75 | 74.46 | 51.63 | -28.54 | 20.26 | 17.94 |

## Large reductions and increases

A reduction starts at a complete-neighborhood local peak and reaches a fall of at least 15 points within ten years. An increase is every observed start year from which debt reaches at least 30 points higher within ten years; overlapping starts are retained, as the fixed protocol does not prescribe de-duplication.

| episode_type | group | episodes | median_debt_change | median_primary | median_growth | median_inflation | median_interest | median_sfa |
|---|---|---|---|---|---|---|---|---|
| increase | advanced | 235 | 44.62 | 20.76 | -7.30 | -12.80 | 31.14 | 14.24 |
| increase | emerging | 250 | 46.66 | 1.47 | -2.03 | -28.35 | 13.65 | 77.57 |
| reduction | advanced | 22 | -26.53 | -33.74 | -17.32 | -14.60 | 29.75 | 1.22 |
| reduction | emerging | 33 | -33.43 | -18.68 | -17.85 | -38.79 | 20.24 | 14.44 |

The signs in this table identify accounting associations, not causal effects. Positive primary-deficit, interest, or SFA contributions raise debt; negative real-growth and inflation contributions reduce the debt ratio.

Debt after local peaks:

| horizon | nobs | mean_change | median_change | p10_change | p90_change |
|---|---|---|---|---|---|
| 5 | 78 | -21.65 | -14.62 | -46.51 | -4.35 |
| 10 | 77 | -22.47 | -16.84 | -65.10 | 6.31 |

## Ageing and primary spending

| specification | outcome | estimate | standard_error | nobs |
|---|---|---|---|---|
| all_20_year_windows | prim_exp_change | 0.6609 | 0.2399 | 1347 |
| all_20_year_windows | pb_change | -0.4896 | 0.1194 | 1347 |
| 1995_2024_long_difference | prim_exp_change | 0.6943 | 0.3558 | 48 |
| 1995_2024_long_difference | pb_change | -0.0234 | 0.2020 | 48 |

S0's implied spending slope is 0.7445 points of GDP per one-point increase in the 65+ share: spending rises from 40.00% to 46.65% while the IBGE share rises from 11.56% to 20.49%. In the historical 20-year windows, faster ageing was associated with primary-balance deterioration (the slope shown above is negative), qualitatively like S0, but not with a debt-and-deficit combination as extreme as S0 except the jointly qualifying window identified above. Overlapping windows and common shocks prevent a causal interpretation.

## Brazil and IFI comparison

Brazil has 50 debt observations in 1975-2024 and 40 complete annual decompositions. S0 reaches 130.08% in 2035, versus IFI RAF 113's 111.6% base case, 80.9% optimistic case, and 148.1% pessimistic case. S0's 2035 primary balance is -4.04% of GDP, compared with the report's primary deficit near 1% of GDP.

## Lead-review robustness (2026-10-21)

### High-inflation contamination and calibration samples

The unrestricted means are r-g -9.22% for emerging economies and -7.83% for Brazil. The unrestricted emerging SFA mean is 6.15 points. These full-sample values are not suitable for calibration: in high-inflation years the FPP interest series behaves like a real/operational-interest measure while the inflation correction is left in SFA (Brazil 1976-1986 is the clearest case). Low inflation means GDP-deflator inflation below 15% in the observation year.

Low-inflation r-g distribution (%):

| period | sample | n | mean | median | p10 | p90 |
|---|---|---|---|---|---|---|
| 1975-2024 | advanced | 1092 | 0.49 | 0.35 | -5.15 | 5.76 |
| 1975-2024 | emerging | 822 | -2.91 | -3.03 | -9.93 | 3.75 |
| 1975-2024 | Brazil | 28 | 3.83 | 3.28 | -1.53 | 10.62 |
| 2000-2024 | advanced | 597 | -0.08 | -0.16 | -4.96 | 4.48 |
| 2000-2024 | emerging | 571 | -2.42 | -2.50 | -8.96 | 3.45 |
| 2000-2024 | Brazil | 25 | 2.83 | 2.76 | -1.54 | 6.73 |
| 2010-2024 | advanced | 358 | -0.91 | -0.88 | -5.67 | 3.09 |
| 2010-2024 | emerging | 347 | -2.09 | -2.23 | -8.49 | 2.88 |
| 2010-2024 | Brazil | 15 | 2.99 | 2.76 | -2.59 | 8.43 |

Low-inflation SFA distribution (percentage points of GDP):

| period | sample | n | mean | median | p10 | p90 |
|---|---|---|---|---|---|---|
| 1975-2024 | advanced | 1092 | 1.65 | 1.01 | -1.77 | 5.63 |
| 1975-2024 | emerging | 825 | 1.67 | 1.20 | -2.21 | 5.64 |
| 1975-2024 | Brazil | 28 | 2.90 | 2.28 | -0.34 | 5.82 |
| 2000-2024 | advanced | 597 | 1.57 | 0.80 | -1.49 | 5.23 |
| 2000-2024 | emerging | 573 | 1.42 | 1.11 | -1.68 | 5.03 |
| 2000-2024 | Brazil | 25 | 3.11 | 2.32 | -0.14 | 6.40 |
| 2010-2024 | advanced | 358 | 1.07 | 0.65 | -1.63 | 4.72 |
| 2010-2024 | emerging | 347 | 1.36 | 1.17 | -1.22 | 4.26 |
| 2010-2024 | Brazil | 15 | 1.68 | 1.07 | -0.14 | 3.84 |

On country-average r-g in the low-inflation 2000-2024 sample, Brazil ranks 1 of 26 emerging economies from highest to lowest.

Brazil r-g by period (all available observations, %):

| period | n | mean | median | p10 | p90 |
|---|---|---|---|---|---|
| 2000-2014 | 15 | 2.16 | 2.35 | -0.98 | 5.41 |
| 2015-2019 | 5 | 8.01 | 6.82 | 3.85 | 13.25 |
| 2020-2024 | 5 | -0.34 | 1.80 | -5.70 | 3.35 |

### Brazil primary-balance check

The official series uses the BCB NFSP convention, in which positive values are deficits; the table converts it to primary balance by multiplying by -1. The gap is FPP minus official, in percentage points of GDP.

| year | fpp_pb | official_pb | fpp_minus_official_gap |
|---|---|---|---|
| 2002 | 8.11 | 3.19 | 4.92 |
| 2003 | 5.03 | 3.24 | 1.79 |
| 2004 | 5.79 | 3.69 | 2.10 |
| 2005 | 6.16 | 3.74 | 2.42 |
| 2006 | 3.44 | 3.15 | 0.29 |
| 2007 | 4.62 | 3.24 | 1.38 |
| 2008 | 4.54 | 3.33 | 1.21 |
| 2009 | 1.89 | 1.94 | -0.05 |
| 2010 | 3.53 | 2.62 | 0.91 |
| 2011 | 4.90 | 2.94 | 1.96 |
| 2012 | 4.59 | 2.18 | 2.41 |
| 2013 | 3.54 | 1.71 | 1.83 |
| 2014 | 1.24 | -0.56 | 1.80 |
| 2015 | 2.64 | -1.86 | 4.50 |
| 2016 | 1.96 | -2.48 | 4.44 |
| 2017 | 1.03 | -1.68 | 2.71 |
| 2018 | 1.84 | -1.55 | 3.39 |
| 2019 | 2.34 | -0.84 | 3.18 |
| 2020 | -5.84 | -9.24 | 3.40 |
| 2021 | 4.18 | 0.72 | 3.46 |
| 2022 | 4.08 | 1.25 | 2.83 |
| 2023 | 0.42 | -2.28 | 2.70 |
| 2024 | 2.09 | -0.40 | 2.49 |

Across the 23 overlapping years, the mean FPP-minus-official gap is 2.44 points. Brazil-specific fiscal-reaction analysis should use the official BCB balance with FPP debt; the FPP-balance regression is retained only as a comparison.

### Fiscal-reaction robustness

The low-inflation panel restriction applies to the current observation year. All specifications retain the same debt, output-gap, and lagged-primary-balance regressors; Brazil uses OLS with Newey-West covariance at two lags. Long-run response is rho/(1-phi).

| sample | specification | debt_lag | long_run_debt_response | pb_lag | nobs |
|---|---|---|---|---|---|
| brazil | brazil_fpp_pb_2000_2024 | -0.0634 | -0.0730 | 0.1322 | 24 |
| brazil | brazil_official_pb_2000_2024 | -0.0230 | -0.0370 | 0.3789 | 22 |
| emerging | 2000_2024_robustness | 0.0139 | 0.0440 | 0.6848 | 624 |
| emerging | low_inflation_2000_2024_calibration | 0.0334 | 0.1045 | 0.6803 | 553 |
| emerging | low_inflation_robustness | 0.0284 | 0.0884 | 0.6792 | 823 |
| full | 2000_2024_robustness | 0.0224 | 0.0634 | 0.6462 | 1200 |
| full | low_inflation_2000_2024_calibration | 0.0341 | 0.0931 | 0.6338 | 1127 |
| full | low_inflation_robustness | 0.0136 | 0.0463 | 0.7054 | 1915 |

Small-sample warning: the Brazil estimates have only one short time series, and the official-balance regression loses its first available observation to the lag.

### Stabilisation arithmetic

The response needed per point of debt is `(r-g)/(1+g)`, with rates expressed as decimals. The emerging-median benchmark uses the same 2% growth assumption as the Brazil historical benchmark. A `yes` only means the estimated long-run response is at least this arithmetic threshold; it is not a forecast or a model change.

| sample | specification | long_run_response | benchmark | r_minus_g_pct | g_pct | response_needed | stabilises |
|---|---|---|---|---|---|---|---|
| full | primary | 0.0372 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | no |
| full | primary | 0.0372 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | yes |
| full | primary | 0.0372 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | yes |
| advanced | primary | 0.0352 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | no |
| advanced | primary | 0.0352 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | yes |
| advanced | primary | 0.0352 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | yes |
| emerging | primary | 0.0377 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | no |
| emerging | primary | 0.0377 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | yes |
| emerging | primary | 0.0377 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | yes |
| brazil | primary | -0.0270 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | no |
| brazil | primary | -0.0270 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | no |
| brazil | primary | -0.0270 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | no |
| full | low_inflation_robustness | 0.0463 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | no |
| full | low_inflation_robustness | 0.0463 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | yes |
| full | low_inflation_robustness | 0.0463 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | yes |
| full | 2000_2024_robustness | 0.0634 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | yes |
| full | 2000_2024_robustness | 0.0634 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | yes |
| full | 2000_2024_robustness | 0.0634 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | yes |
| full | low_inflation_2000_2024_calibration | 0.0931 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | yes |
| full | low_inflation_2000_2024_calibration | 0.0931 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | yes |
| full | low_inflation_2000_2024_calibration | 0.0931 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | yes |
| emerging | low_inflation_robustness | 0.0884 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | yes |
| emerging | low_inflation_robustness | 0.0884 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | yes |
| emerging | low_inflation_robustness | 0.0884 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | yes |
| emerging | 2000_2024_robustness | 0.0440 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | no |
| emerging | 2000_2024_robustness | 0.0440 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | yes |
| emerging | 2000_2024_robustness | 0.0440 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | yes |
| emerging | low_inflation_2000_2024_calibration | 0.1045 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | yes |
| emerging | low_inflation_2000_2024_calibration | 0.1045 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | yes |
| emerging | low_inflation_2000_2024_calibration | 0.1045 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | yes |
| brazil | brazil_official_pb_2000_2024 | -0.0370 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | no |
| brazil | brazil_official_pb_2000_2024 | -0.0370 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | no |
| brazil | brazil_official_pb_2000_2024 | -0.0370 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | no |
| brazil | brazil_fpp_pb_2000_2024 | -0.0730 | S0 central 2045 | 4.9000 | 0.5000 | 0.0488 | no |
| brazil | brazil_fpp_pb_2000_2024 | -0.0730 | Brazil low-inflation 2000-2024 mean | 2.8311 | 2.0000 | 0.0278 | no |
| brazil | brazil_fpp_pb_2000_2024 | -0.0730 | Emerging low-inflation 2000-2024 median | -2.5030 | 2.0000 | -0.0245 | no |

### Historical debt distribution

| sample | p95 | p99 |
|---|---|---|
| full panel | 119.64 | 197.82 |
| emerging | 86.87 | 147.18 |

The data contain no default/restructuring flag, so the maximum debt reached by an emerging economy without such a flag cannot be identified defensibly. The emerging p95 and p99 are reported instead. `historical_p99_debt_pct_gdp` in the proposed YAML replaces the former diagnostic-ceiling name; it remains descriptive, not a sustainability limit.

## Accounting diagnostics and coverage

The decomposition has 2301 observations. SFA has mean 4.07, standard deviation 14.48, and median 1.46 percentage points; 223 observations exceed 10 points in absolute value. These large residuals can reflect defaults, bank support, valuation changes, perimeter/definition changes, or mismatched source concepts and should not be assigned a cause from these data alone.

All observations with absolute SFA above 10 points:

| iso3 | year | delta_d | sfa |
|---|---|---|---|
| ARG | 1976 | -5.10 | 19.93 |
| ARG | 1977 | -3.68 | 14.16 |
| ARG | 1981 | 15.12 | 16.73 |
| ARG | 1982 | 25.70 | 38.47 |
| ARG | 1983 | 12.01 | 50.92 |
| ARG | 1984 | -9.65 | 44.30 |
| ARG | 1985 | 0.65 | 50.69 |
| ARG | 1986 | 0.65 | 29.83 |
| ARG | 1987 | 18.26 | 52.11 |
| ARG | 1988 | -12.75 | 44.07 |
| ARG | 1989 | 56.83 | 115.87 |
| ARG | 1990 | -69.68 | 42.84 |
| ARG | 1991 | -12.81 | 18.20 |
| ARG | 2002 | 99.20 | 104.03 |
| ARG | 2004 | -7.28 | 24.86 |
| ARG | 2005 | -37.60 | -14.54 |
| ARG | 2015 | 7.87 | 12.19 |
| ARG | 2018 | 28.22 | 38.58 |
| ARG | 2019 | 4.59 | 27.09 |
| ARG | 2020 | 13.98 | 23.96 |
| ARG | 2021 | -22.77 | 15.59 |
| ARG | 2022 | 3.26 | 35.23 |
| ARG | 2023 | 70.30 | 112.99 |
| ARG | 2024 | -69.95 | 34.17 |
| BOL | 1976 | 12.74 | 18.33 |
| BOL | 1977 | 13.47 | 12.87 |
| BOL | 1979 | 9.55 | 12.11 |
| BOL | 1980 | 7.99 | 10.12 |
| BOL | 1981 | 21.68 | 32.35 |
| BOL | 1982 | 33.67 | 90.42 |
| BOL | 1983 | 1.92 | 93.16 |
| BOL | 1984 | 9.20 | 130.89 |
| BOL | 1985 | 38.75 | 194.08 |
| BOL | 1986 | -56.25 | 82.48 |
| BOL | 1987 | -3.65 | 10.74 |
| BOL | 1988 | -29.43 | -10.76 |
| BOL | 1990 | 4.94 | 17.98 |
| BOL | 1994 | 3.79 | 10.42 |
| BOL | 2000 | 12.64 | 13.40 |
| BOL | 2006 | -27.78 | -10.13 |
| BRA | 1976 | 4.04 | 14.05 |
| BRA | 1977 | -0.73 | 10.32 |
| BRA | 1978 | 6.01 | 15.56 |
| BRA | 1979 | -0.45 | 14.52 |
| BRA | 1980 | 3.07 | 24.72 |
| BRA | 1981 | -5.07 | 14.94 |
| BRA | 1982 | -1.80 | 17.13 |
| BRA | 1983 | 18.70 | 37.00 |
| BRA | 1984 | 4.30 | 39.21 |
| BRA | 1985 | -3.20 | 36.46 |
| BRA | 1986 | -3.20 | 28.16 |
| BRA | 2000 | 17.70 | 18.51 |
| BRA | 2002 | 8.76 | 12.44 |
| CAN | 2020 | 27.86 | 13.13 |
| CHL | 1976 | -8.82 | 11.14 |
| CHL | 1978 | 9.41 | 16.04 |
| CHL | 1979 | -2.73 | 11.81 |
| CHL | 1983 | 25.18 | 26.56 |
| CHL | 1984 | 11.13 | 16.00 |
| CHL | 1985 | 23.15 | 39.01 |
| CHL | 1986 | 8.61 | 25.37 |
| CHL | 1987 | -6.79 | 17.98 |
| CHL | 1988 | -10.44 | 12.10 |
| CHL | 1990 | -1.64 | 12.52 |
| COL | 2000 | 8.39 | 13.54 |
| CRI | 1978 | 13.91 | 13.34 |
| CRI | 1982 | -0.44 | 12.00 |
| CRI | 1991 | 9.82 | 16.38 |
| CRI | 1998 | 10.13 | 12.75 |
| DNK | 1978 | 10.28 | 12.25 |
| DNK | 1981 | 12.43 | 10.06 |
| DNK | 1982 | 12.78 | 11.04 |
| DNK | 2008 | 5.97 | 10.24 |
| DOM | 1981 | 14.63 | 14.32 |
| DOM | 1985 | 37.43 | 43.72 |
| DOM | 1987 | 23.08 | 35.49 |
| DOM | 1988 | -9.83 | 16.11 |
| DOM | 1990 | 22.15 | 41.11 |
| DOM | 2003 | 26.66 | 27.59 |
| ECU | 2000 | -13.02 | -25.97 |
| FIN | 1992 | 17.40 | 11.53 |
| GRC | 1990 | 13.52 | 10.63 |
| GRC | 1993 | 20.61 | 18.23 |
| GRC | 2012 | -10.80 | -34.29 |
| GRC | 2018 | 6.93 | 10.98 |
| IDN | 1987 | 11.48 | 17.40 |
| IDN | 1998 | 46.12 | 53.29 |
| IDN | 1999 | 23.37 | 31.90 |
| IND | 1991 | 25.88 | 24.59 |
| IRL | 1979 | 12.81 | 10.20 |
| IRL | 2011 | 23.29 | 12.74 |
| ISL | 1980 | 3.71 | 13.08 |
| ISL | 1982 | 6.58 | 16.42 |
| ISL | 1983 | 1.80 | 12.10 |
| ISL | 1984 | 1.67 | 11.40 |
| ISL | 1999 | 32.64 | 37.00 |
| ISL | 2001 | 7.59 | 15.94 |
| ISL | 2006 | 1.72 | 17.00 |
| ISL | 2007 | -2.25 | 11.63 |
| ISL | 2008 | 41.95 | 38.38 |
| ISL | 2009 | 18.42 | 11.81 |
| ISR | 1980 | -1.19 | 66.88 |
| ISR | 1985 | -84.97 | 109.95 |
| ISR | 1986 | -36.52 | 27.77 |
| ISR | 1988 | 2.13 | 21.00 |
| ISR | 1989 | 2.05 | 16.63 |
| ISR | 1990 | -9.16 | 10.09 |
| MEX | 1977 | 10.15 | 15.82 |
| MEX | 1981 | 10.27 | 13.87 |
| MEX | 1986 | 17.37 | 18.07 |
| MEX | 1987 | 4.86 | 21.71 |
| MEX | 1996 | 11.79 | 16.04 |
| NLD | 2008 | 11.61 | 13.97 |
| NOR | 1977 | 5.25 | 10.60 |
| NOR | 1978 | 6.15 | 11.20 |
| NOR | 1984 | 0.43 | 10.49 |
| NOR | 1985 | 2.38 | 14.98 |
| NOR | 1986 | 7.54 | 14.42 |
| NOR | 1991 | 10.30 | 11.82 |
| NOR | 1995 | -17.91 | -11.21 |
| NOR | 2000 | 3.71 | 23.13 |
| NOR | 2001 | -1.43 | 12.97 |
| NOR | 2002 | 6.71 | 15.90 |
| NOR | 2003 | 9.13 | 17.74 |
| NOR | 2004 | 0.75 | 15.93 |
| NOR | 2005 | -1.50 | 18.27 |
| NOR | 2006 | 10.26 | 33.14 |
| NOR | 2007 | -3.07 | 17.66 |
| NOR | 2008 | -1.97 | 22.17 |
| NOR | 2010 | 0.41 | 13.76 |
| NOR | 2012 | 1.28 | 16.71 |
| NOR | 2013 | 0.50 | 12.27 |
| NOR | 2015 | 4.66 | 10.47 |
| NOR | 2018 | 1.16 | 11.64 |
| NOR | 2021 | -4.45 | 14.89 |
| NOR | 2022 | -5.52 | 30.12 |
| NOR | 2023 | 8.07 | 20.36 |
| NOR | 2024 | -1.41 | 12.47 |
| NZL | 1976 | 6.19 | 11.75 |
| PAK | 1991 | 7.50 | 10.01 |
| PAK | 2000 | 0.94 | 23.79 |
| PAK | 2019 | 12.39 | 11.58 |
| PAN | 1976 | 17.11 | 17.56 |
| PAN | 1977 | 7.93 | 10.14 |
| PAN | 1988 | 12.83 | -15.14 |
| PAN | 1989 | -0.63 | -13.94 |
| PAN | 1990 | 8.25 | 12.96 |
| PAN | 1996 | -11.64 | -12.29 |
| PER | 1977 | 10.31 | 12.97 |
| PER | 1978 | 11.18 | 22.82 |
| PER | 1979 | -10.11 | 14.84 |
| PER | 1982 | 3.63 | 12.61 |
| PER | 1983 | 21.93 | 30.23 |
| PER | 1984 | 0.49 | 26.21 |
| PER | 1985 | 6.77 | 40.13 |
| PER | 1986 | -14.88 | 10.05 |
| PER | 1988 | 3.75 | 32.98 |
| PER | 1989 | -7.94 | 31.76 |
| PER | 1990 | 21.36 | 47.69 |
| PER | 1991 | -7.91 | 34.85 |
| PER | 1992 | -1.56 | 14.51 |
| PER | 1993 | 3.15 | 16.75 |
| PHL | 1983 | 10.22 | 14.96 |
| PHL | 1984 | 2.66 | 16.09 |
| PHL | 1985 | 7.31 | 11.81 |
| PHL | 1986 | 24.64 | 27.34 |
| PHL | 1993 | 14.69 | 19.83 |
| PRT | 1985 | 8.13 | 10.08 |
| PRY | 1984 | 8.39 | 13.52 |
| PRY | 1985 | 23.66 | 31.99 |
| PRY | 1986 | 2.43 | 19.14 |
| PRY | 1987 | 11.57 | 29.87 |
| PRY | 1988 | -9.74 | 10.98 |
| PRY | 1989 | -6.02 | 16.47 |
| PRY | 1990 | 14.09 | 37.36 |
| PRY | 1998 | 4.17 | 10.98 |
| PRY | 1999 | 9.88 | 14.41 |
| PRY | 2002 | 13.44 | 17.19 |
| RUS | 1998 | 80.49 | 79.04 |
| RUS | 1999 | -42.81 | 15.09 |
| THA | 1998 | 13.84 | 11.12 |
| THA | 2000 | 28.83 | 28.64 |
| TUR | 1981 | 9.63 | 15.69 |
| TUR | 1984 | 9.88 | 18.13 |
| TUR | 1985 | 1.71 | 11.76 |
| TUR | 1987 | 2.12 | 10.75 |
| TUR | 1988 | -1.70 | 12.12 |
| TUR | 1994 | 10.02 | 18.19 |
| TUR | 1995 | -4.53 | 14.60 |
| TUR | 1999 | 15.56 | 13.82 |
| TUR | 2000 | -0.86 | 10.28 |
| TUR | 2001 | 24.11 | 28.19 |
| URY | 1984 | 18.30 | 20.82 |
| URY | 1986 | 5.57 | 18.66 |
| URY | 1987 | 2.73 | 18.12 |
| URY | 1988 | -2.50 | 12.30 |
| URY | 1992 | 1.83 | 10.98 |
| URY | 2002 | 50.69 | 48.98 |
| URY | 2003 | 1.82 | 13.03 |
| URY | 2012 | 8.55 | 11.22 |
| VEN | 1989 | 15.54 | 34.16 |
| VEN | 1990 | 1.43 | 26.13 |
| VEN | 1991 | -1.07 | 12.44 |
| VEN | 1993 | 2.94 | 13.31 |
| VEN | 1994 | 6.14 | 16.40 |
| VEN | 1996 | -0.00 | 32.50 |
| VEN | 2000 | -1.86 | 10.12 |
| VEN | 2002 | 17.45 | 21.35 |
| VEN | 2003 | 7.85 | 17.49 |
| VEN | 2010 | 10.13 | 13.79 |
| VEN | 2011 | 14.77 | 15.99 |
| VEN | 2013 | 26.95 | 33.61 |
| VEN | 2014 | -0.50 | 31.77 |
| VEN | 2015 | 44.87 | 83.17 |
| VEN | 2016 | 8.64 | 91.63 |
| VEN | 2017 | -4.79 | 106.06 |
| VEN | 2018 | 41.70 | 144.26 |
| VEN | 2019 | 30.68 | 193.96 |
| VEN | 2020 | 130.55 | 315.13 |
| VEN | 2021 | -82.30 | 222.92 |
| VEN | 2022 | -89.82 | 83.44 |
| VEN | 2023 | -25.96 | 103.42 |
| VEN | 2024 | 25.81 | 76.26 |

Country debt coverage and longest annual increase runs:

| iso3 | group | start_year | end_year | debt_observations | pb_observations | interest_observations | growth_observations | inflation_observations | decomposition_observations | longest_increase_run |
|---|---|---|---|---|---|---|---|---|---|---|
| ARG | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 9 |
| AUS | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 13 |
| AUT | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 13 |
| BEL | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 13 |
| BOL | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 10 |
| BRA | emerging | 1975 | 2024 | 50 | 41 | 41 | 50 | 50 | 40 | 7 |
| CAN | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 8 |
| CHE | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 9 |
| CHL | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 17 |
| CHN | emerging | 1984 | 2024 | 35 | 36 | 36 | 50 | 50 | 29 | 13 |
| COL | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 8 |
| CRI | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 13 |
| DEU | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 10 |
| DNK | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 9 |
| DOM | emerging | 1975 | 2024 | 50 | 45 | 45 | 50 | 50 | 45 | 6 |
| ECU | emerging | 1995 | 2024 | 30 | 30 | 30 | 50 | 50 | 29 | 10 |
| ESP | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 8 |
| FIN | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 7 |
| FRA | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 11 |
| GBR | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 14 |
| GRC | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 14 |
| IDN | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 7 |
| IND | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 9 |
| IRL | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 10 |
| ISL | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 8 |
| ISR | advanced | 1975 | 2024 | 48 | 43 | 45 | 50 | 50 | 41 | 3 |
| ITA | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 14 |
| JPN | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 14 |
| KOR | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 13 |
| MAR | emerging | 1990 | 2024 | 35 | 35 | 35 | 50 | 50 | 34 | 6 |
| MEX | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 4 |
| MYS | emerging | 1990 | 2024 | 35 | 35 | 35 | 50 | 50 | 34 | 6 |
| NLD | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 13 |
| NOR | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 6 |
| NZL | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 5 |
| PAK | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 7 |
| PAN | emerging | 1975 | 2024 | 50 | 46 | 46 | 50 | 50 | 45 | 4 |
| PER | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 8 |
| PHL | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 8 |
| POL | emerging | 1990 | 2024 | 35 | 30 | 35 | 34 | 34 | 30 | 4 |
| PRT | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 7 |
| PRY | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 13 |
| RUS | emerging | 1992 | 2024 | 33 | 27 | 27 | 35 | 35 | 27 | 7 |
| SWE | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 9 |
| THA | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 6 |
| TUR | emerging | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 4 |
| URY | emerging | 1975 | 2024 | 49 | 50 | 50 | 50 | 50 | 47 | 7 |
| USA | advanced | 1975 | 2024 | 50 | 50 | 50 | 50 | 50 | 49 | 12 |
| VEN | emerging | 1975 | 2024 | 50 | 42 | 42 | 50 | 50 | 41 | 5 |
| ZAF | emerging | 1975 | 2024 | 50 | 47 | 47 | 50 | 50 | 46 | 12 |

## Implications for a lead-developer decision

- Test an S0 robustness variant with the estimated emerging-economy fiscal response, while retaining uncertainty and reporting ranges.
- Calibrate r-g and SFA from the emerging distribution and show Brazil separately; do not treat either residual accounting term as a policy effect.
- Keep inflation as an explicit debt-ratio channel. Historical inflation contributions can be large, but the evidence does not imply that inflation is a costless adjustment mechanism.
- The within-country r-g/debt slope is evidence about feedback, not a structural risk-premium estimate. The proposed YAML therefore labels any debt ceiling as a diagnostic bound rather than an estimated sustainability limit.

## Limitations

The fiscal data are IMF historical reconstructions and can mix government perimeters across countries and time. WDI deflator inflation and real growth do not always match the fiscal-series denominator, so SFA also absorbs source mismatch. Dynamic fixed effects are biased in short panels; Brazil's sample is small; HP output gaps are end-point sensitive. Overlapping 20-year windows are dependent observations. Peaks require all 11 annual debt observations in the +/-5-year neighborhood. No missing value is interpolated, and JST is a robustness dataset for advanced economies only.
