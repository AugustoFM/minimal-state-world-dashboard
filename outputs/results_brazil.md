# Brazil scenario results

**Internal review - not for publication: D2 gate v2 - Tier 1 (differences vs S0) PASS, Tier 2 (debt/GDP levels) FAIL**

Run seed: `20261020`  
Draws: `1000`  
Inputs commit: `de8c2e2ca7dafab829be2e61046bca9edac91595`  
Created: `2026-10-23T10:30:10+00:00`  
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
| S1 | transitory | -0.80 [-1.00, -0.60] | -1.33 [-1.90, -0.81] | -2.11 [-3.10, -1.19] |
| S1 | persistent | -1.71 [-2.15, -1.21] | -3.83 [-4.89, -2.72] | -8.07 [-10.35, -5.78] |
| R_mod | transitory | -0.45 [-0.54, -0.35] | -0.55 [-0.71, -0.42] | -0.71 [-0.96, -0.52] |
| R_mod | persistent | -1.05 [-1.32, -0.72] | -2.21 [-2.76, -1.54] | -4.44 [-5.51, -3.08] |
| R_amb | transitory | -0.89 [-1.07, -0.70] | -1.11 [-1.42, -0.84] | -0.93 [-1.36, -0.63] |
| R_amb | persistent | -2.09 [-2.63, -1.44] | -4.41 [-5.49, -3.06] | -7.74 [-9.60, -5.37] |
| R_max | transitory | -1.87 [-2.25, -1.46] | -0.91 [-1.28, -0.64] | -1.14 [-1.66, -0.77] |
| R_max | persistent | -4.39 [-5.50, -3.01] | -6.05 [-7.53, -4.20] | -9.39 [-11.66, -6.52] |
| E_mod | transitory | 0.45 [0.35, 0.54] | 0.56 [0.42, 0.72] | 0.72 [0.52, 0.97] |
| E_mod | persistent | 1.05 [0.72, 1.32] | 2.22 [1.55, 2.78] | 4.49 [3.13, 5.61] |
| E_amb | transitory | 0.89 [0.70, 1.08] | 1.11 [0.84, 1.44] | 0.27 [0.09, 0.54] |
| E_amb | persistent | 2.10 [1.44, 2.64] | 4.46 [3.10, 5.58] | 5.18 [3.63, 6.48] |
| E_mod_tax | transitory | 0.31 [0.21, 0.40] | 0.41 [0.28, 0.57] | 0.57 [0.38, 0.82] |
| E_mod_tax | persistent | 0.48 [0.16, 0.75] | 1.05 [0.37, 1.61] | 2.14 [0.78, 3.25] |
| E_amb_tax | transitory | 0.61 [0.42, 0.79] | 0.82 [0.56, 1.14] | 0.29 [0.11, 0.57] |
| E_amb_tax | persistent | 0.96 [0.31, 1.50] | 2.11 [0.75, 3.22] | 2.48 [0.92, 3.76] |

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
| S1 | transitory | -4.3 [-4.6, -3.9] | -17.9 [-19.9, -16.0] | -81.7 [-97.6, -66.9] |
| S1 | persistent | -3.5 [-4.0, -3.1] | -15.5 [-17.2, -13.9] | -73.8 [-85.6, -62.7] |
| R_mod | transitory | -2.8 [-2.9, -2.7] | -11.6 [-12.4, -10.7] | -51.4 [-59.4, -42.2] |
| R_mod | persistent | -2.3 [-2.5, -2.0] | -10.0 [-10.7, -9.3] | -46.1 [-52.0, -39.3] |
| R_amb | transitory | -5.6 [-5.7, -5.4] | -23.3 [-24.7, -21.4] | -100.1 [-116.3, -81.5] |
| R_amb | persistent | -4.5 [-5.1, -4.1] | -20.1 [-21.6, -18.8] | -91.9 [-104.0, -77.5] |
| R_max | transitory | -11.7 [-12.1, -11.3] | -40.8 [-43.8, -36.9] | -139.9 [-165.4, -111.1] |
| R_max | persistent | -9.5 [-10.7, -8.5] | -36.2 [-38.9, -33.4] | -131.6 [-153.0, -107.4] |
| E_mod | transitory | 2.8 [2.7, 2.9] | 11.6 [10.7, 12.4] | 51.4 [42.2, 59.4] |
| E_mod | persistent | 2.3 [2.0, 2.5] | 9.9 [9.3, 10.7] | 45.2 [38.5, 51.1] |
| E_amb | transitory | 5.6 [5.4, 5.7] | 23.3 [21.4, 24.7] | 87.0 [69.2, 102.8] |
| E_amb | persistent | 4.5 [4.1, 5.1] | 19.8 [18.5, 21.3] | 80.1 [65.5, 93.0] |
| E_mod_tax | transitory | -0.2 [-0.3, -0.1] | -0.2 [-0.3, -0.1] | -0.2 [-0.4, -0.1] |
| E_mod_tax | persistent | -0.4 [-0.6, -0.1] | -0.8 [-1.4, -0.2] | -2.3 [-4.7, -0.6] |
| E_amb_tax | transitory | -0.4 [-0.6, -0.3] | -0.4 [-0.6, -0.2] | 0.5 [0.3, 0.8] |
| E_amb_tax | persistent | -0.7 [-1.2, -0.2] | -1.6 [-2.8, -0.4] | -2.0 [-4.4, -0.5] |

