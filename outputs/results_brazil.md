# Brazil scenario results

**Internal review - not for publication: D2 gate v2 - Tier 1 (differences vs S0) PASS, Tier 2 (debt/GDP levels) FAIL**

Run seed: `20261020`  
Draws: `1000`  
Inputs commit: `aa22b54bd6665a64e1a2625c3fce7c57448a0b41`  
Created: `2026-10-21T14:11:02+00:00`  
D2 verdict and diagnostics: parsed from `outputs/backtest.md`

## How to read

Each cell is p50 [p10, p90] across parameter draws. Differences against S0 are paired within each draw. The percentiles describe parameter uncertainty only: triangular sampling for ranges is a modelling choice (fiscal_multipliers_brazil.sampling_rule), not a sourced distribution; parameters are sampled independently: no sourced correlations; persistence (transitory/persistent) is reported as a dimension, not sampled; percentiles describe parameter uncertainty only, not forecast error or external shocks. Persistence settings are shown separately. S0 is a no-policy-change ageing baseline, not a forecast.

## Scenarios

| Scenario | Definition | By-year path vs S0 | Direction | Financing |
| --- | --- | --- | --- | --- |
| S0 | current rules; pension+health rise with ageing; revenue unchanged; debt drifts up | not specified | baseline | not specified |
| S1 | spending/GDP held at today's share (cost of offsetting ageing drift) | not specified | constant size | not specified |
| R_mod | moderate_reduction | 5y: 1 pp; 10y: 2 pp; 15y: 3 pp; 20y: 4 pp | below S0 | not specified |
| R_amb | ambitious_reduction | 5y: 2 pp; 10y: 4 pp; 15y: 6 pp; 20y: 7 pp | below S0 | not specified |
| R_max | B1 central precedent cap: change from today at the 10th percentile of observed middle-income changes; needs legislation of nearly its full size; stress case, not a recommendation | 5y: 4.2 pp; 10y: 5.5 pp; 15y: 7.3 pp; 20y: 8.5 pp | below S0 | not specified |
| E_mod | mirror of R_mod: spending 0.2 pp GDP/yr above S0; within the observed p90 increase at every horizon | 5y: 1 pp; 10y: 2 pp; 15y: 3 pp; 20y: 4 pp | above S0 | debt |
| E_amb | ambitious_expansion | 5y: 2 pp; 10y: 4 pp; 15y: 4.8 pp; 20y: 4.6 pp | above S0 | debt |
| E_mod_tax | E_mod with revenue raised by the same pp of GDP (balanced budget vs S0); tax GDP effect via the Sanches et al. revenue multiplier | 5y: 1 pp; 10y: 2 pp; 15y: 3 pp; 20y: 4 pp | above S0 | taxes |
| E_amb_tax | E_amb with revenue raised by the same pp of GDP | 5y: 2 pp; 10y: 4 pp; 15y: 4.8 pp; 20y: 4.6 pp | above S0 | taxes |

## Headline results

Variant: `default`. S0 is excluded because these indicators are differences against S0. A missing cell is labelled `not modelled`.

### GDP level vs S0 (%)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | -0.61 [-0.76, -0.48] | -0.64 [-0.79, -0.50] | -0.79 [-1.02, -0.58] |
| S1 | persistent | -1.50 [-1.91, -1.04] | -3.04 [-3.88, -2.11] | -6.60 [-8.56, -4.54] |
| R_mod | transitory | -0.40 [-0.48, -0.31] | -0.40 [-0.48, -0.31] | -0.40 [-0.48, -0.31] |
| R_mod | persistent | -0.98 [-1.24, -0.68] | -1.96 [-2.49, -1.36] | -3.91 [-4.97, -2.72] |
| R_amb | transitory | -0.79 [-0.97, -0.62] | -0.79 [-0.97, -0.62] | -0.40 [-0.48, -0.31] |
| R_amb | persistent | -1.96 [-2.49, -1.36] | -3.91 [-4.97, -2.72] | -6.85 [-8.70, -4.76] |
| R_max | transitory | -1.66 [-2.03, -1.31] | -0.51 [-0.63, -0.40] | -0.48 [-0.58, -0.37] |
| R_max | persistent | -4.11 [-5.22, -2.86] | -5.38 [-6.84, -3.74] | -8.32 [-10.56, -5.78] |
| E_mod | transitory | 0.40 [0.31, 0.48] | 0.40 [0.31, 0.48] | 0.40 [0.31, 0.48] |
| E_mod | persistent | 0.98 [0.68, 1.24] | 1.96 [1.36, 2.49] | 3.91 [2.72, 4.97] |
| E_amb | transitory | 0.79 [0.62, 0.97] | 0.79 [0.62, 0.97] | -0.08 [-0.10, -0.06] |
| E_amb | persistent | 1.96 [1.36, 2.49] | 3.91 [2.72, 4.97] | 4.50 [3.13, 5.72] |
| E_mod_tax | transitory | 0.26 [0.17, 0.35] | 0.26 [0.17, 0.35] | 0.26 [0.17, 0.35] |
| E_mod_tax | persistent | 0.43 [0.13, 0.69] | 0.86 [0.26, 1.39] | 1.71 [0.52, 2.77] |
| E_amb_tax | transitory | 0.52 [0.35, 0.69] | 0.52 [0.35, 0.69] | -0.05 [-0.07, -0.03] |
| E_amb_tax | persistent | 0.86 [0.26, 1.39] | 1.71 [0.52, 2.77] | 1.97 [0.60, 3.19] |

