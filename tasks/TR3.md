# TR3 - Presidential travel: redesign by presidential term (user request 2026-10-22)

The user does not want exports and FDI pooled, nor a bilateral visited-country analysis as the headline. Redesign the
TR outputs around **presidential terms**: how FDI and exports evolved in each term, which term saw the larger gains in
attracting FDI and in opening export channels, and how that relates to the number, length and cost of trips
(efficiency). FDI and exports are always separate measures, separate charts, separate tables.
Neutral: identical rules for every term; global conditions shown next to every Brazilian figure; associations, not
causal attribution; data gaps explicit. Keep the earlier bilateral and regression results only in a collapsed
"robustness / previous analysis" section of the report (not in the HTML headline).

## Terms (calendar years; partial years by month where monthly data exist)
FHC I 1995-98, FHC II 1999-2002, Lula I 2003-06, Lula II 2007-10, Dilma I 2011-14, Dilma II 2015 - Aug 2016,
Temer Sep 2016-2018, Bolsonaro 2019-22, Lula III 2023 - latest (Sep 2026, partial; annualise and say so).

## Measures per term (separately for FDI and for exports)
FDI (BCB SGS 22885, monthly US$; World Bank BX.KLT.DINV.CD.WD Brazil and World, annual):
- total and annual average, nominal and real (US CPI is not archived: use constant 2025 US$ via the US GDP deflator if
  present in the repo, else report nominal US$ and % of GDP, and state it);
- FDI as % of GDP (World Bank GDP); Brazil's share of world FDI inflows (%), average per term and change from the
  last year before the term to the term's last full year;
- change vs the previous term (pp of GDP and share points).
Exports (BCB SGS 22708 monthly US$; FUNCEX quantum XQT/XQM/XQB; World Bank/WTO world merchandise exports;
ComexStat by country):
- total and annual average value; export volume growth (quantum, % per year, total and manufactured vs basic);
- Brazil's share of world merchandise exports (%), average and change over the term;
- **export channels opened**: number of destination countries with exports >= US$ 10 million (and >= US$ 1 million
  as robustness) at the end vs the start of the term; new markets = countries crossing the threshold during the term
  and still above it at the end; markets lost likewise; export concentration (top-5 partners' share; HHI).
Global context per term: world FDI and world exports growth, commodity-price change (from repo C7 data if present).

## Travel and efficiency per term
Trips, country-visits, days abroad (lower bound), distinct countries visited; costs (2014+ only): matched travel
support records (lower bound) and, separately, Presidency payment-card spending (all card spending and the part
identifiable as foreign: payee/transaction text), constant Sep-2026 R$; press figures as labelled context.
Efficiency ratios (descriptive, clearly labelled "not causal"): change in Brazil's world FDI share and world export
share per trip and per 100 days abroad; new export markets per trip; for terms with cost data, change per R$ million
of matched travel cost. Show them as a ranked table with the data-coverage caveat beside each ratio.

## HTML (`outputs/presidential_travel/presidential_travel.html`, self-contained, offline, light/dark)
Sections: (1) term selector and summary cards (FDI, exports, travel, cost - each its own card); (2) FDI by term (bars:
% of GDP and world share, with world FDI growth line); (3) exports by term (value, volume, world share, separate);
(4) export channels opened (new/lost markets, concentration), with a map-free list of new markets per term;
(5) travel and cost by term (trips, days, matched cost, card spending; shaded "no cost data" before 2014);
(6) efficiency table (ranked, with coverage and "association, not causation" notes); (7) data gaps and method.
One colour per president from one categorical palette (no party colours). Keep the earlier visited-country analysis
out of the HTML.

## Outputs (same ownership as TR plus this file)
`src/presidential_travel.py`, `tests/test_presidential_travel.py` (add tests: term assignment of monthly data and
partial years; world-share arithmetic; new/lost market counting with thresholds; efficiency ratios with missing
costs), `data/brazil/presidential_terms.csv` (new), existing TR data files, `docs/presidential_travel.md`,
`outputs/presidential_travel.md`, `outputs/presidential_travel/presidential_travel.html`. Inputs as in TR plus
`data/raw/brazil/travel/presidency_cpgf_2013_2026.csv.gz` and `data/raw/brazil/external_sector/wdi_*.json`
(World Bank API JSON: second element is the list of {date, value}). No network, no git. Do not modify tasks/STATUS.md.
