# CYC1: state-dependent (cyclical) fiscal-multiplier diagnostic

Built in direct response to an independent review of this project's academic paper (`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the model's fiscal multipliers never vary with the business cycle. Investigating this surfaced a prior fact worth stating plainly: this model's own deterministic growth trend has no cyclical fluctuation at all on its own (year-over-year growth decelerates smoothly and monotonically, with no booms or slowdowns, under the central draw with no external shocks) -- the model is acyclical by construction at its core, exactly as the review argued, independently of whether multipliers are state-dependent. This diagnostic reintroduces genuine cyclical variation by reusing the existing stochastic external shock path (`src.external`), classifies each year as a recession or expansion regime on a real-time, trailing-mean proxy (the same method as `src.pcy1_fiscal_timing`), and rescales R\_mod and R\_amb's fiscal-multiplier-driven GDP effect by a sampled state-dependence ratio in recession years only. The ratio is sampled, not fixed, because the underlying literature is genuinely contested (see `config/parameters.yaml`'s `multiplier_state_dependence_ratio` for the full sourcing note, including a citation this project explicitly declined to use for lack of verification). This is a first-order diagnostic: it rescales the GDP effect directly but does not re-run the resulting debt consequence through the capital-accumulation/debt identity a genuinely state-dependent multiplier would also move.

Draws: 300 (seed 20261020, central draw plus 299 sampled; independent RNG streams, cannot perturb any `src.montecarlo` output). Sampled state-dependence ratio: median 1.78 [1.20, 2.37].

## GDP level vs S0 (%), fixed multiplier vs state-dependent multiplier

| Scenario | Horizon | Fixed multiplier (p50 [p10,p90]) | State-dependent (p50 [p10,p90]) | Mean recession years to horizon |
|---|---:|---|---|---:|
| R_amb | 5 | -0.804 [-0.981, -0.623] | -1.003 [-1.768, -0.712] | 0.6 |
| R_amb | 10 | -0.804 [-0.981, -0.623] | -1.082 [-1.937, -0.721] | 3.7 |
| R_amb | 15 | -0.804 [-0.981, -0.623] | -1.174 [-1.937, -0.747] | 7.4 |
| R_amb | 20 | -0.402 [-0.490, -0.312] | -0.591 [-0.968, -0.382] | 11.0 |
| R_mod | 5 | -0.402 [-0.490, -0.312] | -0.502 [-0.884, -0.356] | 0.6 |
| R_mod | 10 | -0.402 [-0.490, -0.312] | -0.541 [-0.969, -0.361] | 3.7 |
| R_mod | 15 | -0.402 [-0.490, -0.312] | -0.587 [-0.969, -0.374] | 7.4 |
| R_mod | 20 | -0.402 [-0.490, -0.312] | -0.591 [-0.968, -0.382] | 11.0 |

## Limitations

- The recession/expansion classification depends on the external shock block's own stochastic draw, which is independent of the fiscal scenario; a genuinely endogenous cycle (in which the fiscal contraction itself helps cause the slack it is then penalised or rewarded for) is not modelled.
- Only the GDP effect is rescaled; the debt consequence is the existing fixed-multiplier debt path, not re-derived from the state-dependent GDP path.
- The state-dependence ratio range (1.0-2.5, central 1.5) is a sampled, sourced-but-contested choice, not a fitted Brazilian estimate; see `config/parameters.yaml` for the full provenance, including why Pires (2014) -- cited elsewhere in this paper for Brazilian multipliers generally -- is explicitly NOT used as a source for this specific ratio.
