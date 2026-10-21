# PZ - Privatisation of federal state-owned companies: proceeds, lost dividends, Petrobras

Owner: Codex (inventory build, module, tests, report), Claude (data, legal tiers, review, runs). Requested by the user
2026-10-21. Neutral framing: privatisation is a **measure**, modelled only where a programme proposes it. The Lula
programme proposes none (current law: no sales). The Flávio TSE programme says "resume the National Privatisation
Programme case by case"; the candidate said in Feb 2026 he would privatise "95%" of state companies (no list published;
advisers later excluded Caixa; the team described a selective policy in Aug-Sep 2026). So the TSE programme is the
**default** and the broader statements are labelled **sensitivities**.

## Why
`config/programs_2026.yaml` F5 retires 0-2 pp of GDP of debt over 2027-2030 but "lost dividends not modelled". That
flatters privatisation. Selling a stake at a fair price swaps an asset for less debt: gross debt falls, net worth barely
moves, and the annual flow is interest saved minus dividends lost. Both must be in the model.

## Data (read-only; see `data/raw/SOURCES.md`, section PZ)
- `data/raw/brazil/soe/rtn_serie_historica_jul26.xlsx`, sheet `1.2`, rows `1.4.2.1`-`1.4.2.9`: Union dividends by
  company, R$ million current, monthly 1997-Jul 2026 (BB, BNB, BNDES, Caixa, Correios, Eletrobras, IRB, Petrobras,
  others). Labels may be in a non-UTF-8 encoding: locate rows by their codes.
- `data/raw/brazil/soe/tesouro_dividendos_2015_abr2020.xlsx`: payer-level detail 2015-Apr 2020 (splits "others").
- `data/raw/brazil/soe/sest_boletim_23a_edicao.pdf` (SOE list p.28-29, dependent execution p.25) and
  `raeef_2021_2022.pdf` (per-company equity and profit): pypdf text extraction; record page numbers.
- `data/raw/brazil/soe/yahoo_chart_*.json`: last price (`meta.regularMarketPrice`) and monthly history.
- Share counts and stakes: SOURCES.md PZ header (Petrobras 7,442,231,382 ON + 5,602,042,788 PN, state 36.61%; BB
  5,730,834,040 shares, Union 50.0%).
- `data/brazil/soe_tiers_lead.csv`: lead-developer legal tiers (A existing authority / PND; B needs a specific law;
  C excluded, constitutional or strategic; D Treasury-dependent, not saleable). Read only; flag conflicts with the PDFs.
- `data/raw/brazil/soe/ipeadata_ANP12_PDPET12.json`: Brazil oil production (report only).
- Nominal GDP and deflator: existing model inputs (`config/parameters.yaml`, `src/macro.py` readers).

## Steps (fixed before results)
1. **Inventory** `data/brazil/soe_inventory.csv`: one row per directly controlled company (2022 bulletin list; mark the
   46 -> 44 changes since then as `status_2026: verify` where unknown) with group, dependent flag, tier (from the lead
   CSV; unmatched -> D if dependent else C, flagged), Union stake, valuation basis (market value at 2026-10-21 for listed
   companies; book equity from RAEEF 2021-22 x price-to-book range 0.5-1.5 for unlisted ones, flagged as dated), Union
   dividends 2015-2025 (annual, R$ and % of GDP), dependent Treasury transfers (latest available).
2. **Union dividend yield** per company: cycle average 2015-2025 Union dividends / state-stake value, real terms.
   Petrobras separately: its Union dividends scale with the C7 commodity-price path already in the model; report the
   2015-2020 (low) and 2021-2025 (high) regimes.
3. **Sale packages** (applied only to scenarios that define them; Lula scenarios and S0 unchanged):
   - `f5` (default, the TSE programme): the existing F5 range 0-2 pp GDP, now **with lost dividends**: proceeds come from
     tier A companies (value-weighted); lost dividends = those companies' cycle-average Union dividends.
   - `broad` (sensitivity, "95%" statement, selective version): all tier A + tier B except Petrobras and BB.
   - `broad_bb_petrobras` (sensitivity, "95%" statement, maximal version): `broad` + BB control + the full state stake in
     Petrobras (Union + BNDES + BNDESPar). Caixa, BNDES, BNB, Banco da Amazônia and tiers C/D stay excluded.
   Timing: sales spread over 2027-2030; tier B not before 2028 (a law is needed). Completion probability per tier B
   company drawn U(0.3, 0.8) (stated assumption; history: Eletrobras took about 5 years; the Correios bill has been stalled
   since 2021). Block-sale discount U(0%, 15%) of market value. Each sale retires gross debt in its year; dividends stop
   from the year after. Correios: if it was loss-making on average, the sale also ends Treasury exposure to those losses
   only to the extent the Treasury actually covered them (report the evidence; default 0); Postalis contingent liability
   as a documented assumption range.
4. **Model wiring** (symmetric accounting; one code path for any scenario that sets it):
   - `debt_adjustment_by_year` = proceeds (pp GDP), as F5 today.
   - New `non_tax_revenue_by_year` (pp GDP; negative = lost dividends): enters the primary balance in the C2, C6 and C5
     debt recursions **but not** the C3 household tax incidence (`revenue_change_pp` must exclude it) and not the revenue
     multiplier (dividends are not a tax). Wire it where the primary balance is built: `src/macro.py` run_corner,
     `src/external.py`, `src/feedback.py`, `src/programs.py`.
   - CLI `--privatisation {f5,broad,broad_bb_petrobras}` (default `f5`) in `src/montecarlo.py`; recorded in metadata.
   - New draws on a separate RNG stream `[seed, 5]` so existing streams are unchanged.
5. **Report** `outputs/privatisation.md` (neutral; measures, not candidates; no programme MC results, which never go in
   the repo): inventory by tier; value of the saleable state stakes by package (R$ and % GDP); annual interest saved vs
   dividends lost by package at the S0 fixed rate and the I1 rate path (deterministic arithmetic); break-even dividend
   yield; gross vs net debt; oil: Brazil production 2002-2026 from ANP, noting that royalties, special participation and
   taxes accrue to the state whoever owns Petrobras, so only the dividend share depends on ownership.
6. `docs/privatisation.md`: method; assumptions table (every assumed number with its basis); limitations (dated unlisted
   valuations; no efficiency or price effects of privatisation on GDP beyond the existing wage effect; no change in
   Petrobras investment or production by owner: contested and not estimated here).

## Tests
`tests/test_privatisation.py` (synthetic): proceeds retire debt in the sale year; dividends stop the year after; an empty
package reproduces current outputs; `non_tax_revenue_by_year` changes debt but not C3 indicators; Petrobras stake not
double counted with BNDES; Lula scenarios unaffected; S0 and S1-S5 bit-identical in a default run.

## Outputs (Codex-owned; nothing else may be modified)
`src/privatisation.py` (`python -m src.privatisation` rebuilds inventory and report), `tests/test_privatisation.py`,
`src/programs.py`, `src/macro.py`, `src/external.py`, `src/feedback.py`, `src/montecarlo.py` and their existing test
files only as needed, `config/programs_2026.yaml` (F5 text and the package definitions only),
`data/brazil/soe_inventory.csv`, `data/brazil/soe_dividends.csv`, `outputs/privatisation.md`, `docs/privatisation.md`.
No network, no git.
