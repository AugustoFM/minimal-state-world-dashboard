# Debt-projection models: review against the S0 debt path

Lead developer (Claude), 2026-10-21, at the user's request: "the debt is growing in S0 always, can you review 20 best
models you can find on debt projection to make sure we are not missing anything?" Companion to D3
(`outputs/debt_panel.md`, cross-country evidence). Neutral: compares methods and evidence; no candidates or parties.

## 1. Why S0 debt keeps rising (diagnosis, central deterministic case)

S0 general-government gross debt: 78.6% of GDP (2025) -> 102.7% (2030), 137.4% (2035), 258.5% (2045), central
deterministic case (Monte Carlo median 98.6 / 130.1 / 244.4; 314 with the C5 risk-premium feedback).
Debt-dynamics split of the 2026-2045 increase (+179.9 pp):

| Driver | pp of GDP, 2026-2045 | Mechanism in S0 |
|---|---:|---|
| Primary deficits | +52.1 | Ageing raises primary spending (C1) while revenue/GDP is held at 38.97%; primary balance -0.95% (2026) -> -4.5% (2045). No fiscal reaction. |
| Interest-growth (snowball) | +127.7 | Real implicit rate 5.05% (2021-2025 median, held 20 years) vs potential growth 1.1% (2030) falling to 0.3% (2045): TFP growth central -0.93%/yr (PWT history) on a shrinking labour force. r - g reaches ~4.9 pp. |

Sensitivities (same code, central case, 2045 debt): TFP growth 0 instead of -0.93 -> 214%; real rate 4% -> 219%;
TFP 0 and real rate 3.5% -> 169% (snowball 38 pp instead of 128). The ageing deficit alone keeps debt rising in every case.

Official comparators (2035): Tesouro RPF Dec 2025 reference 88.0% (peak 88.6% in 2032; assumes the fiscal framework is
met); IFI RAF 113 June 2026 base 111.6% (optimistic 80.9%, pessimistic 148.1%; primary deficit ~1% GDP, growth 2.3%,
real implicit rate 5.0%; stabilising primary 2.1% GDP); S0 137.4% (central) / 130.1% (MC median).
S0 is above IFI because of (i) growth ~1% vs 2.3% and (ii) ageing spending with no rule or reaction.

## 2. Twenty frameworks and what each implies for us

Institutional projection frameworks

1. **IMF Sovereign Risk and Debt Sustainability Framework for market-access countries (SRDSF, 2021/22).** Baseline plus
   fan charts from historical shocks; near-term probability model; medium-term index; *realism tools* comparing projected
   fiscal adjustment, growth and r-g with cross-country distributions.
   *Us:* we have no realism check; D3 supplies the distributions. Our percentiles reflect parameter uncertainty only,
   not macro shocks.
2. **IMF/World Bank LIC Debt Sustainability Framework.** Thresholds by debt-carrying capacity (composite indicator).
   *Us:* low relevance (Brazil is a market-access country); the idea of thresholds tied to institutions carries over.
3. **European Commission Debt Sustainability Monitor / DSA in the 2024 EU framework.** No-fiscal-policy-change baseline
   *including ageing costs* (Ageing Report), deterministic stresses, stochastic projections from historical covariances;
   risk read as probability that debt declines (>= 70%); S1/S2 fiscal-gap indicators.
   *Us:* S0 is exactly this kind of baseline, and such baselines are explosive by design. The EC reports the *fiscal
   gap* (permanent adjustment needed) and probabilities rather than 2045 levels. We should do the same.
4. **US CBO Long-Term Budget Outlook (Feb 2026).** Current-law extended baseline: debt held by the public 99% (2025) ->
   175% (2056); spending 23.1 -> 27.9% GDP vs revenue 18.8%; net interest 6.4% GDP; macro feedback from debt to rates
   and output. *Us:* a 30-year no-policy-change baseline that rises without limit is standard practice, if labelled
   "not a forecast". CBO's rise is far slower than S0's because r - g is near zero.
5. **UK OBR Fiscal Risks and Sustainability (July 2025).** 50-year projections; debt >270% GDP by the early 2070s under
   unchanged policy; pensions, health and climate pressures. *Us:* same lesson as CBO/EC.
