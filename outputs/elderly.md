# Older people: pensions, BPC, poverty and health costs

All results are descriptive scenario arithmetic. They compare measures and exposure channels; they do not identify causal effects.

## 2025 income profile

PNAD income-unit conditions 17-19 are excluded. Poverty without pension and BPC subtracts observed household pension and BPC receipts, holds every other income fixed, and floors income at zero.

| age_group | weighted_population | poverty_218_pct | poverty_759_pct | poverty_759_without_pension_bpc_pct | household_income_pension_bpc_share_pct | pension_recipient_pct | bpc_recipient_pct | pension_at_or_below_1_01_minimum_wage_pct_of_recipients |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0-14 | 41484452.07 | 5.01 | 40.58 | 45.59 | 5.61 | 0.30 | 0.90 | 94.86 |
| 15-29 | 46497268.63 | 3.32 | 25.46 | 32.10 | 8.09 | 0.52 | 1.26 | 79.90 |
| 30-64 | 100067385.74 | 2.76 | 18.87 | 29.36 | 12.40 | 9.21 | 1.81 | 58.81 |
| 65+ | 24575178.36 | 1.53 | 5.98 | 63.54 | 60.97 | 80.24 | 7.19 | 58.93 |

People of any age sharing an income unit with a pension/BPC recipient aged 65 or older:

| weighted_population | poverty_218_pct | poverty_759_pct | poverty_759_without_pension_bpc_pct |
| --- | --- | --- | --- |
| 41174441.58 | 0.09 | 6.80 | 58.46 |

The full CSV reports income composition for every age-group/weighted-income-decile cell. Component income is aggregated within the income unit and shared per capita; the residual reconciles detailed PNAD components to official household per-capita income.

## Minimum-benefit indexation

Real values use 2025=100. INPC-only indexation remains at 100 in INPC purchasing power; current-law sensitivities compound annual real gains of 0.6%, 1.5%, and 2.5%.

| year | case | real_benefit_index_2025_100 | cumulative_gain_vs_inpc_only_pct | inpc_only_shortfall_vs_case_pct |
| --- | --- | --- | --- | --- |
| 2030.000 | inpc_only | 100.000 | 0.000 | 0.000 |
| 2035.000 | inpc_only | 100.000 | 0.000 | 0.000 |
| 2030.000 | current_law_0.6_pct_real_gain | 103.036 | 3.036 | 2.947 |
| 2035.000 | current_law_0.6_pct_real_gain | 106.165 | 6.165 | 5.807 |
| 2030.000 | current_law_1.5_pct_real_gain | 107.728 | 7.728 | 7.174 |
| 2035.000 | current_law_1.5_pct_real_gain | 116.054 | 16.054 | 13.833 |
| 2030.000 | current_law_2.5_pct_real_gain | 113.141 | 13.141 | 11.615 |
| 2035.000 | current_law_2.5_pct_real_gain | 128.008 | 28.008 | 21.880 |

## C3 stylised allocation check

This check isolates a 0.1 percentage-point-of-GDP pension/indexation reduction, uses the indexation-floor allocation, and changes no macro, labour, tax, or means-tested-transfer input. `BPC on` allocates the gap across minimum-wage-linked pension income and all BPC income; `BPC off` retains the former pension-only treatment.

| indicator | BPC off | BPC on |
| --- | --- | --- |
| gini | 0.5117 | 0.5118 |
| poverty_headcount_218_pct | 3.1815 | 3.1815 |
| poverty_headcount_759_age_65_plus_pct | 8.4167 | 8.8812 |
| poverty_headcount_759_living_with_65_plus_pension_bpc_recipient_pct | 9.4879 | 9.9696 |
| poverty_headcount_759_pct | 23.8320 | 24.1105 |

## Health prices and benefit purchasing power

Monthly changes are compounded over the common archived window and annualised. A negative real-change entry is annual erosion for a benefit indexed to INPC.

| index | category | start_period | end_period | annualised_inflation_pct | inpc_benefit_real_change_pct_per_year |
| --- | --- | --- | --- | --- | --- |
| INPC | general | 201201 | 202609 | 5.655 | 0.000 |
| INPC | health_group | 201201 | 202609 | 6.029 | -0.353 |
| INPC | health_plans | 201201 | 202609 | 8.491 | -2.614 |
| INPC | medical_services | 201201 | 202609 | 6.826 | -1.097 |
| INPC | medicines | 201201 | 202609 | 5.546 | 0.103 |
| IPCA | general | 201201 | 202609 | 5.687 | -0.030 |
| IPCA | health_group | 201201 | 202609 | 6.459 | -0.755 |
| IPCA | health_plans | 201201 | 202609 | 8.508 | -2.630 |
| IPCA | medical_services | 201201 | 202609 | 6.912 | -1.177 |
| IPCA | medicines | 201201 | 202609 | 5.351 | 0.288 |

Regulated medicine prices rose less than INPC over this window, while health plans rose more. The raw files contain price changes but no expenditure weights, so an exact double-health-weight index is infeasible. The labelled older-household row uses the health-group price as an extra-health-exposure proxy. The plan-holder row uses the plan series. The non-holder robustness proxy gives medicines and medical services equal multiplicative weight; it is not an official basket.

| category | annualised_inflation_pct | inpc_benefit_real_change_pct_per_year | feasibility |
| --- | --- | --- | --- |
| inpc_weights | 5.655 | 0.000 | exact_by_construction |
| older_double_health_exposure_proxy | 6.029 | -0.353 | closest_feasible_no_archived_expenditure_weight |
| plan_holder_extra_health_exposure_proxy | 8.491 | -2.614 | closest_feasible_no_archived_expenditure_weight |
| nonholder_equal_medicines_services_proxy | 6.184 | -0.499 | robustness_equal_item_weights_not_primary_definition |

## SUS resources per age-weighted person

The age-cost denominator applies the C1 2018 health profile to the IBGE projection. S0 combines C1's health share with S0 real GDP. The revenue-linked path keeps the 2025 health share constant while real GDP grows. Because no 2027 health-spending observation is archived and interpolation is prohibited, the inflation-only-floor path is the closest feasible version: real spending is held at its observed 2025 level and is explicitly labelled as a proxy.

| year | path | age_weighted_population_index_2025_100 | real_health_spending_index_2025_100 | real_spending_per_age_weighted_person_index_2025_100 | feasibility |
| --- | --- | --- | --- | --- | --- |
| 2025.000 | s0_health_path | 100.000 | 100.000 | 100.000 | primary_specification |
| 2045.000 | s0_health_path | 128.509 | 147.551 | 114.818 | primary_specification |
| 2025.000 | constant_real_from_2025_proxy_for_2027_floor | 100.000 | 100.000 | 100.000 | closest_feasible_2025_anchor_no_2027_observation |
| 2045.000 | constant_real_from_2025_proxy_for_2027_floor | 128.509 | 100.000 | 77.816 | closest_feasible_2025_anchor_no_2027_observation |
| 2025.000 | current_law_revenue_linked | 100.000 | 100.000 | 100.000 | primary_specification |
| 2045.000 | current_law_revenue_linked | 128.509 | 118.382 | 92.119 | primary_specification |

## Data limits

The PNAD calculation is static and does not model take-up, behavioural responses, mortality, household re-formation, or private health spending. SIDRA 2026 observations end in September, so the annualised price comparison is a common-window rate rather than a calendar-2026 rate. The C1 health profile is a relative public-transfer-cost profile, not a clinical need measure. The requested literature file `docs/elderly_review.md` was unavailable at build time, so no literature result is restated here; it remains the designated review source when supplied.