### Debt/GDP vs S0, with C5 feedback (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | -4.3 [-4.7, -3.9] | -19.9 [-22.4, -17.5] | -100.3 [-115.6, -85.4] |
| S1 | persistent | -3.4 [-4.0, -3.0] | -16.7 [-19.0, -14.6] | -86.8 [-99.2, -75.9] |
| R_mod | transitory | -2.9 [-3.0, -2.7] | -13.4 [-14.4, -11.9] | -63.1 [-72.2, -55.2] |
| R_mod | persistent | -2.3 [-2.6, -2.1] | -11.1 [-12.3, -10.1] | -55.1 [-61.3, -49.3] |
| R_amb | transitory | -5.7 [-6.0, -5.5] | -26.8 [-28.9, -23.7] | -126.7 [-144.0, -108.5] |
| R_amb | persistent | -4.6 [-5.2, -4.1] | -22.4 [-24.8, -20.4] | -112.6 [-125.3, -99.0] |
| R_max | transitory | -12.0 [-12.6, -11.5] | -47.6 [-52.7, -40.8] | -188.9 [-220.1, -145.4] |
| R_max | persistent | -9.7 [-11.0, -8.6] | -41.6 [-45.7, -36.6] | -172.2 [-195.9, -140.7] |
| E_mod | transitory | 2.9 [2.7, 3.0] | 13.3 [12.0, 14.1] | 61.3 [52.6, 71.4] |
| E_mod | persistent | 2.3 [2.1, 2.6] | 11.0 [10.1, 12.1] | 52.3 [46.6, 58.6] |
| E_amb | transitory | 5.8 [5.5, 6.0] | 26.4 [24.2, 27.9] | 106.6 [88.3, 127.4] |
| E_amb | persistent | 4.6 [4.1, 5.2] | 21.9 [20.1, 24.0] | 95.7 [81.6, 111.3] |
| E_mod_tax | transitory | -0.3 [-0.4, -0.2] | -0.5 [-0.8, -0.3] | -1.3 [-2.2, -0.6] |
| E_mod_tax | persistent | -0.4 [-0.7, -0.1] | -1.3 [-2.2, -0.4] | -4.4 [-8.7, -1.5] |
| E_amb_tax | transitory | -0.6 [-0.8, -0.4] | -1.0 [-1.6, -0.6] | -0.5 [-1.3, -0.0] |
| E_amb_tax | persistent | -0.9 [-1.4, -0.3] | -2.5 [-4.4, -0.9] | -4.7 [-9.1, -1.6] |

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
| R_mod | transitory | 0.077 [0.055, 0.273] | 0.155 [0.133, 0.572] | 0.362 [0.340, 1.271] |
| R_mod | persistent | 0.084 [0.039, 0.276] | 0.171 [0.087, 0.576] | 0.371 [0.221, 1.278] |
| R_amb | transitory | 0.158 [0.122, 0.573] | 0.363 [0.327, 1.273] | 0.820 [0.798, 2.630] |
| R_amb | persistent | 0.171 [0.087, 0.576] | 0.371 [0.221, 1.278] | 0.805 [0.541, 2.658] |
| R_max | transitory | 0.392 [0.322, 1.352] | 0.567 [0.541, 1.901] | 1.133 [1.108, 3.470] |
| R_max | persistent | 0.395 [0.237, 1.356] | 0.571 [0.360, 1.911] | 1.090 [0.773, 3.538] |
| E_mod | transitory | -0.066 [-0.248, -0.039] | -0.103 [-0.460, -0.076] | -0.143 [-0.814, -0.116] |
| E_mod | persistent | -0.092 [-0.266, -0.026] | -0.178 [-0.509, -0.044] | -0.331 [-0.936, -0.060] |
| E_amb | transitory | -0.120 [-0.472, -0.068] | -0.163 [-0.828, -0.110] | -0.132 [-0.889, -0.124] |
| E_amb | persistent | -0.178 [-0.509, -0.044] | -0.331 [-0.936, -0.060] | -0.368 [-1.049, -0.060] |
| E_mod_tax | transitory | -0.036 [-0.242, 0.172] | -0.030 [-0.453, 0.356] | 0.062 [-0.807, 0.773] |
| E_mod_tax | persistent | -0.038 [-0.244, 0.174] | -0.060 [-0.462, 0.362] | -0.047 [-0.835, 0.781] |
| E_amb_tax | transitory | -0.043 [-0.459, 0.359] | 0.047 [-0.814, 0.775] | 0.125 [-0.889, 0.910] |
| E_amb_tax | persistent | -0.060 [-0.462, 0.362] | -0.047 [-0.835, 0.781] | -0.028 [-0.930, 0.917] |

### Poverty below R$218 change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.01 [0.00, 0.02] | 0.03 [0.01, 0.05] | 0.07 [0.04, 0.13] |
| R_mod | persistent | 0.03 [0.00, 0.05] | 0.06 [0.01, 0.13] | 0.16 [0.06, 0.31] |
| R_amb | transitory | 0.03 [0.01, 0.07] | 0.09 [0.04, 0.14] | 0.14 [0.11, 0.90] |
| R_amb | persistent | 0.06 [0.01, 0.13] | 0.16 [0.06, 0.31] | 0.63 [0.16, 1.26] |
| R_max | transitory | 0.12 [0.04, 0.19] | 0.10 [0.06, 0.36] | 0.21 [0.17, 1.33] |
| R_max | persistent | 0.16 [0.06, 0.32] | 0.37 [0.10, 0.62] | 0.80 [0.23, 1.79] |
| E_mod | transitory | -0.01 [-0.03, -0.00] | -0.02 [-0.03, -0.01] | -0.02 [-0.04, -0.01] |
| E_mod | persistent | -0.04 [-0.07, -0.02] | -0.08 [-0.12, -0.04] | -0.13 [-0.21, -0.05] |
| E_amb | transitory | -0.04 [-0.07, -0.02] | -0.05 [-0.07, -0.03] | -0.01 [-0.01, -0.01] |
| E_amb | persistent | -0.08 [-0.12, -0.04] | -0.13 [-0.21, -0.05] | -0.15 [-0.24, -0.05] |
| E_mod_tax | transitory | 0.16 [0.04, 0.18] | 0.33 [0.17, 0.36] | 0.86 [0.41, 0.88] |
| E_mod_tax | persistent | 0.13 [0.03, 0.18] | 0.26 [0.14, 0.36] | 0.62 [0.30, 0.86] |
| E_amb_tax | transitory | 0.31 [0.16, 0.36] | 0.81 [0.39, 0.88] | 0.95 [0.49, 0.96] |
| E_amb_tax | persistent | 0.26 [0.14, 0.36] | 0.62 [0.30, 0.86] | 0.65 [0.36, 0.92] |

### Poverty below R$759 change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 1.91 [1.83, 2.01] | 2.13 [2.07, 2.41] | 2.69 [2.63, 3.65] |
| R_mod | persistent | 2.02 [1.91, 2.18] | 2.59 [2.31, 2.88] | 4.01 [3.20, 4.65] |
| R_amb | transitory | 2.30 [2.11, 2.49] | 2.87 [2.68, 3.74] | 3.92 [3.85, 8.38] |
| R_amb | persistent | 2.59 [2.31, 2.88] | 4.01 [3.20, 4.65] | 7.05 [5.06, 10.57] |
| R_max | transitory | 3.22 [2.91, 4.10] | 3.48 [3.38, 4.37] | 4.45 [4.37, 9.34] |
| R_max | persistent | 4.17 [3.25, 4.79] | 5.26 [4.18, 6.33] | 8.52 [6.01, 12.39] |
| E_mod | transitory | -0.39 [-0.52, -0.28] | -0.61 [-0.76, -0.49] | -0.93 [-1.22, -0.82] |
| E_mod | persistent | -0.63 [-1.00, -0.44] | -1.47 [-1.71, -1.21] | -2.17 [-2.61, -1.79] |
| E_amb | transitory | -0.78 [-0.97, -0.66] | -1.12 [-1.43, -0.97] | -0.25 [-0.65, -0.25] |
| E_amb | persistent | -1.47 [-1.71, -1.21] | -2.17 [-2.61, -1.79] | -2.33 [-2.85, -1.93] |
| E_mod_tax | transitory | 0.96 [0.81, 1.26] | 1.59 [0.93, 2.04] | 2.75 [1.77, 3.39] |
| E_mod_tax | persistent | 0.93 [0.74, 1.22] | 1.15 [0.83, 1.69] | 2.10 [1.36, 3.07] |
| E_amb_tax | transitory | 1.22 [0.89, 2.02] | 2.57 [1.70, 3.38] | 3.22 [2.26, 3.85] |
| E_amb_tax | persistent | 1.15 [0.83, 1.69] | 2.10 [1.36, 3.07] | 2.39 [1.45, 3.42] |

