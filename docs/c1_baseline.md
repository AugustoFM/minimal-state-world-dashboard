# C1 age-profile spending baseline

## Scope and base year

The model projects Brazilian general-government primary spending under S0
(status-quo demographic drift) and S1 (constant spending/GDP). The latest
complete fiscal observation is 2025: 39.7620150669% of GDP. The partial 2026
observation is excluded. Results cover 5, 10, 15 and 20 years and are
sensitivity bounds, not forecasts or statistical percentiles.

## Base-year category shares

All category shares come from the official 2024 general-government COFOG table
and are carried one year to the 2025 model base:

| Category | % GDP | Exact source |
|---|---:|---|
| Health | 5.031903317955291 | `COFOG_GG_2024.xlsx`, sheet `1.5.a`; `Q4` = 2024, `Q52` = COFOG 07 Saúde |
| Education | 5.101686126613569 | same sheet; `Q66` = COFOG 09 Educação |
| Pension | 11.65005863811359 | same sheet; `Q77` = COFOG 10.2 Terceira idade (8.86420230043415) plus `Q78` = COFOG 10.3 Sobreviventes (2.7858563376794394) |

The pension base is old age plus survivors, not total social protection (a
different concept). Shares are point-valued because the source gives no range.
The residual 17.9783669842% of GDP is non-age-related primary spending and is
held fixed. S1 holds every category and the total fixed.

## Profiles and calculation

`scripts/build_brazil_age_profiles.py` reads sheet `Per capita Normalized` of
the archived `NTA_Brasil.xlsx` and writes 546 rows: three accounts, ages 0–90+,
and vintages 2003 and 2018. It preserves the published NTA values; it does not
renormalize them. Population ages 90 and above map to the workbook's age-90
(90+) value.

The accounts are public-transfer inflows for education, health, and RGPS
pensions. The README describes “Other cash” only as an undifferentiated NTA
account, and the Translation sheet likewise says only “Outros em numerário.”
Neither supports identifying an RPPS component, nor separating BPC or Bolsa
Família. Therefore no “Other cash” amount is added. The RGPS profile is marked
`is_proxy=true` because it supplies the shape for the broader COFOG old-age and
survivors base, which includes RPPS; health and education are direct account
matches and are not marked as proxies.

For health and education:

`share(t) = share(base) × mean_cost(t) / mean_cost(base)`

For pensions the model geometrically combines that per-capita multiplier with
a GDP-per-working-age-person multiplier (ages 15–64). The weight is 0, 0.5, or
1. The model evaluates all six combinations of the two observed profile
vintages and three indexation weights. At each horizon, low and high select the
combinations with the lowest and highest total S0 spending; central is the 2018
profile with weight 0.5. Each selected combination is used consistently for
all category rows, so components add to the reported total.

## Resulting S0–S1 drift

| Horizon | Low | Central | High | Low combination | High combination |
|---:|---:|---:|---:|---|---|
| 5 years | 1.414 pp | 1.629 pp | 1.667 pp | 2003, weight 0 | 2018, weight 1 |
| 10 years | 2.859 pp | 3.323 pp | 3.407 pp | 2003, weight 0 | 2018, weight 1 |
| 15 years | 4.347 pp | 5.211 pp | 5.434 pp | 2003, weight 0 | 2018, weight 1 |
| 20 years | 5.843 pp | 7.345 pp | 7.863 pp | 2003, weight 0 | 2018, weight 1 |

The 2003 shape is the older, pre-2019-reform sensitivity; the 2018 shape is
central. `drift_pct_gdp` is S0 minus S1 and is repeated on both scenario rows.
The output records the selected `profile_year`, indexation case, and numeric
weight, making every bound reproducible.

## Sources and remaining gaps

Population is the IBGE 2024 revision (Brazil, both sexes, single ages). The
fiscal total is Tesouro's GFSM 2014 general-government series. Raw C1 files,
downloaded by Claude on 2026-10-20, hashes, URLs and licence notes are recorded
in `data/raw/SOURCES.md` and `SOURCE_ACCESS_NOTE.txt`.

The model carries 2024 category shares into 2025, uses working-age population
rather than age-specific labour-force participation, and applies an RGPS shape
to RPPS-inclusive pension spending. Fixed 2003/2018 shapes do not model the
2019 pension reform's transition rules or later benefit composition. Health
and education COFOG totals include spending that is not perfectly age
assignable. These are the remaining substantive gaps; no missing values are
invented or interpolated.
