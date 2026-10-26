# MR1: Taylor-rule monetary-reaction-function diagnostic

## Why

An independent review argued the model has no monetary-policy reaction
function at all: the real interest rate is a fixed macro input regardless of
inflation or the output gap a scenario itself creates. A sustained,
debt-financed expansion would plausibly raise both, and a central bank
following anything like a textbook reaction function would raise the Selic
in response -- a channel this model does not have, and one the review named
explicitly as part of the omitted-channel chain behind its "probably biased
in favour of expansion" claim.

## A design decision: standalone diagnostic, not a rewiring of `run_corner`

The plan flagged this as the highest-interaction-risk item in the whole
review-response sequence, because the obvious way to add a reactive Selic
is to make `src.macro.real_interest_rate_for_year` itself state-dependent --
but that function is called by `run_corner`, which every scenario, every
diagnostic (CYC1, DC1, D4) and the published Monte Carlo itself depend on.
Instead, MR1 runs the usual `run_corner` + `external.apply_external` pass
unchanged, then **recomputes the debt path afterwards**, on top of the
already-external-adjusted corner, substituting a Taylor-rule rate for the
fixed one in an otherwise identical re-run of the debt identity
(`src.mr1_taylor_rule._rerun_debt_with_rate_rule`, line-for-line the same
loop as `external.apply_external`'s own, confirmed to reproduce it exactly
when the Taylor coefficients are zero). This gets the same substantive
answer -- what would this scenario's debt path look like under a reactive
Selic -- without touching the shared function at all.

## Specification

Taylor (1993)'s classic form: i_t = r*_t + pi_t + phi_pi*(pi_t - pi*) +
phi_y*y_gap_t. Expressed in the real-rate terms this model already keeps
separate from nominal (`src.macro.nominal_rate_from_real` does the Fisher
reinflation), this reduces to r_taylor_t = r*_t + phi_pi*(pi_t - pi*) +
phi_y*y_gap_t, where r*_t is the model's own existing
`real_interest_rate_for_year`, pi_t is `inflation_with_external_pct` (the
same for every scenario in this model, so the inflation term shifts every
scenario's rate equally), pi* is the 3.0% BCB continuous inflation target
already used elsewhere, and y_gap_t is `gdp_level_vs_s0_pct` -- zero for S0
by construction, so this term is exactly what makes a scenario's Selic path
diverge from S0's.

## Coefficients: another literature dead end, handled the same way as CYC1's

A WebSearch pass found several Brazil-specific Taylor-rule studies (an
undergraduate thesis covering Feb 2003-Jun 2025, OLS; two further studies
covering 2001-2024 and 2003-2024; a Tombini-era 2003-2016 study), all
reporting a positive, statistically significant Selic response to both the
inflation and the output gap. None of their numeric coefficients could be
read: their tables are in PDFs this environment cannot extract text from
(the same limitation documented for CYC1's Auerbach-Gorodnichenko/Pires
sources), confirmed again here by fetching one paper's own HTML repository
page directly and finding the abstract states the result only qualitatively
("smaller than advanced economies," "not constant over time"), with no
numbers. Rather than invent a Brazilian point estimate, `config/
parameters.yaml mr1_taylor_rule.discount_vs_taylor_1993` samples a discount
factor (low 0.3, central 0.6, high 1.0) on Taylor's own classic 0.5
coefficient, applied equally to phi_pi and phi_y.

## Finding

At the paper's main 10-year horizon, switching on the Taylor rule adds a
median +1.46pp of GDP to `E_mod`'s debt vs S0 (p10-p90: +0.83 to +2.39) and
+3.02pp to `E_amb`'s (p10-p90: +1.71 to +4.95), on top of the baseline
(fixed-rate) debt differential of +11.6pp and +23.2pp respectively -- a real,
non-trivial addition, roughly 13-15% larger at this horizon, driven entirely
by the Selic genuinely rising (median +0.13pp for `E_mod`, +0.26pp for
`E_amb` at this horizon) in response to the expansion's own output gap. The
effect grows with horizon: at 20 years, the median addition reaches +5.45pp
(`E_mod`) and +6.32pp (`E_amb`), with the 90th percentile reaching +10.3pp
and +12.7pp. The mirror-image result holds for the reduction scenarios
(`R_mod`, `R_amb`): a reactive Selic *cuts* with the contraction's negative
output gap, giving modest additional debt relief.

Combined with IY1's finding (the same expansion scenarios' Gini improvement
is overstated once interest income is correctly distributed), MR1 gives the
second of the two most directly quantified confirmations, in this whole
review-response sequence, of the reviewer's core claim: an endogenous
monetary reaction makes a debt-financed expansion genuinely more costly in
debt terms than the model's fixed-rate baseline reports, by a magnitude
worth citing in the paper rather than leaving as an unquantified caveat.

## Outputs

- `data/brazil/mr1_taylor_rule.csv`, `outputs/mr1_taylor_rule.md`
- Never calls `src.montecarlo.run()` or `evaluate_draw()`; cannot change any
  published Monte Carlo output (bytecode-inspection test, as for CYC1/DC1/IY1).

## Limitations

- The inflation-gap term is common to every scenario, so only the
  output-gap term differentiates a scenario's Selic path from S0's.
- No interest-rate smoothing/gradualism term, which several of the surveyed
  studies report explicitly for the BCB.
- First-order diagnostic: the Taylor-adjusted path is not re-run through the
  sovereign-risk-premium feedback channel (`src.feedback`), the same
  simplification CYC1 and DC1 already document.
- The coefficient is sampled from a documented range, not fitted to a
  Brazilian estimate (see Coefficients above).

## Tests

`tests/test_mr1_taylor_rule.py` (8 tests): the rate formula reduces to the
base rate at zero coefficients and responds positively to both gaps; the
debt re-run exactly reproduces the existing `debt_gdp_with_external` path
when the Taylor coefficients are zero (the core non-interference guarantee);
draw-0 reproducibility and the central discount; sampled coefficients stay
in range; expansions raise the rate and contractions cut it vs S0 at the
short horizon; a report-rendering smoke test; the bytecode call-check.