### Poverty below R$218, age 0-14, change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.01 [0.00, 0.04] | 0.08 [0.02, 0.10] | 0.14 [0.08, 0.26] |
| R_mod | persistent | 0.03 [0.01, 0.08] | 0.10 [0.02, 0.20] | 0.30 [0.13, 0.52] |
| R_amb | transitory | 0.08 [0.02, 0.13] | 0.18 [0.08, 0.29] | 0.30 [0.24, 1.32] |
| R_amb | persistent | 0.10 [0.02, 0.20] | 0.30 [0.13, 0.52] | 0.97 [0.34, 1.82] |
| R_max | transitory | 0.24 [0.09, 0.36] | 0.21 [0.14, 0.65] | 0.41 [0.35, 1.81] |
| R_max | persistent | 0.32 [0.14, 0.55] | 0.65 [0.21, 1.02] | 1.25 [0.45, 2.45] |
| E_mod | transitory | -0.02 [-0.05, -0.00] | -0.02 [-0.06, -0.01] | -0.04 [-0.08, -0.01] |
| E_mod | persistent | -0.08 [-0.14, -0.05] | -0.14 [-0.21, -0.08] | -0.21 [-0.35, -0.10] |
| E_amb | transitory | -0.08 [-0.12, -0.06] | -0.09 [-0.14, -0.06] | -0.03 [-0.03, -0.02] |
| E_amb | persistent | -0.14 [-0.21, -0.08] | -0.21 [-0.35, -0.10] | -0.25 [-0.39, -0.12] |
| E_mod_tax | transitory | 0.37 [0.12, 0.42] | 0.76 [0.41, 0.81] | 1.95 [0.98, 2.01] |
| E_mod_tax | persistent | 0.34 [0.11, 0.42] | 0.67 [0.37, 0.81] | 1.58 [0.80, 1.95] |
| E_amb_tax | transitory | 0.74 [0.39, 0.81] | 1.88 [0.95, 2.01] | 2.17 [1.15, 2.17] |
| E_amb_tax | persistent | 0.67 [0.37, 0.81] | 1.58 [0.80, 1.95] | 1.67 [0.94, 2.09] |

### Poverty below R$218, age 65+, change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.00 [0.00, 0.01] | 0.02 [0.00, 0.02] | 0.03 [0.02, 0.05] |
| R_mod | persistent | 0.00 [0.00, 0.01] | 0.02 [0.00, 0.03] | 0.05 [0.02, 0.07] |
| R_amb | transitory | 0.02 [0.00, 0.02] | 0.04 [0.02, 0.05] | 0.06 [0.05, 0.81] |
| R_amb | persistent | 0.02 [0.00, 0.03] | 0.05 [0.02, 0.07] | 0.12 [0.05, 0.88] |
| R_max | transitory | 0.05 [0.02, 0.06] | 0.04 [0.03, 0.24] | 0.10 [0.08, 1.55] |
| R_max | persistent | 0.05 [0.02, 0.07] | 0.09 [0.03, 0.27] | 0.18 [0.09, 1.65] |
| E_mod | transitory | 0.00 [-0.00, 0.00] | 0.00 [-0.00, 0.00] | -0.00 [-0.00, 0.00] |
| E_mod | persistent | -0.00 [-0.01, -0.00] | -0.00 [-0.02, -0.00] | -0.01 [-0.02, -0.00] |
| E_amb | transitory | -0.00 [-0.01, -0.00] | -0.00 [-0.01, -0.00] | 0.00 [-0.00, 0.00] |
| E_amb | persistent | -0.00 [-0.02, -0.00] | -0.01 [-0.02, -0.00] | -0.01 [-0.03, -0.00] |
| E_mod_tax | transitory | 0.00 [-0.00, 0.00] | 0.00 [0.00, 0.01] | 0.02 [0.01, 0.03] |
| E_mod_tax | persistent | 0.00 [-0.00, 0.00] | 0.00 [-0.00, 0.01] | 0.01 [-0.00, 0.03] |
| E_amb_tax | transitory | 0.00 [-0.00, 0.01] | 0.02 [0.00, 0.03] | 0.03 [0.02, 0.03] |
| E_amb_tax | persistent | 0.00 [-0.00, 0.01] | 0.01 [-0.00, 0.03] | 0.02 [0.00, 0.03] |

### Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.00 [0.00, 0.01] | 0.02 [0.01, 0.06] | 0.07 [0.06, 0.14] |
| R_mod | persistent | 0.01 [0.00, 0.01] | 0.03 [0.01, 0.06] | 0.09 [0.06, 0.14] |
| R_amb | transitory | 0.03 [0.01, 0.06] | 0.08 [0.06, 0.14] | 0.15 [0.14, 1.40] |
| R_amb | persistent | 0.03 [0.01, 0.06] | 0.09 [0.06, 0.14] | 0.19 [0.14, 1.48] |
| R_max | transitory | 0.08 [0.06, 0.14] | 0.08 [0.07, 0.48] | 0.24 [0.22, 2.47] |
| R_max | persistent | 0.09 [0.06, 0.14] | 0.10 [0.07, 0.51] | 0.31 [0.24, 2.59] |
| E_mod | transitory | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E_mod | persistent | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E_amb | transitory | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E_amb | persistent | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E_mod_tax | transitory | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E_mod_tax | persistent | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E_amb_tax | transitory | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E_amb_tax | persistent | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |

### Poverty below R$759, age 0-14, change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 1.40 [1.32, 1.47] | 1.60 [1.51, 1.86] | 2.09 [2.00, 2.66] |
| R_mod | persistent | 1.52 [1.42, 1.71] | 2.19 [1.87, 2.49] | 3.45 [2.86, 4.10] |
| R_amb | transitory | 1.80 [1.57, 1.97] | 2.29 [2.06, 2.77] | 2.88 [2.79, 3.80] |
| R_amb | persistent | 2.19 [1.87, 2.49] | 3.45 [2.86, 4.10] | 5.72 [4.57, 6.86] |
| R_max | transitory | 2.74 [2.37, 3.22] | 2.59 [2.44, 3.12] | 3.19 [3.08, 4.23] |
| R_max | persistent | 3.58 [2.95, 4.26] | 4.66 [3.66, 5.70] | 6.70 [5.42, 8.15] |
| E_mod | transitory | -0.42 [-0.51, -0.28] | -0.67 [-0.81, -0.52] | -1.00 [-1.41, -0.87] |
| E_mod | persistent | -0.73 [-1.33, -0.54] | -1.96 [-2.23, -1.62] | -2.90 [-3.49, -2.38] |
| E_amb | transitory | -0.91 [-1.11, -0.77] | -1.30 [-1.72, -1.10] | -0.38 [-0.93, -0.37] |
| E_amb | persistent | -1.96 [-2.23, -1.62] | -2.90 [-3.49, -2.38] | -3.18 [-3.84, -2.59] |
| E_mod_tax | transitory | 1.24 [1.01, 1.64] | 2.30 [1.40, 2.78] | 4.21 [2.78, 4.93] |
| E_mod_tax | persistent | 1.19 [0.92, 1.56] | 1.62 [1.25, 2.44] | 3.21 [2.14, 4.48] |
| E_amb_tax | transitory | 1.77 [1.35, 2.74] | 4.00 [2.67, 4.88] | 4.94 [3.58, 5.63] |
| E_amb_tax | persistent | 1.62 [1.25, 2.44] | 3.21 [2.14, 4.48] | 3.82 [2.32, 4.98] |

