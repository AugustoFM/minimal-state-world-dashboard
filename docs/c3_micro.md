# C3 household microsimulation

## Scope and interface

`src/micro.py` is a static, arithmetic microsimulation of the 2025 PNAD
Contínua visit-1 cross-section. It takes a person table plus one C2
scenario-year's GDP-level gap, unemployment change, package gaps and revenue
change. `simulate_household_incomes` returns one row per IBGE income unit;
`calculate_indicators` returns the Gini, two poverty headcounts and survey top
1%/10% shares. Every behavioural setting is an argument. `prepare_microdata`
does the invariant validation/grouping once so D1 can reuse arrays across
draws without changing results.

The CLI reads only central C2 rows and writes aggregate results:

```text
python -m src.micro
```

Output is `data/brazil/micro.csv`, with year, horizon, scenario, C2
persistence, composition, pension, labour and tax variants, indicator and
value. It contains no person records. S1 is deliberately omitted: C1/C2 give
its aggregate offset to ageing but neither CLI input assigns that offset to a
package, so imposing household incidence would invent a composition.

## Income-unit identity

The model preserves official `VD5008` as the no-change income identity. For
each household it starts from `VD5008 * income-unit size`, sums modeled changes
over eligible members, then divides by the same size. Conditions 17--19
(pensionistas, domestic workers and their relatives) are excluded from both
the sum and denominator, matching the IBGE concept. Survey weights are constant
within household. Distribution statistics use household weight times eligible
income-unit size; the separately reported survey population includes every
person record.

This avoids pretending that the selected source components exhaust VD5008.
Missing source amounts mean zero receipts of that source; no missing official
per-capita income is accepted for an eligible person.

## Mechanisms and lead-developer choices

All five rules below are choices, not estimates.

1. **Pensions.** A gap of `g` percentage points of GDP is an annual aggregate
   cut `g/100 * nominal GDP`. The proportional variant allocates it in
   proportion to each pension. The `indexation_floor` variant allocates in
   proportion to `min(pension, R$1,518)`: benefits at/below the minimum wage
   bear the full common rate on their benefit, while a higher pension bears the
   same absolute charge as a minimum-wage pension and therefore a smaller
   proportional cut. The allocation reproduces the target weighted BRL total;
   an infeasible cut fails instead of clipping silently.
2. **Means-tested transfers.** Bolsa Família and BPC are pooled and scaled
   proportionally. A positive gap cuts them and a negative gap increases them.
   This supports the future `compensating_transfers` D1 variant, although the
   deterministic CLI uses the default package because the checked-in C2 macro
   file is itself the default composition.
3. **Labour income.** `gdp_only` multiplies every positive labour income by
   `1 + gdp_level_vs_s0_pct/100`. The `employment` variant also draws persons
   with seed 20261020: a positive unemployment change randomly removes enough
   survey-weighted employed persons to approximate the implied labour-force
   share and sets their post-GDP labour income to zero. A negative change draws
   unemployed persons and gives them the weighted median positive labour
   income of their education level (the overall median if their level has no
   employed observations). Whole sampled people move, so the weighted target
   is approximate at the last record.
4. **Taxes.** A positive revenue change is converted from annual GDP points to
   a monthly survey total. `proportional` allocates by post-policy household
   income. `consumption_like` allocates by `household size * per-capita
   income^0.8`; exponent 0.8 is an assumption until POF incidence is wired.
   The tax cannot make household income negative: a water-filling allocation
   caps liability at income and reallocates the remainder while preserving the
   aggregate target. A zero revenue change is an exact no-op under both rules.
5. **Other packages.** Subsidies/tax expenditures, efficiency, other current
   spending and public investment have no direct household cash entry. Their
   only C3 effect is through the C2 GDP/unemployment inputs.

The deterministic model applies future scenario gaps to the 2025 cross-section
using 2025 nominal GDP and nominal statutory poverty lines. It is a comparative
incidence exercise, not a forecast of nominal incomes, household composition or
poverty thresholds. C2's transitory and persistent GDP choices are both shown.

## Inputs and sources

`config/c3_inputs_proposed.yaml` holds the R$12,738,566 million 2025 nominal
GDP (IBGE SIDRA 1846), R$1,518 minimum wage, R$218 Bolsa Família eligibility
line (Law 14,601/2023) and R$759 half-minimum-wage line (Decree 12,342/2024 plus
arithmetic). URLs, dates and licences are also recorded in
`data/raw/SOURCES.md`. No monetary constant is hand-coded in the model or CLI.