### GDP level vs S0, with C5 feedback (%)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | -0.79 [-0.98, -0.59] | -1.28 [-1.84, -0.76] | -1.94 [-2.94, -1.03] |
| S1 | persistent | -1.69 [-2.14, -1.20] | -3.78 [-4.84, -2.67] | -7.93 [-10.20, -5.59] |
| R_mod | transitory | -0.44 [-0.53, -0.34] | -0.52 [-0.68, -0.38] | -0.61 [-0.86, -0.42] |
| R_mod | persistent | -1.04 [-1.30, -0.71] | -2.17 [-2.73, -1.50] | -4.34 [-5.43, -3.00] |
| R_amb | transitory | -0.87 [-1.06, -0.68] | -1.04 [-1.35, -0.77] | -0.74 [-1.16, -0.46] |
| R_amb | persistent | -2.08 [-2.61, -1.42] | -4.34 [-5.45, -3.00] | -7.56 [-9.46, -5.22] |
| R_max | transitory | -1.83 [-2.22, -1.43] | -0.81 [-1.18, -0.54] | -0.91 [-1.42, -0.56] |
| R_max | persistent | -4.35 [-5.46, -2.97] | -5.95 [-7.47, -4.12] | -9.18 [-11.46, -6.33] |
| E_mod | transitory | 0.44 [0.34, 0.53] | 0.52 [0.38, 0.68] | 0.61 [0.42, 0.87] |
| E_mod | persistent | 1.04 [0.71, 1.31] | 2.18 [1.51, 2.75] | 4.37 [3.02, 5.51] |
| E_amb | transitory | 0.88 [0.68, 1.06] | 1.04 [0.77, 1.36] | 0.13 [-0.03, 0.40] |
| E_amb | persistent | 2.08 [1.42, 2.61] | 4.37 [3.03, 5.52] | 5.05 [3.49, 6.35] |
| E_mod_tax | transitory | 0.30 [0.20, 0.39] | 0.37 [0.24, 0.53] | 0.46 [0.28, 0.72] |
| E_mod_tax | persistent | 0.47 [0.14, 0.74] | 1.02 [0.34, 1.57] | 2.04 [0.68, 3.14] |
| E_amb_tax | transitory | 0.59 [0.40, 0.77] | 0.75 [0.48, 1.06] | 0.15 [-0.00, 0.43] |
| E_amb_tax | persistent | 0.94 [0.29, 1.49] | 2.04 [0.68, 3.15] | 2.35 [0.79, 3.63] |

### Unemployment change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | 0.11 [0.08, 0.14] | 0.11 [0.09, 0.14] | 0.14 [0.10, 0.18] |
| S1 | persistent | 0.26 [0.18, 0.35] | 0.53 [0.37, 0.71] | 1.17 [0.80, 1.56] |
| R_mod | transitory | 0.07 [0.06, 0.09] | 0.07 [0.06, 0.09] | 0.07 [0.06, 0.09] |
| R_mod | persistent | 0.17 [0.12, 0.22] | 0.34 [0.24, 0.44] | 0.69 [0.47, 0.89] |
| R_amb | transitory | 0.14 [0.11, 0.17] | 0.14 [0.11, 0.17] | 0.07 [0.06, 0.09] |
| R_amb | persistent | 0.34 [0.24, 0.44] | 0.69 [0.47, 0.89] | 1.20 [0.83, 1.55] |
| R_max | transitory | 0.29 [0.23, 0.37] | 0.09 [0.07, 0.11] | 0.08 [0.07, 0.10] |
| R_max | persistent | 0.72 [0.50, 0.93] | 0.94 [0.65, 1.22] | 1.46 [1.01, 1.89] |
| E_mod | transitory | -0.07 [-0.09, -0.06] | -0.07 [-0.09, -0.06] | -0.07 [-0.09, -0.06] |
| E_mod | persistent | -0.17 [-0.22, -0.12] | -0.34 [-0.44, -0.24] | -0.69 [-0.89, -0.47] |
| E_amb | transitory | -0.14 [-0.17, -0.11] | -0.14 [-0.17, -0.11] | 0.01 [0.01, 0.02] |
| E_amb | persistent | -0.34 [-0.44, -0.24] | -0.69 [-0.89, -0.47] | -0.79 [-1.02, -0.55] |
| E_mod_tax | transitory | -0.05 [-0.06, -0.03] | -0.05 [-0.06, -0.03] | -0.05 [-0.06, -0.03] |
| E_mod_tax | persistent | -0.08 [-0.12, -0.02] | -0.15 [-0.25, -0.04] | -0.30 [-0.49, -0.09] |
| E_amb_tax | transitory | -0.09 [-0.12, -0.06] | -0.09 [-0.12, -0.06] | 0.01 [0.01, 0.01] |
| E_amb_tax | persistent | -0.15 [-0.25, -0.04] | -0.30 [-0.49, -0.09] | -0.35 [-0.57, -0.10] |

