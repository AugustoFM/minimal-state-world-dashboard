# A3 dictionary (PNAD mapping approved and validated 2026-10-20)

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
| `household_income_per_capita_brl` | `VD5008` | Household per-capita income, habitual from all jobs + effective from other sources (excludes pensionistas, domestic workers and their relatives). **This is the concept of IBGE's published Gini** (SIDRA 7435): computed 0.5112 vs published 0.511 for 2025. `VD5002` (all effective) gives 0.5226 and is not used. |
| `retirement_pension_income_brl` | `V5004A2` | Amount from retirement/pension source in annual all-sources visit layout; verify edition-specific names and reference period. |
| `bpc_income_brl` | `V5001A2` | Amount from BPC/LOAS source in annual all-sources visit layout. |
| `bolsa_familia_income_brl` | `V5002A2` | Amount from Bolsa Família/Auxílio Brasil source in annual all-sources visit layout. |
| `other_program_income_brl` | `V5003A2` | Amount from other government social programs; keep distinct from BPC and Bolsa Família. |
| `household_size` | `V2001` | Official number of persons in the household; no household keys are read. |
| `household_condition` | `V2005` | Condition in the household (17-19 = pensionista, domestic worker, relative of domestic worker; excluded from per-capita income). |
| `household_income_brl` | `VD5007` | Household income (habitual work + effective other sources). |
| `other_sources_income_brl` | `VD4048` | Effective income from all non-work sources. |
| `unemployment_insurance_income_brl` | `V5005A2` | Unemployment insurance / seguro-defeso. |
| `private_transfer_income_brl` | `V5006A2` | Alimony, donations, allowances from non-residents. |
| `rent_income_brl` | `V5007A2` | Rent or lease income. |
| `financial_and_other_income_brl` | `V5008A2` | Scholarships, savings and financial income, other. |
| `survey_weight` | `V1032` | Annual visit-1 weight with calibration. (`V1028` is the quarterly-file weight and does not exist in the annual visit file.) |

Approved mapping: `mappings/pnadc_2025_visita1.json`. Source-income codes V5001A2-V5008A2 checked against the question texts in the official 2025 dictionary (V5001 BPC, V5002 Auxilio Brasil/Bolsa Familia, V5003 other government programs, V5004 public and private pensions, V5005 unemployment insurance, V5006 private transfers, V5007 rent, V5008 financial/other). Validation: `validation_pnadc_2025.csv`. The official 2025 visit-1 dictionary/input layout and IBGE derived-variable documentation have been downloaded. `VD5002` is identified in IBGE's derived-variable documentation as effective household per-capita income. The source-income codes shown are candidate codes from the all-sources annual layout and still require transcription against the official dictionary before a year-specific mapping is approved. Retain source visit and reference period; do not combine first- and fifth-visit records without an explicit survey design decision. Use temporary household grouping only to calculate household size or a separately requested derived value, not to replace the official per-capita measure.

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

Transcribed codes (approved mapping `mappings/pof_2017_2018_morador.json`): Morador table `UF`, `TIPO_SITUACAO_REG`, `V0403` (age), `V0404` (sex), `NIVEL_INSTRUCAO`, `ANOS_ESTUDO`, `PESO_FINAL`, `RENDA_TOTAL` (UC gross monthly income); keys `COD_UPA`, `NUM_DOM`, `NUM_UC`, `COD_INFORMANTE`. Income tables: `V9001` (income type, see Cadastro de Produtos), `V8500` and `V8500_DEFLA`. POF microdata still not downloaded.

**Internal-only grouping:** household, dwelling, unit-of-consumption and person keys may be read temporarily from official layouts to calculate household size or per-capita measures, but must be dropped before the analysis export. The exact POF key structure and all POF variable codes remain unapproved until transcribed and checked against the downloaded official POF dictionary and reading programs. No POF microdata download is authorized by this dictionary.

## Fields excluded from all exports

Names, CPF/CNPJ, addresses, phone numbers, email addresses, direct person/household identifiers, and raw free-text responses. The loader rejects identifier-like mapped fields and keeps only explicitly mapped columns.

## Tax-return centiles (Receita Federal, calendar year 2024)

`tax_centiles_2024.csv` (built by `scripts/build_brazil_tax_centiles.py` from `data/raw/brazil/tax/centis-br-ac2024.xlsx`): one row per table (I-XI, each ranking declarants by a different income concept) and published row; one column per published field, values in R$ exactly as published.

- Rows overlap: 1-100 are centiles of declarants (row 100 = whole top 1%), 101-110 split the top 1% into tenths, 111-120 split the top 0.1% into tenths. Use `partition == True` (rows 1-99, 101-109, 111-120) to sum without double counting; `p_low`/`p_high` give each row's bounds in % of declarants.
- Broadest income concept: Table V, RB4 = taxable + exempt (incl. dividends) + exclusively taxed income, minus inheritances and gifts. 2024 total RB4 R$ 5,839.7 bn over 41.68 m declarants.
- Shares are among **declarants**, not adults: top 1% of declarants hold 25.1% of declarants' RB4, top 0.1% 13.1%. Converting to adult-population top shares needs an external income total (national accounts) and adult population; that is a C3 method choice, not done here.
