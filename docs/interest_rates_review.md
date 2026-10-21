# Interest rates in Brazil: where they are, why they are high, what lowers them, and the programmes

Lead developer (Claude), 2026-10-21, at the user's request. Companion to I1 (`outputs/rates.md`, estimates) and D3.
Neutral: measures are compared against the same evidence-based criteria; no candidate is scored as better or worse.
Results for the programme scenarios are not published (runoff 2026-10-25); this file covers methods and evidence only.

## 1. Where rates are (BCB SGS; monthly averages)

| Period | Selic (avg, % a.y.) | Real ex-post (Selic deflated by 12m IPCA) |
|---|---:|---:|
| 1999-2002 | 18.06 | 9.88 |
| 2003-2006 | 18.50 | 9.65 |
| 2007-2010 | 11.05 | 5.96 |
| 2011-2014 | 9.81 | 3.45 |
| 2015-2016 | 13.72 | 4.44 |
| 2017-2018 | 8.28 | 4.56 |
| 2019-2022 | 6.39 | 0.26 |
| 2023-Sep 2026 | 13.12 | 8.13 |
| Sep 2026 | 13.78 | 8.80 (IPCA 12m 4.58) |

The Selic peaked at 15.00% and has been cut five times to 13.75% (Sep 2026). The BCB's neutral real rate is reported at
~5% (market estimates 6-8%). So the real policy rate is 3-4 pp above neutral: restrictive by design, to bring inflation
(Copom 2026 projection ~5.2%, target 3%) down.

**Both programmes' claims check out on their own terms.** The 2019-2022 period has the lowest average Selic since 2000
(Flávio programme, p.33), but the real rate was ~0 because of the 2020 global zero-rate period and the 2021-22 inflation
surge. The Selic was 13.65% in Dec 2022 (Lula programme, "we inherited a high Selic"), after being raised from 2% (Mar
2021) to 13.75% (Aug 2022) in the global inflation shock. Neither period's rate is attributable to fiscal policy alone.

## 2. Why Brazil's rates are high (evidence)

1. **Low national and public saving.** Segura-Ubiergo (IMF WP 12/62): Brazil's equilibrium real rate would converge to
   peers if domestic saving rose, and most strongly if public saving rose. About 2 pp remain unexplained (credit
   segmentation, indexation).
2. **Fiscal risk premium.** Blanchard (2004) and Favero & Giavazzi (2004): in 2002, with high debt and dollar-linked
   debt, higher rates could raise default risk ("fiscal dominance"). Today's debt is mostly domestic (lower risk of that
   loop), but BCB WP 637 (2007-2025 term premia) finds fiscal indicators matter for long rates in periods of
   uncertainty. Market episodes: long real yields fell after the 2019 pension reform and rose in 2014-15 and late 2024 on
   fiscal doubts. D3: high debt makes r - g higher and right-skewed (Lian, Presbitero & Wiriadinata 2020).
3. **Debt structure.** A large share of federal debt is Selic-linked (LFT) or short, so a Selic rise passes into the
   interest bill within one to two years (I1 item 5 estimates the pass-through).
4. **Earmarked and subsidised credit** (BNDES, rural, housing) blunts monetary transmission, so the Selic must move more.
   Evidence that TJLP lending raised the neutral rate: Furtado & Barboza (2021). The 2018 move from TJLP to TLP reduced this.
5. **Indexation and inflation inertia** (Segura-Ubiergo 2012), including minimum-wage and benefit indexation.
6. **Global rates.** US rates and risk appetite move Brazil's rates (D2/C7: the external channel B was not supported
   out of sample for spreads, but US rates enter I1 as a control).

## 3. What evidence says lowers rates durably (criteria applied identically to each programme)

| Criterion | Evidence | Lula programme (TSE) | Flávio programme (TSE) |
|---|---|---|---|
| A. Explicit debt anchor | Fiscal rules with a debt anchor lower risk premia when credible (EC DSA, IMF fiscal-rules literature); Brazil 2016 cap and 2019 pension reform episodes | Keeps LC 200/2023 (spending growth 70% of revenue growth, primary targets); no debt target stated | New rules "focused on stabilising and then reducing debt/GDP", primary surpluses, no number or deadline stated |
| B. Size of adjustment vs need | Debt-stabilising primary ~2.1% GDP (IFI RAF 113); consolidated primary ~-0.5% GDP (IFI, 2025-26) | Rule-based path (P_lula_rule) or 2022-25 trend (P_lula_record); 2027 PLOA target +0.5% GDP (questioned by market) | Size not stated in programme; reported plan 1.5-2.0% GDP (Folha, denied) and a press-reported 1.5% GDP primary improvement in 18 months (investor note); modelled as 1.0/1.5/2.0 |
| C. Revenue side | Tax cuts without matching spending cuts widen deficits | Tax increases on top incomes / fewer tax expenditures (unquantified, 0 to +0.5 pp) | Tax cuts on VAT, fuel, energy, payroll (unquantified, 0 to -1.0 pp) |
| D. Delivery record | F1: Brazilian governments miss planned primary results; pooled median miss applied to both | Same F1 bias | Same F1 bias |
| E. Subsidised credit (transmission) | Earmarked/subsidised credit raises the Selic needed | Expands subsidised lines (Plano Safra, cheaper credit lines) | Limits Treasury-subsidised credit |
| F. Central-bank autonomy | Autonomy (LC 179/2021) lowers inflation expectations | Not mentioned (law stays: current law) | Not mentioned (law stays) |
| G. Inflation inertia / indexation | Real minimum-wage gains raise benefit spending and indexation | Keeps real-gain rule (0.6-2.5%/yr) | Not in programme; reported plan: INSS/BPC by INPC only (denied) |

