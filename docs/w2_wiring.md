# W2 Monte Carlo wiring

W2 adds two education GDP-level channels and four indicator-only outputs to the annual Monte Carlo. All scenario effects are differences from S0; S0 is exactly zero. Equal-sized increases and cuts use the same equations and opposite signed doses.

## Education

The existing C5 schooling channel remains unchanged and is not counted again. `education_capacity` applies a draw-level elasticity sampled uniformly from 0 to 0.04 to ED's signed log higher-education/IF capacity change, with a 15-year phase-in. `innovation_capacity` applies an elasticity sampled uniformly from 0 to 0.02 to ED's public-R&D perpetual-inventory stock (15% depreciation). Both parameters use the independent `[seed, 6]` stream, shared by every scenario in a draw. Their `*_contribution_pct` columns enter feedback-adjusted GDP and its debt path.

Education and R&D spending doses use each scenario's `efficiency_health_education_admin` package gap and ED's central COFOG allocation/service-loss assumptions. The CLI option `--education-sensitivity` selects `none`, the Flávio mid-case `half_record` or `record_repeat`, or the Lula rule-case `lula_half_recomposition` or `lula_record_recomposition`. These sensitivities use the exact scenario definitions in `config/ed_proposed.yaml` and do not affect S0-S5.

`employer_share_change_pp` is ED's fixed-composition indicator. `youth_homicide_rate_change_per_100k` applies half the magnitude of the descriptive state-panel schooling association and fixes its direction using the reviewed causal literature. Neither indicator feeds back to GDP.

## Firm distress

The annual real-rate deviation is the scenario's exposed C5 sovereign-risk premium minus S0's premium. Any I1 offset is common to all scenarios and therefore cancels. Firm NPL and exit-rate changes multiply this deviation by coefficients sampled from the independent `[seed, 7]` stream:

- NPL: normal mean 0.460, standard error `(0.664 - 0.256) / 3.92`.
- Exit rate: normal mean 0.713, standard error `(1.512 + 0.085) / 3.92`.

Both are associational indicators only and never feed back to GDP or debt. The exit-rate estimate is explicitly labelled imprecise because its confidence interval includes zero.

## Performance and reproducibility

Household indicators sort income once per table; the capped tax allocation solves its sorted breakpoints instead of performing 50 full-array bisection passes. C5 debt evaluation uses scenario NumPy arrays instead of repeated row-wise pandas lookups, and invariant S0 micro indicators are reused. The original implementations remain private numerical oracles for regression tests.

Before adding the new channels, the three-draw programme summary was written under the system temp directory and compared on all 24,000 existing rows. The maximum absolute p10/p50/p90 difference was 0 (required tolerance `1e-9`). The same-machine timings were 343.1 seconds before and 238.5 seconds after the performance-only changes. Progress is printed to stderr every 25 completed draws with elapsed time and ETA; it does not alter result files.
