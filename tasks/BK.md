# BK - Firm distress (defaults, judicial recovery, bankruptcy, exits) and interest rates

Owner: Codex (estimation, module, tests, report), Claude (data, review, wiring). Requested by the user 2026-10-22:
"understand the closure, chapter eleven, bankruptcy of companies in Brazil, correlate it with high interest rates".
Neutral: no scenario or candidate is discussed; the result is a channel applied identically to every scenario.

## Data (read-only; `data/raw/SOURCES.md`, section "BK / ED / TR data")
- `data/brazil/rates_monthly.csv` (I1): Selic, ex-post and ex-ante real rates, 2000-2026 monthly.
- `data/raw/brazil/bankruptcy/ipeadata_BM12_*.json`: BCB firm credit NPL rate (total, free credit), firm lending
  rate and spread (total, free), monthly 2011-03 to 2026-08. `ipeadata_SGS12_IBCBRDESSAZ12.json`: IBC-Br (activity).
  Ipeadata JSON: `value` list with `VALDATA`, `VALVALOR`.
- `data/raw/brazil/bankruptcy/serasa_falencias-e-recuperacoes-mai26.xlsx`: monthly Jan 2024-May 2026 (processes and
  CNPJs; bankruptcies requested/decreed; RJ requested/granted/approved; by size and sector). Labels may be non-UTF-8.
- `data/raw/brazil/bankruptcy/serasa_annual_press_releases_2026-10-22.csv`: sparse annual counts (methods differ:
  pre-2025 vs relaunched 2025 method; never splice without flagging).
- `data/raw/brazil/firms/ibge_sidra_2718_firm_events_BR.json` (2008-2021: active firms, births, entries, exits) and
  `ibge_sidra_9924_employer_events_BR.json` (2015-2022: employer births and deaths). SIDRA v3 JSON.

## Steps (fixed before results)
1. Build `data/brazil/firm_distress_monthly.csv` (2011-03 to latest) and `data/brazil/firm_distress_annual.csv`
   (2008-2025: firm birth/exit rates from IBGE, annual mean NPL, Serasa annual counts with a `method` column, annual
   mean real rates).
2. **Primary monthly specification** (2011-03 to 2026-08): change in firm NPL rate (free credit) over 12 months on the
   12-month change in the ex-ante one-year real rate lagged 0, 6, 12 and 18 months, plus the 12-month change in log
   IBC-Br; Newey-West SE (18 lags, overlapping 12-month changes). Report the cumulative response (sum of lag
   coefficients, pp of NPL per pp of real rate) with CI. Robustness: Selic instead of the real rate; lending rate;
   excluding 2020-03 to 2021-12 (pandemic credit programmes and moratoria); local projections h = 0..24 of NPL on a
   real-rate change with the same controls.
3. **Annual firm exits** (2008-2021, n = 14, imprecise: say so): exit rate and birth rate on the annual mean real rate
   (same and previous year) and real GDP growth; report point estimates, CIs, and a scatter table. Same for employer
   death rate 2015-2022.
4. **Serasa 2024-2026** (descriptive): RJ requests and bankruptcy requests by size and sector, against the Selic path
   (15% peak). Annual sparse points: show them with the method flag; no regression across the method break.
5. **Proposed model channel** (`config/bk_proposed.yaml`, proposal only): firm NPL rate and an exit-rate index as
   functions of the scenario real rate (base rate + I1 offset where used + C5 risk premium) and the scenario output gap,
   with the step-2 and step-3 coefficients and CIs; identical equation for every scenario. No model files are modified.
6. Report `outputs/bankruptcy.md` (neutral), method `docs/bankruptcy.md` (limitations: association not causation;
   Serasa public series is short; method breaks; NPL measures bank credit, not all firm finance; pandemic programmes).

## Tests
`tests/test_bankruptcy.py` (synthetic): Ipeadata/SIDRA parsing, 12-month differencing and lag alignment, NW SE on
simulated data, cumulative-response arithmetic, method flag preserved, pandemic exclusion window.

## Outputs (Codex-owned; nothing else may be modified)
`src/bankruptcy.py` (`python -m src.bankruptcy` rebuilds everything), `tests/test_bankruptcy.py`,
`data/brazil/firm_distress_monthly.csv`, `data/brazil/firm_distress_annual.csv`, `data/brazil/bankruptcy_estimates.csv`,
`config/bk_proposed.yaml`, `outputs/bankruptcy.md`, `docs/bankruptcy.md`. statsmodels is not installed: numpy OLS and
Newey-West as in `src/rates.py`. No network, no git.
