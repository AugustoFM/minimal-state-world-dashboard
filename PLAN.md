# Plan and tasks

Owner split: **Claude** = plan, method, scripts skeleton, first dashboard prototype. **Codex** = tasks marked [Codex]. Each task = one branch/PR; check the box when done.

## Minimal-state score (method, v1)
Three dimensions, each 0-100 (100 = most minimal), equal weights, as in the report:
1. **Budget size**: general government expense % GDP (WB `GC.XPN.TOTL.GD.ZS`), fallback IMF WEO general government expenditure. Lower spending = higher score.
2. **Economic footprint**: state-owned enterprise share (OECD PMR / OECD SOE data where available) and Heritage/EFW "size of government" component as proxy elsewhere.
3. **Functional scope**: EFW Area 1 "Size of Government" and Heritage "Government integrity / spending" sub-scores as proxy for how far the state reaches beyond core functions.
Score = mean of available dimensions (minimum 2 of 3 required, else "insufficient data"). Report the number of dimensions used. Keep every sub-score visible in the dashboard. Caveat: proxies, not a direct measure; indices are from market-oriented think tanks.

## Outcome indicators (latest year available, 2018-2024; always keep the year)
| Field | Source / code |
|---|---|
| GDP (current US$) | WB `NY.GDP.MKTP.CD` |
| GDP per capita (PPP, intl $) | WB `NY.GDP.PCAP.PP.CD` |
| Unemployment % | WB `SL.UEM.TOTL.ZS` |
| Access to health (UHC service coverage index) | WB `SH.UHC.SRVS.CV.XD` |
| Life expectancy | WB `SP.DYN.LE00.IN` |
| Gini | WB `SI.POV.GINI` |
| Income share top 10% | WB `SI.DST.10TH.10` |
| HDI | UNDP HDR composite indices CSV (hdr.undp.org/data-center) |
| Civil rights / political rights | Freedom House "Freedom in the World" (global scores, xlsx) |
| Number of rich people (millionaires) | UBS Global Wealth Report (country tables); alt. WID top 1% wealth share |
| Economic freedom | Fraser EFW 2026, Heritage Index 2026 (manual download) |

## Tasks
- [ ] T1 [Claude] Scaffold repo, method, scripts (this commit)
- [ ] T2 [Codex] Run `fetch_worldbank.py`, fix any API issues, commit `data/raw/worldbank_long.csv`
- [ ] T3 [Codex] Download UNDP HDI, Freedom House, EFW, Heritage, UBS millionaires files into `data/raw/` with a `data/raw/SOURCES.md` (URL, date, licence)
- [ ] T4 [Codex] Write `scripts/build_dataset.py`: one row per country (ISO3), country-name harmonisation, drop aggregates, keep value + year per indicator
- [ ] T5 [Codex] Implement/validate `scripts/build_score.py`; add unit tests; document missing data per country
- [ ] T6 [Claude/Codex] Dashboard: world map (choropleth) coloured by score or any indicator, scatter score vs outcome, ranking table with search, country detail panel; static site in `dashboard/` (d3 + TopoJSON world atlas)
- [ ] T7 [Claude] Review: spot-check 10 countries against sources, update report with results
- [ ] T8 [Claude/Codex] GitHub Pages deploy

## Rules of honesty
Never fill gaps with invented numbers; show missing as missing. Label proxies. Note that correlation with outcomes is not causation.