### Debt/GDP vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | -4.3 [-4.6, -3.9] | -17.8 [-19.9, -16.1] | -81.7 [-97.6, -66.9] |
| S1 | persistent | -3.5 [-4.0, -3.0] | -15.4 [-17.2, -13.9] | -73.4 [-85.2, -62.6] |
| R_mod | transitory | -2.8 [-2.9, -2.7] | -11.6 [-12.4, -10.7] | -51.4 [-59.4, -42.2] |
| R_mod | persistent | -2.3 [-2.5, -2.0] | -9.9 [-10.7, -9.3] | -46.0 [-51.8, -39.3] |
| R_amb | transitory | -5.6 [-5.7, -5.4] | -23.3 [-24.7, -21.4] | -100.2 [-116.4, -81.6] |
| R_amb | persistent | -4.5 [-5.0, -4.1] | -20.0 [-21.5, -18.7] | -91.6 [-103.8, -77.2] |
| R_max | transitory | -11.6 [-12.1, -11.3] | -40.9 [-43.9, -36.9] | -139.9 [-165.6, -111.1] |
| R_max | persistent | -9.5 [-10.6, -8.5] | -36.1 [-38.8, -33.3] | -131.3 [-152.0, -107.1] |
| E_mod | transitory | 2.8 [2.7, 2.9] | 11.6 [10.7, 12.4] | 51.4 [42.2, 59.4] |
| E_mod | persistent | 2.3 [2.0, 2.5] | 9.9 [9.2, 10.6] | 45.0 [38.5, 50.9] |
| E_amb | transitory | 5.6 [5.4, 5.7] | 23.3 [21.4, 24.7] | 87.0 [69.2, 102.9] |
| E_amb | persistent | 4.5 [4.1, 5.0] | 19.7 [18.4, 21.2] | 80.0 [65.4, 92.8] |
| E_mod_tax | transitory | -0.2 [-0.3, -0.1] | -0.2 [-0.3, -0.1] | -0.2 [-0.4, -0.1] |
| E_mod_tax | persistent | -0.4 [-0.6, -0.1] | -0.8 [-1.4, -0.2] | -2.3 [-4.9, -0.6] |
| E_amb_tax | transitory | -0.4 [-0.6, -0.3] | -0.4 [-0.6, -0.2] | 0.5 [0.3, 0.8] |
| E_amb_tax | persistent | -0.7 [-1.2, -0.2] | -1.6 [-2.8, -0.4] | -2.0 [-4.6, -0.5] |

### Debt/GDP vs S0, with C5 feedback (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | -4.3 [-4.7, -3.9] | -20.0 [-22.4, -17.6] | -99.5 [-114.9, -85.8] |
| S1 | persistent | -3.4 [-4.0, -3.0] | -16.7 [-19.0, -14.7] | -85.8 [-97.6, -75.7] |
| R_mod | transitory | -2.9 [-3.0, -2.8] | -13.5 [-14.3, -12.0] | -62.5 [-72.3, -55.1] |
| R_mod | persistent | -2.3 [-2.6, -2.1] | -11.2 [-12.3, -10.2] | -54.6 [-60.1, -49.4] |
| R_amb | transitory | -5.8 [-6.0, -5.5] | -27.1 [-28.8, -23.9] | -125.5 [-143.6, -109.8] |
| R_amb | persistent | -4.6 [-5.3, -4.1] | -22.6 [-24.8, -20.4] | -111.8 [-122.6, -99.9] |
| R_max | transitory | -12.1 [-12.6, -11.5] | -48.3 [-53.1, -41.4] | -189.0 [-216.8, -149.4] |
| R_max | persistent | -9.7 [-11.0, -8.6] | -41.9 [-46.0, -36.9] | -171.2 [-191.7, -142.9] |
| E_mod | transitory | 2.9 [2.8, 3.0] | 13.3 [12.2, 14.0] | 61.2 [52.4, 71.7] |
| E_mod | persistent | 2.3 [2.1, 2.6] | 11.0 [10.1, 12.1] | 52.0 [46.4, 58.3] |
| E_amb | transitory | 5.8 [5.5, 6.0] | 26.4 [24.5, 27.7] | 106.5 [88.1, 127.8] |
| E_amb | persistent | 4.6 [4.1, 5.2] | 21.8 [20.2, 23.9] | 95.4 [81.5, 111.0] |
| E_mod_tax | transitory | -0.3 [-0.4, -0.2] | -0.5 [-0.7, -0.3] | -1.0 [-1.9, -0.4] |
| E_mod_tax | persistent | -0.4 [-0.7, -0.1] | -1.3 [-2.2, -0.4] | -4.2 [-8.4, -1.3] |
| E_amb_tax | transitory | -0.6 [-0.8, -0.4] | -1.0 [-1.5, -0.5] | -0.1 [-0.9, 0.3] |
| E_amb_tax | persistent | -0.9 [-1.4, -0.3] | -2.5 [-4.3, -0.8] | -4.4 [-8.8, -1.4] |

