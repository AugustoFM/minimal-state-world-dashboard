# F1 fiscal delivery: LDO targets versus outturns

## Method and conventions

The builder extracts whitespace-normalised text from the archived official LDO/PLDO annexes with `pypdf`; the 2019 DOCX is read directly from `word/document.xml`. The fiscal figures are hand-transcribed because layouts and concepts vary, and every stored quote is checked as an exact substring of the extracted source text. Blank cells mean that the annex does not report the requested concept—not zero. Government Federal (central government plus federal state-owned enterprises) is not silently relabelled as central government.

**Sign convention:** surplus is positive and deficit is negative for targets and outturns. A miss is `outturn − target`, in percentage points of GDP; a negative miss therefore means a result below the target. Original/final targets are kept before permitted deductions, which are reported separately. The 2024–25 zero central target is likewise kept separate from its tolerance band and exclusions.

Percentages marked † were not printed by the annex and are derived from its R$ amount using annual nominal GDP: the sum of the four quarterly values in offline SIDRA table 1846. Published annex percentages are retained even when a later GDP vintage differs. The annexes are the source of the main series; BCB SGS 5793 is only a cross-check.

## Per-year results

R$ values are billions; GDP values and misses are percentage points.

| Year | Concept | Original R$ / % GDP | Final R$ / % GDP | Deductions R$ | Outturn R$ / % GDP | Miss original | Miss final | Government |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1999 | consolidated public sector | — / — | — / — | — | — / — | — | — | FHC II (PSDB) |
| 1999 | central government | 16.20 / 1.49† | 16.20 / 1.49† | — | 21.50 / 2.13 | 0.64 | 0.64 | FHC II (PSDB) |
| 2000 | consolidated public sector | — / — | — / — | — | — / — | — | — | FHC II (PSDB) |
| 2000 | central government | 28.50 / 2.65 | — / — | — | — / — | — | — | FHC II (PSDB) |
| 2002 | consolidated public sector | — / — | — / — | — | — / — | — | — | FHC II (PSDB) |
| 2002 | central government | 26.40 / 2.00 | 29.20 / 2.24 | — | 31.90 / 2.42 | 0.42 | 0.18 | FHC II (PSDB) |
| 2008 | consolidated public sector | — / 3.80 | — / 3.80 | — | 118.00 / 4.07 | 0.27 | 0.27 | Lula I-II (PT) |
| 2008 | central government | — / 2.20 | — / 2.20 | — | 71.30 / 2.46 | 0.26 | 0.26 | Lula I-II (PT) |
| 2010 | consolidated public sector | — / 3.30 | — / 3.10 | 22.10 | 101.70 / 2.62† | -0.68 | -0.48 | Lula I-II (PT) |
| 2010 | central government | 72.60 / 2.15 | 76.30 / 2.15 | 22.10 | 78.72 / 2.22 | 0.07 | 0.07 | Lula I-II (PT) |
| 2011 | consolidated public sector | 117.90 / 2.69† | 127.90 / 2.92† | 0.00 | 128.72 / 2.94† | 0.25 | 0.02 | Dilma (PT) |
| 2011 | central government | 81.80 / 1.87† | 91.80 / 2.10† | 0.00 | 93.04 / 2.13† | 0.26 | 0.03 | Dilma (PT) |
| 2012 | consolidated public sector | 139.80 / 2.90† | 139.80 / 2.90† | 39.30 | — / — | — | — | Dilma (PT) |
| 2012 | central government | 97.00 / 2.01† | 97.00 / 2.01† | 39.30 | 86.09 / 1.79† | -0.23 | -0.23 | Dilma (PT) |
| 2014 | consolidated public sector | — / — | — / — | — | — / — | — | — | Dilma (PT) |
| 2014 | central government | 116.07 / 2.01† | 116.07 / 2.01† | 161.74 | -20.47 / -0.35† | -2.36 | -2.36 | Dilma (PT) |
| 2015 | consolidated public sector | 66.30 / 1.11† | -48.90 / -0.85 | 66.90 | -111.20 / -1.85† | -2.96 | -1.00 | Dilma (PT) |
| 2015 | central government | 55.30 / 0.92† | -51.82 / -0.86† | 66.86 | -116.66 / -1.95† | -2.87 | -1.08 | Dilma (PT) |
| 2016 | consolidated public sector | 30.60 / 0.49† | -163.90 / -2.61† | 0.00 | -155.80 / -2.49† | -2.97 | 0.13 | 2016 transition |
| 2016 | central government | 24.00 / 0.38† | -170.50 / -2.72† | 0.00 | -159.47 / -2.54† | -2.93 | 0.18 | 2016 transition |
| 2017 | consolidated public sector | -143.10 / -2.17† | -163.10 / -2.48† | 0.00 | -110.60 / -1.68† | 0.49 | 0.80 | Temer (MDB) |
| 2017 | central government | -139.00 / -2.11† | -159.00 / -2.41† | 0.00 | -118.40 / -1.80† | 0.31 | 0.62 | Temer (MDB) |
| 2018 | consolidated public sector | -131.30 / -1.87† | -161.30 / -2.30† | 0.00 | -108.30 / -1.55† | 0.33 | 0.76 | Temer (MDB) |
| 2018 | central government | -129.00 / -1.84† | -159.00 / -2.23 | 0.00 | -116.17 / -1.70 | 0.14 | 0.53 | Temer (MDB) |
| 2019 | consolidated public sector | -132.00 / -1.79† | -132.00 / -1.79† | 0.00 | -61.90 / -0.84† | 0.95 | 0.95 | Bolsonaro (PSL/PL) |
| 2019 | central government | -139.00 / -1.84 | -139.00 / -1.84 | 0.00 | -88.90 / -1.23 | 0.61 | 0.61 | Bolsonaro (PSL/PL) |
| 2020 | consolidated public sector | -118.90 / -1.56† | -158.71 / -1.51 | 0.00 | -702.95 / -9.44 | -7.88 | -7.93 | Bolsonaro (PSL/PL) |
| 2020 | central government | -124.10 / -1.63† | -124.10 / -1.58 | 0.00 | -745.27 / -10.01 | -8.38 | -8.43 | Bolsonaro (PSL/PL) |
| 2021 | consolidated public sector | -250.89 / -3.74 | -250.89 / -3.74 | 84.50 | 64.73 / 0.75 | 4.49 | 4.49 | Bolsonaro (PSL/PL) |
| 2021 | central government | -247.12 / -3.16 | -247.12 / -3.16 | 84.50 | -35.87 / -0.41 | 2.75 | 2.75 | Bolsonaro (PSL/PL) |
| 2022 | consolidated public sector | -177.49 / -2.00 | -177.49 / -2.00 | 40.50 | 125.99 / 1.27 | 3.27 | 3.27 | Bolsonaro (PSL/PL) |
| 2022 | central government | -170.47 / -1.92 | -170.47 / -1.92 | 40.50 | 54.95 / 0.55 | 2.47 | 2.47 | Bolsonaro (PSL/PL) |
| 2023 | consolidated public sector | -69.01 / -0.66 | -69.01 / -0.66 | 241.30 | -249.12 / -2.29 | -1.63 | -1.63 | Lula III (PT) |
| 2023 | central government | -65.91 / -0.63 | -65.91 / -0.63 | 241.30 | -264.53 / -2.44 | -1.81 | -1.81 | Lula III (PT) |
| 2024 | consolidated public sector | -13.31 / -0.12 | -13.31 / -0.12 | 36.60 | -47.09 / -0.40 | -0.28 | -0.28 | Lula III (PT) |
| 2024 | central government | 0.00 / 0.00 | 0.00 / 0.00 | 36.60 | -45.36 / -0.38 | -0.38 | -0.38 | Lula III (PT) |
| 2025 | consolidated public sector | -5.21 / -0.04† | -5.21 / -0.04† | 48.60 | -54.76 / -0.43 | -0.39 | -0.39 | Lula III (PT) |
| 2025 | central government | 0.00 / 0.00 | 0.00 / 0.00 | 48.60 | -58.69 / -0.46 | -0.46 | -0.46 | Lula III (PT) |

