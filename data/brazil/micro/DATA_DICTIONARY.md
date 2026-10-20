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
| `household_income_per_capita_brl` | `VD5002` | Official effective household per-capita income measure. Respect its exclusions (benefits in kind/tickets and income of lodgers, domestic workers and their relatives); retain edition/reference period. |
| `retirement_pension_income_brl` | `V5004A2` | Amount from retirement/pension source in annual all-sources visit layout; verify edition-specific names and reference period. |
| `bpc_income_brl` | `V5001A2` | Amount from BPC/LOAS source in annual all-sources visit layout. |
| `bolsa_familia_income_brl` | `V5002A2` | Amount from Bolsa Família/Auxílio Brasil source in annual all-sources visit layout. |
| `other_program_income_brl` | `V5003A2` | Amount from other government social programs; keep distinct from BPC and Bolsa Família. |
| `household_size` | derived with temporary household grouping | Number of resident person records in each dwelling, computed internally and exported as a count only. Grouping key is dropped before output. |
| `survey_weight` | `V1028` | Expansion weight; check interview/annual release layout. |

The official 2025 visit-1 dictionary/input layout and IBGE derived-variable documentation have been downloaded. `VD5002` is identified in IBGE's derived-variable documentation as effective household per-capita income. The source-income codes shown are candidate codes from the all-sources annual layout and still require transcription against the official dictionary before a year-specific mapping is approved. Retain source visit and reference period; do not combine first- and fifth-visit records without an explicit survey design decision. Use temporary household grouping only to calculate household size or a separately requested derived value, not to replace the official per-capita measure.

## POF 2017–2018 (resident, household/unit-of-consumption and income tables)

The POF is distributed as multiple linked files with distinct record levels. The loader must process them as separate table exports; do not flatten or join them until the official reading programs and key structure are reviewed.

| Canonical field | Source field | Meaning / handling |
|---|---|---|
| `year` | survey metadata | Reference period 2017–2018; preserve file/table reference period. |
| `state_code` | resident table residence field | Federative unit code; exact variable name must be transcribed from the downloaded official POF dictionary before mapping approval. |
| `urban_rural` | resident table residence field | Residence situation; exact variable name must be transcribed from official dictionary. |
| `sex`, `age`, `education_level` | resident table | Demographic fields; exact variable names must be transcribed from official dictionary. |
| `household_income_brl` | corrected derived `renda_total` | Household/unit-of-consumption income; preserve the corrected derived field and its reference period. |
| `household_income_per_capita_brl` | documented total divided by unit size, or official field | Use official derived field where available; otherwise derive only from documented income and roster definitions. |
| `consumption_expenditure_brl` | expenditure-table value | Preserve table's expenditure reference period and monetary unit. |
| `survey_weight` | official unit/person weight | Keep table-level weight and sampling design metadata; exact variable is record-level specific. |

**Internal-only grouping:** household, dwelling, unit-of-consumption and person keys may be read temporarily from official layouts to calculate household size or per-capita measures, but must be dropped before the analysis export. The exact POF key structure and all POF variable codes remain unapproved until transcribed and checked against the downloaded official POF dictionary and reading programs. No POF microdata download is authorized by this dictionary.

## Fields excluded from all exports

Names, CPF/CNPJ, addresses, phone numbers, email addresses, direct person/household identifiers, and raw free-text responses. The loader rejects identifier-like mapped fields and keeps only explicitly mapped columns.