6. **IFI (Brazil Senate) Relatório de Acompanhamento Fiscal, debt scenarios (RAF 113, June 2026).** Three deterministic
   scenarios plus a stochastic fan chart; P(debt > 90% GDP in some year 2026-2030) = 78.9%; stabilising primary table by
   r and g. *Us:* the right Brazilian benchmark. Its base case assumes partial delivery of the fiscal framework and 2.3%
   growth.
7. **Tesouro Nacional Relatório de Projeções Fiscais (Dec 2025; Jul 2026 edition published).** Reference scenario with the
   fiscal framework met: debt peaks ~88.6% (2032). *Us:* an "official policy delivered" bound; with D2/F1 delivery
   evidence we can show how far delivery gaps move it.

Fiscal-behaviour (reaction) models

8. **Bohn (1998, 2008)**, model-based sustainability: a positive primary-balance response to debt is sufficient for
   sustainability; US response ~0.05. *Us:* S0 has a zero response by construction. That is the main conceptual
   difference with history; D3 estimates the response for 50 countries and Brazil.
9. **Mendoza & Ostry (2008)**, industrial vs emerging fiscal reaction: positive in both groups, but in emerging markets it
   weakens at high debt. *Us:* any S0 reaction variant should allow weaker responses at high debt.
10. **Ghosh, Kim, Mendoza, Ostry & Qureshi (2013)**, fiscal fatigue and debt limits: a nonlinear (cubic) reaction gives
   an endogenous debt limit and "fiscal space". *Us:* gives a defensible upper bound where S0 paths stop being meaningful
   (market access lost), in place of extrapolating to 250-300%.
11. **Mauro, Romeu, Binder & Zaman (2015)**, *A modern history of fiscal prudence and profligacy* (55 countries,
   1800-2011, the IMF FPP data D3 uses): prudence varies over time and responds to surprises in potential growth and
   borrowing costs. *Us:* the reaction coefficient is not a constant; treat it as uncertain.
12. **Eichengreen & Panizza (2016)**, *A surplus of ambition*: primary surpluses >= 5% GDP for 10 years occurred only 3
   times (54 countries, 1974-2013). *Us:* a realism bound on reactions too. Any rule-delivery scenario requiring large,
   long surpluses is improbable.

Debt-dynamics accounting and its residual

13. **Escolano (2010)**, IMF technical note on the debt-dynamics identity (primary balance, interest, real growth,
   inflation, stock-flow adjustment). *Us:* our `debt_step` follows it. D3 applies it to 50 countries; we should report
   S0's decomposition as above.
14. **Campos, Jaimovich & Panizza (2006)**, *The unexplained part of public debt* (117 countries, 1972-2003): stock-flow
   adjustments are a major driver, with debt growing ~3 pp GDP/yr faster than deficits imply in emerging markets
   (balance-sheet effects, contingent liabilities). *Us:* S0 sets SFA = 0. D2 found Brazil 2011-2017 mean -0.5 (SD 2.4).
   A stochastic SFA term with a fat right tail is missing.
15. **Bova, Ruiz-Arranz, Toscani & Ture (2016)**, fiscal costs of contingent liabilities (IMF WP 16/14): realisations
   average ~6% of GDP, ~10% for financial-sector events (from memory; to verify before citing). *Us:* states'
   debts, public banks and pension liabilities are not in S0's risk set.

Interest rates, growth and r - g

16. **Blanchard (2019) and Mauro & Zhou (2021)**, r - g: r < g was common, including in emerging markets, but it
   gives little warning, because r - g jumps before defaults. *Us:* S0 holds r - g at about 4-5 pp for 20 years. That is
   above Brazil's own history (D3: low-inflation 2000-2024 mean +2.83 pp, already the highest of 26 emerging economies, whose median is -2.50) and drives 71% of S0's debt increase.
17. **Lian, Presbitero & Wiriadinata (2020)**, *Public debt and r - g at risk* (56 economies): higher debt shortens
   negative r - g episodes and makes r - g higher and right-skewed, especially with foreign-currency debt. *Us:* supports
   a debt-dependent r - g, as in our C5 premium, but as a distribution, not a fixed slope.