Missing evaluated years (no archived annex): **2001, 2003–2007, 2009, 2013**. The archived 1999, 2000, 2002, 2012 and 2014 annexes also leave some consolidated cells unavailable under the requested definition.

Special events are retained: 1999 devaluation; 2008 global crisis; and 2020 pandemic, when the state of calamity suspended the requirement to attain fiscal targets.

## Summaries

Only rows with both an outturn and the relevant target enter each statistic. Pandemic year 2020 remains included. Numbers are pp of GDP.

| Concept | Government period | n | Mean miss vs original | Median | Mean miss vs final | Median |
|---|---|---:|---:|---:|---:|---:|
| consolidated public sector | Lula I-II (PT) | 2 | -0.21 | -0.21 | -0.11 | -0.11 |
| consolidated public sector | Dilma (PT) | 2 | -1.36 | -1.36 | -0.49 | -0.49 |
| consolidated public sector | 2016 transition | 1 | -2.97 | -2.97 | 0.13 | 0.13 |
| consolidated public sector | Temer (MDB) | 2 | 0.41 | 0.41 | 0.78 | 0.78 |
| consolidated public sector | Bolsonaro (PSL/PL) | 4 | 0.21 | 2.11 | 0.19 | 2.11 |
| consolidated public sector | Lula III (PT) | 3 | -0.77 | -0.39 | -0.77 | -0.39 |
| consolidated public sector | Pooled | 14 | -0.48 | -0.02 | -0.07 | 0.07 |
| central government | FHC II (PSDB) | 2 | 0.53 | 0.53 | 0.41 | 0.41 |
| central government | Lula I-II (PT) | 2 | 0.17 | 0.17 | 0.17 | 0.17 |
| central government | Dilma (PT) | 4 | -1.30 | -1.29 | -0.91 | -0.65 |
| central government | 2016 transition | 1 | -2.93 | -2.93 | 0.18 | 0.18 |
| central government | Temer (MDB) | 2 | 0.23 | 0.23 | 0.57 | 0.57 |
| central government | Bolsonaro (PSL/PL) | 4 | -0.64 | 1.54 | -0.65 | 1.54 |
| central government | Lula III (PT) | 3 | -0.88 | -0.46 | -0.88 | -0.46 |
| central government | Pooled | 18 | -0.64 | 0.11 | -0.36 | 0.12 |