### Infant mortality difference vs S0 (per 1,000)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | 0.049 [0.035, 0.063] | 0.178 [0.130, 0.234] | 0.312 [0.226, 0.411] |
| S1 | persistent | 0.055 [0.040, 0.073] | 0.213 [0.155, 0.280] | 0.389 [0.279, 0.512] |
| R_mod | transitory | 0.011 [0.006, 0.017] | 0.035 [0.017, 0.055] | 0.058 [0.027, 0.095] |
| R_mod | persistent | 0.015 [0.010, 0.023] | 0.058 [0.038, 0.087] | 0.111 [0.072, 0.164] |
| R_amb | transitory | 0.021 [0.012, 0.033] | 0.069 [0.034, 0.110] | 0.096 [0.043, 0.160] |
| R_amb | persistent | 0.030 [0.019, 0.045] | 0.115 [0.075, 0.173] | 0.191 [0.125, 0.282] |
| R_max | transitory | 0.044 [0.024, 0.069] | 0.086 [0.039, 0.141] | 0.117 [0.052, 0.194] |
| R_max | persistent | 0.062 [0.040, 0.093] | 0.158 [0.103, 0.235] | 0.231 [0.152, 0.340] |
| E_mod | transitory | -0.011 [-0.017, -0.006] | -0.035 [-0.056, -0.017] | -0.058 [-0.096, -0.027] |
| E_mod | persistent | -0.015 [-0.023, -0.010] | -0.059 [-0.089, -0.039] | -0.114 [-0.171, -0.074] |
| E_amb | transitory | -0.022 [-0.033, -0.012] | -0.070 [-0.112, -0.035] | -0.058 [-0.099, -0.023] |
| E_amb | persistent | -0.030 [-0.046, -0.020] | -0.120 [-0.180, -0.078] | -0.132 [-0.197, -0.086] |
| E_mod_tax | transitory | -0.010 [-0.015, -0.005] | -0.032 [-0.053, -0.015] | -0.056 [-0.093, -0.025] |
| E_mod_tax | persistent | -0.011 [-0.017, -0.006] | -0.041 [-0.066, -0.023] | -0.077 [-0.125, -0.043] |
| E_amb_tax | transitory | -0.019 [-0.030, -0.010] | -0.065 [-0.106, -0.031] | -0.058 [-0.099, -0.024] |
| E_amb_tax | persistent | -0.021 [-0.034, -0.012] | -0.082 [-0.133, -0.045] | -0.089 [-0.144, -0.049] |

### Life expectancy difference vs S0 (years)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | -0.093 [-0.097, -0.085] | -0.346 [-0.355, -0.311] | -0.614 [-0.624, -0.541] |
| S1 | persistent | -0.103 [-0.113, -0.094] | -0.396 [-0.436, -0.360] | -0.724 [-0.805, -0.650] |
| R_mod | transitory | -0.020 [-0.028, -0.012] | -0.066 [-0.095, -0.035] | -0.111 [-0.163, -0.055] |
| R_mod | persistent | -0.029 [-0.038, -0.020] | -0.112 [-0.145, -0.079] | -0.212 [-0.273, -0.153] |
| R_amb | transitory | -0.041 [-0.056, -0.024] | -0.133 [-0.190, -0.071] | -0.185 [-0.276, -0.087] |
| R_amb | persistent | -0.058 [-0.075, -0.040] | -0.222 [-0.287, -0.157] | -0.367 [-0.469, -0.265] |
| R_max | transitory | -0.085 [-0.117, -0.051] | -0.165 [-0.244, -0.080] | -0.224 [-0.335, -0.105] |
| R_max | persistent | -0.120 [-0.155, -0.084] | -0.303 [-0.391, -0.215] | -0.443 [-0.565, -0.321] |
| E_mod | transitory | 0.020 [0.012, 0.028] | 0.067 [0.036, 0.096] | 0.112 [0.055, 0.164] |
| E_mod | persistent | 0.029 [0.020, 0.038] | 0.114 [0.079, 0.149] | 0.220 [0.156, 0.286] |
| E_amb | transitory | 0.041 [0.025, 0.057] | 0.134 [0.072, 0.193] | 0.112 [0.047, 0.171] |
| E_amb | persistent | 0.059 [0.041, 0.077] | 0.230 [0.160, 0.301] | 0.253 [0.179, 0.329] |
| E_mod_tax | transitory | 0.018 [0.010, 0.026] | 0.063 [0.031, 0.092] | 0.107 [0.051, 0.160] |
| E_mod_tax | persistent | 0.021 [0.012, 0.030] | 0.080 [0.046, 0.114] | 0.151 [0.088, 0.215] |
| E_amb_tax | transitory | 0.037 [0.020, 0.052] | 0.125 [0.063, 0.184] | 0.113 [0.048, 0.172] |
| E_amb_tax | persistent | 0.042 [0.024, 0.060] | 0.161 [0.092, 0.231] | 0.174 [0.101, 0.248] |