### Poverty below R$759, age 65+, change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 3.24 [3.20, 3.46] | 3.66 [3.63, 4.12] | 4.78 [4.74, 7.39] |
| R_mod | persistent | 3.29 [3.22, 3.48] | 3.78 [3.65, 4.23] | 5.16 [4.87, 7.66] |
| R_amb | transitory | 3.69 [3.63, 4.14] | 4.83 [4.76, 7.42] | 8.03 [7.99, 30.90] |
| R_amb | persistent | 3.78 [3.65, 4.23] | 5.16 [4.87, 7.66] | 8.85 [8.29, 31.70] |
| R_max | transitory | 4.96 [4.86, 7.63] | 6.99 [6.95, 9.07] | 9.29 [9.24, 34.34] |
| R_max | persistent | 5.24 [4.93, 7.81] | 7.53 [7.13, 9.95] | 10.77 [9.67, 35.93] |
| E_mod | transitory | -0.51 [-0.83, -0.46] | -0.88 [-1.07, -0.84] | -1.25 [-1.58, -1.21] |
| E_mod | persistent | -0.59 [-0.86, -0.47] | -1.06 [-1.23, -0.96] | -1.53 [-1.79, -1.34] |
| E_amb | transitory | -0.91 [-1.11, -0.85] | -1.26 [-1.62, -1.21] | -1.15 [-1.56, -1.15] |
| E_amb | persistent | -1.06 [-1.23, -0.96] | -1.53 [-1.79, -1.34] | -1.63 [-1.90, -1.43] |
| E_mod_tax | transitory | -0.16 [-0.28, 0.12] | -0.20 [-0.62, 0.14] | -0.41 [-0.84, 0.28] |
| E_mod_tax | persistent | -0.17 [-0.29, 0.12] | -0.25 [-0.64, 0.09] | -0.53 [-0.90, 0.24] |
| E_amb_tax | transitory | -0.22 [-0.63, 0.14] | -0.43 [-0.86, 0.27] | -0.32 [-0.84, 0.35] |
| E_amb_tax | persistent | -0.25 [-0.64, 0.09] | -0.53 [-0.90, 0.24] | -0.53 [-1.01, 0.27] |

### Poverty below R$759, living with a 65+ pension/BPC recipient, change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 3.50 [3.45, 3.82] | 4.17 [4.11, 4.90] | 5.75 [5.71, 9.04] |
| R_mod | persistent | 3.57 [3.48, 3.86] | 4.34 [4.16, 5.08] | 6.30 [5.93, 9.45] |
| R_amb | transitory | 4.20 [4.12, 4.93] | 5.83 [5.73, 9.09] | 9.95 [9.89, 27.23] |
| R_amb | persistent | 4.34 [4.16, 5.08] | 6.30 [5.93, 9.45] | 11.11 [10.32, 28.38] |
| R_max | transitory | 6.04 [5.88, 9.40] | 8.51 [8.43, 11.15] | 11.55 [11.47, 30.64] |
| R_max | persistent | 6.40 [6.02, 9.68] | 9.28 [8.76, 12.53] | 13.88 [12.16, 32.74] |
| E_mod | transitory | -0.77 [-1.20, -0.70] | -1.31 [-1.70, -1.23] | -2.01 [-2.70, -1.94] |
| E_mod | persistent | -0.84 [-1.23, -0.72] | -1.53 [-1.86, -1.33] | -2.36 [-2.95, -2.02] |
| E_amb | transitory | -1.37 [-1.76, -1.26] | -2.05 [-2.76, -1.95] | -2.10 [-2.96, -2.10] |
| E_amb | persistent | -1.53 [-1.86, -1.33] | -2.36 [-2.95, -2.02] | -2.59 [-3.20, -2.23] |
| E_mod_tax | transitory | -0.38 [-0.66, 0.16] | -0.51 [-1.14, 0.09] | -0.82 [-1.66, 0.25] |
| E_mod_tax | persistent | -0.45 [-0.67, 0.16] | -0.64 [-1.18, 0.08] | -1.07 [-1.76, 0.19] |
| E_amb_tax | transitory | -0.54 [-1.16, 0.08] | -0.86 [-1.69, 0.25] | -0.73 [-1.78, 0.34] |
| E_amb_tax | persistent | -0.64 [-1.18, 0.08] | -1.07 [-1.76, 0.19] | -1.15 [-2.01, 0.21] |

### Poverty below R$759, smoothed (0.95-1.05 x line), change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.89 [0.77, 1.02] | 1.18 [1.05, 1.41] | 1.68 [1.56, 2.61] |
| R_mod | persistent | 1.10 [0.93, 1.28] | 1.75 [1.46, 2.06] | 3.29 [2.48, 4.10] |
| R_amb | transitory | 1.38 [1.17, 1.57] | 1.89 [1.68, 2.77] | 2.97 [2.84, 7.40] |
| R_amb | persistent | 1.75 [1.46, 2.06] | 3.29 [2.48, 4.10] | 6.48 [4.56, 10.08] |
| R_max | transitory | 2.41 [1.99, 3.23] | 2.48 [2.35, 3.65] | 3.54 [3.41, 8.39] |
| R_max | persistent | 3.44 [2.60, 4.29] | 4.68 [3.62, 5.78] | 7.97 [5.54, 11.70] |
| E_mod | transitory | -0.81 [-0.93, -0.69] | -1.08 [-1.23, -0.97] | -1.40 [-1.70, -1.29] |
| E_mod | persistent | -1.01 [-1.18, -0.82] | -1.56 [-1.84, -1.32] | -2.52 [-3.05, -2.09] |
| E_amb | transitory | -1.24 [-1.39, -1.07] | -1.59 [-1.85, -1.40] | -1.27 [-1.65, -1.25] |
| E_amb | persistent | -1.56 [-1.84, -1.32] | -2.52 [-3.05, -2.09] | -2.79 [-3.38, -2.30] |
| E_mod_tax | transitory | 0.31 [-0.04, 0.73] | 0.94 [0.45, 1.45] | 2.15 [1.25, 2.74] |
| E_mod_tax | persistent | 0.27 [-0.10, 0.71] | 0.70 [0.19, 1.31] | 1.57 [0.81, 2.41] |
| E_amb_tax | transitory | 0.82 [0.34, 1.38] | 2.02 [1.18, 2.69] | 2.72 [1.62, 3.33] |
| E_amb_tax | persistent | 0.70 [0.19, 1.31] | 1.57 [0.81, 2.41] | 1.84 [0.96, 2.79] |

