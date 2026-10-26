# CYC1: state-dependent (cyclical) fiscal-multiplier diagnostic

## Why

An independent review argued the model's fiscal multipliers never vary with the
business cycle, despite the paper citing state-dependence evidence
(Auerbach & Gorodnichenko 2012; Pires 2014) it does not use.

## A prior finding, before the diagnostic itself

Investigating this surfaced a more basic fact worth stating on its own: this
model's deterministic growth trend has **no cyclical fluctuation whatsoever**
without the external shock block -- under the central draw, S0's year-over-year
real GDP growth decelerates smoothly and monotonically (1.18% in 2026 down to
0.94% by 2035, with no bumps). The model's core is acyclical by construction,
independently of whether multipliers are state-dependent -- confirming the
review's underlying diagnosis directly, before any multiplier work was done.

## Literature verification (an honest dead end, reported rather than hidden)

Attempting to source a precise recession/expansion multiplier ratio from the
two papers already cited in the paper's bibliography failed on both counts:

- Auerbach & Gorodnichenko (2012): verified from the paper's own NBER abstract
  that it finds multipliers "considerably more effective in recessions than in
  expansions," but the paper's own numeric tables could not be machine-read in
  this environment (PDF extraction failed), so no specific point ratio from
  this paper is used.
- Pires (2014): a secondary source suggested this paper's positive finding is
  about a *volatility* regime split, not a business-cycle-phase split, which
  would mean it does **not** actually support a recession/expansion multiplier
  ratio for Brazil. This could not be confirmed or refuted (PDF extraction
  failed here too). Rather than risk citing a paper for a finding it may not
  support, **Pires (2014) is explicitly not used as a source for this specific
  ratio** -- it remains validly cited elsewhere in this paper for Brazilian
  multiplier estimation generally.

Given this, `config/parameters.yaml`'s new `multiplier_state_dependence_ratio`
is sampled (low 1.0, central 1.5, high 2.5), not a fixed point estimate,
reflecting genuine literature disagreement (low = Ramey 2019 / Ramey & Zubairy
2018's sceptical reading that the asymmetry is not robust; high = a
conservative reading of Auerbach-Gorodnichenko's qualitative finding).

## Method

Since the model's core has no cyclicality, CYC1 reuses the existing stochastic
external shock path (`src.external.bootstrap_path`) to reintroduce genuine
year-to-year growth variation, classifies each year as a recession or
expansion regime using the same real-time, trailing-mean proxy as PCY1
(`src.pcy1_fiscal_timing.classify_recession_years`, reused directly), and
rescales R_mod and R_amb's fiscal-multiplier-driven GDP effect
(`gdp_level_vs_s0_pct`, which *is* the multiplier's effect, since S0's own gap
is zero by construction) by the sampled ratio in recession years only.

This is a first-order diagnostic: it rescales the GDP effect directly but does
not re-run the resulting debt consequence through the capital-accumulation/
debt identity (the same simplification D4's fiscal-reaction-function
diagnostics already make and document).

## Finding

At the 10-year horizon, R_amb's median GDP cost moves from -0.80% (fixed
multiplier) to -1.08% (state-dependent), roughly a 35% larger cost once
cyclicality is reintroduced -- a real, meaningful difference, consistent with
the review's underlying intuition that ignoring state-dependence likely
understates the true cost of contraction, even though the precise magnitude of
that understatement rests on a contested, sampled ratio rather than a single
settled estimate.

## Outputs

- `data/brazil/cyc1_state_dependent_multiplier.csv`, `outputs/cyc1_state_dependent_multiplier.md`
- Never calls `src.montecarlo.run()` or `evaluate_draw()`; cannot change any
  published Monte Carlo output (`tests/test_cyc1_state_dependent_multiplier.py`
  checks this directly by inspecting the module's bytecode).

## Tests

`tests/test_cyc1_state_dependent_multiplier.py`: the recession classifier on a
hand-built series, draw-0 reproducibility and that it uses the configured
central ratio, that sampled ratios stay in range, that the state-dependent
effect differs from the fixed one *only* by the exact sampled ratio (and only
in recession years), a report-rendering smoke test, and a bytecode check that
the module never calls `evaluate_draw`. 6 tests, all passing.
