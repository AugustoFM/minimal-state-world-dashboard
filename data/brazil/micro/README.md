# Household microdata intake (A3)

PNAD Contínua 2025 (annual visit 1) is downloaded, mapped and validated; POF 2017-2018 codes are transcribed but its microdata is not downloaded yet. Raw microdata and person-level exports are git-ignored; only mappings and aggregate validation are versioned.

## Pipeline (run from repo root)

```
python scripts/read_ibge_fwf.py data/raw/brazil/microdata/PNADC_2025_visita1_20260923.zip data/raw/brazil/layouts/pnadc_2025_visita1_input.txt data/processed/brazil/microdata/pnadc_2025_visita1_selected.csv --mapping data/brazil/micro/mappings/pnadc_2025_visita1.json
python scripts/load_brazil_microdata.py pnadc data/processed/brazil/microdata/pnadc_2025_visita1_selected.csv data/brazil/micro/mappings/pnadc_2025_visita1.json data/processed/brazil/microdata/pnadc_2025_visita1_canonical.csv
python scripts/validate_brazil_microdata.py
```

Download the zip first from the IBGE FTP (URL and SHA-256 in `data/raw/SOURCES.md`) into `data/raw/brazil/microdata/`. Validation (2025): Gini of household per-capita income 0.5112 vs IBGE published 0.511; weighted population within 0.35% of the IBGE projection.

## Sources

- [PNAD Contínua annual microdata and documentation](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/)
- [POF 2017–2018 microdata, documentation, questionnaires and official reading programs](https://www.ibge.gov.br/estatisticas/multidominio/condicoes-de-vida-desigualdade-e-pobreza/24786-pesquisa-de-orcamentos-familiares-2.html)
- [PNAD Contínua derived-variable definitions](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Visita/Documentacao_Geral/Definicao_variaveis_derivadas_PNADC_20200211.pdf)
- [PNAD Contínua annual income deflator documentation](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Visita/Documentacao_Geral/PNADcIBGE_Deflator_Anual_Visita.pdf)

## Loader contract

Use `scripts/load_brazil_microdata.py` after generating an export with the matching official IBGE reading layout/program. The loader accepts CSV or Parquet, requires a reviewed JSON mapping, retains only mapped fields, and rejects identifier-like columns. It does not unpack fixed-width data or download files. Preserve raw downloads separately under `data/raw/brazil/` only after variable mappings are approved.

Example mapping format:

```json
{
  "dataset": "pnadc",
  "columns": {
    "UF": "state_code",
    "V1028": "survey_weight",
    "V2009": "age",
    "VD4019": "labor_income_nominal_brl"
  },
  "household_key_columns": ["<official household key field(s)>"]
}
```

This is illustrative, not an approved map. `household_key_columns` are temporary calculation inputs: the loader uses them to compute `household_size` and never exports them. Add those fields only after the official year-specific layout is reviewed. Never map sample IDs, direct personal identifiers, or names/contact fields into the analysis output. Full microdata remains excluded from git and is not downloaded until the source mappings are agreed.