### Gini change vs S0 (points)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.032 [0.010, 0.225] | 0.067 [0.045, 0.479] | 0.187 [0.165, 1.101] |
| R_mod | persistent | 0.040 [-0.006, 0.228] | 0.081 [-0.002, 0.482] | 0.192 [0.042, 1.103] |
| R_amb | transitory | 0.069 [0.033, 0.480] | 0.188 [0.151, 1.102] | 0.525 [0.503, 2.383] |
| R_amb | persistent | 0.081 [-0.002, 0.482] | 0.192 [0.042, 1.103] | 0.497 [0.231, 2.405] |
| R_max | transitory | 0.207 [0.136, 1.174] | 0.329 [0.303, 1.685] | 0.784 [0.760, 3.206] |
| R_max | persistent | 0.208 [0.049, 1.175] | 0.327 [0.115, 1.689] | 0.727 [0.405, 3.270] |
| E_mod | transitory | -0.021 [-0.197, 0.006] | -0.014 [-0.356, 0.013] | 0.035 [-0.603, 0.062] |
| E_mod | persistent | -0.047 [-0.215, 0.019] | -0.090 [-0.406, 0.044] | -0.156 [-0.730, 0.115] |
| E_amb | transitory | -0.031 [-0.369, 0.021] | 0.014 [-0.617, 0.067] | 0.072 [-0.646, 0.081] |
| E_amb | persistent | -0.090 [-0.406, 0.044] | -0.156 [-0.730, 0.115] | -0.170 [-0.811, 0.140] |
| E_mod_tax | transitory | 0.015 [-0.191, 0.217] | 0.074 [-0.350, 0.446] | 0.274 [-0.595, 0.953] |
| E_mod_tax | persistent | 0.010 [-0.193, 0.219] | 0.036 [-0.359, 0.452] | 0.161 [-0.624, 0.960] |
| E_amb_tax | transitory | 0.060 [-0.356, 0.449] | 0.258 [-0.602, 0.954] | 0.369 [-0.645, 1.117] |
| E_amb_tax | persistent | 0.036 [-0.359, 0.452] | 0.161 [-0.624, 0.960] | 0.212 [-0.688, 1.122] |

### Poverty below R$218 change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.01 [0.00, 0.02] | 0.02 [0.01, 0.04] | 0.06 [0.02, 0.09] |
| R_mod | persistent | 0.03 [0.00, 0.05] | 0.06 [0.01, 0.12] | 0.14 [0.05, 0.28] |
| R_amb | transitory | 0.03 [0.01, 0.06] | 0.08 [0.02, 0.11] | 0.10 [0.07, 0.60] |
| R_amb | persistent | 0.06 [0.01, 0.12] | 0.14 [0.05, 0.28] | 0.58 [0.11, 0.96] |
| R_max | transitory | 0.08 [0.03, 0.15] | 0.09 [0.05, 0.23] | 0.22 [0.19, 1.89] |
| R_max | persistent | 0.15 [0.05, 0.29] | 0.25 [0.09, 0.48] | 0.82 [0.24, 2.38] |
| E_mod | transitory | -0.01 [-0.03, -0.00] | -0.01 [-0.03, -0.00] | -0.02 [-0.03, -0.00] |
| E_mod | persistent | -0.04 [-0.07, -0.02] | -0.07 [-0.12, -0.03] | -0.12 [-0.21, -0.04] |
| E_amb | transitory | -0.04 [-0.06, -0.02] | -0.04 [-0.07, -0.02] | -0.01 [-0.01, -0.00] |
| E_amb | persistent | -0.07 [-0.12, -0.03] | -0.12 [-0.21, -0.04] | -0.14 [-0.24, -0.05] |
| E_mod_tax | transitory | 0.16 [0.04, 0.18] | 0.33 [0.17, 0.36] | 0.87 [0.42, 0.89] |
| E_mod_tax | persistent | 0.13 [0.04, 0.18] | 0.27 [0.15, 0.36] | 0.64 [0.30, 0.88] |
| E_amb_tax | transitory | 0.31 [0.16, 0.36] | 0.83 [0.39, 0.89] | 0.97 [0.49, 0.97] |
| E_amb_tax | persistent | 0.27 [0.15, 0.36] | 0.64 [0.30, 0.88] | 0.66 [0.36, 0.93] |

