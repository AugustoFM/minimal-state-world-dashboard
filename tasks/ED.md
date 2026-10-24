# ED - Education: attainment, programmes, university and IF capacity, entrepreneurship, crime; programme channels

Owner: Codex (data build, estimation, module, tests, report), Claude (data, literature in `docs/education_review.md`,
review, Monte Carlo wiring). Requested by the user 2026-10-22: review education levels and their evolution, the money
in universities and federal institutes (IFs), ProUni/Fies/Pé-de-Meia, link a better-educated population to
entrepreneurship, firm creation, formal jobs, innovation, competitiveness and lower crime, using Brazilian and
international evidence (Germany, Switzerland, USA, India, peers), and model it for both programmes.
Neutral: every channel is driven by each scenario's own education spending path and stated measures, with identical
rules for increases and cuts. Read `docs/education_review.md` first (evidence, parameter ranges, programme mapping).

## Data (read-only; `data/raw/SOURCES.md`, sections "BK / ED / TR data" and "ED data")
- Attainment (PNAD Contínua, SIDRA v3 JSON): `data/raw/brazil/education/ibge_sidra_7126_*` (mean years of schooling,
  15+, by age group, Brazil and states, 2016-2025); `ibge_sidra_7267_*` (education-level distribution and levels, 14+,
  Brazil and states, 2016-2025).
- Entrepreneurs by education (PNAD Contínua, Brazil and macro-regions, 2012-2025): `ibge_sidra_7193_*` (employers or
  own-account), `7195` (employers), `7196` (employers with CNPJ), `7247` (own-account), `7248` (own-account with CNPJ);
  denominator `ibge_sidra_4095_occupied_by_education_quarterly.json` (occupied by education level, quarterly).
- Firm births/exits: `data/raw/brazil/firms/ibge_sidra_2718_firm_events_BR.json` (2008-2021),
  `ibge_sidra_9924_employer_events_BR.json` (2015-2022); `data/brazil/firm_distress_annual.csv` (BK).
- Crime: `data/raw/brazil/crime/ipeadata_atlas_violencia_homicides.csv.gz` (homicides total, youth 15-29, and rate per
  100k; Brazil, states, municipalities; 1979/80-2024).
- Spending: `data/raw/brazil/education/tesouro_cofog_gc_2010_2024_aggregated.csv.gz` (central government by year x
  COFOG function x GFS economic class x budget unit; **unit: R$ for 2010-2023, R$ million for 2024** - rescale and
  check totals). Federal universities, IFs, FNDE (Fies, Pé-de-Meia) are identifiable by budget unit.
- Programme figures with sources: `data/raw/brazil/education/programme_facts.csv` (IF units, Fies contracts, ProUni
  offers, Pé-de-Meia cost and ex-ante effect, university budget measures, Bergmann 2020 estimates, international
  elasticities).
- Existing model: C5 schooling channel in `src/feedback.py` (`schooling_log_output_effect`, PWT mapping,
  cohort replacement), C1 population, `config/programs_2026.yaml`, `config/parameters.yaml`.

