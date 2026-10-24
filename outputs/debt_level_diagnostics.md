# D4 debt-level diagnostics (follow-up to the D2 gate)

**This is a diagnostic layer about the S0 baseline's debt level, not a policy-comparison scenario and not a new validated forecast.** `outputs/backtest.md`'s Tier 2 (debt/GDP levels) verdict is unchanged and remains FAIL; nothing here makes a point debt forecast more trustworthy. It answers, with ranges, the questions `outputs/debt_panel.md`'s "Implications for a lead-developer decision" raised and left unimplemented.

Draws: 300 (seed 20261020, central draw plus 299 sampled; independent stream, cannot perturb any `src.montecarlo` output). Every coefficient used here is already in `config/d3_proposed.yaml` or `config/parameters.yaml`, or is an explicitly labelled choice; nothing is re-estimated.

## Probability of breaching stated debt/GDP thresholds, S0

EC/IFI-style risk statement instead of a bare median path. `no_sfa` uses the plain debt identity; `sfa_brazil` is today's default stochastic stock-flow-adjustment term (Brazil's own 2011-2024 history, block-bootstrapped); `sfa_emerging` substitutes the cross-country emerging-panel moments for comparison.

| Horizon | P(>90%) no SFA | P(>90%) SFA (Brazil) | P(>90%) SFA (emerging) | P(>100%) SFA (Brazil) | P(>120%) SFA (Brazil) |
|---:|---:|---:|---:|---:|---:|
| 5 | 78.6% | 73.6% | 93.3% | 35.8% | 0.7% |
| 10 | 97.7% | 95.0% | 100.0% | 86.3% | 61.5% |
| 15 | 100.0% | 99.7% | 100.0% | 98.0% | 89.0% |
| 20 | 100.0% | 100.0% | 100.0% | 100.0% | 98.3% |

## Debt/GDP levels under the Brazil-own vs. emerging-panel SFA prior (p10/p50/p90, % GDP)

| Horizon | Brazil-own SFA (default) | Emerging-panel SFA (alternative) |
|---:|---|---|
| 5 | 96.7 [82.7, 109.8] | 106.1 [92.6, 117.1] |
| 10 | 127.1 [96.0, 153.2] | 147.1 [115.6, 175.9] |
| 15 | 170.9 [118.0, 220.5] | 205.7 [149.7, 258.9] |
| 20 | 235.8 [152.3, 324.8] | 287.6 [194.2, 382.7] |

## Stabilising primary balance and fiscal gap, S0 (pp of GDP)

The primary balance that would hold debt flat at each year's own implied (1+i)/(1+g), against S0's actual projected primary balance. A positive fiscal gap is the further adjustment still needed to stabilise debt at that year's own rates; this is a point-in-time, EC S1/S2-style statement, not a forecast of what adjustment will occur.

| Horizon | Stabilising primary balance (p50 [p10, p90]) | S0 actual primary balance (p50 [p10, p90]) | Fiscal gap (p50 [p10, p90]) |
|---:|---|---|---|
| 5 | +2.60 [-0.22, +4.84] | -2.39 [-2.44, -2.22] | +4.85 [+2.11, +7.16] |
| 10 | +3.60 [-0.14, +7.16] | -4.04 [-4.17, -3.68] | +7.42 [+3.74, +11.13] |
| 15 | +5.28 [+0.14, +11.02] | -5.80 [-6.14, -5.21] | +10.90 [+5.75, +16.82] |
| 20 | +7.95 [+0.65, +17.26] | -7.68 [-8.45, -6.80] | +15.63 [+8.06, +25.10] |

## S0 diagnostic variants: fiscal-reaction-function and nonlinear risk premium

These are **diagnostics about the no-reaction S0 baseline, not policy-comparison scenarios**: they are never differenced against S0 the way R/E scenarios are, and they do not appear in `outputs/runs/summary_percentiles.csv`.

`frf_emerging` recomputes S0's primary balance each year as `pb_t = pb_S0,t + rho*(debt_{t-1} - debt_2025)` using the emerging-economy panel's estimated long-run response (`config/d3_proposed.yaml fiscal_reaction.rho`). **Robustness note:** Brazil's own 2000-2024 estimated response has the opposite sign (`docs/debt_models_review.md`: -0.037, n=22) -- Brazil's history argues for *less* reaction than S0 already assumes (none), not more, so `frf_emerging` should be read as "what a typical emerging economy's historical behaviour would imply here," never as "the realistic path." `frf_brazil_robustness` applies Brazil's own estimate instead, and (being negative) widens the debt path further than plain S0, consistent with that finding.

`premium_nonlinear` replaces the linear, capped C5 sovereign-risk premium (unchanged for every other scenario) with a fiscal-fatigue-style shape for this diagnostic only: zero below the D3 cross-country historical P95 debt level (119.6% of GDP), rising with the square of the excess above it. This is an explicitly labelled modelling choice (no identified equation), not a new estimated ceiling.

| Horizon | Plain S0 | frf_emerging | frf_brazil_robustness | premium_nonlinear |
|---:|---|---|---|---|
| 5 | 98.8 | 97.6 [85.7, 106.5] | 100.2 [86.6, 110.4] | 98.8 [86.1, 108.3] |
| 10 | 130.4 | 124.0 [99.3, 145.6] | 138.9 [104.8, 168.8] | 130.5 [101.7, 157.1] |
| 15 | 177.6 | 159.6 [118.9, 199.0] | 204.0 [136.1, 270.0] | 188.7 [126.2, 330.5] |
| 20 | 245.5 | 206.7 [146.4, 270.9] | 308.8 [184.8, 441.8] | 487.8 [165.8, 1080.0] |

## Limitations

- `frf_emerging`/`frf_brazil_robustness` hold S0's own (1+i)/(1+g) path fixed and change only the primary balance; they do not re-run the GDP/multiplier chain a genuinely different fiscal stance would also affect.
- `premium_nonlinear` adds its premium directly to the effective (1+i)/(1+g) ratio rather than decomposing and reinflating i and g separately; adequate for a diagnostic, not a replacement for the C5 channel.
- `sfa_emerging` is sampled i.i.d. per year from the cross-country panel's summary moments, not block-bootstrapped from an observed sequence (none is checked into this repository): it therefore has no cross-year persistence, unlike `sfa_brazil`.
- All of the above are differences about **S0 alone**. They are never compared against the policy scenarios (R_mod, R_amb, E_mod, ...), and no existing Monte Carlo output changes.