### Poverty below R$759 change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 1.65 [1.59, 1.73] | 1.81 [1.75, 2.07] | 2.24 [2.17, 2.97] |
| R_mod | persistent | 1.75 [1.64, 1.90] | 2.26 [1.99, 2.54] | 3.38 [2.74, 3.98] |
| R_amb | transitory | 1.97 [1.79, 2.15] | 2.40 [2.22, 3.06] | 3.18 [3.12, 7.05] |
| R_amb | persistent | 2.26 [1.99, 2.54] | 3.38 [2.74, 3.98] | 6.33 [4.34, 9.25] |
| R_max | transitory | 2.74 [2.44, 3.46] | 2.88 [2.79, 6.19] | 3.68 [3.59, 8.07] |
| R_max | persistent | 3.54 [2.80, 4.17] | 5.01 [3.56, 7.91] | 7.71 [5.34, 11.02] |
| E_mod | transitory | -0.33 [-0.41, -0.22] | -0.53 [-0.62, -0.41] | -0.71 [-0.91, -0.59] |
| E_mod | persistent | -0.53 [-0.96, -0.39] | -1.33 [-1.56, -1.14] | -1.88 [-2.31, -1.57] |
| E_amb | transitory | -0.69 [-0.81, -0.58] | -0.89 [-1.09, -0.75] | 0.05 [-0.22, 0.05] |
| E_amb | persistent | -1.33 [-1.56, -1.14] | -1.88 [-2.31, -1.57] | -2.04 [-2.53, -1.69] |
| E_mod_tax | transitory | 1.28 [1.17, 1.56] | 2.02 [1.34, 2.38] | 3.30 [2.30, 3.79] |
| E_mod_tax | persistent | 1.25 [1.08, 1.51] | 1.53 [1.25, 2.13] | 2.60 [1.90, 3.46] |
| E_amb_tax | transitory | 1.63 [1.31, 2.35] | 3.12 [2.25, 3.76] | 3.75 [2.89, 4.25] |
| E_amb_tax | persistent | 1.53 [1.25, 2.13] | 2.60 [1.90, 3.46] | 2.95 [2.06, 3.83] |

## Debt/GDP levels

**Caution:** these levels carry the D2 debt-engine bias: one-step mean +1.36 pp/year and cumulative +18.6 pp over 2010-2024. Levels explode in S0 because of the C5 risk premium; differences against S0 are the meaningful quantity.

### Transitory

| Scenario | 2030 debt | 2030 with feedback | 2035 debt | 2035 with feedback | 2045 debt | 2045 with feedback |
| --- | --- | --- | --- | --- | --- | --- |
| S0 | 98.6 [85.8, 108.2] | 100.1 [86.3, 110.9] | 130.1 [101.1, 154.8] | 141.9 [104.2, 174.5] | 244.4 [161.2, 333.9] | 314.0 [191.6, 448.7] |
| S1 | 94.4 [81.6, 103.8] | 95.9 [82.0, 106.5] | 112.6 [84.4, 136.0] | 121.1 [86.1, 153.7] | 163.1 [93.4, 238.5] | 215.8 [101.4, 337.6] |
| R_mod | 95.8 [83.1, 105.3] | 97.2 [83.4, 107.9] | 118.5 [90.5, 142.4] | 128.1 [92.4, 160.5] | 193.2 [119.0, 274.9] | 251.2 [134.7, 377.4] |
| R_amb | 93.0 [80.3, 102.5] | 94.3 [80.6, 105.0] | 106.8 [79.8, 130.0] | 114.4 [80.4, 146.1] | 144.0 [79.2, 218.2] | 190.3 [79.8, 304.9] |
| R_max | 86.8 [74.3, 96.2] | 88.0 [74.3, 98.6] | 89.2 [64.2, 111.0] | 93.1 [63.0, 121.6] | 104.4 [49.7, 168.5] | 124.1 [42.3, 234.6] |
| E_mod | 101.3 [88.5, 111.1] | 103.0 [89.1, 113.8] | 141.7 [111.8, 167.2] | 155.4 [116.3, 188.2] | 295.9 [203.0, 392.8] | 375.3 [244.1, 520.3] |
| E_amb | 104.1 [91.2, 113.9] | 105.9 [91.9, 116.7] | 153.3 [122.5, 179.5] | 168.4 [129.1, 202.0] | 331.3 [230.2, 435.9] | 420.2 [281.3, 577.4] |
| E_mod_tax | 98.3 [85.6, 108.0] | 99.8 [86.0, 110.5] | 129.8 [100.9, 154.6] | 141.3 [103.9, 173.9] | 244.2 [161.1, 333.6] | 312.8 [190.9, 447.0] |
| E_amb_tax | 98.1 [85.4, 107.7] | 99.6 [85.8, 110.2] | 129.5 [100.8, 154.3] | 140.7 [103.6, 173.2] | 244.9 [161.6, 334.5] | 313.6 [191.4, 448.1] |

### Persistent

