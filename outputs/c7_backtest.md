# C7 external block v2: fixed-protocol back-test

The primary specifications were fixed before estimation. No specification was selected after seeing 2015-2024 outcomes. The main 2000-2014 fits contain only 15 annual observations; B3 is smaller still (six usable differences, 2012-2017). OLS uncertainty is Newey-West with one lag, and 90% intervals are normal approximations.

## Primary estimates

| channel | coefficient | estimate | newey_west_se | ci90_low | ci90_high | nobs | r2 |
|---|---|---|---|---|---|---|---|
| A_output | constant | 1.2332 | 0.5616 | 0.3095 | 2.1569 | 15 | 0.737 |
| A_output | dlnP | 0.1254 | 0.0243 | 0.0854 | 0.1653 | 15 | 0.737 |
| A_output | dlnP_lag | -0.0070 | 0.0200 | -0.0398 | 0.0259 | 15 | 0.737 |
| A_output | world_gdp_growth_pct | 0.5201 | 0.1701 | 0.2403 | 0.7999 | 15 | 0.737 |
| B1_spread | constant | -59.5775 | 45.8900 | -135.0598 | 15.9048 | 15 | 0.152 |
| B1_spread | dlnP | -4.7208 | 3.5236 | -10.5166 | 1.0750 | 15 | 0.152 |
| B1_spread | dUS | -131.4028 | 79.7124 | -262.5180 | -0.2875 | 15 | 0.152 |
| B2_real_rate | constant | -0.3166 | 0.5219 | -1.1751 | 0.5418 | 14 | 0.015 |
| B2_real_rate | dEMBI_per_100 | 0.1242 | 0.1421 | -0.1095 | 0.3579 | 14 | 0.015 |
| B3_debt_rate | dr | 0.1690 | 0.3738 | -0.4459 | 0.7839 | 6 | 0.125 |
| B3_debt_rate | dr_lag | 0.3948 | 0.3853 | -0.2389 | 1.0286 | 6 | 0.125 |
| C_investment | constant | 0.0592 | 0.2249 | -0.3107 | 0.4291 | 15 | 0.307 |
| C_investment | dlnP | 0.0403 | 0.0128 | 0.0193 | 0.0613 | 15 | 0.307 |
| C_investment | dlnP_lag | -0.0115 | 0.0141 | -0.0346 | 0.0116 | 15 | 0.307 |
| D_revenue | constant | -3.9413 | 0.9885 | -5.5673 | -2.3153 | 8 | 0.699 |
| D_revenue | lnP | 1.1526 | 0.2230 | 0.7859 | 1.5194 | 8 | 0.699 |
| D_dividends | constant | -3.3713 | 0.6782 | -4.4868 | -2.2558 | 8 | 0.666 |
| D_dividends | lnP | 0.8380 | 0.1496 | 0.5919 | 1.0840 | 8 | 0.666 |
| D_concessions | constant | -0.5700 | 1.2830 | -2.6803 | 1.5403 | 8 | 0.145 |
| D_concessions | lnP | 0.3147 | 0.2845 | -0.1533 | 0.7826 | 8 | 0.145 |

B3 pass-through of a one percentage-point policy real-rate change is 0.169 pp in year 1 and 0.564 pp cumulatively by year 2.

## Out-of-sample results

Residual and mean error are predicted minus observed. Sign agreement is the fraction of years with equal observed/predicted signs. The D regressions are levels, so their sign agreement is mechanically uninformative. The C6 column is the standalone C6 external growth contribution, not a complete GDP forecast.

| channel | RMSE | naive RMSE | mean error | sign agreement | RMSE excl. 2020 | naive excl. 2020 | C6 RMSE | verdict |
|---|---|---|---|---|---|---|---|---|
| A_output | 3.004 | 3.881 | +1.745 | 80.0% | 2.970 | 3.435 | 2.991 | supported |
| B1_spread | 128.436 | 82.326 | -76.400 | 60.0% | 135.294 | 74.635 | NA | not supported |
| B2_real_rate | 3.642 | 3.654 | -0.496 | 70.0% | 3.734 | 3.758 | NA | supported |
| B3_debt_rate | 1.608 | 1.187 | +0.177 | 57.1% | 1.616 | 1.270 | NA | not supported |
| C_investment | 1.222 | 1.325 | +0.337 | 60.0% | 1.248 | 1.365 | NA | supported |
| D_revenue | 0.910 | 0.910 | -0.747 | 100.0% | 0.983 | 0.980 | NA | not supported |
| D_dividends | 0.231 | 0.285 | -0.130 | 100.0% | 0.246 | 0.293 | NA | supported |
| D_concessions | 0.737 | 0.729 | -0.617 | 100.0% | 0.795 | 0.788 | NA | not supported |