### R$759 poverty gap, change vs S0 (pp of line)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.216 [0.172, 0.293] | 0.361 [0.317, 0.544] | 0.677 [0.632, 1.167] |
| R_mod | persistent | 0.301 [0.219, 0.382] | 0.619 [0.448, 0.790] | 1.350 [0.936, 1.738] |
| R_amb | transitory | 0.439 [0.352, 0.604] | 0.756 [0.667, 1.229] | 1.293 [1.248, 2.952] |
| R_amb | persistent | 0.619 [0.448, 0.790] | 1.350 [0.936, 1.738] | 2.808 [1.835, 4.106] |
| R_max | transitory | 0.968 [0.780, 1.442] | 0.982 [0.923, 1.770] | 1.681 [1.627, 4.514] |
| R_max | persistent | 1.431 [0.989, 1.844] | 1.992 [1.355, 2.597] | 3.585 [2.363, 5.985] |
| E_mod | transitory | -0.158 [-0.194, -0.115] | -0.238 [-0.309, -0.191] | -0.372 [-0.506, -0.326] |
| E_mod | persistent | -0.215 [-0.283, -0.158] | -0.407 [-0.538, -0.306] | -0.755 [-1.006, -0.574] |
| E_amb | transitory | -0.300 [-0.368, -0.222] | -0.446 [-0.563, -0.357] | -0.329 [-0.494, -0.322] |
| E_amb | persistent | -0.407 [-0.538, -0.306] | -0.755 [-1.006, -0.574] | -0.853 [-1.134, -0.651] |
| E_mod_tax | transitory | 0.271 [0.150, 0.361] | 0.622 [0.350, 0.762] | 1.395 [0.793, 1.625] |
| E_mod_tax | persistent | 0.232 [0.124, 0.347] | 0.474 [0.260, 0.703] | 0.989 [0.561, 1.465] |
| E_amb_tax | transitory | 0.557 [0.314, 0.733] | 1.325 [0.755, 1.593] | 1.717 [0.982, 1.940] |
| E_amb_tax | persistent | 0.474 [0.260, 0.703] | 0.989 [0.561, 1.465] | 1.154 [0.658, 1.705] |

### Poverty below R$759, age 0-14, smoothed (0.95-1.05 x line), change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.67 [0.54, 0.79] | 0.96 [0.80, 1.15] | 1.41 [1.25, 1.95] |
| R_mod | persistent | 0.94 [0.75, 1.14] | 1.70 [1.36, 2.02] | 3.23 [2.51, 3.96] |
| R_amb | transitory | 1.19 [0.96, 1.37] | 1.69 [1.41, 2.17] | 2.23 [2.07, 3.13] |
| R_amb | persistent | 1.70 [1.36, 2.02] | 3.23 [2.51, 3.96] | 5.50 [4.38, 6.65] |
| R_max | transitory | 2.26 [1.81, 2.71] | 1.94 [1.77, 2.58] | 2.63 [2.46, 3.56] |
| R_max | persistent | 3.37 [2.64, 4.13] | 4.40 [3.48, 5.36] | 6.54 [5.26, 7.84] |
| E_mod | transitory | -0.64 [-0.73, -0.50] | -0.89 [-1.06, -0.75] | -1.27 [-1.69, -1.13] |
| E_mod | persistent | -0.86 [-1.05, -0.68] | -1.54 [-1.89, -1.26] | -2.86 [-3.56, -2.24] |
| E_amb | transitory | -1.09 [-1.27, -0.90] | -1.54 [-1.90, -1.28] | -1.09 [-1.62, -1.07] |
| E_amb | persistent | -1.54 [-1.89, -1.26] | -2.86 [-3.56, -2.24] | -3.25 [-4.02, -2.54] |
| E_mod_tax | transitory | 0.87 [0.53, 1.21] | 2.00 [1.31, 2.46] | 3.99 [2.64, 4.67] |
| E_mod_tax | persistent | 0.80 [0.43, 1.17] | 1.61 [0.95, 2.27] | 3.06 [1.98, 4.21] |
| E_amb_tax | transitory | 1.83 [1.16, 2.37] | 3.81 [2.54, 4.59] | 4.87 [3.20, 5.56] |
| E_amb_tax | persistent | 1.61 [0.95, 2.27] | 3.06 [1.98, 4.21] | 3.52 [2.23, 4.81] |

### R$759 poverty gap, age 0-14, change vs S0 (pp of line)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.266 [0.198, 0.330] | 0.413 [0.345, 0.583] | 0.728 [0.659, 1.159] |
| R_mod | persistent | 0.369 [0.275, 0.465] | 0.753 [0.558, 0.956] | 1.584 [1.152, 2.015] |
| R_amb | transitory | 0.531 [0.402, 0.675] | 0.847 [0.717, 1.252] | 1.279 [1.210, 2.192] |
| R_amb | persistent | 0.753 [0.558, 0.956] | 1.584 [1.152, 2.015] | 3.004 [2.156, 3.863] |
| R_max | transitory | 1.148 [0.881, 1.527] | 1.027 [0.938, 1.677] | 1.612 [1.529, 2.792] |
| R_max | persistent | 1.669 [1.213, 2.126] | 2.267 [1.636, 2.903] | 3.772 [2.700, 4.870] |
| E_mod | transitory | -0.230 [-0.282, -0.169] | -0.352 [-0.452, -0.279] | -0.553 [-0.751, -0.479] |
| E_mod | persistent | -0.324 [-0.422, -0.243] | -0.628 [-0.811, -0.475] | -1.184 [-1.547, -0.907] |
| E_amb | transitory | -0.446 [-0.544, -0.332] | -0.671 [-0.842, -0.532] | -0.475 [-0.729, -0.465] |
| E_amb | persistent | -0.628 [-0.811, -0.475] | -1.184 [-1.547, -0.907] | -1.342 [-1.759, -1.032] |
| E_mod_tax | transitory | 0.525 [0.306, 0.655] | 1.170 [0.684, 1.372] | 2.558 [1.493, 2.895] |
| E_mod_tax | persistent | 0.442 [0.264, 0.633] | 0.894 [0.543, 1.276] | 1.839 [1.128, 2.646] |
| E_amb_tax | transitory | 1.072 [0.628, 1.324] | 2.450 [1.434, 2.841] | 3.110 [1.824, 3.439] |
| E_amb_tax | persistent | 0.894 [0.543, 1.276] | 1.839 [1.128, 2.646] | 2.138 [1.311, 3.067] |

### Poverty below R$759, age 65+, smoothed (0.95-1.05 x line), change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 1.75 [1.71, 2.08] | 2.27 [2.24, 2.77] | 3.28 [3.24, 5.85] |
| R_mod | persistent | 1.83 [1.74, 2.14] | 2.46 [2.32, 2.92] | 3.74 [3.44, 6.22] |
| R_amb | transitory | 2.32 [2.26, 2.81] | 3.33 [3.27, 5.88] | 6.67 [6.63, 29.55] |
| R_amb | persistent | 2.46 [2.32, 2.92] | 3.74 [3.44, 6.22] | 7.67 [7.03, 30.52] |
| R_max | transitory | 3.59 [3.46, 6.22] | 5.37 [5.32, 8.59] | 7.90 [7.85, 33.02] |
| R_max | persistent | 3.92 [3.61, 6.49] | 6.04 [5.63, 9.34] | 9.51 [8.54, 34.56] |
| E_mod | transitory | -1.62 [-1.94, -1.58] | -2.09 [-2.35, -2.05] | -2.49 [-2.83, -2.46] |
| E_mod | persistent | -1.68 [-1.99, -1.60] | -2.24 [-2.45, -2.11] | -2.81 [-3.03, -2.58] |
| E_amb | transitory | -2.12 [-2.37, -2.07] | -2.53 [-2.85, -2.48] | -2.53 [-2.90, -2.53] |
| E_amb | persistent | -2.24 [-2.45, -2.11] | -2.81 [-3.03, -2.58] | -2.93 [-3.17, -2.69] |
| E_mod_tax | transitory | -0.73 [-1.62, -0.33] | -1.43 [-1.85, -0.79] | -1.55 [-2.11, -1.11] |
| E_mod_tax | persistent | -0.77 [-1.63, -0.33] | -1.53 [-1.89, -0.82] | -1.73 [-2.17, -1.17] |
| E_amb_tax | transitory | -1.46 [-1.86, -0.80] | -1.57 [-2.12, -1.12] | -1.52 [-2.13, -1.05] |
| E_amb_tax | persistent | -1.53 [-1.89, -0.82] | -1.73 [-2.17, -1.17] | -1.79 [-2.23, -1.16] |