| Scenario | 2030 debt | 2030 with feedback | 2035 debt | 2035 with feedback | 2045 debt | 2045 with feedback |
| --- | --- | --- | --- | --- | --- | --- |
| S0 | 98.6 [85.8, 108.2] | 100.1 [86.3, 110.9] | 130.1 [101.1, 154.8] | 141.9 [104.2, 174.5] | 244.4 [161.2, 333.9] | 314.0 [191.6, 448.7] |
| S1 | 95.2 [82.3, 104.7] | 96.7 [82.7, 107.5] | 114.7 [86.2, 138.9] | 124.5 [88.4, 158.0] | 170.6 [97.8, 251.2] | 229.8 [108.6, 358.8] |
| R_mod | 96.2 [83.4, 105.9] | 97.7 [83.8, 108.7] | 120.0 [91.7, 144.3] | 130.0 [93.6, 163.1] | 198.1 [121.8, 281.5] | 260.6 [140.1, 388.9] |
| R_amb | 94.0 [81.2, 103.6] | 95.3 [81.4, 106.3] | 109.8 [81.7, 134.0] | 118.3 [82.6, 151.9] | 152.4 [84.0, 230.3] | 204.5 [87.3, 329.1] |
| R_max | 88.9 [76.1, 99.0] | 90.2 [76.3, 101.4] | 93.4 [66.9, 117.0] | 98.6 [66.5, 130.4] | 112.9 [53.4, 182.8] | 143.1 [47.8, 261.2] |
| E_mod | 100.8 [88.0, 110.5] | 102.4 [88.5, 113.1] | 139.9 [110.4, 165.4] | 152.9 [115.0, 185.5] | 290.1 [199.3, 383.8] | 365.4 [239.4, 506.8] |
| E_amb | 103.1 [90.3, 112.7] | 104.8 [90.8, 115.5] | 150.0 [119.6, 175.9] | 163.6 [125.5, 196.3] | 324.9 [226.0, 424.7] | 408.6 [274.6, 560.6] |
| E_mod_tax | 98.2 [85.4, 107.8] | 99.7 [85.8, 110.3] | 129.1 [100.4, 154.0] | 140.5 [103.4, 172.6] | 242.2 [159.4, 329.7] | 309.0 [188.5, 442.0] |
| E_amb_tax | 97.9 [85.1, 107.4] | 99.2 [85.4, 109.8] | 128.4 [99.6, 153.2] | 139.4 [102.3, 170.8] | 242.3 [159.6, 330.2] | 308.7 [188.5, 441.9] |

## Composition variants

All 5 committed variants are shown. C3 distribution indicators exist only for the `default` composition, so they are not included in this cross-variant table.

### Transitory

| Scenario | Horizon (years) | Variant | GDP vs S0 (%) | Infant mortality vs S0 (per 1,000) | Debt/GDP vs S0 (pp) |
| --- | --- | --- | --- | --- | --- |
| R_mod | 10 | default | -0.40 [-0.48, -0.31] | 0.035 [0.017, 0.055] | -11.6 [-12.4, -10.7] |
| R_mod | 10 | pension_only | -0.96 [-1.13, -0.83] | 0.016 [0.011, 0.022] | -11.1 [-11.8, -10.3] |
| R_mod | 10 | efficiency_only | -0.02 [-0.05, -0.00] | 0.142 [0.060, 0.242] | -12.0 [-12.7, -10.9] |
| R_mod | 10 | investment_also_cut_stress | -0.54 [-0.62, -0.46] | 0.031 [0.017, 0.049] | -11.5 [-12.2, -10.6] |
| R_mod | 10 | compensating_transfers | -0.34 [-0.42, -0.26] | 0.036 [0.018, 0.059] | -11.7 [-12.4, -10.7] |
| R_mod | 20 | default | -0.40 [-0.48, -0.31] | 0.058 [0.027, 0.095] | -51.4 [-59.4, -42.2] |
| R_mod | 20 | pension_only | -0.96 [-1.13, -0.83] | 0.016 [0.011, 0.022] | -50.8 [-58.5, -41.9] |
| R_mod | 20 | efficiency_only | -0.02 [-0.05, -0.00] | 0.258 [0.108, 0.439] | -51.7 [-60.0, -42.3] |
| R_mod | 20 | investment_also_cut_stress | -0.54 [-0.62, -0.46] | 0.050 [0.024, 0.080] | -51.2 [-59.2, -42.1] |
| R_mod | 20 | compensating_transfers | -0.34 [-0.42, -0.26] | 0.062 [0.028, 0.102] | -51.4 [-59.5, -42.2] |
| R_amb | 10 | default | -0.79 [-0.97, -0.62] | 0.069 [0.034, 0.110] | -23.3 [-24.7, -21.4] |
| R_amb | 10 | pension_only | -1.92 [-2.27, -1.66] | 0.031 [0.022, 0.043] | -22.2 [-23.5, -20.7] |
| R_amb | 10 | efficiency_only | -0.04 [-0.10, -0.01] | 0.285 [0.119, 0.483] | -23.9 [-25.5, -21.8] |
| R_amb | 10 | investment_also_cut_stress | -1.08 [-1.23, -0.93] | 0.063 [0.034, 0.098] | -23.0 [-24.4, -21.2] |
| R_amb | 10 | compensating_transfers | -0.68 [-0.85, -0.51] | 0.073 [0.035, 0.118] | -23.4 [-24.8, -21.4] |
| R_amb | 20 | default | -0.40 [-0.48, -0.31] | 0.096 [0.043, 0.160] | -100.2 [-116.4, -81.6] |
| R_amb | 20 | pension_only | -0.96 [-1.13, -0.83] | 0.016 [0.011, 0.022] | -99.8 [-115.8, -81.6] |
| R_amb | 20 | efficiency_only | -0.02 [-0.05, -0.00] | 0.451 [0.189, 0.767] | -100.4 [-116.8, -81.7] |
| R_amb | 20 | investment_also_cut_stress | -0.54 [-0.62, -0.46] | 0.080 [0.037, 0.133] | -100.1 [-116.3, -81.6] |
| R_amb | 20 | compensating_transfers | -0.34 [-0.42, -0.26] | 0.104 [0.046, 0.175] | -100.2 [-116.5, -81.6] |