18. **Garcia & Rigobon (2004)**, risk-management DSA applied to Brazil, and **Tanner & Samake (2008)**, probabilistic
   VAR-based debt paths for Brazil, Mexico and Turkey: simulate correlated shocks to growth, rates, the exchange rate and
   the primary balance. Brazil's debt could look sustainable on averages yet show a high probability of unsustainable
   paths. *Us:* the Brazilian precedent for adding macro-shock covariance to our Monte Carlo.
19. **Bi (2011), Bi & Leeper (2013)**, fiscal limits: the maximum debt is set by a dynamic Laffer curve and political
   tolerance; risk premia are nonlinear in debt and rise sharply near the limit. *Us:* our C5 premium is linear (5 bp
   per pp) and capped at +/-50 pp of debt change. A nonlinear premium plus a limit is the better structure; until then
   paths far beyond the limit should be read as crisis indicators, not levels.
20. **Reinhart & Sbrancia (2015)**, *The liquidation of government debt*: in 1945-1980, negative real rates and moderate
   inflation (financial repression) liquidated 3-4% GDP a year in the US and UK. **IMF WEO April 2023, ch. 3** (debt
   episodes 1970-2021): a 0.4% GDP consolidation lowers debt ~0.7 pp after 1 year and ~2.1 pp after 5; consolidations
   work in good times and with strong institutions, and growth and inflation did much of the work in large reductions.
   *Us:* history reduces debt through channels S0 switches off (inflation surprises, repression, growth surprises,
   restructuring). These should be reported as "how past debt surges ended" (D3 episodes), not modelled as policy.

Also consulted: Abbas et al. (2011/2013, Historical Public Debt Database, decomposition of debt reversals); Kose,
Nagle, Ohnsorge & Sugawara (2021, *Global Waves of Debt*); Blanchard, Leandro & Zettelmeyer (2021, stochastic DSA as an
EU standard); Celasun, Debrun & Ostry (2006, fan charts with an estimated fiscal reaction); D'Erasmo, Mendoza & Zhang
(2016, *What is a sustainable public debt?*); Collard, Habib & Rochet (2015, maximum sustainable debt); Arslanalp &
Eichengreen (2023, *Living with high public debt*: sustained reductions are rare; Jamaica the exception); Mian, Straub &
Sufi (2022, debt-dependent r - g).

## 3. What we are missing (ranked by effect on S0)

Status column added 2026-10-24 (D4, `docs/d4_debt_level_diagnostics.md`).

