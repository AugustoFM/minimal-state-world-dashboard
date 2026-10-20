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
| `brazil/ibge_projecoes_2024_tab1_idade_simples.xlsx` | [IBGE FTP directory](https://ftp.ibge.gov.br/Projecao_da_Populacao/Projecao_da_Populacao_2024/) (`projecoes_2024_tab1_idade_simples.xlsx`) | 2026-10-20 | Public download; no explicit licence found in FTP directory | Untouched workbook; population by sex and single age, 2000–2070, Brazil and federative units. UN WPP cross-check not yet included. |
| `brazil/worldbank_country_metadata.json` | [World Bank Countries API](https://api.worldbank.org/v2/country?format=json&per_page=400) | 2026-10-20 | CC BY 4.0, consistent with World Bank open data terms | Untouched response used to select current lower-middle and upper-middle income country ISO3 codes; aggregate entries excluded. |
| `brazil/worldbank_expense_1990_2025.json` | [World Bank WDI API, `GC.XPN.TOTL.GD.ZS`, 1990–2025](https://api.worldbank.org/v2/country/all/indicator/GC.XPN.TOTL.GD.ZS?date=1990%3A2025&per_page=20000&format=json) | 2026-10-20 (API data last updated 2026-10-08) | CC BY 4.0 | Untouched API response, refetched for A4 episode windows. This is central-government expense (% GDP), not general-government spending. Exact observed endpoint pairs only. |
| `brazil/layouts/pnadc_2025_visita1_dictionary.xls`, `pnadc_2025_visita1_input.txt` | [IBGE PNAD Contínua annual visit-1 documentation directory](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Visita/Visita_1/Documentacao/) | 2026-10-20 | Official public download; no explicit licence located | Layout files only; no microdata downloaded. |
| `brazil/layouts/pof_2017_2018_documentation.zip`, `pof_2017_2018_reading_programs.zip` | [IBGE POF 2017–2018 microdata directory](https://ftp.ibge.gov.br/Orcamentos_Familiares/Pesquisa_de_Orcamentos_Familiares_2017_2018/Microdados/) | 2026-10-20 | Official public download; no explicit licence located | Documentation and reading programs only; full microdata archive was not downloaded. Exact POF field mapping remains pending review of the dictionary. |
| `worldbank_long.csv` (`gov_expense_pct_gdp`) | [World Bank WDI API, `GC.XPN.TOTL.GD.ZS`](https://api.worldbank.org/v2/country/all/indicator/GC.XPN.TOTL.GD.ZS?format=json&per_page=20000) | 2026-10-20 | CC BY 4.0 | A4 fallback indicator is **central-government expense (% GDP), not general-government expenditure**. Exact endpoint values only; no interpolation. |
| `brazil/age_profiles/correa_2023_cadernos.pdf` | [Correa, Gutierrez and Turra (2023), Cadernos de Finanças Públicas](https://publicacoes.tesouro.gov.br/index.php/cadernos/article/download/202/210/833) | 2026-10-20 (downloaded by Claude) | Published by Tesouro Nacional; no explicit article licence located | Untouched PDF; SHA-256 `3578cfcdaccc13b20cd71917b0f491e7b440a49ef8646fabd029456b94847b2e`. Background and definitions for the NTA profiles. |
| `brazil/age_profiles/NTA_Brasil.xlsx` | [Authors' National Transfer Accounts repository](https://github.com/charlescodigos/National-Transfer-Accounts/raw/main/NTA_Brasil.xlsx) | 2026-10-20 (downloaded by Claude) | No repository licence found; workbook citation instructions name the associated 2025 article | Untouched workbook; SHA-256 `ec6500c680f7f36e0bc7ef26f629a4993d8f02b9fdb774ea1b0e7f6735750970`. Sheet `Per capita Normalized` supplies ages 0–90+ for 2003 and 2018. |
| `brazil/age_profiles/COFOG_GG_2024.xlsx` | [Tesouro Nacional COFOG 2024 annex](https://cdn.tesouro.gov.br/sistemas-internos/apex/producao/sistemas/thot/arquivos/publicacoes/53401_1725040/anexos/27169_866411/COFOG%20GG.xlsx) | 2026-10-20 (downloaded by Claude) | Tesouro portal states CC BY-ND 3.0; dataset-specific terms not verified | Untouched official workbook; SHA-256 `440403f80d408c383259032ac52612bbf7a0d765549d2ac0132d8b42bf3e507b`. Sheet `1.5.a` cells Q52, Q66, Q77 and Q78 supply the 2024 C1 shares. |

## B2 parameter sources (config/parameters.yaml)

Papers are cited, not stored; no files saved under `data/raw/`. "Verified" matches the `verified` field in the YAML.

| Paper | URL / DOI | Retrieved | Licence / terms | Verified | Used for |
|---|---|---|---|---|---|
| Sanches, Santos & Martins (2026), Estudos Econômicos 56(1) | [SciELO](https://www.scielo.br/j/ee/a/pjHsgbX5bB3Zms7hxsK6txg/?lang=en), DOI 10.1590/1980-53575612mhg | 2026-10-20 | SciELO open access (CC BY) | full text, Tables 2, C1, D1, E1, F1; footnote 7 | `fiscal_multipliers_brazil` |
| Ball, Furceri, Leigh & Loungani (2013), IMF WP 13/151 | [IMF PDF](https://www.imf.org/external/pubs/ft/wp/2013/wp13151.pdf) | 2026-10-20 | IMF copyright; free to read | full text, section IV, Figures 5-6 | `consolidation_gini_effect` |
| Szklo, Clarke & Rocha (2024), IZA DP 16829 | [IZA PDF](https://docs.iza.org/dp16829.pdf) | 2026-10-20 | IZA DP; free to read | full text, Table B.2, section 5.2.3 | `social_outcome_elasticities.infant_mortality_*` |
| Arnold (2022), AEJ: Applied 14(4) | [AEA](https://www.aeaweb.org/doi/10.1257/app.20190428) | 2026-10-20 | AEA copyright | abstract (+ 2019 Princeton WP abstract) | `privatisation_wage_effects` |
| Gallet & Doucouliagos (2017), Soc Sci Med 179 | [RePEc](https://ideas.repec.org/a/eee/socmed/v179y2017icp9-17.html) | 2026-10-20 | Elsevier copyright | abstract | `social_outcome_elasticities.life_expectancy_*`, `mortality_*_meta` |
| IMF Western Hemisphere REO, May 2018, ch. 4 | [IMF](https://www.imf.org/-/media/files/publications/reo/whd/2018/may/wreo0518-chp4.pdf.md) | 2026-10-20 | IMF copyright; free to read | abstract/summary | `fiscal_multipliers_lac_benchmark` |
| Alesina, Favero & Giavazzi (2018), NBER WP 24246; Asimakopoulos & Karavias (2015); Tourinho & Brum (2020); Cuevas et al. (2017), IMF WP 17/99; Freitas & Paes (2023); Higgins & Pereira (2013), CEQ WP 7; Souza & Medeiros (2015); Gagliardi, Marinho & de Paula (2023) | see Claude Doc literature review | 2026-10-20 | various | secondary (literature review, not re-checked) | context and cross-check entries |

## B1 calibration sources

| File | Source URL | Retrieved | Licence / terms | Notes |
|---|---|---|---|---|
| `brazil/b1/raf101_jun2025.pdf` | [IFI, Relatório de Acompanhamento Fiscal nº 101, June 2025](https://www12.senado.leg.br/ifi/pdf/raf101_jun2025.pdf) | 2026-10-20 (Claude) | Senado Federal / IFI publication; free reuse with citation | Untouched PDF; SHA-256 `d4c205df012d5f1b61351ef3f1c6b1f3a7a0a890c47cc44f2e07e33b975dc76f`. Table 6: federal discretionary spending R$ 183.7 bn = 1.6% of GDP, 8.4% of federal primary spending (2024 realised). |
| `brazil/b1/ifi_raf103_ago2025.pdf` | [IFI, Relatório de Acompanhamento Fiscal nº 103, August 2025](https://static.poder360.com.br/2025/08/IFI-relatorio-acompanhamento-fiscal-ago-2025.pdf) (mirror; original on senado.leg.br/ifi) | 2026-10-20 (Claude) | Senado Federal / IFI publication; free reuse with citation | Untouched PDF; SHA-256 `4dadf93052521c5dc4686cde28f4c6a5c172da1f03fefe1e9ed80aac4a19727f`. Footnote 20 quotes LC 200/2023 art. 7 para 2 (discretionary floor 75% of authorised). |

## C2 macro input sources

The Tesouro workbook and the two raw macro files listed below are read directly
by `src/macro.py`. Other sources were read through official publication
pages/full text on 2026-10-20. Exact locators are recorded in
`config/parameters.yaml` (C2 sections).

| Source | URL | Accessed | Licence / terms | Inputs |
|---|---|---:|---|---|
| Tesouro Nacional, Estatisticas Fiscais do Governo Geral, workbook sheet `1.2.a` | https://www.tesourotransparente.gov.br/publicacoes/estatisticas-fiscais-do-governo-geral/2021/22 | 2026-10-20 | Tesouro site states CC BY-ND 3.0; verify dataset-specific terms before redistribution | 2025 primary revenue/spending/balance; 2021-2025 interest payable |
| `brazil/macro/bcb_sgs_13762_dbgg_pct_gdp.json` — Banco Central do Brasil, SGS 13762 | https://api.bcb.gov.br/dados/serie/bcdata.sgs.13762/dados?formato=json | 2026-10-20 (downloaded by Claude) | BCB public API; explicit dataset licence not located | Untouched monthly DBGG/GGGD % GDP, Dec. 2006-Aug. 2026; 2021-2025 December history and 2025 anchor. SHA-256 `32d822f4c0a14bbdef321aa338ff957cd9d899fa6c1208fa902100298ccf6197`. |
| `brazil/macro/pwt1001.dta` — Penn World Table 10.01 | https://dataverse.nl/api/access/datafile/354098 (DOI 10.34894/QT5BCC) | 2026-10-20 (downloaded by Claude) | CC BY 4.0 | Untouched Stata file; Brazil `rgdpna`, `rnna`, `delta`, `emp`, `avh`, `hc`, `labsh`, `rtfpna` through 2019. SHA-256 `746a483666a5371f8e686f8bfea6c20e211e5ecdd928842c6e01d2bd623ffb4c`. |
| IBGE, Anuario Estatistico 2024, table 7.5.1.2 | https://anuario.ibge.gov.br/images/aeb/2024/s7/2_pdf/s7t5102.pdf | 2026-10-20 | Official public download; no explicit licence located | GDP deflator |
| Banco Central do Brasil, inflation targeting regime | https://www.bcb.gov.br/en/monetarypolicy/inflationtargeting | 2026-10-20 | Official public page; no explicit licence located | Continuous 3.0% inflation target used as low/central long-run deflator assumption |
| IMF, Brazil 2025 Article IV Consultation | https://www.imf.org/-/media/files/publications/cr/2025/english/1braea2025001-source-pdf.pdf | 2026-10-20 | IMF copyright; free to read | Published 2.5% medium-term/potential-growth comparison |
| Jin & Harper, Okun's Law: an Empirical Test Using Brazilian Data | https://scholar.valpo.edu/cba_fac_pub/72/ | 2026-10-20 | Author/repository page; terms not located | low Okun coefficient |
| Pessoa, Okun's Law: Evidence for the Brazilian Economy | https://mpra.ub.uni-muenchen.de/56388/1/MPRA_paper_56388.pdf | 2026-10-20 | MPRA open repository; author retains copyright | central/high Okun coefficients |
| `brazil/macro/ibge_sidra_6784.json` | [IBGE SIDRA table 6784](https://apisidra.ibge.gov.br/values/t/6784/n1/all/v/all/p/2020,2021,2022,2023,2024?formato=json) | 2026-10-20 (Claude) | Official public data | Untouched API response; SHA-256 `3d72b9dc368717e1cc509552e9f91bff02616b8b70b2e9cd4ca963e66bd1c953`. GDP deflator annual change 2020-2023 (2024 not yet published in this table). |
| `brazil/macro/ibge_sidra_1846_gdp_current_2024.json`, `ibge_sidra_1846_gdp_current_2025.json` | [IBGE SIDRA table 1846](https://sidra.ibge.gov.br/tabela/1846), v585, c11255/90707 (GDP at market prices, current R$ million) | 2026-10-20 (Claude) | Official public data | Untouched API responses; SHA-256 `c668015a25e5a607c39bfb22004d1e53a42dcb63cc16a5197964b542c1bd26e4`, `cafe03d26ee0c5458dffbe563a1f4fd9ec024f0ca8cc142034f889dd06870d6b`. Quarterly sums: 2024 R$11,779,251 m; 2025 R$12,738,566 m. |
| `brazil/macro/ibge_sidra_5932_gdp_real_growth_2025.json` | [IBGE SIDRA table 5932](https://sidra.ibge.gov.br/tabela/5932), v6563, 2025 Q4 | 2026-10-20 (Claude) | Official public data | Untouched API response; SHA-256 `ce9a02dc7d63b146d5a831705f1d2f54aae4614f6d0e4a2faf432ce43798048a`. 2025 real GDP growth 2.3%; with table 1846 gives 2025 deflator 5.71%. |

## C4 social sources

| File | Source URL | Retrieved | Licence / terms | Notes |
|---|---|---|---|---|
| `brazil/social/worldbank_bra_infant_mortality.json` | [World Bank WDI API, `SP.DYN.IMRT.IN`, Brazil](https://api.worldbank.org/v2/country/BRA/indicator/SP.DYN.IMRT.IN?format=json&per_page=100) | 2026-10-20 (Claude) | CC BY 4.0 | Untouched API response; SHA-256 `a573f536bb6c5df8ccabb0561c076868936cd11b691b5427f523df66d361322b`. Infant mortality per 1,000 live births (UN IGME estimates); 2024 = 12.3. |
