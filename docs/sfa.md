# Stock-flow adjustment (SFA) noise in the Monte Carlo

## Why

D2's gate v2 Tier 2 (debt/GDP levels) fails: a 2017-anchor out-of-sample recursion misses 2024 debt by
+12.472 pp of GDP even with the best available correction (the 2011-2017 mean implied stock-flow
adjustment). The implied SFA (observed debt minus the one-step debt-engine prediction) is dominated by
discretionary Treasury<->BNDES loan operations (Treasury lending to BNDES 2011-2012; BNDES early
repayments and BCB result transfers 2016-2022) — decisions, not quantities any macro covariate in this
model (growth, rates, terms of trade, EMBI) predicts. A forward projection cannot know future
Treasury/BNDES operations, bond buybacks or debt recognitions, so no amount of better historical sourcing
turns this into a point-forecastable term. Trying to close Tier 2 with a better point estimate is not
possible with available data; this module instead represents the uncertainty honestly, widening debt-level
bands in the Monte Carlo instead of implying false precision.

## Mechanism

`src.external.historical_sfa_changes` reads D2's `sfa_summary.values_by_year` from
`config/d2_inputs_proposed.yaml` (observed implied SFA, 2011-2024, pp of GDP) and demeans it, so a
bootstrap draw adds historical-sized shocks, not a trend (future stock-flow operations are not assumed to
average the same sign as 2011-2024's).

`src.montecarlo.run()` block-bootstraps this series (3-year blocks, reusing `external.bootstrap_path`, the
same mechanism C6/C7 use for terms-of-trade/FX/commodity-price paths) on a dedicated RNG stream
`[seed, 9]`, drawing one path per Monte Carlo draw. That one path is applied **identically to every
scenario** in that draw — like the C6/C7 external path and the G2 corruption shock — because it represents
historical reconciliation uncertainty, not a policy choice.

The path enters `src.macro.run_corner`'s `frame["debt_adjustment_pp"]` column, the same column
privatisation and programme-specific `debt_adjustment_by_year` use, so it stacks additively with any
scenario-specific debt adjustment rather than replacing it. Sign convention: D2's SFA is positive when
observed debt grew *more* than the identity implies (debt-increasing), while `debt_adjustment_pp` is
positive when debt is *retired* (debt-reducing), so the SFA path enters with a flipped sign
(`debt_adjustment_pp -= sfa`).

Because `debt_adjustment_pp` is read once in `run_corner` and the same `frame` is passed through
`external.apply_external` and `feedback.apply_feedback`, the noise flows into all three debt series
(`debt_gdp`, `debt_gdp_with_external`, `debt_gdp_with_feedback`) consistently.

## What stays untouched

- The deterministic paths — `central_draw`/`evaluate_draw` used for the published `data/brazil/macro.csv`
  and `data/brazil/social.csv`, and `reference_paths()`'s fixed boom/neutral/bust diagnostic — never set
  `draw["sfa_debt_adjustment_by_year"]`, so they are bit-for-bit unaffected regardless of this module.
- Every other sampled stream (`[seed, 1]` through `[seed, 8]`): the SFA stream is independently seeded, so
  turning it on or off does not perturb parameter draws, the external C6/C7 path, education/firm
  coefficients, or the corruption shock.

## What this does and does not change

- It widens Monte Carlo debt-*level* uncertainty bands (`debt_gdp`, `debt_gdp_with_external`,
  `debt_gdp_with_feedback` and anything downstream of them, including the sovereign-risk-premium feedback
  channel in `src/feedback.py`, which responds to a scenario's debt deviation from its base year).
- It does **not** change D2's historical backtest point-error: `src/backtest.py`'s gate v2 is a
  non-stochastic, historical identity check and is untouched by this module. The two must not be conflated:
  this module does not make Tier 2 pass, and is not intended to.
- It is not an exact cancellation in `debt_gdp_vs_s0_pp` over multiple years. The same draw hits every
  scenario, but each scenario's own GDP effect feeds the nominal-growth denominator of the debt recursion,
  so small scenario-specific differences in how the shock compounds can appear; the shock itself does not
  favour any scenario.

## Status

On by default in `src.montecarlo.load_context()` / `run()` as of 2026-10-23 (Claude, user-requested,
following the D2 review). This default — representing it as an always-on uncertainty source rather than an
opt-in sensitivity like W3/G2 — was proposed to the user and not yet separately confirmed.
