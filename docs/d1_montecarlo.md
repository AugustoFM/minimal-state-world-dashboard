# D1 Monte Carlo

`python -m src.montecarlo [--draws 1000] [--seed 20261020]` runs the C1 -> C2 -> C4 chain for every draw, composition variant and persistence setting, and writes:

- `outputs/runs/summary_percentiles.csv` - p10/p50/p90 by variant, persistence, scenario, horizon and indicator (versioned);
- `outputs/runs/run_metadata.json` - seed, draws, sampled vs fixed parameters, choices, runtime, inputs commit (versioned);
- `outputs/runs/draws/` - draw-level results and sampled parameters (git-ignored; reproducible from the seed).

## How a draw works
1. Sample every ranged parameter (table below).
2. Copy the configuration with that value as low = central = high, and run the unchanged C1/C2 code at its `central` corner. No model equation is duplicated, so D1 cannot drift from C2.
3. Compute C4 health outcomes with the C4 functions (`health_spending_per_capita`, `apply_spending_elasticity`, `hdi_health_index`), using the efficiency share of the active composition variant.
4. Take differences against S0 inside the draw (paired), so a percentile of "R_amb minus S0" describes the policy effect under shared parameter uncertainty, not the gap between two independent clouds.

`tests/test_montecarlo.py` checks that the all-central draw reproduces the published `data/brazil/macro.csv` and `data/brazil/social.csv` central values exactly.

## Sampling

| Parameter | Distribution | Source of range |
|---|---|---|
| Multipliers: public investment, social benefits, subsidies, other expenditures | triangular(low, central, high) | `fiscal_multipliers_brazil.accumulated` (spread across Sanches et al. specifications) |
| Efficiency output effect | triangular(0, 0, 0.28) | `macro_modelling_choices` (choice) |
| Real interest rate, GDP deflator, TFP growth, human-capital growth, investment rate, Okun coefficient | triangular(low, central, high) | C2 inputs in `parameters.yaml` |
| Pension indexation weight | uniform(0, 1), snapped to a 0.025 grid | C1 (choice) |
| NTA profile vintage | 2003 or 2018, equal probability | C1 |
| Service-cut fraction | triangular(0, 0.5, 1) | `social_modelling_choices` (choice) |
| Infant-mortality elasticity | triangular(-0.206, -0.126, -0.071) | Szklo, Clarke & Rocha (2024) |

Fixed: life-expectancy elasticity (point estimate), initial debt, revenue/GDP, capital share, K/Y, depreciation, GDP anchors, C1 category shares.

Choices to keep in view: triangular shapes are a modelling choice, not sourced distributions; parameters are independent (no sourced correlations); persistence is a reported dimension, not sampled.

## Composition variants (`config/scenarios.yaml` -> `variant_definitions`)
`default`, `pension_only`, `efficiency_only`, `investment_also_cut_stress` (public investment protection lifted), `compensating_transfers` (means-tested transfers protection lifted to allow the increase). S0 and S1 are reported for every variant; their spending paths do not depend on the variant, but S1's GDP effect uses the variant's package mix to offset ageing drift.

## What the percentiles mean
Uncertainty about the model's parameters only. They are not forecast intervals: they exclude external shocks (C6), long-run feedback (C5), distribution (C3, rows marked `not_modelled`), model misspecification and policy implementation risk. No result is published before the D2 back-test.
