# FX1: endogenous exchange-rate response to fiscal stress

## Why

An independent review argued the exchange rate should respond to a
scenario's own fiscal stress -- a sustained, debt-financed expansion would
plausibly widen the sovereign spread and weaken the real -- not only to the
common, policy-blind external shock path every scenario already shares.

## Why this is a modelling choice, not a fitted regression

This project already tried fitting a debt-to-spread relationship directly
for Brazil (C7 "channel B": fit 2000-2014, test 2015-2024) and found it
**not supported out of sample**. That is a direct, in-repo precedent against
repeating the same mistake for the FX analogue. FX1 instead chains two
pieces that are each already either verified or theory-grounded, never a
new fitted elasticity:

1. The model's own already-verified debt-to-risk-premium parameter
   (`long_run_feedback.sovereign_risk_premium`, Baldacci & Kumar 2010),
   reused via `src.feedback.sovereign_risk_premium_path`, not re-derived.
2. A sampled, not fitted, spread-to-depreciation elasticity anchored on
   uncovered interest parity (a standard theoretical relationship): a
   sustained risk-premium widening of X pp should correspond to roughly X%
   of expected annual depreciation under simple arbitrage-free UIP. The
   upper bound is informed only qualitatively by a BIS working paper
   (Banerjee, Mehrotra & Zampolli 2023) finding the exchange-rate-to-fiscal-
   stress channel "much stronger in emerging markets than in advanced
   economies" -- its own regression tables could not be read in this
   environment, the same PDF-extraction limitation already documented for
   CYC1's and MR1's literature sources. See `config/parameters.yaml
   fx1_endogenous_fx` for the full sourcing note.

## A structural finding that reshaped this module's design

The first implementation routed the extra depreciation through the
existing exchange-rate-pass-through-to-inflation channel and re-ran the
debt identity exactly as `external.apply_external` does, substituting the
higher inflation for the baseline. **That produced an exactly-zero debt/GDP
effect, to floating-point precision, at every draw and horizon.** This is
not a bug: in this model's Fisher-consistent debt identity, the nominal
interest rate and nominal GDP growth both reprice by the same inflation
factor (`nominal_rate_from_real` on one side, the price-level compounding
on the other), so a pure inflation shock with no real-economy effect cannot
move the debt/GDP ratio at all, by construction. This is the same kind of
independently-confirming structural fact CYC1 found for the model's
acyclical growth core, and worth recording for the same reason: it is a
genuine property of this model, not an incidental result of this one
diagnostic.

FX1 therefore routes its depreciation through the one channel in this
model that genuinely is **not** Fisher-neutral: DC1's FX-linked debt
tranche, a real foreign-currency liability that revalues directly in BRL
terms when the real weakens, independent of domestic inflation. FX1 reuses
DC1's own `fx_linked_share_pct_of_dpf` parameter rather than introducing a
second debt-composition assumption. The (confirmed-inert) extra-inflation
figure is still computed and reported (`extra_inflation_pp_inert`), so the
zero-by-construction finding stays visible in the data rather than being
quietly dropped once the design changed.

## Method

For each scenario and year: the baseline (no-FX1) debt deviation from the
base year feeds `src.feedback.sovereign_risk_premium_path` (reused
directly, same 50pp out-of-sample cap already used there) to get a premium
in pp; the sampled elasticity converts that into an extra depreciation
(%); and the sampled FX-linked share of that scenario's baseline debt/GDP
is revalued by it -- exactly DC1's own revaluation formula, applied to a
stress-induced depreciation path instead of the common bootstrapped one.
First-order: driven by the baseline debt path, not re-derived from the
FX1-adjusted one, to avoid a new compounding feedback loop.

## Finding

The effect is small in absolute terms, as expected given the FX-linked
share itself is only ~4% of debt: at the paper's main 10-year horizon,
switching FX1 on adds a median +0.18pp of GDP to `E_mod`'s debt and
+0.21pp to `E_amb`'s (300 draws, seed 20261026), growing to +0.42pp and
+0.47pp respectively by 20 years (p90 up to +0.83pp/+0.93pp). This is
consistent with -- and quantitatively reinforces -- DC1's own finding that
Brazil's FX-linked debt channel is a genuinely second-order effect at the
paper's main horizon, even once the depreciation driving it is itself made
to respond to fiscal stress rather than drawn from the unconditional
historical bootstrap. Unlike IY1 and MR1, FX1 does not materially complicate
the paper's existing "second order" framing for this specific channel;
read alongside DC1 (whose own finding does complicate that framing at the
20-year horizon via the common external-shock path), the two diagnostics
together show the FX-linked channel stays small specifically because the
underlying FX-linked share is small, not because fiscal stress fails to
move the exchange rate.

## Outputs

- `data/brazil/fx1_endogenous_fx.csv`, `outputs/fx1_endogenous_fx.md`
- Never calls `src.montecarlo.run()` or `evaluate_draw()`; cannot change any
  published Monte Carlo output (bytecode-inspection test, as for CYC1/DC1/IY1/MR1).

## Limitations

- Debt/GDP effect runs only through the FX-linked tranche; the
  inflation-pass-through route is reported but, by construction, inert for
  debt/GDP in this model.
- Elasticity is sampled from a UIP-anchored range, not fitted.
- Models a smooth, contemporaneous level relationship, not a discrete
  currency-crisis or overshooting event.

## Tests

`tests/test_fx1_endogenous_fx.py` (7 tests): the pass-through formula
matches a hand computation (reported but confirmed inert); draw-0
reproducibility and the three central config values (elasticity, premium,
FX share); sampled parameters stay in their configured bounds; the
incremental debt matches the exact revaluation formula; depreciation and
incremental debt are non-negative for every scenario under the central
draw; a report-rendering smoke test; the bytecode call-check.
