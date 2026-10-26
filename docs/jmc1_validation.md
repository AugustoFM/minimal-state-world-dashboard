# JMC1 validation: does the joint rate/FX mechanism improve on 2000-2024 history?

Narrowed gate (see `src/backtest_jmc1.py` module docstring for why): only MR1 (the Taylor-rule rate mechanism) and DC1 (FX-linked debt revaluation using the *actual* observed BRL/USD path) have a genuine historical analogue. CYC1, FX1's extra depreciation layer, and IY1 are scenario-vs-S0 concepts with no counterfactual in a single realized history, and are not tested here.

Fixed real-rate assumption: 5.050% (the model's own `effective_real_interest_rate.central` -- already the historical median real rate, so this is a tough benchmark, not a strawman). Taylor coefficients: phi_pi = phi_y = 0.300. FX-linked share: 4.00% (DC1's own config central).

## Debt/GDP reconstruction error vs observed, 2006-2024 (pp)

| Mechanism | Mean error | MAE | RMSE | n |
|---|---:|---:|---:|---:|
| fixed | -5.826 | 9.372 | 10.168 | 19 |
| taylor_only | -1.770 | 9.470 | 11.211 | 19 |
| joint | -1.074 | 9.927 | 11.976 | 19 |

## Debt/GDP one-step error (re-anchored on observed lagged debt each year, pp) -- the fairer test, mirroring `src.backtest.debt_one_step`'s own precedent for isolating rate-setting fit from cumulative stock-flow-adjustment noise

| Mechanism | Mean error | MAE | RMSE | n |
|---|---:|---:|---:|---:|
| fixed | +0.871 | 3.080 | 3.685 | 18 |
| taylor_only | +1.400 | 3.387 | 4.253 | 18 |
| joint | +1.530 | 3.383 | 4.299 | 18 |

## Nominal-Selic reconstruction error vs observed, years with both inflation and Selic (pp)

| Mechanism | Mean error | MAE | RMSE | n |
|---|---:|---:|---:|---:|
| fixed | -0.419 | 3.124 | 3.869 | 25 |
| taylor_only | +1.172 | 2.784 | 3.352 | 21 |

## Verdict

Cumulative debt/GDP RMSE (dominated by SFA noise, reported for transparency, not the gate): fixed 10.168pp vs taylor_only 11.211pp vs joint 11.976pp.

**One-step debt/GDP RMSE (the actual gate)**: fixed 3.685pp vs taylor_only 4.253pp vs joint 4.299pp -- **FAIL**: the joint (MR1+DC1) mechanism's one-step reconstruction error is larger than the published model's fixed-rate mechanism's own error on the same 2006-2024 window.

**Selic RMSE**: fixed 3.869pp vs taylor 3.352pp -- **PASS**: the Taylor rule's *own* implied rate path is closer to the actual observed Selic than the fixed-rate assumption, over 2000-2024.

If the one-step debt/GDP verdict and the Selic verdict disagree, that is itself the finding: it would mean MR1 genuinely improves on describing *Selic-setting behaviour* without that translating into a better *debt-level* reconstruction once debt_step's own dynamics (and whatever stock-flow noise survives even the one-step re-anchoring) are involved -- reported plainly either way, not reconciled into a single number.

## Refined test: `src.backtest`'s own SIDRA nominal-GDP inputs (2010-2024)

Same comparison (a *generated*, not oracle-fed, rate), but using the exact data behind `outputs/backtest.md`'s `debt_engine`/`debt_engine_one_step` rows (actual SIDRA current-price GDP, not the CPI/real-growth Fisher approximation used above) -- a fairer, more rigorous version of the same question, and directly comparable in level to those rows.

| Mechanism | Cumulative RMSE (pp) | One-step RMSE (pp) |
|---|---:|---:|
| fixed | 7.464 | 3.234 |
| taylor_only | 9.809 | 3.880 |
| *oracle (observed implicit rate, `outputs/backtest.md`'s own rows)* | *9.322* | *2.390* |

**FAIL** on this refined one-step test too: 3.234pp (fixed) vs 3.880pp (taylor_only) -- the fixed-rate mechanism fits better, confirming the CPI-based result above with the project's own more accurate historical dataset, not contradicting it. Both generated-rate mechanisms remain well short of the oracle (2.390pp one-step), which uses the *true* realized implicit rate.

**Why Selic-tracking and debt-fit disagree (the likely mechanism, not just a coincidence of this sample)**: `effective_real_interest_rate` is calibrated to approximate the government's *effective, blended* rate on its whole diversified debt stock (a mix of Selic-linked, inflation-linked and fixed-rate instruments, per DC1's own debt-composition note), not the Selic policy rate itself. MR1's Taylor rule was built, and tested above, as a Selic-tracking mechanism -- it is a better description of Selic-setting behaviour, but using it as a direct stand-in for the *effective rate on the whole debt stock* conflates two different rates. That conflation, not a flaw in Taylor's rule per se, is the more likely reason it does not help here.

## Coverage: how often does the published model's own uncertainty range contain the truth?

A wider literature benchmark of this project's own methodology (`reports/Debt model methodology and journal fit.md`) found that the ESM's own operational fan-chart validation (Brief 05/2025) reports a calibrated coverage/error-rate statistic rather than a bare pass/fail verdict on a single central reconstruction. The same idea applied here, at no new estimation cost: using the model's own already-published `effective_real_interest_rate` low (-2.042%) and high (7.197%) corners (not a new estimate) to bound the one-step SIDRA-based reconstruction instead of a single central-case line.

**Coverage rate: 64.3% (9/14 years)** -- the actual observed debt/GDP fell inside the model's own low/high-rate band in 9 of 14 one-step-reconstructed years, mean band width 6.02pp, missed in 2011, 2012, 2014, 2015, 2022.

## Limitations

- Nominal GDP growth is approximated as `(1+real growth)(1+inflation)-1` (a Fisher compounding of the observed real-growth and CPI series), not the SIDRA nominal-GDP level series `src.backtest`'s own `debt_engine` test uses -- any error this introduces is common to every mechanism compared here, so it does not bias the *relative* comparison this report exists to make, but it does mean these RMSEs are not directly comparable in level to `outputs/backtest.md`'s own `debt_engine`/`debt_engine_one_step` rows (which use the SIDRA series and, for `debt_engine`, an *observed*, not generated, implicit interest rate).
- The Taylor rule's output-gap term uses PCY1's own real-time trailing-mean proxy, not a structural output gap; see `src.pcy1_fiscal_timing`'s own stated limitations.
- The `fixed` mechanism's own benchmark is not naive: `effective_real_interest_rate.central` is calibrated as the median of the same historical real-rate series being tested against, so beating it on debt/GDP RMSE is a genuine test of whether year-to-year reactivity adds anything, not a test against an arbitrary flat guess.
