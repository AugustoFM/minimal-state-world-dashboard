# D4 debt-level diagnostics

Follow-up to D2 (`outputs/backtest.md`) and the unimplemented "Implications for a
lead-developer decision" in `outputs/debt_panel.md` (D3). Status: implemented
2026-10-24, off to the side of the published Monte Carlo.

## Why

D2's Tier 2 (absolute debt/GDP levels) fails, and is expected to keep failing: the
2017-anchor out-of-sample recursion misses 2024 debt by +12.5 pp of GDP even with
the best available stock-flow-adjustment correction, because that residual is
dominated by discretionary Treasury<->BNDES loan operations and BCB result
transfers with no macro antecedent (`docs/sfa.md`). D3 (`docs/debt_models_review.md`)
and I1 (`docs/interest_rates_review.md`) proposed several source-backed ways to make
the debt-level *story* more informative without pretending to fix the point
forecast -- none of them had been wired into any `src/` file (`config/d3_proposed.yaml`
and `config/i1_proposed.yaml` are explicitly "not read by the model"). D4 wires the
D3 proposals; D2's gate verdict itself is untouched.

## What it is not

Not a new policy-comparison scenario. `src.debt_level_diagnostics` never touches
`config/scenarios.yaml`, `src/montecarlo.py`, or any published Monte Carlo column
(`outputs/runs/summary_percentiles.csv` is unaffected; its own RNG stream,
`[seed, 10]`, is one `src.montecarlo.run()` never uses). It is a diagnostic layer
about **S0 alone**: how uncertain its own debt level is, and what a few
documented alternative assumptions about Brazil's own no-reaction baseline would
imply, never a basis for ranking R/E policy scenarios against each other.

## Method

`python -m src.debt_level_diagnostics` reuses, without duplicating, the existing
Monte Carlo machinery: `src.montecarlo.load_context`, `sample_draw`/`central_draw`,
`parameters_for_draw`/`inputs_for_draw`, and `src.macro.run_corner`. Unlike
`src.montecarlo.evaluate_draw` (which discards the full annual path and keeps only
the four published horizon years), it keeps every annual value, which both of the
new S0 variants below need.

For `n_draws` draws (default 300; the central draw plus 299 sampled, far fewer than
the published 1,000 because this produces a diagnostic report, not a result
feeding any other output) it computes, for S0 only:

- **Implied annual r-g.** Backed out of the debt identity alone --
  `(1+i)/(1+g) = (debt_t + pb_t + adj_t) / debt_{t-1}` -- so no rate or growth input
  is re-derived; this is exactly D3's own decomposition applied to this model's path.
- **Stabilising primary balance and fiscal gap.** `debt_{t-1} * (r-g)`, against S0's
  actual projected primary balance; EC S1/S2-style, not a forecast of what
  adjustment will occur.
- **Probability of breaching 90/100/120% of GDP**, under the plain identity and
  under each of two SFA priors (below).
- **`frf_emerging`**: S0's primary balance recomputed as
  `pb_t = pb_S0,t + rho*(debt_{t-1} - debt_2025)`, using the D3 emerging-panel
  long-run response (`rho = 0.0334`, `config/d3_proposed.yaml fiscal_reaction`).
  Brazil's own 2000-2024 estimate (`-0.037`, opposite sign, n=22) is reported
  alongside as `frf_brazil_robustness`, explicitly as a robustness check, not an
  alternative "more realistic" path -- D3's own finding is that Brazil's history
  argues for *less* reaction than S0 already assumes (none), not more.
- **`premium_nonlinear`**: the linear, ±50pp-capped C5 sovereign-risk premium
  (unchanged for every other scenario) replaced, for this diagnostic alone, by a
  fiscal-fatigue-style shape: zero below the D3 cross-country historical P95 debt
  level (119.6% of GDP), rising with the square of the excess above it, itself
  capped at 2,000 basis points (D3: "flag paths beyond the D3 historical maximum
  as crisis indicators, not levels"). This is a labelled modelling choice, not an
  estimated ceiling -- D3 is explicit that none exists in this model's data.
- **SFA source comparison.** `sfa_brazil` reuses the existing default mechanism
  exactly (block bootstrap of Brazil's own demeaned 2011-2024 series). `sfa_emerging`
  has no raw annual cross-country series checked into this repository, so it is
  sampled i.i.d. per year from a triangular distribution anchored on
  `config/d3_proposed.yaml`'s emerging-panel low-inflation moments (p10/median/p90)
  -- a documented choice, not a block bootstrap, and with no cross-year persistence
  unlike the Brazil-own series.

Both financing-side variants (`frf_*`, `premium_nonlinear`) hold S0's own
`(1+i)/(1+g)` path fixed and change only the primary balance or the premium; they do
not re-run the GDP/multiplier chain a genuinely different fiscal stance would also
affect, and the nonlinear premium is added directly to the effective ratio rather
than decomposed into i and g separately. Both are explicitly labelled as such.

## Outputs

`outputs/debt_level_diagnostics.md` (report), `data/brazil/debt_level_diagnostics.csv`
(every draw x horizon row). `outputs/backtest.md` points to this report directly
under its Tier 2 verdict.

## Tests

`tests/test_debt_level_diagnostics.py`: the r-g identity against a hand-built debt
path; the fiscal-reaction-function recursion at rho=0 reproduces the input identity
exactly, and a positive/negative rho moves debt in the documented direction; the
nonlinear premium is exactly zero below its threshold and never exceeds its cap even
under a forced extreme path; the Brazil SFA source matches the existing bootstrap
mechanism bit-for-bit under the same seed; the emerging SFA source stays within its
stated moments; the module's RNG stream index does not collide with any of
`src.montecarlo.run()`'s nine existing streams; the central draw is reproducible and
seed-independent.