## BCB consolidated-sector cross-check

BCB SGS 5793 is stored with negative values for surpluses, so it is sign-flipped before comparison. Difference is `annex − sign-flipped BCB`, in pp of GDP.

| Year | Annex | BCB (sign-flipped) | Difference | Note |
|---:|---:|---:|---:|---|
| 2008 | 4.07 | 3.33 | +0.74 | Annex includes the R$14.2bn FFIE/Fundo Soberano capitalisation; BCB SGS 5793 uses the current below-the-line series. |
| 2010 | 2.62 | 2.62 | -0.00 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2011 | 2.94 | 2.94 | +0.00 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2015 | -1.85 | -1.86 | +0.01 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2016 | -2.49 | -2.48 | -0.01 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2017 | -1.68 | -1.68 | +0.00 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2018 | -1.55 | -1.55 | +0.00 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2019 | -0.84 | -0.84 | +0.00 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2020 | -9.44 | -9.24 | -0.20 | Annex percentage uses its contemporary GDP estimate; SGS is the current vintage. |
| 2021 | 0.75 | 0.72 | +0.03 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2022 | 1.27 | 1.25 | +0.02 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2023 | -2.29 | -2.28 | -0.01 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |
| 2024 | -0.40 | -0.40 | +0.00 | Within 0.2 pp; small differences reflect rounding and GDP vintages. |

## Neutrality and attribution

The same statistics and inclusion rules are applied to every government period; this document uses no ranking language. Calendar-year attribution is descriptive, not causal: budgets and LDOs are often prepared in the prior year, economic shocks cross administrations, and 2016 is explicitly labelled a transition year (Dilma until 12 May; Temer thereafter). Bolsonaro's party label notes election by PSL and PL affiliation from 2021. Missing annex years are not filled or interpolated, so government-period sample sizes differ.

The proposed pooled empirical distribution is isolated in `config/f1_proposed.yaml`; it is not a model parameter until lead-developer review.