### R$759 poverty gap, age 65+, change vs S0 (pp of line)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.261 [0.247, 0.419] | 0.520 [0.505, 0.867] | 1.088 [1.072, 2.099] |
| R_mod | persistent | 0.279 [0.253, 0.433] | 0.574 [0.522, 0.908] | 1.232 [1.120, 2.219] |
| R_amb | transitory | 0.533 [0.509, 0.878] | 1.103 [1.077, 2.113] | 2.363 [2.343, 8.272] |
| R_amb | persistent | 0.574 [0.522, 0.908] | 1.232 [1.120, 2.219] | 2.701 [2.456, 8.640] |
| R_max | transitory | 1.199 [1.154, 2.299] | 1.647 [1.625, 3.365] | 3.190 [3.167, 15.181] |
| R_max | persistent | 1.309 [1.188, 2.384] | 1.866 [1.701, 3.570] | 3.677 [3.322, 15.754] |
| E_mod | transitory | -0.108 [-0.148, -0.092] | -0.184 [-0.253, -0.168] | -0.304 [-0.423, -0.289] |
| E_mod | persistent | -0.123 [-0.160, -0.097] | -0.223 [-0.281, -0.180] | -0.391 [-0.477, -0.314] |
| E_amb | transitory | -0.192 [-0.261, -0.171] | -0.311 [-0.430, -0.292] | -0.319 [-0.458, -0.319] |
| E_amb | persistent | -0.223 [-0.281, -0.180] | -0.391 [-0.477, -0.314] | -0.435 [-0.526, -0.350] |
| E_mod_tax | transitory | -0.032 [-0.076, 0.011] | -0.043 [-0.126, 0.033] | -0.049 [-0.193, 0.090] |
| E_mod_tax | persistent | -0.040 [-0.079, 0.009] | -0.064 [-0.136, 0.024] | -0.090 [-0.219, 0.068] |
| E_amb_tax | transitory | -0.052 [-0.130, 0.029] | -0.059 [-0.198, 0.086] | -0.033 [-0.203, 0.117] |
| E_amb_tax | persistent | -0.064 [-0.136, 0.024] | -0.090 [-0.219, 0.068] | -0.093 [-0.238, 0.084] |

### Poverty below R$759, living with a 65+ pension/BPC recipient, smoothed (0.95-1.05 x line), change vs S0 (pp)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 2.03 [1.97, 2.50] | 2.81 [2.76, 3.57] | 4.28 [4.23, 7.53] |
| R_mod | persistent | 2.11 [2.00, 2.57] | 3.04 [2.85, 3.74] | 4.86 [4.47, 7.97] |
| R_amb | transitory | 2.87 [2.78, 3.61] | 4.35 [4.26, 7.57] | 8.62 [8.55, 25.93] |
| R_amb | persistent | 3.04 [2.85, 3.74] | 4.86 [4.47, 7.97] | 9.96 [9.04, 27.16] |
| R_max | transitory | 4.68 [4.52, 7.99] | 6.90 [6.83, 10.59] | 10.25 [10.17, 29.35] |
| R_max | persistent | 5.10 [4.69, 8.32] | 7.75 [7.18, 11.62] | 12.58 [11.12, 31.29] |
| E_mod | transitory | -1.90 [-2.35, -1.83] | -2.61 [-3.05, -2.54] | -3.34 [-4.04, -3.28] |
| E_mod | persistent | -2.00 [-2.41, -1.85] | -2.79 [-3.17, -2.60] | -3.67 [-4.25, -3.38] |
| E_amb | transitory | -2.66 [-3.08, -2.55] | -3.39 [-4.06, -3.29] | -3.45 [-4.23, -3.45] |
| E_amb | persistent | -2.79 [-3.17, -2.60] | -3.67 [-4.25, -3.38] | -3.93 [-4.52, -3.57] |
| E_mod_tax | transitory | -0.87 [-1.89, -0.40] | -1.68 [-2.37, -0.89] | -1.92 [-2.98, -1.18] |
| E_mod_tax | persistent | -0.93 [-1.90, -0.40] | -1.82 [-2.42, -0.93] | -2.24 [-3.07, -1.28] |
| E_amb_tax | transitory | -1.73 [-2.39, -0.91] | -1.96 [-3.00, -1.20] | -1.89 [-3.09, -1.09] |
| E_amb_tax | persistent | -1.82 [-2.42, -0.93] | -2.24 [-3.07, -1.28] | -2.34 [-3.23, -1.27] |

### R$759 poverty gap, living with a 65+ pension/BPC recipient, change vs S0 (pp of line)

| Scenario | Persistence | 2030 | 2035 | 2045 |
| --- | --- | --- | --- | --- |
| S1 | transitory | not modelled | not modelled | not modelled |
| S1 | persistent | not modelled | not modelled | not modelled |
| R_mod | transitory | 0.352 [0.335, 0.565] | 0.704 [0.686, 1.176] | 1.482 [1.463, 2.810] |
| R_mod | persistent | 0.367 [0.341, 0.578] | 0.756 [0.706, 1.220] | 1.639 [1.520, 2.957] |
| R_amb | transitory | 0.717 [0.692, 1.187] | 1.501 [1.470, 2.826] | 3.158 [3.136, 8.627] |
| R_amb | persistent | 0.756 [0.706, 1.220] | 1.639 [1.520, 2.957] | 3.565 [3.281, 9.109] |
| R_max | transitory | 1.626 [1.572, 3.067] | 2.225 [2.202, 4.443] | 4.230 [4.201, 14.273] |
| R_max | persistent | 1.740 [1.612, 3.173] | 2.474 [2.296, 4.707] | 4.830 [4.409, 15.025] |
| E_mod | transitory | -0.188 [-0.271, -0.169] | -0.333 [-0.484, -0.316] | -0.579 [-0.833, -0.563] |
| E_mod | persistent | -0.209 [-0.284, -0.173] | -0.385 [-0.512, -0.327] | -0.657 [-0.878, -0.583] |
| E_amb | transitory | -0.349 [-0.491, -0.318] | -0.591 [-0.838, -0.566] | -0.629 [-0.915, -0.629] |
| E_amb | persistent | -0.385 [-0.512, -0.327] | -0.657 [-0.878, -0.583] | -0.738 [-0.968, -0.653] |
| E_mod_tax | transitory | -0.080 [-0.167, -0.017] | -0.131 [-0.299, -0.021] | -0.211 [-0.511, -0.006] |
| E_mod_tax | persistent | -0.095 [-0.170, -0.019] | -0.162 [-0.309, -0.029] | -0.281 [-0.533, -0.030] |
| E_amb_tax | transitory | -0.147 [-0.303, -0.025] | -0.227 [-0.515, -0.011] | -0.212 [-0.560, 0.010] |
| E_amb_tax | persistent | -0.162 [-0.309, -0.029] | -0.281 [-0.533, -0.030] | -0.310 [-0.590, -0.025] |

