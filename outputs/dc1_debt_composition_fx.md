# DC1: FX-linked debt-stock revaluation diagnostic

Built in direct response to an independent review of this project's academic paper (`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the debt stock should be split by currency, holder and maturity so a depreciation directly revalues foreign-currency-linked debt. A full multi-instrument decomposition was scoped down: Brazil's FX-linked share of federal debt is small and stable (3.7-4.4% of the DPF, Secretaria do Tesouro Nacional, already cited in the paper as `tesourormd2026`), and a genuine multi-decade historical composition series could not be machine-read in this environment (the Treasury publishes it only inside monthly PDF tables). This diagnostic instead revalues only that FX-linked tranche directly by the same bootstrapped cumulative BRL/USD path `src.external` already draws per Monte Carlo draw, additive to the existing inflation-pass-through effect, not a replacement for it.

Draws: 300 (seed 20261026, central draw plus 299 sampled; independent RNG streams, cannot perturb any `src.montecarlo` output). Sampled FX-linked share: median 4.06% [3.79%, 4.32%].

## Debt/GDP (%): external baseline vs with direct FX-linked revaluation

| Scenario | Horizon | Baseline (p50 [p10,p90]) | Additional pp from FX revaluation (p50 [p10,p90]) | With FX revaluation (p50 [p10,p90]) |
|---|---:|---|---|---|
| R_amb | 5 | 93.39 [79.32, 102.25] | +0.989 [-0.611, +3.794] | 94.25 [81.69, 104.14] |
| R_amb | 10 | 107.27 [78.05, 130.72] | +2.631 [-0.388, +8.460] | 110.36 [81.43, 133.69] |
| R_amb | 15 | 123.48 [76.23, 166.08] | +5.145 [+0.344, +15.829] | 131.19 [82.39, 173.98] |
| R_amb | 20 | 146.77 [78.03, 217.65] | +9.789 [+0.944, +28.456] | 162.41 [87.58, 228.46] |
| R_mod | 5 | 96.16 [82.06, 105.12] | +1.018 [-0.629, +3.919] | 97.01 [84.50, 107.00] |
| R_mod | 10 | 118.88 [88.62, 143.04] | +2.919 [-0.433, +9.441] | 122.23 [92.47, 146.17] |
| R_mod | 15 | 150.80 [99.64, 196.03] | +6.366 [+0.415, +18.981] | 159.88 [107.32, 206.68] |
| R_mod | 20 | 195.39 [116.62, 274.40] | +13.463 [+1.376, +37.535] | 218.21 [131.38, 290.33] |
| S0 | 5 | 98.91 [84.79, 107.99] | +1.046 [-0.647, +4.044] | 99.76 [87.32, 109.84] |
| S0 | 10 | 130.48 [99.18, 155.36] | +3.205 [-0.476, +10.393] | 134.39 [103.51, 158.85] |
| S0 | 15 | 177.84 [123.06, 225.98] | +7.497 [+0.487, +22.714] | 188.91 [132.05, 239.11] |
| S0 | 20 | 246.46 [157.87, 333.34] | +16.928 [+1.836, +47.501] | 274.50 [178.51, 354.17] |

## Limitations

- `data/brazil/debt_composition.csv` holds two verified point-in-time Treasury snapshots and the PAF 2026 target bands, not a historical time series; the FX-linked share is therefore held constant over the projection horizon rather than estimated as a trend.
- Only the FX-linked tranche is revalued; the Selic-linked, inflation-linked and fixed-rate shares (which make up the other ~96% of the DPF) are not modelled separately and remain inside the single blended interest rate the debt identity already uses.
- The revaluation is a direct stock effect only; it does not re-run the resulting debt change through the sovereign-risk-premium feedback channel (the same first-order simplification CYC1 and D4 already make and document).
