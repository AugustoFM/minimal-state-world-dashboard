# Household microdata intake (A3)

This directory contains the proposed ingestion contract and variable list only. Full PNAD Contínua and POF microdata have **not** been downloaded. That download is deferred until the source-to-canonical variable mapping in `DATA_DICTIONARY.md` is agreed.

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
  }
}
```

This is illustrative, not an approved map. Never map sample IDs, direct personal identifiers, or names/contact fields into the analysis output.
