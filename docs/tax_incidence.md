# Tax incidence by instrument

## Method

The C3 microsimulation allocates a revenue change by tax instrument when a scenario supplies
`revenue_by_instrument_by_year`. A positive change is a household burden and a negative change is a
credit. The allocation score for an instrument is identical in both directions. Positive changes use
the existing capacity cap, so no household is assigned a burden larger than its simulated income;
negative changes do not require a cap. Instrument amounts are in percentage points of annual nominal
GDP and are converted to monthly survey totals before allocation.

If the instrument mapping is absent (`None`), the previous `tax_variant` calculation is used without
change. This keeps S0 and S1-S5 on their existing path. The Monte Carlo option
`--tax-incidence uniform` also uses that previous rule for every programme revenue change;
`--tax-incidence instrument` is the default. The selection is recorded in run metadata. Tax changes
continue to enter the macro block only through their summed `revenue_by_year` path.

| Instrument | Household allocation base | Interpretation |
|---|---|---|
| `top_income` | Household income above the person-weighted PNAD top-1% per-capita threshold | Entire allocation is within the top 1%; the score is income above the threshold. |
| `consumption` | Household size times per-capita income to the power 0.8 | Existing consumption-like proxy. |
| `fuel_energy` | Same as `consumption` | No POF energy budget shares are available in the repository. |
| `payroll` | Labour income of persons coded employed | Burden or credit is allocated to wages. |
| `tax_expenditures` | Total household income | Mixed beneficiaries are represented by the existing proportional rule. |
| `business_capital` | Same as `top_income` | Proxy for capital ownership; incidence is contested. |

## Assumptions and bases

Every assumed number used by this change is listed here. Source-derived monetary inputs remain in
`config/c3_inputs_proposed.yaml`.

| Assumed number | Use | Basis |
|---:|---|---|
| 1% | Threshold population for `top_income` and `business_capital` | Task specification; the threshold is calculated with PNAD person weights. |
| 0.8 | Consumption-like exponent | Existing C3 default in `config/c3_inputs_proposed.yaml`; retained for comparability, not an estimated budget share. |
| 50% / 50% | Revenue-up split: `top_income` / `tax_expenditures` | Equal split of the two stated instruments because no amounts are stated; stored once in `config/programs_2026.yaml`. |
| 40% / 20% / 30% / 10% | Revenue-down split: `consumption` / `fuel_energy` / `payroll` / `business_capital` | Modelling assumption across the four stated instruments (VAT; fuel and energy; payroll; export and investment exemptions) because no amounts are stated; stored once in `config/programs_2026.yaml`. |
| 100% | Payroll incidence assigned to workers | Prepared PNAD has labour income and employment status but no usable formal/informal or employer/worker incidence split. |
| 0.1 pp GDP | Size of each rise and cut in the diagnostic report | Stylised common shock chosen to compare instrument allocation, not a programme result or forecast. |
| R$218/month | First diagnostic poverty line | Statutory Bolsa Família line, Law 14,601/2023; value and source are in `config/c3_inputs_proposed.yaml`. |
| R$759/month | Second diagnostic poverty line | Half the 2025 statutory minimum wage; value and source are in `config/c3_inputs_proposed.yaml`. |

## Poverty measurement at a mass point

The lead's PNAD 2025 check, after excluding household conditions 17-19 as in C3, finds that 1.60% of
persons have per-capita household income exactly R$759.00. The share is 2.86% among people aged 65
or older. A common case is a two-person household supported by one minimum-wage benefit or wage:
R$1,518 divided by two is exactly the R$759 poverty line. There is no corresponding mass point at
the R$218 line.

The retained raw headcount uses the strict test `income < line`. It is useful as a diagnostic, but at
R$759 it is discontinuous: an arbitrarily small simulated loss moves the full mass at the line into
poverty. In the stylised consumption-tax rise, a change of 0.1 pp GDP (about R$5 per person per
month) consequently raises the raw R$759 headcount by about 1.7 percentage points. That jump is a
feature of a static survey distribution and its exact statutory mass point; it must not be read as a
welfare loss of that magnitude.

Two continuous or damped measures are therefore the headline R$759 measures:

- **Smoothed headcount:** the arithmetic mean of 21 strict headcounts evaluated at equally spaced
  lines from 0.95 to 1.05 times the stated line. A small income change moves only a proportional
  fraction of the mass point through this grid.
- **Poverty gap (FGT1):** the person-weighted mean of
  `max((line - income) / line, 0)`, reported as a percentage of the line. It changes continuously
  with the size of a shortfall. FGT2 is the mean squared normalised shortfall and is also retained.

The same definitions are applied to every scenario and tax instrument, for all persons, ages 0-14,
ages 65+, and people living with a 65+ pension/BPC recipient. Smoothing is a robustness measure, not
an alteration of the statutory line or an interpolation of household incomes.

## Limitations

- The calculation is static and has no behavioural, price, labour-supply, avoidance, evasion or general-equilibrium response.
- PNAD under-reports top and capital incomes. The PNAD top-1% income share is therefore shown beside the existing IRPF 2024 share in the diagnostic report. The IRPF figure is among declarants, not the whole population, so it is contextual rather than a like-for-like correction.
- The consumption-like score is an income-based proxy. No POF consumption or energy budget shares are present in the repository, so `fuel_energy` cannot reflect household-specific energy spending.
- Payroll incidence is placed fully on workers. The prepared file does not support a formal/informal split and the model does not divide incidence between employers and workers.
- `tax_expenditures` combines heterogeneous measures without measure-level beneficiaries.
- Allocating `business_capital` to the top-income base is contestable and does not identify shareholders, exporters or investors directly.
- Raw poverty headcounts are discontinuous at the lines. Equal-sized symmetric cash changes can therefore produce asymmetric measured changes even though the allocation rule itself is symmetric; at R$759 the smoothed headcount and FGT1 are the headline measures.