| # | Gap | Effect on S0 | Evidence | Proposed action (user decision) | Status |
|---|---|---|---|---|---|
| 1 | r - g calibration: real rate fixed at 2021-25 median (5.05%) on ~1% growth -> r - g ~4.9 pp | 128 of 180 pp | 16, 17, 6, D3 | Brazil 2000-2024 r - g mean +2.83 (2000-14 +2.16; 2015-19 +8.01; 2020-24 -0.34); the real rate is in line with history, the gap comes from low growth. Show r - g sensitivity; see the interest-rate review (I1). | Partially addressed: I1's real-rate path (`config/i1_proposed.yaml`, `--rate-path i1`) is wired as an off-by-default sensitivity (W1). No further r-g recalibration was done in D4; left open. |
| 2 | Growth: central TFP -0.93%/yr, below IFI/Tesouro (~2.3% GDP) | ~45 pp | 6, 7 | Keep as the model's evidence-based central case, but add an "official growth" sensitivity (TFP 0). | Open. Not pursued in D4; the TFP=0 "official growth" sensitivity is a separate small addition, not done here. |
| 3 | No fiscal reaction in S0 | 52 pp primary + snowball | 8-12 | Keep S0 as the no-policy-change reference (needed for paired differences); add S0_frf (D3-estimated reaction) and S0_rule (framework with F1 delivery bias) as level variants. | Addressed (partially): `src.debt_level_diagnostics` adds `frf_emerging` (D3's emerging-panel rho) and `frf_brazil_robustness` (Brazil's own, oppositely-signed estimate) as S0-only diagnostics, deliberately kept out of the R/E policy grid, per this row's own instruction. S0_rule (F1 delivery-bias framework variant) is not built; left open. |
| 4 | Reporting levels beyond any historical precedent | presentation | 3, 10, 19 | Report probabilities (debt > 90/100/120%), the fiscal gap and the stabilising primary, as EC/IFI do; flag paths beyond the D3 historical maximum as crisis indicators. | Addressed: `src.debt_level_diagnostics` reports exactly these (`outputs/debt_level_diagnostics.md`), and the nonlinear premium (row 5) is capped rather than left to compound without bound past the historical range. |
| 5 | Linear risk premium with a ±50 pp cap | +70 pp by 2045 (feedback run) | 10, 17, 19 | Nonlinear premium up to a debt limit (fiscal fatigue); premium only as sensitivity until estimated. | Addressed, as a choice: `premium_nonlinear` in `src.debt_level_diagnostics` (flat below the D3 P95 debt level, then rising with the square of the excess, capped at 2,000bp). Explicitly labelled a modelling choice, not an estimated ceiling, since none exists in this model's data; the default C5 linear premium is unchanged for every published scenario. |
| 6 | SFA = 0 | small mean, wide tails | 13-15, D3 | Brazil's FPP-based SFA mean +3.11 pp is mostly a primary-balance definition gap (FPP pb exceeds official BCB by 2.44 pp on average), so ~0.7 pp/yr on official data; emerging low-inflation SD ~3.9. Add as a stochastic term. | Addressed: Brazil's own-history stochastic SFA term is wired by default (`docs/sfa.md`, prior to D4). D4 adds `sfa_emerging` as a comparison, sampled from this row's own emerging-panel moments, i.i.d. per year (no raw cross-country annual series is checked in to block-bootstrap); it is a diagnostic comparison only, not a change to the default. |
| 7 | Macro-shock covariance (growth, rate, FX, primary) | width of fan | 1, 3, 6, 18 | Bootstrap historical joint shocks (Brazil 2000-2024) in D1 alongside parameter draws. | Open. Not pursued in D4; parameters remain sampled independently in `src.montecarlo`, as documented. |
| 8 | Inflation / repression / restructuring channels | historical reductions | 20 | Report only (D3 episodes); not modelled as policy. | Unchanged by design: reported only in `outputs/debt_panel.md`'s historical episodes, not modelled as a policy lever. |

None of these changes the paired scenario differences much: they share S0's r, g and SFA. Items 1-3 move levels a lot, and
item 1 is the largest. Tier 2 (levels) of the D2 gate fails for the same reason.

## 4. D3 cross-country evidence (summary; full report `outputs/debt_panel.md`)

- S0's 2025-2045 change (+165.8 pp, MC median) is at the 99.8th percentile of 1,400 observed 20-year windows (50 countries,
  1975-2024); only Venezuela 1999-2019 matches it together with S0's -7.7% terminal primary balance (hyperinflation and
  extreme SFA, not a smooth drift). Japan 1990-2014 (+140 to +160 pp) is the only smooth precedent.
- Debt surges end: five years after a local peak debt is a median 14.6 pp lower, ten years after 16.8 pp lower.
- Ageing: primary expenditure rose 0.66 pp GDP per point of 65+ share in history (S0: 0.74), and primary balances fell
  0.49 pp per point. S0's spending drift is realistic; the absence of any reaction is not.
- Fiscal reaction: emerging long-run response 0.038 (primary), 0.044 (2000-2024), 0.088-0.104 (low-inflation). The
  response that would stabilise debt is 0.049 at S0's 2045 r - g and 0.028 at Brazil's historical r - g. So most estimates
  stabilise debt at historical r - g, and only the low-inflation estimates do so at S0's.
- Brazil itself, 2000-2024 (official BCB primary balance): long-run response -0.037 (n = 22, small sample). Brazil's
  primary balance fell while its debt rose, the opposite of the panel norm, and r - g was the highest among emerging peers.
  This supports keeping a no-reaction S0 as the reference while adding reaction variants as level sensitivities.