Reading the table: the programmes differ on A, C, E and G in opposite directions. Flávio's states a debt objective and
limits subsidised credit, but cuts taxes. Lula's keeps an existing, tested rule and raises taxes on top incomes, but has no
debt anchor and keeps benefit indexation and subsidised credit. **The model does not score these features.** Each
programme's rate effect comes only from its own projected debt path, through the same debt-to-rate sensitivity (C5
premium; I1 item 3 tests it against market expectations, section 5), after the same F1 delivery bias. Markets' 1 pp rally after the first round (press reports)
reflects expectations about policy, not evidence about outcomes, and is not used as an input.

## 4. Why the models disagree on Brazil's debt (2035, % GDP)

| Projection | 2035 debt | Growth | Real implicit rate | Primary balance | Fiscal behaviour |
|---|---:|---|---|---|---|
| Tesouro RPF (Dec 2025) | 88.0 | official (~2.5%) | falls with Selic | framework met (surpluses) | rule delivered |
| IFI RAF 113 base (Jun 2026) | 111.6 | 2.3% | ~5.0% | deficit ~1% GDP | partial delivery |
| IFI pessimistic | 148.1 | lower | higher | larger deficits | — |
| S0 (this model, MC median) | 130.1 | ~1.0% falling to 0.4% (TFP history) | 5.05% fixed | -0.95% -> -4.0% (ageing, revenue fixed) | none (no-policy-change) |

The spread comes from three assumptions: (1) growth (S0 extrapolates Brazil's productivity record onto a shrinking labour
force; official projections assume ~2-2.5%); (2) the primary balance (S0 lets ageing raise spending with revenue
fixed; official projections assume the rule is met); (3) the real rate (S0 fixed; I1 builds a path from today's peak).
S0 is a reference for paired differences (D2 Tier 1 passes), not a forecast (Tier 2 fails).

## 5. What I1 found (`outputs/rates.md`, `data/brazil/rates_estimates.csv`)

- **Today:** ex-post real Selic 8.77% (Selic 13.75%, IPCA 12m 4.58%): 72nd percentile since 2000, 90th since 2010.
  Focus (16 Oct 2026) expects real policy rates of 7.6% (2026), 7.4% (2027), 6.5% (2028), 6.3% (2029).
- **Fiscal expectations and expected rates (market association, not causal).** Monthly changes 2010-2026 (n = 200):
  expected primary balance -3.6 bp per pp of GDP (95% CI -15 to +8); expected net debt +0.2 bp per pp (CI -2.5 to
  +2.8). Since 2017: +1.5 bp per pp of expected net debt (CI -0.4 to +3.4); gross debt from 2018: +1.0 bp (CI -1.6 to
  +3.7). US 10-year yields dominate the levels regression (+0.71 pp per pp). **Monthly revisions to Focus fiscal
  expectations do not move the expected policy rate three years ahead by a detectable amount.** This measures the
  expected *policy* rate, not the term premium on long bonds, where BCB WP 637 does find a fiscal effect; the model's
  C5 premium (5 bp per pp of debt) is above the Focus-based association but within the range of the term-premium
  literature, so it stays, applied identically to every scenario, with I1's near-zero estimate as the low sensitivity.
- **Events (descriptive):** expected real rate t+3 fell 0.60 pp around EC 95 (Dec 2016) and 0.48 pp around the pension
  reform (Oct 2019); it rose 0.48 pp around the Nov-Dec 2024 package, when expected debt rose 4.5 pp. Other news overlaps
  these windows, so they show co-movement only.
- **Pass-through to the debt bill:** each 1 pp of Selic moves the implicit nominal rate on gross debt by ~0.43 pp in the
  long run, ~94% of it in the same year (2010-2025, n = 15, imprecise: CI 0.21-0.65).
- **Proposed S0 rate path (proposal, not yet in the model):** 2025 implicit real rate on debt 8.63% (IPCA-deflated);
  Focus to 2029, then the policy rate converges to the 5.0% neutral by 2034. The implied real rate on debt is 7.9%
  (2026), 7.1% (2030), 6.7% (2034 onward), against the fixed 5.05% now in S0. This would **raise** S0's debt path: today's
  peak is above the 2021-2025 median used by S0, and the low pass-through keeps it there. Range for the long-run neutral
  rate: 4.5-6.0%. This changes S0 levels, so it is a lead/user decision (sensitivity first); differences between
  scenarios are affected only through the shared r - g.

**Implication for "why models disagree":** S0's fixed 5.05% is *below* what today's market path implies for the next
decade; official projections (Tesouro RPF) assume the rate falls faster. The rate assumption alone moves 2035 debt by
tens of points of GDP (D3 sensitivities: real rate 4% instead of 5.05% lowers 2045 debt from 258 to 219).
