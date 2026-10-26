# IY1: interest-income and inflation-tax distribution diagnostic

Built in direct response to an independent review of this project's academic paper (`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the microsimulation omits the regressive channels of (1) higher government interest expense accruing to bondholders concentrated at the top of the income distribution and (2) an inflation tax falling hardest on poor households' non-indexed transfers. Both are wired as off-by-default arguments to `src.micro.simulate_household_incomes` and run here as a standalone diagnostic comparing Gini/poverty with and without both channels switched on.

Capital-income concentration (Receita Federal declared capital/financial income, Table V, 2024): top 1% of declarants hold 68.3% of it, top 10% hold 90.7%.

Draws: 300 (seed 20261026, central draw plus 299 sampled).

## Effect of switching both IY1 channels on, vs the published (channels-off) Gini/poverty

| Scenario | Horizon | Gini change from IY1 (points, p50 [p10,p90]) | Poverty (R$218) with IY1 (p50 [p10,p90]) | Poverty (R$218) without IY1 (p50 [p10,p90]) |
|---|---:|---|---|---|
| E_amb | 5 | +0.301 [+0.106, +0.470] | 3.26 [3.01, 3.49] | 3.15 [3.12, 3.16] |
| E_amb | 10 | +1.309 [+0.716, +1.980] | 3.41 [3.03, 3.78] | 3.14 [3.11, 3.15] |
| E_amb | 15 | +3.037 [+1.765, +4.310] | 3.54 [3.15, 4.08] | 3.17 [3.15, 3.17] |
| E_amb | 20 | +5.023 [+2.484, +7.187] | 3.71 [3.15, 4.63] | 3.17 [3.17, 3.17] |
| E_mod | 5 | +0.201 [+0.035, +0.335] | 3.29 [3.03, 3.51] | 3.17 [3.16, 3.18] |
| E_mod | 10 | +0.755 [+0.405, +1.157] | 3.43 [3.04, 3.91] | 3.17 [3.15, 3.18] |
| E_mod | 15 | +1.763 [+1.043, +2.535] | 3.56 [3.17, 4.12] | 3.16 [3.15, 3.17] |
| E_mod | 20 | +3.127 [+1.595, +4.561] | 3.76 [3.18, 4.62] | 3.16 [3.15, 3.17] |

## Limitations

- The capital-income concentration curve comes from Receita Federal tax declarants, not the PNAD survey population; declarants are themselves concentrated among higher earners, so this is a reasonable but not survey-consistent proxy for 'how concentrated is capital income among the rich'.
- Government interest expense is derived from the debt identity's own rate-times-stock definition, not a separately estimated bond-holding-by-income-decile survey (no such survey exists for Brazil at this granularity).
- The inflation-tax erosion applies only to the baseline Bolsa Familia amount for one scenario-year's worth of cumulative extra inflation; it does not model a household's full multi-year exposure or any policy catch-up adjustment beyond what the scenario already assumes.
- Within-band allocation of the interest windfall is proportional to each household's own income, a documented choice, not an estimated incidence.
