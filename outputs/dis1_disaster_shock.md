# DIS1: climate/natural-disaster tail-shock diagnostic

Built in response to a wider literature benchmark of this project's own debt-sustainability methodology, which found the IMF's Natural Disaster Debt Dynamics Tool (ND-DDT) is now institutionalised in its debt-sustainability frameworks and is structurally close to this model's own existing major-corruption-shock mechanism (`src.corruption`). DIS1 reuses that exact machinery for a climate/disaster shock, adding a shared-draw primary-balance hit (emergency relief spending) alongside the existing GDP-level channel. Calibration is anchored on a single, well-documented Brazilian event (the 2024 Rio Grande do Sul floods, federal fiscal cost ~0.07-0.12% of GDP), not an estimated distribution -- see the module docstring for the full sourcing note and its limits, including why a generic cross-country (EM-DAT) calibration was not used (it is independently documented to understate Brazilian disaster losses by roughly an order of magnitude relative to Brazil's own S2iD system).

Draws: 300 (seed 20261026, central draw plus 299 sampled). Sampled annual event probability: median 0.080 [0.039, 0.112].

## Additional debt/GDP from the disaster-shock channel

| Scenario | Horizon | Baseline (p50 [p10,p90]) | Additional pp from disaster shock (p50 [p10,p90]) |
|---|---:|---|---|
| E_amb | 5 | 104.33 [89.87, 113.44] | +0.000 [+0.000, +1.348] |
| E_amb | 10 | 154.11 [120.10, 178.84] | +0.142 [+0.000, +1.856] |
| E_amb | 15 | 230.44 [166.44, 282.87] | +0.156 [+0.000, +2.927] |
| E_amb | 20 | 334.57 [225.38, 434.01] | +0.207 [+0.000, +4.497] |
| E_mod | 5 | 101.54 [87.14, 110.63] | +0.000 [+0.000, +1.315] |
| E_mod | 10 | 142.48 [109.55, 166.54] | +0.130 [+0.000, +1.723] |
| E_mod | 15 | 205.83 [146.01, 255.38] | +0.139 [+0.000, +2.619] |
| E_mod | 20 | 298.86 [198.95, 390.49] | +0.183 [+0.000, +4.048] |
| R_amb | 5 | 93.17 [78.97, 102.18] | +0.000 [+0.000, +1.217] |
| R_amb | 10 | 107.80 [77.93, 129.65] | +0.098 [+0.000, +1.288] |
| R_amb | 15 | 124.47 [75.97, 164.93] | +0.083 [+0.000, +1.593] |
| R_amb | 20 | 148.29 [77.75, 215.80] | +0.081 [+0.000, +2.188] |
| R_mod | 5 | 95.96 [81.68, 105.01] | +0.000 [+0.000, +1.250] |
| R_mod | 10 | 119.38 [88.47, 141.95] | +0.109 [+0.000, +1.441] |
| R_mod | 15 | 151.59 [99.25, 195.08] | +0.102 [+0.000, +1.926] |
| R_mod | 20 | 197.32 [116.35, 272.40] | +0.111 [+0.000, +2.763] |
| S0 | 5 | 98.75 [84.41, 107.82] | +0.000 [+0.000, +1.282] |
| S0 | 10 | 130.90 [99.01, 154.24] | +0.118 [+0.000, +1.584] |
| S0 | 15 | 178.71 [122.59, 225.23] | +0.120 [+0.000, +2.271] |
| S0 | 20 | 247.97 [157.65, 331.35] | +0.146 [+0.000, +3.427] |

## Limitations

- Both the event probability and the magnitude bands are judgement calls anchored on a single severe Brazilian event (2024), not an estimated hazard rate or loss distribution -- the ~20-year window this project's own back-test covers contains exactly one federal-fiscal-scale climate event, far too thin a sample to fit a frequency to.
- The GDP-level and primary-balance channels are applied as a direct, first-order revaluation of the already-external-adjusted baseline, not re-run through the full debt recursion -- the same simplification CYC1, DC1 and FX1 already document.
- The same drawn event sequence and magnitudes are applied identically to every scenario within a draw, exactly as the G2 corruption-shock module already does, so this channel widens uncertainty without mechanically favouring any policy path.
