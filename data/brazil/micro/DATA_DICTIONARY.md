# Proposed A3 dictionary for review

This is the source-variable shortlist for discussion before any full microdata download. Keep nominal/real amounts and their reference years explicit. The loader only writes variables listed in an approved JSON mapping.

## PNAD Contínua (annual person records; income and labor)

| Canonical field | Candidate IBGE variable | Meaning / handling |
|---|---|---|
| `year` | file reference year | Keep the observation year from the file name/metadata. |
| `state_code` | `UF` | Federative unit code; retain source code, do not convert to country ISO3. |
| `urban_rural` | `V1022` | Urban/rural situation. |
| `sex` | `V2007` | Sex category as coded by IBGE. |
| `age` | `V2009` | Age in years. |
| `education_level` | `VD3004` | Highest completed level; verify edition-specific layout. |
| `labor_force_status` | `VD4001` | Labor-force status; verify edition-specific layout. |
| `employment_status` | `VD4002` | Employment status; verify edition-specific layout. |
| `labor_income_nominal_brl` | `VD4019` | Habitual earnings from all jobs, age 14+; nominal BRL and reference year. |
| `labor_income_real_brl` | `VD4019` × official annual deflator | Derive only with matching official deflator and documented price base; keep nominal field too. |
| `survey_weight` | `V1028` | Expansion weight; check interview/annual release layout. |

Candidate earnings definitions are supported by the IBGE derived-variable and deflator documentation linked in `README.md`. Confirm all candidate codes against the exact year-specific reading program before approving the mapping. Do not combine first- and fifth-visit records without an explicit survey design decision.

## POF 2017–2018 (resident, household/unit-of-consumption and income tables)

The POF is distributed as multiple linked files with distinct record levels. The loader must process them as separate table exports; do not flatten or join them until the official reading programs and key structure are reviewed.

| Canonical field | Source field | Meaning / handling |
|---|---|---|
| `year` | survey metadata | Reference period 2017–2018; preserve file/table reference period. |
| `state_code` | official residence field | Federative unit code; confirm source field in the official layout. |
| `urban_rural` | official residence field | Residence situation; confirm source field in the official layout. |
| `sex` | resident table | Sex category as coded by IBGE; confirm source field in the official layout. |
| `age` | resident table | Age in years; confirm source field in the official layout. |
| `education_level` | resident table | Education; confirm source field and categories in the official layout. |
| `household_income_brl` | derived `renda_total` or documented income components | Household/unit-of-consumption total income; respect IBGE's corrected derived variable and record reference period. |
| `household_income_per_capita_brl` | documented total divided by unit size, or official field | Use official derived variable where available; otherwise derive only from documented income and roster definitions. |
| `consumption_expenditure_brl` | expenditure-table value | Preserve table's expenditure reference period and monetary unit. |
| `survey_weight` | official unit/person weight | Keep table-level weight and sampling design metadata; confirm exact field by record level. |

**Not in the initial loader contract:** sample cluster, dwelling, household, unit-of-consumption or person keys. They are not person names or direct identifiers, but they can enable record linkage; keep them out of the analysis export unless an agreed research design requires a controlled, non-public intermediate.

## Fields excluded from all exports

Names, CPF/CNPJ, addresses, phone numbers, email addresses, direct person/household identifiers, and raw free-text responses. The loader rejects identifier-like mapped fields and keeps only explicitly mapped columns.
