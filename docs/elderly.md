# E3 older-people analysis method

`python -m src.elderly` deterministically rebuilds the four E3 CSVs, the evidence report, and this method note from local files only.

## Income

The PNAD input is restricted to income-unit conditions other than 17-19. Survey weights are constant within an income unit. Age groups are 0-14, 15-29, 30-64 and 65+. National income deciles are assigned from household per-capita income using person-weighted rank midpoints. Detailed individual receipts are summed within the income unit and divided by its eligible member count before composition is measured. Counterfactual income removes observed pension and BPC receipts without replacing them or allowing negative income.

## Microsimulation

Prepared microdata retain age. Simulated household rows contain member counts aged 0-14 and 65+, plus the count living in an income unit containing a pension/BPC recipient aged 65+. `calculate_indicators` applies household post-simulation income to those person-count denominators. With `bpc_follows_pension_indexation=True`, the pension/indexation fiscal amount is allocated over pension and BPC income. In the indexation-floor variant, pension exposure is capped at one minimum wage while all BPC income is exposed. Negative fiscal gaps work symmetrically.

## Indexation and prices

The indexation table compounds fixed real gains from 2025. Price rates compound every archived monthly change from January 2012 through the shared last month and annualise by the exact number of months. Real benefit change is `(1 + INPC)/(1 + comparison deflator) - 1`. No expenditure weights are present in the archived SIDRA extracts; consequently the double-health-weight and plan-status rows are clearly labelled exposure proxies, with an equal-item non-holder row reported only as robustness.

## SUS

The denominator is the sum over age of IBGE population times the C1 2018 relative health-cost profile. Results remain at C1's observed five-year horizons; no year is interpolated. Real GDP is GDP per capita times population, using the sourced 2025 parameter and S0 macro output thereafter. S0 health spending is its GDP share times real GDP; the revenue-linked path grows with GDP at a fixed 2025 share. The constant-real proxy holds the 2025 real level because an exact 2027 anchor is absent.

## Reproduction and limitations

Raw downloads are read-only. Monetary microsimulation inputs come from `config/c3_inputs_proposed.yaml`; the sourced 2025 GDP-per-capita anchor comes from `config/parameters.yaml`. Outputs are deterministic CSV/Markdown files. The literature synthesis is designated to `docs/elderly_review.md`; if that file is absent, the report states the gap rather than inventing a review.
