# IY1: interest-income and inflation-tax distribution diagnostic

## Why

An independent review argued the household microsimulation omits two
regressive channels a sustained, debt-financed expansion would plausibly
trigger: (1) higher government interest expense accrues disproportionately
to bondholders, concentrated at the top of the income distribution, and
(2) an inflation tax falls hardest on poor households' largely non-indexed
transfers. The reviewer's conclusion was that the model's finding --
"expansions reduce the Gini coefficient" -- is "probably biased in favour of
expansion" because it omits exactly these channels.

## A scoping decision: which scenarios to test

The reviewer's claim is specifically about the paper's **debt-financed
expansion** scenarios (`E_mod`, `E_amb`), not the fiscal-reduction scenarios
(`R_mod`, `R_amb`) that CYC1 and DC1 test. This was confirmed by first
building and running the diagnostic against `R_mod`/`R_amb` by mistake
(matching CYC1/DC1's house convention without checking it against this
specific task's question) and finding the direction came out backwards --
contractions *reduce* debt and therefore interest expense, so IY1's channel
correctly *reduced* Gini there, which does not engage with what the reviewer
actually argued. Switching to `E_mod`/`E_amb` is the right test.

## A real bug found and fixed during implementation

The first version of the within-band allocation formula
(`src.micro._allocate_by_income_band`) multiplied the per-household share by
the survey weight *twice* -- once implicitly through the band's weighted
total (the denominator, correctly) and again by using that same
weight-inflated numerator directly as a per-household amount. This made the
windfall roughly two orders of magnitude too large per household, enough to
drive thousands of households' income to zero (clipped by the existing
`np.maximum(0.0, ...)` floor) and send the Gini to ~0.99 and the poverty
headcount to ~99% on a diagnostic smoke test -- an obviously wrong result
that caught the bug immediately. Fixed by removing the extra weight factor
from the numerator, verified by a new test
(`test_allocate_by_income_band_conserves_the_pool_and_is_proportional_to_income`)
that checks the allocation, re-weighted and summed, reproduces the input
pool exactly.

## Method

Both channels are wired as off-by-default, optional arguments to
`src.micro.simulate_household_incomes` (defaults reproduce the exact prior
behaviour byte-for-byte):

- **Capital-income windfall.** Government interest expense (% GDP) is
  derived from the debt identity's own numbers: previous year's
  `debt_gdp_with_external` times that year's nominal interest rate (the
  standard rate-times-stock definition of interest paid, not the debt
  identity's growth-netted term). The difference between a scenario and S0
  is converted to monthly BRL and allocated across the PNAD household
  population: the top 1% of the per-capita income distribution (ranked
  exactly as the model's own `survey_top_1_income_share_pct` already is)
  receives the same share of it that Receita Federal's declared
  capital/financial income data says the top 1% of tax declarants hold; the
  next 9% and bottom 90% likewise. Within each band, the allocation is
  proportional to each household's own income (a documented choice).
- **Inflation-tax erosion.** A scenario-year's cumulative *extra*
  (above-baseline) inflation, from `src.external`'s own
  `external_extra_inflation_pp` path, is applied as a proportional reduction
  of each household's baseline Bolsa Familia amount (not BPC or pensions,
  which are minimum-wage-linked and annually re-indexed; not the
  policy-driven delta, which is unaffected).

`src/iy1_interest_income_distribution.py` runs both channels together as a
standalone Monte Carlo diagnostic against `E_mod`/`E_amb`, comparing Gini and
poverty with and without IY1 switched on. It never calls
`src.montecarlo.run()`/`evaluate_draw()`.

## Finding

At the paper's main 10-year horizon, switching IY1 on moves the Gini by
+0.76 points (median) for `E_mod` and +1.31 points for `E_amb`, relative to
the published (IY1-off) figures -- small in absolute terms, but entirely in
the direction the reviewer predicted, and **directly confirming, not just
plausibly suggesting, that the "expansion reduces the Gini" finding
overstates the distributional improvement** once this channel is counted.
The effect grows with horizon: at 20 years, the median Gini shift reaches
+3.13 points (`E_mod`) and +5.02 points (`E_amb`), with the 90th percentile
reaching +4.56 and +7.19 points respectively (300 draws, seed 20261026).
Poverty headcount (R$218 line) barely moves (well under 1pp throughout),
confirming the capital-income windfall -- not the inflation-tax erosion of
Bolsa Familia -- is the dominant channel here, since poverty is measured at
the bottom of the distribution and the windfall is concentrated at the top.

This is the most direct, quantified confirmation of the reviewer's core
inequality-bias claim produced anywhere in this review-response sequence
(RV0-IY1): PCY1 and CYC1 both independently confirmed parts of the
reviewer's cyclicality critique, but IY1 is the first diagnostic to show,
with real magnitudes, that the specific headline finding the reviewer
challenged does move in the direction they argued, by an amount worth
reporting in the paper's Discussion rather than leaving as an unquantified
caveat.

## Outputs

- `data/brazil/iy1_interest_income_distribution.csv`, `outputs/iy1_interest_income_distribution.md`
- Never calls `src.montecarlo.run()` or `evaluate_draw()`; cannot change any
  published Monte Carlo output (checked by the same bytecode-inspection test
  used for CYC1/DC1).

## Limitations

- The capital-income concentration curve comes from Receita Federal tax
  declarants, not the PNAD survey population; declarants already skew
  higher-income, so this is a reasonable but not survey-consistent proxy.
- No Brazilian survey of bond-holding by income decile exists at this
  granularity; both the derivation of interest expense and the within-band
  incidence rule are stylised, documented choices, not fitted estimates.
- The inflation-tax erosion is a one-scenario-year assumption (full,
  within-year pass-through to Bolsa Familia's real value), not a
  multi-year accumulation or an estimated adjustment-lag rate.

## Tests

`tests/test_micro.py` (new, 7 tests): the two channels default off and are
byte-identical to prior behaviour when unset; a missing share argument
raises; the weighted-percentile-rank helper matches a hand computation; the
band-allocation helper conserves the input pool exactly and allocates
proportional to income, not weight (the test that would have caught the bug
above); a larger synthetic-population integration test confirms the
windfall is pool-conserving and concentrated at the richest household; the
inflation erosion shrinks only the Bolsa Familia-bearing household by
exactly the given fraction.

`tests/test_iy1_interest_income_distribution.py` (new, 6 tests): the
capital-income shares are well-formed; the cumulative extra-inflation helper
matches a hand computation; draw-0 reproducibility; a direction test (where
interest expense genuinely rises, IY1 must raise the Gini, not lower it);
a report-rendering smoke test; the bytecode call-check.
