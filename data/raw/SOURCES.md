# Raw data sources
- worldbank_long.csv: World Bank WDI API (scripts/fetch_worldbank.py), downloaded 2026-10-20. Licence CC BY 4.0.
- efotw-2026-master-index-data-for-researchers-iso.xlsx: Fraser Institute, Economic Freedom of the World 2026 (data year 2024).
- heritage-index-of-economic-freedom-2026-*.csv: Heritage Foundation, 2026 Index of Economic Freedom.
- hdr-data.json: UNDP Human Development Report data centre (HDI components, 1990-latest).
- ubs_gwr2026_extracted.csv: hand-extracted from the UBS Global Wealth Report 2026 PDF. Only ~34 countries are listed in the report (millionaires, mean wealth per adult for the top 30, wealth Gini for top ~32). Not a full-world series.
- FIW2026 PDF (Freedom House): narrative report only; no country score table, so not used. Civil rights come from World Bank WGI Voice & Accountability (see fetch script) until the Freedom House country scores Excel is added.
- freedom_house_country_scores.xlsx: Freedom House, Country and Territory Ratings and Statuses. Latest column = Freedom in the World 2025 edition (year under review 2024). PR and CL are 1-7 (1 = freest); the dashboard's "rights index" is derived: ((7-PR)+(7-CL))/12*100.
- World Bank WGI (Voice & Accountability, Rule of Law): fetched via GOV_WGI_* codes in scripts/fetch_worldbank.py.
# Brazil scenario inputs

| File | Source URL | Retrieved | Licence / terms | Notes |
|---|---|---:|---|---|
| `brazil/demonstrativos-governo-geral.xlsx` | [Tesouro Nacional: Estatísticas Fiscais do Governo Geral](https://www.tesourotransparente.gov.br/publicacoes/estatisticas-fiscais-do-governo-geral/2021/22) (download: `https://cdn.tesouro.gov.br/sistemas-internos/apex/producao/sistemas/thot/arquivos/publicacoes/40185_2097592/demonstrativos-governo-geral.xlsx`) | 2026-10-20 | Tesouro site states CC BY-ND 3.0; verify dataset-specific terms before redistribution | Untouched workbook downloaded from official source. Tables 1.2 and 1.2.a provide quarterly general-government operations and % GDP from 2010. |
