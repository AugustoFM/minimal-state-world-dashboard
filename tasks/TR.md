# TR - Presidential international travel: costs, FDI and exports (FHC 1995 to Lula III 2026)

Owner: Codex (parsing, analysis, HTML tool, tests), Claude (data, review). Requested by the user 2026-10-22: compile
the costs of presidential trips abroad (including the President's spouse where identifiable) for every president from
FHC to Lula III, adjust for inflation, set them against FDI and exports, test whether travel is significantly
associated with FDI and exports, and build an HTML comparison tool in `outputs/`.
Neutral: every president is measured with the same rules; where data do not exist for a period, the tool says so
instead of filling it. The HTML is written to `outputs/presidential_travel/` (git-ignored until the lead decides).

## Data (read-only; `data/raw/SOURCES.md`, section TR)
- Trips and countries: `data/raw/brazil/travel/wikipedia_pt_viagens_*.wikitext` (FHC, Lula 2003-2010 and 2023-,
  Dilma, Temer, Bolsonaro; Portuguese Wikipedia, FHC list sourced from the Presidency Library) and
  `wikipedia_trips_*.wikitext` (English lists, cross-check). Parse wikitext tables: per trip, start/end dates and
  countries visited. Count trips (departure-return), country-visits and days abroad (end - start + 1, union of dates
  per trip). Report parsing conflicts between pt and en lists; pt is primary for FHC and Lula, en for the others.
- Costs 2014-2026: `data/raw/brazil/travel/presidency_travel_2014_2026.csv.gz` (Portal da Transparência travel
  records: Presidency organ; Defence records supporting presidential missions; other organs whose motive cites a
  presidential trip; per diems, tickets, other costs; `international` flag; traveller names removed). The Presidency
  uses travel records for staff, security and advance teams; the President's and spouse's own aircraft costs (FAB)
  are not in these records (gap, stated). Records whose motive mentions the President's family/spouse
  ("FAMILIAR DO SR PRESIDENTE", "PRIMEIRA-DAMA", "CONJUGE") are tagged `spouse_related` (security and support staff
  travelling with the spouse; the spouse's own costs are not itemised).
- Payment card 2013-2026: `presidency_cpgf_2013_2026.csv.gz` will be added later by the lead (downloads still
  rate-limited). Code must run without it and include it automatically when present (Presidency card
  transactions; hotels abroad appear there; classify foreign transactions by payee/transaction text).
- The Presidency organ (20000) covers all its bodies (GSI security, staff, Vice-Presidency, etc.), not only the
  President's trips. Define **presidential-trip support** records as international records whose dates overlap a
  presidential trip (from the trip lists) and whose destination country matches one of that trip's countries; report
  them separately from other Presidency international travel. Records tagged `spouse_related` likewise.
- Cited totals: `cited_figures_press.csv` (card totals by term 2003-2022 as released in Jan 2023, FHC 347 days abroad,
  press estimates for 2023-2025). Use only as labelled context, never mixed into the computed series.
- Prices: IPCA monthly `data/raw/brazil/rates/bcb_sgs_433_ipca_monthly.json` -> constant Sep-2026 reais.
- FDI: `data/raw/brazil/external_sector/bcb_sgs_22885.json` (direct investment in the country, net, US$ million,
  monthly 1995-2026). Exports: `bcb_sgs_22708.json` (goods exports, US$ million, monthly); export volume
  `ipeadata_FUNCEX_XQT.json` (quantum index 2018 = 100; also XQM manufactured, XQB basic). Exports by destination
  country 1997-2026: `comexstat_exports_by_country_YYYY.json` (MDIC ComexStat; FOB US$ and kg).
- Controls already in the repo: commodity prices, US rates, China/world growth used by C6/C7 (`data/raw/brazil/external`,
  `data/raw/world`); use what exists, document which.

## Analyses (fixed before results)
1. Per president and per year: trips, country-visits, days abroad; costs (2014+) in constant reais, total and
   international, by category; cost per trip and per day abroad where both exist.
2. Aggregate association (annual 1995-2025, n = 31; small, say so): FDI (US$, and % of GDP) and exports (value and
   FUNCEX volume) on trips or days abroad, levels with trend and first differences, lags 0-2, controls for commodity
   prices, world demand and the exchange rate; Newey-West SE; permutation test of the travel coefficient (shuffle
   years, 10,000 draws, fixed seed). Report that aggregate correlations are dominated by global cycles.
3. **Bilateral test (primary, better identified):** country-year panel 1997-2025 of Brazilian exports to each partner;
   regressor = presidential visit to that country in year t (and t-1, t-2); country fixed effects, year fixed effects,
   country-specific trends as robustness; clustered by country. This follows the state-visits literature (e.g. Nitsch
   2007, "State visits and international trade", The World Economy) - cite only as context, no numbers taken from it.
   Report the visit coefficient (% change in exports) with CI, and a placebo with visits moved to t+2.
4. HTML tool `outputs/presidential_travel/presidential_travel.html` (self-contained, offline, no external requests):
   president selector; yearly bars of trips/days/costs (constant R$) with clear "no cost data before 2014" shading;
   FDI and exports overlay; table by president; the regression results with plain-language reading; data gaps panel.
   Neutral styling: one colour per president from a single categorical palette, no party colours.
5. Report `outputs/presidential_travel.md` and method `docs/presidential_travel.md`.

## Tests
`tests/test_presidential_travel.py` (synthetic): wikitext table parsing, trip/day counting with multi-country trips,
international flag, deflation, permutation test reproducibility, bilateral FE regression recovers a planted effect.

## Outputs (Codex-owned; nothing else may be modified)
`src/presidential_travel.py` (`python -m src.presidential_travel` rebuilds data, estimates and HTML),
`tests/test_presidential_travel.py`, `data/brazil/presidential_trips.csv`, `data/brazil/presidential_travel_costs.csv`,
`data/brazil/travel_trade_estimates.csv`, `outputs/presidential_travel.md`, `docs/presidential_travel.md`,
`outputs/presidential_travel/presidential_travel.html`. No network, no git.