### Persistent

| Scenario | Horizon (years) | Variant | GDP vs S0 (%) | Infant mortality vs S0 (per 1,000) | Debt/GDP vs S0 (pp) |
| --- | --- | --- | --- | --- | --- |
| R_mod | 10 | default | -1.96 [-2.49, -1.36] | 0.058 [0.038, 0.087] | -9.9 [-10.7, -9.3] |
| R_mod | 10 | pension_only | -4.60 [-5.44, -3.98] | 0.075 [0.053, 0.103] | -7.3 [-8.0, -6.3] |
| R_mod | 10 | efficiency_only | -0.16 [-0.38, -0.04] | 0.144 [0.060, 0.244] | -11.8 [-12.6, -10.8] |
| R_mod | 10 | investment_also_cut_stress | -2.63 [-3.06, -2.12] | 0.064 [0.044, 0.091] | -9.3 [-9.9, -8.7] |
| R_mod | 10 | compensating_transfers | -1.69 [-2.24, -1.04] | 0.057 [0.036, 0.087] | -10.2 [-11.0, -9.5] |
| R_mod | 20 | default | -3.91 [-4.97, -2.72] | 0.111 [0.072, 0.164] | -46.0 [-51.8, -39.3] |
| R_mod | 20 | pension_only | -9.20 [-10.88, -7.97] | 0.150 [0.106, 0.207] | -37.1 [-40.4, -33.6] |
| R_mod | 20 | efficiency_only | -0.33 [-0.77, -0.07] | 0.263 [0.110, 0.443] | -51.1 [-59.4, -42.1] |
| R_mod | 20 | investment_also_cut_stress | -5.25 [-6.12, -4.24] | 0.123 [0.086, 0.173] | -43.9 [-48.7, -38.2] |
| R_mod | 20 | compensating_transfers | -3.37 [-4.48, -2.08] | 0.107 [0.068, 0.162] | -46.9 [-53.0, -39.7] |
| R_amb | 10 | default | -3.91 [-4.97, -2.72] | 0.115 [0.075, 0.173] | -20.0 [-21.5, -18.7] |
| R_amb | 10 | pension_only | -9.20 [-10.88, -7.97] | 0.150 [0.106, 0.207] | -14.5 [-15.9, -12.3] |
| R_amb | 10 | efficiency_only | -0.33 [-0.77, -0.07] | 0.288 [0.120, 0.487] | -23.5 [-25.2, -21.6] |
| R_amb | 10 | investment_also_cut_stress | -5.25 [-6.12, -4.24] | 0.127 [0.088, 0.180] | -18.6 [-19.9, -17.5] |
| R_amb | 10 | compensating_transfers | -3.37 [-4.48, -2.08] | 0.113 [0.071, 0.171] | -20.5 [-22.1, -19.1] |
| R_amb | 20 | default | -6.85 [-8.70, -4.76] | 0.191 [0.125, 0.282] | -91.6 [-103.8, -77.2] |
| R_amb | 20 | pension_only | -16.10 [-19.04, -13.94] | 0.262 [0.185, 0.362] | -76.3 [-83.5, -68.9] |
| R_amb | 20 | efficiency_only | -0.58 [-1.34, -0.13] | 0.459 [0.192, 0.773] | -99.3 [-115.8, -81.2] |
| R_amb | 20 | investment_also_cut_stress | -9.20 [-10.71, -7.41] | 0.212 [0.149, 0.299] | -88.0 [-98.5, -75.6] |
| R_amb | 20 | compensating_transfers | -5.90 [-7.83, -3.64] | 0.185 [0.117, 0.279] | -93.0 [-105.6, -77.9] |

## Caveats

At the 20-year horizon, the following default-variant p10-p90 intervals include zero (listed by scenario and persistence):

- `S1` — transitory: none; persistent: none.
- `R_mod` — transitory: none; persistent: none.
- `R_amb` — transitory: none; persistent: none.
- `R_max` — transitory: none; persistent: none.
- `E_mod` — transitory: Gini change vs S0 (points); persistent: Gini change vs S0 (points).
- `E_amb` — transitory: GDP level vs S0, with C5 feedback (%), Gini change vs S0 (points), Poverty below R$759 change vs S0 (pp); persistent: Gini change vs S0 (points).
- `E_mod_tax` — transitory: Gini change vs S0 (points); persistent: Gini change vs S0 (points).
- `E_amb_tax` — transitory: GDP level vs S0, with C5 feedback (%), Debt/GDP vs S0, with C5 feedback (pp), Gini change vs S0 (points); persistent: Gini change vs S0 (points).

The D2 backtest showed the C6 external block explained about 0.8 pp of the 24% 2006-2010 boom; the runs now use C7 channel A (commodity prices), which out of sample reproduces about 59% of it (`outputs/c7_backtest.md`). External paths, commodity-linked dividends and the G2 corruption shock are common to every scenario.

Metadata `not_modelled`: none listed. The summary separately contains 1,480 rows explicitly marked not modelled: C3 distribution results are available only for the `default` composition and exclude S1 because it has no package allocation.

The report compares policy scenarios; no candidate or party appears in it.
