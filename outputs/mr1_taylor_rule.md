# MR1: Taylor-rule monetary-reaction-function diagnostic

Built in direct response to an independent review of this project's academic paper (`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the model has no monetary reaction function: the real interest rate is a fixed input regardless of inflation or the output gap a scenario itself creates. This diagnostic recomputes each scenario's debt path under a textbook Taylor (1993) rule instead of the fixed rate, as a standalone layer on top of the already-external-adjusted corner -- it never modifies `src.macro.run_corner` or the published Monte Carlo.

Draws: 300 (seed 20261026, central draw plus 299 sampled). Sampled Taylor coefficient (phi_pi = phi_y, a discount on Taylor's classic 0.5): median 0.331 [0.188, 0.471].

## Real-rate differential and incremental debt/GDP vs S0, from switching on the Taylor rule

| Scenario | Horizon | Rate differential vs S0 (pp, p50 [p10,p90]) | Incremental debt/GDP vs S0 from the Taylor rule (pp, p50 [p10,p90]) |
|---|---:|---|---|
| E_amb | 5 | +0.262 [+0.145, +0.384] | +1.079 [+0.598, +1.601] |
| E_amb | 10 | +0.262 [+0.145, +0.384] | +3.020 [+1.708, +4.947] |
| E_amb | 15 | +0.105 [+0.058, +0.154] | +5.041 [+2.617, +8.997] |
| E_amb | 20 | -0.026 [-0.038, -0.014] | +6.316 [+3.284, +12.660] |
| E_mod | 5 | +0.131 [+0.072, +0.192] | +0.535 [+0.297, +0.794] |
| E_mod | 10 | +0.131 [+0.072, +0.192] | +1.456 [+0.825, +2.387] |
| E_mod | 15 | +0.131 [+0.072, +0.192] | +2.962 [+1.565, +5.356] |
| E_mod | 20 | +0.131 [+0.072, +0.192] | +5.448 [+2.916, +10.262] |
| R_amb | 5 | -0.262 [-0.384, -0.145] | -1.043 [-1.547, -0.578] |
| R_amb | 10 | -0.262 [-0.384, -0.145] | -2.624 [-4.310, -1.466] |
| R_amb | 15 | -0.262 [-0.384, -0.145] | -4.896 [-8.863, -2.538] |
| R_amb | 20 | -0.131 [-0.192, -0.072] | -7.349 [-14.380, -3.730] |
| R_mod | 5 | -0.131 [-0.192, -0.072] | -0.526 [-0.780, -0.292] |
| R_mod | 10 | -0.131 [-0.192, -0.072] | -1.362 [-2.239, -0.764] |
| R_mod | 15 | -0.131 [-0.192, -0.072] | -2.625 [-4.745, -1.369] |
| R_mod | 20 | -0.131 [-0.192, -0.072] | -4.492 [-8.657, -2.362] |

## Limitations

- The inflation-gap term is common to every scenario (this model's inflation input does not vary by scenario), so only the output-gap term differentiates a scenario's Selic path from S0's; see `config/parameters.yaml mr1_taylor_rule` for why the coefficients are sampled, not fitted to a Brazil-specific estimate.
- No interest-rate smoothing/gradualism term, which several of the Brazil-specific studies surveyed for this task report explicitly for the BCB.
- First-order diagnostic: the Taylor-adjusted debt path is not re-run through the sovereign-risk-premium feedback channel (`src.feedback`), the same simplification CYC1/DC1 already document.
