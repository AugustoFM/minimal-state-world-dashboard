# PCY1: historical fiscal-timing (procyclicality) diagnostic

Built in direct response to an independent review of this project's academic paper (`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the forward-looking scenario model cannot show whether past Brazilian fiscal policy was itself procyclical. This is a pure historical diagnostic: it reads only `data/brazil/backtest_observed.csv`, has no interaction with `src.montecarlo` or `src.macro.run_corner`, and cannot change any existing published Monte Carlo output.

**Method** (stated plainly; not a structural/cyclically-adjusted balance in the OECD/IMF sense): a real-time, backward-looking output-gap proxy (observed GDP growth minus its own trailing 5-year rolling mean, a one-sided choice made explicitly to avoid the end-of-sample revision a two-sided HP-style filter would introduce, at the acknowledged cost of lagging during a structural acceleration or deceleration), and a sign-flipped year-over-year change in the primary balance as the fiscal-impulse measure (impulses inside ±0.1pp are reported as broadly neutral rather than forced into a cyclical category).

## Year-by-year classification

| Year | GDP growth (%) | Trailing trend (%) | Output-gap proxy (pp) | Primary balance (% GDP, surplus positive) | Fiscal impulse (pp) | Classification |
|---:|---:|---:|---:|---:|---:|---|
| 2000 | +4.39 | n.a. | n.a. | n.a. | n.a. | not_classified |
| 2001 | +1.39 | n.a. | n.a. | n.a. | n.a. | not_classified |
| 2002 | +3.05 | n.a. | n.a. | +3.19 | n.a. | not_classified |
| 2003 | +1.14 | n.a. | n.a. | +3.24 | -0.05 | not_classified |
| 2004 | +5.76 | +3.15 | +2.61 | +3.69 | -0.45 | countercyclical |
| 2005 | +3.20 | +2.91 | +0.29 | +3.74 | -0.05 | broadly_neutral |
| 2006 | +3.96 | +3.42 | +0.54 | +3.15 | +0.59 | procyclical_expansionary |
| 2007 | +6.07 | +4.03 | +2.04 | +3.24 | -0.09 | broadly_neutral |
| 2008 | +5.09 | +4.82 | +0.28 | +3.33 | -0.09 | broadly_neutral |
| 2009 | -0.13 | +3.64 | -3.77 | +1.94 | +1.39 | countercyclical |
| 2010 | +7.53 | +4.51 | +3.02 | +2.62 | -0.68 | countercyclical |
| 2011 | +3.97 | +4.51 | -0.53 | +2.94 | -0.32 | procyclical_contractionary |
| 2012 | +1.92 | +3.68 | -1.76 | +2.18 | +0.76 | countercyclical |
| 2013 | +3.00 | +3.26 | -0.26 | +1.71 | +0.47 | countercyclical |
| 2014 | +0.50 | +3.39 | -2.88 | -0.56 | +2.27 | countercyclical |
| 2015 | -3.55 | +1.17 | -4.72 | -1.86 | +1.30 | countercyclical |
| 2016 | -3.28 | -0.28 | -3.00 | -2.48 | +0.62 | countercyclical |
| 2017 | +1.32 | -0.40 | +1.72 | -1.68 | -0.80 | countercyclical |
| 2018 | +1.78 | -0.64 | +2.43 | -1.55 | -0.13 | countercyclical |
| 2019 | +1.22 | -0.50 | +1.72 | -0.84 | -0.71 | countercyclical |
| 2020 | -3.28 | -0.45 | -2.83 | -9.24 | +8.40 | countercyclical |
| 2021 | +4.76 | +1.16 | +3.60 | +0.72 | -9.96 | countercyclical |
| 2022 | +3.02 | +1.50 | +1.52 | +1.25 | -0.53 | countercyclical |
| 2023 | +3.24 | +1.79 | +1.45 | -2.28 | +3.53 | procyclical_expansionary |
| 2024 | +3.42 | +2.23 | +1.19 | -0.40 | -1.88 | countercyclical |

## Reading the 2011-2014 period the review singled out

Year by year on this proxy -- 2011: procyclical_contractionary; 2012: countercyclical; 2013: countercyclical; 2014: countercyclical.

The period is mixed on this proxy: 1 of 4 years classify as procyclical and 3 as countercyclical, so the review's characterisation of 2011-2014 as a whole as procyclical is only partly borne out -- this proxy's more precise reading should be taken over the review's broader-brush one where they disagree, since the review did not itself compute a year-by-year series.

## All years classified procyclical

- 2006: procyclical_expansionary (output-gap proxy +0.54pp, fiscal impulse +0.59pp)
- 2011: procyclical_contractionary (output-gap proxy -0.53pp, fiscal impulse -0.32pp)
- 2023: procyclical_expansionary (output-gap proxy +1.45pp, fiscal impulse +3.53pp)

## Limitations

- This is a proxy output gap (trailing realised-growth deviation), not a structural/potential-GDP-based output gap; it will systematically lag true turning points.
- The fiscal impulse uses the headline primary balance, not one adjusted for one-off items (e.g. the 2021-2022 commodity-revenue windfalls already flagged in `data/brazil/fiscal_delivery.csv`), so part of a measured impulse may reflect revenue surprises rather than discretionary policy.
- The classification thresholds (five-year trailing window, ±0.1pp neutral band) are stated choices, not estimated or optimised; a different reasonable choice could relabel a small number of close-to-threshold years.