A verdict is `supported` only when the fixed model's test RMSE beats the fit-window-mean naive benchmark and its key coefficient has the prespecified literature-consistent sign. Dividends and concessions are reported separately but do not create extra searched specifications.

The rule produces two knife-edge cases: B2 beats naive RMSE by only 0.012 pp and its key 90% interval includes zero; total D misses naive by only 0.0003 pp. A is supported against naive but its annual RMSE is slightly above the standalone C6 contribution. These labels apply the prespecified rule, not a claim of strong validation.

## Episodes

| episode | period | observed_cumulative_growth_pct | A_cumulative_growth_pct | C6_cumulative_growth_pct |
|---|---|---|---|---|
| commodity boom | 2006-2010 | 24.46 | 20.93 | 0.69 |
| domestic recession | 2014-2016 | -6.24 | 3.82 | -0.39 |

Channel A is a full conditional growth equation. C6 is only its external GDP-level contribution; the comparison is therefore diagnostic rather than like-for-like.

## Fixed robustness checks (not selected)

| channel | coefficient | estimate | newey_west_se | nobs fit | test RMSE | naive RMSE | sign agreement |
|---|---|---|---|---|---|---|---|
| A_output_CTOT | dlnCTOT | 3.7071 | 0.8883 | 15 | 3.362 | 3.881 | 80.0% |
| A_output_china | dlnP | 0.1154 | 0.0227 | 15 | 2.893 | 3.881 | 90.0% |
| B1_spread_fed_funds | dlnP | -4.2008 | 2.6421 | 15 | 134.469 | 82.326 | 70.0% |
| A_output_reverse | dlnP | 0.0824 | 0.0352 | 15 | 1.594 | 2.589 | 100.0% |
| B1_spread_reverse | dlnP | -2.0596 | 0.7808 | 15 | 267.858 | 277.208 | 90.0% |
| C_investment_reverse | dlnP | 0.0410 | 0.0097 | 15 | 0.804 | 0.878 | 60.0% |

These alternatives are reported without changing any primary verdict: CTOT for Pcx; China growth added to A; federal funds replacing the US 10-year yield in B1; and the prespecified 2010-2024 fit / 2000-2009 reverse tests for A, B1 and C.

## Literature reference points

Céspedes-Velasco (2012) reports that a roughly 60% commodity-price rise is associated with about +1% output relative to trend and +3.5 pp in the investment rate. For the comparable one-off log price change, the fixed C7 coefficients imply about 5.54% GDP after two years and 1.35 pp in the investment rate, holding world growth at its fit mean. These are scale references, not targets imposed on estimation. Uribe-Yue (2006) attributes roughly 20% and 12% of activity variance to US-rate and spread shocks respectively; that variance decomposition is qualitative context and is not directly comparable with these annual equations. Notably, C7's B1 US-rate coefficient is negative, contrary to the usual positive spread response, and B1 fails its OOS benchmark.

## Limits and data warnings

- Annual samples are tiny and the models are intentionally parsimonious. HAC intervals are especially fragile for B3's six fit observations.
- EMBI and Selic are endogenous to Brazilian activity and policy; coefficients are predictive associations, not identified causal effects.
- Pcx is a commodity export price index, not an export-volume measure.
- The 2020 pandemic lies in the test window; RMSE is shown both with and without 2020, but the primary verdict uses the fixed full window.
- The 2024 EMBI observation is only an annual mean through July. Its B1 prediction/residual is retained and explicitly flagged in the CSV.
- The fiscal-workbook concessions line includes oil royalties and special participations but is broader than a pure commodity-revenue measure.
- B3 cannot estimate a 2011 difference because the requested implicit-rate series starts in 2011; its actual fit observations are 2012-2017.
- The 2014-2016 collapse contains large domestic political, corruption-investigation and monetary shocks that these external regressors do not explain.
