# Privatisation module method

## Accounting

For each completed sale, discounted proceeds reduce gross debt in the sale year. The sold tranche's Union dividends stop in the following year and enter `non_tax_revenue_by_year` with a negative sign. That flow changes the primary balance in C2, C6 and C5, but is excluded from household tax incidence and the revenue multiplier. The same path builder is used for every scenario that defines a package.

## Assumptions

| Assumed number or rule | Value | Basis |
|---|---:|---|
| Unlisted price-to-book range | 0.5-1.5 | Task PZ prespecification; applied to RAEEF 2021 adjusted book equity |
| Block-sale discount | uniform 0%-15% | Task PZ prespecification; no sourced distribution claimed |
| Tier-B completion probability | probability drawn uniform 0.3-0.8, then Bernoulli | Task PZ prespecification; Eletrobras took about five years and the Correios bill has stalled since 2021 |
| Sale timing | tier A: 2027-2030; tier B: 2028-2030; equal tranches | Task PZ timing; equal tranches are the neutral implementation of “spread over” the period |
| F5 size | existing uniform 0-2 pp GDP draw, capped by available tier-A midpoint value | Existing programme F5 range; PZ requires tier-A, value-weighted proceeds |
| Dividends | real annual mean of identified receipts; unassigned receipts not allocated | Archived RTN series and payer workbook; avoids inventing payer shares |
| Petrobras full state stake | 36.61% of total capital | Petrobras profile; Union direct plus BNDES and BNDESPar holdings |
| Petrobras Union direct stake | 28.67% of total capital | 36.61% full state stake less 7.94% indirect holding through BNDES and BNDESPar |
| Petrobras lost-dividend scale | 36.61 / 28.67 = 1.276945 | Applies the full-state/direct-stake ratio to RTN line 1.4.2.8; treats BNDES as passing those Petrobras dividends through to the Treasury, an upper bound because BNDES retains part of its profit; BNDES's own dividend line is unchanged and BNDES is not sold |
| Correios Treasury-covered operating loss | 0 | RAEEF identifies Correios as non-dependent; no evidence in the supplied files that Treasury covered the later reported loss |
| Postalis contingent liability | R$0-R$7.79919bn | Lower bound assumes no transfer to the state; upper bound is the 2021 accumulated technical deficit on RAEEF p.91 |
| Petrobras ownership | full state stake sold once; no BNDES double count | Petrobras fact sheet figures recorded in SOURCES.md; BNDES and BNDESPar are represented only through Petrobras's 7.94% indirect holding |
| Banco do Brasil ownership | Union stake 50.0% | BB results figure recorded in SOURCES.md |
| Debt-interest comparator | S0 fixed real rate 5.05%; I1 annual path separately | Existing model rate and `config/i1_proposed.yaml` |

## Sources and construction

The inventory is the 46 directly controlled companies listed on SEST bulletin pp.28-29. Company financials use RAEEF 2021-22 company pages recorded in `raeef_page`; dependent-budget evidence is on bulletin p.25. Market values use archived 2026-10-21 prices only when supplied share counts permit a value. Annual Union receipts use RTN sheet 1.2 codes 1.4.2.1-1.4.2.9; the payer workbook provides the partial split of “other” receipts for 2015-April 2020.

## Limitations

Unlisted valuations are dated and are ranges, not appraisals. Later “other” dividends cannot be allocated by company. The module estimates neither efficiency nor product-price effects of privatisation on GDP beyond the model's existing wage channel. It imposes no change in Petrobras investment or production by owner; that contested effect is not estimated. Legal tiers are supplied lead-developer classifications, and rows unmatched to them are explicitly defaulted and flagged. Gross-debt reduction must not be read as an equal net-worth gain.