## Debt/GDP levels

**Caution:** these levels carry the D2 debt-engine bias: one-step mean +1.36 pp/year and cumulative +18.6 pp over 2010-2024. Levels explode in S0 because of the C5 risk premium; differences against S0 are the meaningful quantity.

### Transitory

| Scenario | 2030 debt | 2030 with feedback | 2035 debt | 2035 with feedback | 2045 debt | 2045 with feedback |
| --- | --- | --- | --- | --- | --- | --- |
| S0 | 96.3 [82.0, 109.5] | 97.4 [82.2, 112.3] | 126.2 [95.7, 154.0] | 136.9 [98.0, 172.7] | 236.4 [153.2, 326.3] | 301.5 [180.8, 439.4] |
| S1 | 91.9 [77.9, 105.2] | 93.2 [78.0, 108.0] | 108.4 [78.8, 134.7] | 116.2 [79.6, 152.0] | 153.6 [84.8, 229.3] | 201.7 [87.2, 326.3] |
| R_mod | 93.4 [79.3, 106.6] | 94.6 [79.5, 109.3] | 114.6 [85.0, 141.9] | 122.9 [86.0, 159.0] | 185.1 [110.8, 267.0] | 239.9 [122.7, 368.0] |
| R_amb | 90.6 [76.6, 103.8] | 91.7 [76.8, 106.3] | 103.0 [74.4, 129.5] | 109.3 [74.2, 145.0] | 136.4 [72.0, 210.2] | 176.5 [70.2, 297.7] |
| R_max | 84.5 [70.6, 97.6] | 85.4 [70.5, 99.9] | 85.1 [58.7, 110.6] | 88.4 [56.8, 121.3] | 97.1 [42.0, 161.9] | 109.7 [33.8, 224.2] |
| E_mod | 99.0 [84.7, 112.4] | 100.4 [85.0, 115.3] | 138.0 [106.3, 166.2] | 150.2 [110.3, 186.5] | 287.9 [196.4, 384.6] | 363.6 [233.3, 510.2] |
| E_amb | 101.8 [87.6, 115.3] | 103.3 [87.9, 118.3] | 149.7 [116.9, 178.4] | 163.2 [122.4, 199.8] | 323.6 [223.0, 427.8] | 409.7 [270.5, 566.4] |
| E_mod_tax | 96.0 [81.8, 109.3] | 97.2 [82.0, 112.0] | 126.0 [95.5, 153.6] | 136.3 [97.7, 172.0] | 236.2 [153.1, 325.9] | 300.1 [179.9, 437.2] |
| E_amb_tax | 95.8 [81.7, 109.2] | 97.0 [81.8, 111.8] | 125.8 [95.3, 153.3] | 135.8 [97.4, 171.5] | 236.9 [153.5, 327.1] | 301.0 [180.4, 438.3] |

### Persistent

| Scenario | 2030 debt | 2030 with feedback | 2035 debt | 2035 with feedback | 2045 debt | 2045 with feedback |
| --- | --- | --- | --- | --- | --- | --- |
| S0 | 96.3 [82.0, 109.5] | 97.4 [82.2, 112.3] | 126.2 [95.7, 154.0] | 136.9 [98.0, 172.7] | 236.4 [153.2, 326.3] | 301.5 [180.8, 439.4] |
| S1 | 92.7 [78.5, 106.0] | 94.1 [78.7, 108.9] | 110.5 [80.7, 137.9] | 119.5 [81.7, 156.4] | 161.7 [88.3, 243.8] | 214.4 [93.4, 347.2] |
| R_mod | 93.9 [79.8, 107.1] | 95.1 [80.0, 109.9] | 116.1 [86.4, 143.9] | 125.0 [87.5, 162.0] | 190.5 [113.2, 275.1] | 247.5 [127.0, 380.5] |
| R_amb | 91.7 [77.5, 104.9] | 92.9 [77.6, 107.7] | 105.8 [76.9, 133.3] | 113.3 [77.1, 150.8] | 144.6 [75.5, 224.0] | 190.0 [76.0, 318.2] |
| R_max | 86.6 [72.4, 99.9] | 87.7 [72.3, 102.7] | 89.5 [62.1, 115.9] | 93.7 [60.9, 129.3] | 105.0 [45.5, 176.3] | 125.2 [37.8, 250.3] |
| E_mod | 98.5 [84.4, 112.0] | 99.9 [84.6, 114.8] | 136.5 [104.9, 163.9] | 148.1 [108.6, 183.9] | 281.5 [192.9, 377.0] | 353.6 [229.1, 498.9] |
| E_amb | 100.9 [86.9, 114.1] | 102.2 [87.2, 116.9] | 146.4 [114.2, 174.4] | 159.4 [119.0, 194.1] | 316.2 [220.0, 418.9] | 397.5 [265.7, 550.4] |
| E_mod_tax | 95.9 [81.8, 109.3] | 97.1 [81.9, 112.1] | 125.5 [94.9, 152.8] | 135.5 [97.1, 171.0] | 233.4 [151.9, 322.7] | 296.3 [178.2, 432.2] |
| E_amb_tax | 95.6 [81.7, 108.9] | 96.7 [81.8, 111.4] | 124.7 [94.2, 151.9] | 134.4 [95.8, 169.4] | 233.7 [152.2, 322.8] | 296.0 [178.2, 432.2] |

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
| R_mod | 20 | pension_only | -0.96 [-1.13, -0.83] | 0.016 [0.011, 0.022] | -50.8 [-58.4, -41.9] |
| R_mod | 20 | efficiency_only | -0.02 [-0.05, -0.00] | 0.258 [0.108, 0.439] | -51.7 [-60.0, -42.3] |
| R_mod | 20 | investment_also_cut_stress | -0.54 [-0.62, -0.46] | 0.050 [0.024, 0.080] | -51.2 [-59.2, -42.1] |
| R_mod | 20 | compensating_transfers | -0.34 [-0.42, -0.26] | 0.062 [0.028, 0.102] | -51.4 [-59.5, -42.2] |
| R_amb | 10 | default | -0.79 [-0.97, -0.62] | 0.069 [0.034, 0.110] | -23.3 [-24.7, -21.4] |
| R_amb | 10 | pension_only | -1.92 [-2.27, -1.66] | 0.031 [0.022, 0.043] | -22.2 [-23.5, -20.7] |
| R_amb | 10 | efficiency_only | -0.04 [-0.10, -0.01] | 0.285 [0.119, 0.483] | -23.9 [-25.5, -21.8] |
| R_amb | 10 | investment_also_cut_stress | -1.08 [-1.23, -0.93] | 0.063 [0.034, 0.098] | -23.0 [-24.4, -21.2] |
| R_amb | 10 | compensating_transfers | -0.68 [-0.85, -0.51] | 0.073 [0.035, 0.118] | -23.4 [-24.8, -21.4] |
| R_amb | 20 | default | -0.40 [-0.48, -0.31] | 0.096 [0.043, 0.160] | -100.1 [-116.3, -81.5] |
| R_amb | 20 | pension_only | -0.96 [-1.13, -0.83] | 0.016 [0.011, 0.022] | -99.8 [-115.7, -81.6] |
| R_amb | 20 | efficiency_only | -0.02 [-0.05, -0.00] | 0.451 [0.189, 0.767] | -100.4 [-116.8, -81.7] |
| R_amb | 20 | investment_also_cut_stress | -0.54 [-0.62, -0.46] | 0.080 [0.037, 0.133] | -100.0 [-116.1, -81.5] |
| R_amb | 20 | compensating_transfers | -0.34 [-0.42, -0.26] | 0.104 [0.046, 0.175] | -100.2 [-116.4, -81.5] |

