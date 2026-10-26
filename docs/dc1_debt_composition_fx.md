# DC1: FX-linked debt-stock revaluation diagnostic

## Why

An independent review argued the model's single undifferentiated debt stock
should be split by currency, holder and maturity, since a depreciation would
directly revalue foreign-currency-linked debt upward in domestic-currency
terms -- a channel the debt identity does not have (the exchange rate
currently only reaches debt indirectly, through inflation pass-through).

## Scope decision, and why it was scaled down

A full multi-instrument debt-composition model was not built, for two
reasons surfaced while starting this task:

1. **The channel is genuinely small for Brazil.** The Treasury's own
   published figure -- already fetched, verified and cited in the paper's
   RV0 limitations paragraph (`tesourormd2026`) -- puts the FX-linked share
   of the federal public debt (DPF) at a stable 3.7-4.4%, far below a
   typical dollar-indebted emerging market.
2. **A genuine historical composition series could not be obtained.** The
   Treasury's Relatorio Mensal da Divida publishes the full indexer
   breakdown only inside monthly PDF tables, which this environment cannot
   extract text from (the same PDF-extraction limitation already hit and
   documented for CYC1's literature sources). A WebSearch pass surfaced only
   a finance blog and a 2007 working-paper excerpt as candidate sources for
   a longer series, neither independently verifiable here, so neither is
   used. `data/brazil/debt_composition.csv` therefore holds only the two
   verified Treasury snapshots already cited in the paper (end-2025,
   August 2026) and the PAF 2026 target bands -- a point-in-time record, not
   a time series -- and leaves the inflation-linked/fixed-rate split blank
   at the snapshot dates where the paper's own source gives only a range,
   rather than inventing a precise split that was never published.

## Method

`src/dc1_debt_composition_fx.py` layers one specific, data-supported channel
on top of the existing external-shock machinery: it revalues only the
FX-linked share of debt/GDP directly by the same bootstrapped cumulative
BRL/USD path `src.external` already draws per Monte Carlo draw (reusing
`external.historical_changes`/`bootstrap_path`/`gdp_and_inflation_effects`/
`apply_external`, the same pattern as `src.cyc1_state_dependent_multiplier`).
For each draw, the cumulative depreciation fraction vs the base year is
`exp(cumsum(fx_change_pct) / 100) - 1` (these are log changes, so this is
exact compounding), and the additional debt/GDP from revaluation is
`fx_share * debt_gdp_with_external * cumulative_depreciation_frac`, added to
`debt_gdp_with_external` to produce `debt_gdp_with_fx_revaluation`. The
FX-linked share itself is sampled per draw (uniform 3.7-4.4%, central draw
4.0%), reflecting the Treasury's own published range rather than a fitted
distribution. This is additive to, not a duplicate of, the existing
inflation-pass-through effect: one is a stock revaluation, the other an
income/inflation effect.

This is a first-order diagnostic, matching CYC1 and D4's own documented
simplification: it does not re-run the revalued debt path through the
sovereign-risk-premium feedback channel.

## Finding

At the 5- and 10-year horizons, the effect is indeed small, as the "second
order" framing in the paper's RV0 paragraph expects: median additional
debt/GDP from FX revaluation is +1.0pp at 5y and +2.6 to +3.2pp at 10y across
S0/R_mod/R_amb (300 draws, seed 20261026). **But this complicates rather than
simply confirms that framing at longer horizons**: by 15-20 years, the median
effect grows to +5 to +17pp of GDP, and the p90 tail reaches +20 to +47pp,
because the FX-linked tranche is revalued by the *cumulative* bootstrapped
BRL/USD path, and Brazil's own 2000-2024 history (used as the bootstrap's
only source of variation, consistent with every other external-shock
diagnostic in this project) includes BRL/USD moving by well over 100% across
some 20-year windows. A 4% share of debt revalued by that much cumulative
depreciation is no longer negligible in absolute terms, even though it
remains modest relative to the already very wide uncertainty band on total
debt/GDP itself at that horizon (which spans well over 200pp at 20y). The
honest statement is therefore horizon-dependent: the FX-linked revaluation
channel is correctly treated as second-order at the paper's main 10-year
horizon, but should not be described as negligible at the 20-year horizon
without qualification.

## Outputs

- `data/brazil/debt_composition.csv` (the two Treasury snapshots + PAF bands)
- `data/brazil/dc1_debt_composition_fx.csv`, `outputs/dc1_debt_composition_fx.md`
- Never calls `src.montecarlo.run()` or `evaluate_draw()`; cannot change any
  published Monte Carlo output (`tests/test_dc1_debt_composition_fx.py`
  checks this directly by inspecting the module's bytecode, the same method
  used for CYC1).

## Tests

`tests/test_dc1_debt_composition_fx.py`: the cumulative-depreciation formula
against a hand-computed toy log-change series, draw-0 reproducibility and
that it uses the configured central FX share, that sampled shares stay in
range, that the additional pp is exactly `share * baseline * depreciation`
(not some other formula) on real draw output, a report-rendering smoke test,
and a bytecode check that the module never calls `evaluate_draw`.
