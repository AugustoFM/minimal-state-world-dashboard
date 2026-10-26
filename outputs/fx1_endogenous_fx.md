# FX1: endogenous exchange-rate response to fiscal stress

Built in direct response to an independent review of this project's academic paper (`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the exchange rate should respond to a scenario's own fiscal stress, not only to the common, policy-blind external shock path. Rather than fit a new debt-to-FX regression -- this project already tried the closest analogue (C7 channel B, debt-to-spread) and found it not supported out of sample -- FX1 chains the model's own already-verified debt-to-risk-premium parameter to a sampled, UIP-anchored (not fitted) spread-to-depreciation elasticity.

**A structural finding along the way**: routing this extra depreciation through the existing inflation-pass-through channel and re-running the debt identity produced an *exactly zero* debt/GDP effect at every draw -- a genuine, not a bugged, result: this model's Fisher-consistent debt identity reprices the nominal rate and nominal GDP growth by the same inflation factor, so a pure inflation shock with no real-economy effect cannot move the debt/GDP ratio at all. FX1 therefore routes its depreciation through DC1's FX-linked debt tranche instead -- a genuine foreign-currency liability that is not Fisher-neutral -- reusing DC1's own `fx_linked_share_pct_of_dpf` rather than a new assumption.

Draws: 300 (seed 20261026, central draw plus 299 sampled). Sampled elasticity (% extra depreciation per 1pp of sovereign risk premium): median 1.67 [0.72, 2.73].

## Extra depreciation and incremental debt/GDP from switching FX1 on

| Scenario | Horizon | Extra depreciation (%, p50 [p10,p90]) | Incremental debt/GDP from FX1 (pp, p50 [p10,p90]) |
|---|---:|---|---|
| E_amb | 5 | +1.214 [+0.375, +2.639] | +0.0506 [+0.0141, +0.1149] |
| E_amb | 10 | +3.226 [+1.318, +6.087] | +0.2046 [+0.0792, +0.3965] |
| E_amb | 15 | +3.492 [+1.524, +6.550] | +0.3273 [+0.1254, +0.6080] |
| E_amb | 20 | +3.492 [+1.524, +6.550] | +0.4739 [+0.1773, +0.9272] |
| E_mod | 5 | +1.084 [+0.305, +2.427] | +0.0438 [+0.0124, +0.1028] |
| E_mod | 10 | +3.003 [+1.169, +5.896] | +0.1748 [+0.0600, +0.3622] |
| E_mod | 15 | +3.434 [+1.524, +6.531] | +0.2915 [+0.1101, +0.5485] |
| E_mod | 20 | +3.492 [+1.524, +6.550] | +0.4242 [+0.1570, +0.8304] |
| R_amb | 5 | +0.713 [+0.041, +1.801] | +0.0264 [+0.0013, +0.0719] |
| R_amb | 10 | +1.501 [-0.017, +4.154] | +0.0642 [-0.0006, +0.2087] |
| R_amb | 15 | +2.118 [-0.078, +5.439] | +0.1109 [-0.0024, +0.3345] |
| R_amb | 20 | +2.627 [-0.061, +5.791] | +0.1594 [-0.0020, +0.4176] |
| R_mod | 5 | +0.838 [+0.135, +2.006] | +0.0316 [+0.0044, +0.0827] |
| R_mod | 10 | +2.146 [+0.516, +5.133] | +0.1021 [+0.0181, +0.2728] |
| R_mod | 15 | +2.908 [+0.964, +5.904] | +0.1850 [+0.0462, +0.4094] |
| R_mod | 20 | +3.226 [+1.299, +6.207] | +0.2601 [+0.0863, +0.5565] |

## Limitations

- The spread-to-depreciation elasticity is sampled from a UIP-anchored, literature-informed range, not fitted to a Brazilian or EM-panel estimate (see `config/parameters.yaml fx1_endogenous_fx` for the full sourcing note and why a new fitted regression was not attempted, given C7 channel B's own out-of-sample failure).
- The debt/GDP effect runs only through the FX-linked debt tranche (DC1's channel): the inflation-pass-through route is reported (`extra_inflation_pp_inert`) but is, by construction, inert for debt/GDP in this model's Fisher-consistent debt identity.
- The premium driving the extra depreciation is computed from the baseline (no-FX1) debt path, not re-derived each year from the FX1-adjusted path, to avoid a new compounding feedback loop; this is a first-order diagnostic, the same simplification CYC1/DC1/MR1 already document.
- Models only a smooth, contemporaneous level relationship, not a discrete currency-crisis or overshooting event.