### Persistent

| Scenario | Horizon (years) | Variant | GDP vs S0 (%) | Infant mortality vs S0 (per 1,000) | Debt/GDP vs S0 (pp) |
| --- | --- | --- | --- | --- | --- |
| R_mod | 10 | default | -1.96 [-2.49, -1.36] | 0.058 [0.038, 0.087] | -10.0 [-10.7, -9.3] |
| R_mod | 10 | pension_only | -4.60 [-5.44, -3.98] | 0.075 [0.053, 0.103] | -7.4 [-8.1, -6.3] |
| R_mod | 10 | efficiency_only | -0.16 [-0.38, -0.04] | 0.144 [0.060, 0.244] | -11.8 [-12.6, -10.8] |
| R_mod | 10 | investment_also_cut_stress | -2.63 [-3.06, -2.12] | 0.064 [0.044, 0.091] | -9.3 [-10.0, -8.8] |
| R_mod | 10 | compensating_transfers | -1.69 [-2.24, -1.04] | 0.057 [0.036, 0.087] | -10.2 [-11.1, -9.6] |
| R_mod | 20 | default | -3.91 [-4.97, -2.72] | 0.111 [0.072, 0.164] | -46.1 [-52.0, -39.3] |
| R_mod | 20 | pension_only | -9.20 [-10.88, -7.97] | 0.150 [0.106, 0.207] | -37.6 [-41.1, -33.9] |
| R_mod | 20 | efficiency_only | -0.33 [-0.77, -0.07] | 0.263 [0.110, 0.443] | -51.1 [-59.4, -42.1] |
| R_mod | 20 | investment_also_cut_stress | -5.25 [-6.12, -4.24] | 0.123 [0.086, 0.173] | -44.1 [-49.2, -38.4] |
| R_mod | 20 | compensating_transfers | -3.37 [-4.48, -2.08] | 0.107 [0.068, 0.162] | -46.9 [-53.1, -39.8] |
| R_amb | 10 | default | -3.91 [-4.97, -2.72] | 0.115 [0.075, 0.173] | -20.1 [-21.6, -18.8] |
| R_amb | 10 | pension_only | -9.20 [-10.88, -7.97] | 0.150 [0.106, 0.207] | -14.6 [-16.1, -12.3] |
| R_amb | 10 | efficiency_only | -0.33 [-0.77, -0.07] | 0.288 [0.120, 0.487] | -23.5 [-25.2, -21.5] |
| R_amb | 10 | investment_also_cut_stress | -5.25 [-6.12, -4.24] | 0.127 [0.088, 0.180] | -18.7 [-20.0, -17.6] |
| R_amb | 10 | compensating_transfers | -3.37 [-4.48, -2.08] | 0.113 [0.071, 0.171] | -20.6 [-22.2, -19.2] |
| R_amb | 20 | default | -6.85 [-8.70, -4.76] | 0.191 [0.125, 0.282] | -91.9 [-104.0, -77.5] |
| R_amb | 20 | pension_only | -16.10 [-19.04, -13.94] | 0.262 [0.185, 0.362] | -77.0 [-84.7, -69.5] |
| R_amb | 20 | efficiency_only | -0.58 [-1.34, -0.13] | 0.459 [0.192, 0.773] | -99.3 [-115.8, -81.2] |
| R_amb | 20 | investment_also_cut_stress | -9.20 [-10.71, -7.41] | 0.212 [0.149, 0.299] | -88.5 [-99.0, -76.0] |
| R_amb | 20 | compensating_transfers | -5.90 [-7.83, -3.64] | 0.185 [0.117, 0.279] | -93.0 [-105.8, -78.0] |

## Caveats

At the 20-year horizon, the following default-variant p10-p90 intervals include zero (listed by scenario and persistence):

- `S1` — transitory: none; persistent: none.
- `R_mod` — transitory: none; persistent: none.
- `R_amb` — transitory: none; persistent: none.
- `R_max` — transitory: none; persistent: none.
- `E_mod` — transitory: Poverty below R$218, age 65+, change vs S0 (pp), Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp); persistent: Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp).
- `E_amb` — transitory: Poverty below R$218, age 65+, change vs S0 (pp), Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp); persistent: Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp).
- `E_mod_tax` — transitory: Gini change vs S0 (points), Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp), Poverty below R$759, age 65+, change vs S0 (pp), Poverty below R$759, living with a 65+ pension/BPC recipient, change vs S0 (pp), R$759 poverty gap, age 65+, change vs S0 (pp of line); persistent: Gini change vs S0 (points), Poverty below R$218, age 65+, change vs S0 (pp), Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp), Poverty below R$759, age 65+, change vs S0 (pp), Poverty below R$759, living with a 65+ pension/BPC recipient, change vs S0 (pp), R$759 poverty gap, age 65+, change vs S0 (pp of line).
- `E_amb_tax` — transitory: Gini change vs S0 (points), Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp), Poverty below R$759, age 65+, change vs S0 (pp), Poverty below R$759, living with a 65+ pension/BPC recipient, change vs S0 (pp), R$759 poverty gap, age 65+, change vs S0 (pp of line), R$759 poverty gap, living with a 65+ pension/BPC recipient, change vs S0 (pp of line); persistent: Gini change vs S0 (points), Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp), Poverty below R$759, age 65+, change vs S0 (pp), Poverty below R$759, living with a 65+ pension/BPC recipient, change vs S0 (pp), R$759 poverty gap, age 65+, change vs S0 (pp of line).

The D2 backtest showed the C6 external block explained about 0.8 pp of the 24% 2006-2010 boom; the runs now use C7 channel A (commodity prices), which out of sample reproduces about 59% of it (`outputs/c7_backtest.md`). External paths, commodity-linked dividends and the G2 corruption shock are common to every scenario.

Metadata `not_modelled`: none listed. The summary separately contains 8,584 rows explicitly marked not modelled: C3 distribution results are available only for the `default` composition and exclude S1 because it has no package allocation.

The report compares policy scenarios; no candidate or party appears in it.