Table V of `tax_centiles_2024.csv` is context only. Partition rows give top 1%
and top 10% RB4 shares of **25.068% and 52.195% among income-tax declarants,
not the population**. C3 does not splice these values to PNAD or construct a
corrected top-income series.

## Validation

No-change results from the prepared file are:

| Check | Result | Target / treatment |
|---|---:|---|
| Gini | 0.511190 | 0.5112 ± 0.0005; IBGE published 0.511 |
| All-record weighted population | 212.683 million | 212.7 million |
| Eligible income-unit population | 212.624 million | conditions 17--19 excluded |
| Weighted household count | 79.305 million | 79.3 million lead-developer calculation |
| Poverty below R$218 | 3.181% | reported; no offline SIDRA poverty table found |
| Poverty below R$759 | 23.055% | reported; no offline SIDRA poverty table found |
| Survey top 1% share | 11.021% | survey-only |
| Survey top 10% share | 40.266% | survey-only |

Toy tests establish Gini zero for equal incomes and `(n-1)/n` when one of `n`
equally weighted people owns all income. They also establish that a pension
cut changes pensioner households only, a means-tested increase reduces R$218
poverty, excluded conditions stay outside the income unit, and zero tax is an
exact no-op.

Median runtime for a prepared R_amb-like scenario-year, including all
indicators, is **0.077 seconds** (five runs on this worktree). The complete CLI
Cartesian output takes about 65 seconds.

## Ten-year central results versus S0

The table gives the minimum--maximum over all eight combinations of pension
(`proportional`, `indexation_floor`), labour (`gdp_only`, `employment`) and tax
(`proportional`, `consumption_like`) variants. Tax variants coincide when the
revenue change is zero. Gini and poverty entries are changes from S0 in points;
top shares are scenario levels in percent. Exact values for every named
combination are in `data/brazil/micro.csv`.

| C2 persistence | Scenario | Δ Gini points | Δ poverty R$218 pp | Δ poverty R$759 pp | Top 1% share | Top 10% share |
|---|---|---:|---:|---:|---:|---:|
| transitory | R_mod | +0.045 to +0.479 | +0.006 to +0.040 | +1.750 to +2.060 | 11.089 to 11.191 | 40.366 to 40.738 |
| transitory | R_amb | +0.152 to +1.110 | +0.025 to +0.108 | +2.222 to +3.052 | 11.173 to 11.373 | 40.514 to 41.249 |
| transitory | E_mod | -0.356 to +0.013 | -0.026 to -0.001 | -0.629 to -0.442 | 10.856 to 10.976 | 39.817 to 40.192 |
| transitory | E_mod_tax | -0.351 to +0.446 | +0.166 to +0.357 | +1.328 to +2.383 | 10.857 to 11.144 | 39.819 to 40.558 |
| persistent | R_mod | -0.002 to +0.502 | +0.015 to +0.133 | +2.047 to +2.525 | 11.086 to 11.201 | 40.344 to 40.763 |
| persistent | R_amb | +0.042 to +1.134 | +0.053 to +0.282 | +2.795 to +3.947 | 11.165 to 11.414 | 40.459 to 41.311 |
| persistent | E_mod | -0.405 to +0.044 | -0.122 to -0.032 | -1.560 to -1.210 | 10.841 to 10.975 | 39.786 to 40.208 |
| persistent | E_mod_tax | -0.371 to +0.457 | +0.145 to +0.357 | +1.165 to +1.915 | 10.850 to 11.143 | 39.806 to 40.563 |

These are deterministic central paths and sensitivity variants, not forecasts
or probability ranges. D1 must pass draws through the public arguments before
distributional p10/p50/p90 results can be published.

## Ball et al. cross-check and limitations

At year 8, central R_amb is a 3.2 pp GDP package. C3 raises the Gini under every
pension/labour combination: **+0.096 to +0.841 points** with transitory C2 and
**+0.018 to +0.865 points** with persistent C2. The direction agrees with Ball
et al. (2013), where an approximately 1% GDP consolidation raises the Gini by
about 0.9 points at year 8. Magnitudes are not a calibration target: Ball uses
OECD consolidation episodes, while C3 mechanically maps Brazil's PNAD cash
components and C2 labour effects.

PNAD under-captures top incomes; top shares are therefore labelled survey-only.
The tax base is assumed to be household income rather than a named tax. There
is no labour-supply, take-up, informal-sector, price, demographic or general-
equilibrium response beyond C2. Poverty comparisons use fixed nominal lines.
POF tax/consumption incidence and a method for combining survey and tax data
remain reserved for later review.
