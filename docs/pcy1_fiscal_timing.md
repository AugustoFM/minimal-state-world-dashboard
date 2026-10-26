# PCY1: historical fiscal-timing (procyclicality) diagnostic

## Why

An independent review of this project's academic paper
(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`) argued that because the model is
forward-looking and acyclical, it cannot show whether Brazil's *past* fiscal policy
was itself procyclical, and singled out 2011-2014 as a period it suspected was
expansionary while growth was slowing and inflation was high. This module answers
that specific question directly and honestly, using only data already in the
repository.

## What it is not

Not a structural/cyclically-adjusted primary balance in the OECD/IMF sense (no
revenue-elasticity correction for the cycle is applied). Not a replacement for a
proper real-time output-gap estimate. It is a stated, reproducible proxy built to
answer one question, nothing more.

## Method

- **Data**: `data/brazil/backtest_observed.csv`, `gdp_growth_pct` and
  `primary_result_pct_gdp` (BCB SGS 5793), 2000-2024.
- **Sign fix**: SGS 5793 is a *borrowing requirement* ("negative = surplus"), the
  opposite convention from a conventional primary balance. `load_series` negates it
  immediately into `primary_balance_pct_gdp` (surplus positive), matching how the
  rest of this project (`src.macro`'s `primary_balance_gdp`) defines the balance.
  **This was a real bug caught during implementation**: the first version used the
  raw series directly, which inverted every classification (e.g. it initially
  showed 2012-2014 as procyclical-contractionary; after the fix, those years are
  countercyclical).
- **Output-gap proxy**: `gdp_growth_pct` minus its own trailing 5-year
  (`TREND_WINDOW_YEARS`) rolling mean -- a one-sided, real-time proxy chosen
  explicitly over a two-sided HP-style filter to avoid end-of-sample revision, at
  the acknowledged cost of lagging during a structural acceleration or
  deceleration.
- **Fiscal impulse**: the year-over-year change in `primary_balance_pct_gdp`,
  sign-flipped so a positive impulse is expansionary.
- **Classification**: `procyclical_expansionary` / `procyclical_contractionary` /
  `countercyclical` / `broadly_neutral` (|impulse| < 0.1pp) / `not_classified`
  (insufficient trailing data).

## Finding

On this proxy, Brazilian fiscal policy over 2000-2024 reads as predominantly
**countercyclical**, not procyclical: 2009 and 2020-2021 (the two largest growth
shocks in the sample) both show a clearly countercyclical response, and the
2011-2014 period the review singled out is **mixed, not uniformly procyclical**:
2011 classifies as procyclical-contractionary (a mild tightening into a
slightly-below-trend year), but 2012, 2013 and 2014 all classify as
countercyclical (an expansionary impulse during below-trend growth). Only 2006 and
2023 classify as procyclical-expansionary in the full sample. This partly
complicates, rather than confirms, the review's qualitative reading of 2011-2014,
and is reported as such in `outputs/fiscal_timing_diagnostic.md` rather than
adjusted to fit the review's narrative.

## Outputs

- `outputs/fiscal_timing_diagnostic.md`: the full year-by-year table and narrative.
- No interaction with `src.montecarlo` or `src.macro.run_corner`; cannot change any
  published Monte Carlo output.

## Tests

`tests/test_pcy1_fiscal_timing.py`: the sign-fix against a synthetic CSV, the
rolling-trend and impulse arithmetic by hand, the classification boundary
(including the neutral threshold's strict inequality), and a smoke test that the
report renders against the real repository data. 12 tests, all passing.