## Calibration of education/science cuts (user request: "make your best guess of the overall cut")
Recompute from the COFOG extract (budget-unit patterns: federal universities = units whose description contains
UNIVERSIDADE/FUND. UNIV; federal institutes = INSTITUTO FEDERAL / INST. FED / CEFET / COLEGIO PEDRO II (check that IFs
are found: the lead's quick pattern missed most of them); MCTI = budget units whose code starts with 24; personnel =
GFS 'REMUNERACAO' and 'BENEFICIOS SOCIAIS') the real (IPCA, 2024 prices) 2018->2022 and 2022->2024 changes. Lead's
quick figures: universities total -13.5% / +4.7%, non-personnel -28.5% / +10%, MCTI -31% / +40%. Flávio sensitivities:
`current_law` (default), `record_repeat` (lead's central guess: repeat the 2018-2022 changes over 2027-2030, held
after), `half_record`. Lula: `current_law` + stated measures (Pé-de-Meia, 100 IF campi, PBIA). Cascade each through
channels (i)-(v) below and report by channel.

## Steps (fixed before results)
1. **Trends** `data/brazil/education_panel.csv`: attainment by state-year; employer and own-account rates by education
   level (Brazil and regions; rate = entrepreneurs / occupied in the same level, annual mean of quarters); firm birth
   and exit rates; youth homicide rate by state-year; real (IPCA) central-government spending on tertiary, secondary,
   vocational, Fies and Pé-de-Meia lines 2010-2024.
2. **Entrepreneurship gradient**: employer rate and CNPJ-employer rate by education level, 2012-2025 (descriptive,
   regional fixed effects). Composition arithmetic: change in the national employer rate implied by the 2016-2025
   attainment shift at fixed level-specific rates. Report against Bergmann 2020 (no local campus effect on the employer
   rate) and IZA DP 14655 (IV: schooling raises incorporated self-employment).
3. **Crime association** (state panel 2016-2024, state and year FE, clustered by state): youth homicide rate on the
   share of 18-24-year-olds with completed secondary (or mean years 18-24, whichever is available in 7126/7267). Label
   as association; compare with the causal literature ranges in the review.
4. **Module `src/education.py`** (deterministic, scenario paths 2025-2045; not wired into the Monte Carlo yet):
   a. inputs per scenario: education spending change vs S0 (pp GDP, from the scenario's packages, as C5 uses) and
      explicit measures: `pe_de_meia` (on/off; dropout effect -6.5 pp among vulnerable students, sensitivity -3.25),
      `if_campi` (count added; 100 under Novo PAC by 2026), `university_budget_change_pct` (default 0; sensitivities
      -10%, -20%, +10% from 2028);
   b. channels: (i) schooling of entering cohorts -> adult mean schooling (reuse C5 logic; Pé-de-Meia adds secondary
      completions among 15-17 cohorts); (ii) higher-education capacity -> long-run GDP per capita level with elasticity
      0.04 per log capacity (upper bound, Valero & Van Reenen), central 0.02 (relocation haircut, Andrews), low 0
      (Bergmann), phased in linearly over 15 years from the capacity change; capacity proportional to real tertiary +
      IF spending; (iii) entrepreneurship: employer share via composition only (gradient x attainment), local effect 0
      (sensitivity: small positive from IZA); output indicator, no GDP effect beyond (i)-(ii); (v) innovation
      capacity: public R&D/technology stock (perpetual inventory, 15% depreciation) from real public R&D spending
      (COFOG R&D lines and the PBIA, R$ 23 bn over 2024-2028), output elasticity 0 / 0.01 / 0.02 per log stock; (iv) youth homicide:
      change via secondary completion with an elasticity range from the step-3 association bounded by the literature
      (state as indicator; no GDP feedback);
   c. investment accounting: present value (3% real) of the fiscal cost/saving of the education and R&D measures vs
      the GDP gain/loss and the revenue on it (revenue/GDP held) to 2045 and to 2060 (tail reported separately);
   d. outputs per scenario-year: adult mean schooling, tertiary share 25-34, capacity index, GDP-per-capita level effect
      (by channel), employer share, youth homicide rate change; ranges low/central/high.
5. **Programme mapping** (`config/ed_proposed.yaml`, proposal): Lula = Pé-de-Meia on, 100 IF campi, university budget
   current law, PBIA as planned; Flávio = Pé-de-Meia current law (the TSE plan is silent: keep as current law), IF campi as current law
   (the 100 under construction complete), university budget default 0 with -10%/-20% labelled sensitivities ("not in
   the plan; plan moves governance to the MCTI without a budget figure"), PBIA current law, applied-research focus as
   a symmetric +/-10% effectiveness sensitivity on the capacity channel (unquantified in the evidence). All scenarios also carry their package
   education cuts or increases through (a).
6. Report `outputs/education.md` (neutral) and method `docs/education.md`.

## Tests
`tests/test_education.py`: SIDRA parsing, 2024 unit rescale, composition arithmetic, capacity phase-in, symmetry
(+x then -x returns to baseline), zero inputs -> zero effects, cohort replacement consistency with C5 on a synthetic
case.

## Outputs (Codex-owned; nothing else may be modified)
`src/education.py` (`python -m src.education` rebuilds everything), `tests/test_education.py`,
`data/brazil/education_panel.csv`, `data/brazil/education_estimates.csv`, `data/brazil/education_scenarios.csv`,
`config/ed_proposed.yaml`, `outputs/education.md`, `docs/education.md`. Do not modify `src/feedback.py`,
`src/montecarlo.py` or any existing file. numpy OLS/NW as in `src/rates.py`. No network, no git.
