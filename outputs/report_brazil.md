# Brazil state-size scenarios: a written report

**Status: internal project report, not a forecast or a policy recommendation.**
Companion to the raw results (`outputs/results_brazil.md`), the back-test
(`outputs/backtest.md`), the follow-up debt-level diagnostics
(`outputs/debt_level_diagnostics.md`), the interactive dashboard
(`dashboard/brazil.html`) and the academic write-up (`paper/minimum_state_brazil.tex`).

Run seed `20261020`, 1,000 Monte Carlo draws, inputs commit `de8c2e2c`, created
2026-10-23. Back-test: **Tier 1 (scenario differences vs S0) PASS; Tier 2
(absolute debt/GDP levels) FAIL, permanently** — read Section 6 before citing any
debt *level* from this report.

---

## 1. The question, in one paragraph

Brazilian general-government primary spending was 39.8% of GDP in 2025.
Population ageing alone will raise age-related spending (pensions, health) by a
further 3.3 percentage points of GDP over the next decade and 7.3 points over two
decades, with no change in policy. This project builds a model to answer, with
ranges rather than single numbers: what happens — to growth, debt, unemployment,
inequality, poverty and health outcomes — if Brazil responds to that pressure by
cutting the state's size, holding it constant, or expanding it; and how much of
any such answer is a sourced estimate, a disclosed modelling choice, or an
acknowledged gap.

It does **not** answer who should win an election, whether corruption will occur,
or what debt level Brazil will actually reach. Section 6 explains why the last of
those, in particular, is a question this kind of model cannot honestly answer with
a single number.

## 2. The scenario grid

Every scenario is compared against **S0**, a status-quo baseline in which pension
and health spending rise with the population's age structure and nothing else
changes — not a forecast, a reference point. Against it:

| Scenario | What it is | 10-year size vs S0 |
|---|---|---:|
| S1 | Spending held at today's share of GDP (the cost of fully offsetting ageing) | not applicable (constant share) |
| R_mod | Moderate reduction | 2 pp below S0 |
| R_amb | Ambitious reduction | 4 pp below S0 |
| R_max | Precedent-based stress case (B1: 10th percentile of observed middle-income changes); needs legislation of nearly its full size | 5.5 pp below S0 |
| E_mod | Moderate expansion, debt-financed | 2 pp above S0 |
| E_amb | Ambitious expansion, debt-financed | 4 pp above S0 |
| E_mod_tax | E_mod financed by an equal-sized tax rise instead of debt | 2 pp above S0 |
| E_amb_tax | E_amb financed by an equal-sized tax rise instead of debt | 4 pp above S0 |

A default reduction/expansion is composed 40% pension/indexation, 25%
subsidies/tax expenditures, 20% administrative efficiency, 15% other current
spending, with public investment and means-tested transfers protected; four
alternative compositions (pension-only, efficiency-only, an investment-also-cut
stress test, and a compensating-transfers variant) are run as sensitivities,
because **the composition of a change, not only its size, drives most of its
consequences** — this is the single most load-bearing finding in the project's own
documentation (`docs/c2_macro.md`, `docs/c3_micro.md`).

Results are reported at 5, 10, 15 and 20 years; **10 years is the model's own
primary validated horizon** (`config/scenarios.yaml`). Every number below is the
`default` composition, `transitory` multiplier persistence, 10-year horizon,
unless stated otherwise; the dashboard and `outputs/results_brazil.md` give every
other combination.

## 3. How the model is built

Nine chained blocks, each reading only the outputs of the one before it, with
every coefficient traceable to a single parameter registry (`config/parameters.yaml`):

1. **Demographic/fiscal baseline (C1).** IBGE population projections and National
   Transfer Accounts age-profiles (2003, 2018 vintages) project pension, health
   and education spending by age structure.
2. **Macro block (C2).** A Cobb-Douglas production function with capital
   accumulated from Penn World Table data, Brazil-specific fiscal multipliers by
   spending category (Sanches et al.), and the debt identity
   `d_t = (1+i)/(1+g) d_{t-1} - pb_t`. Central 10-year S0 debt: 145.5% of GDP
   (2035), of which 61% of the ten-year increase is the interest-growth
   differential, not the (ageing-driven) primary deficit.
3. **Household microsimulation (C3).** A static arithmetic microsimulation of the
   2025 PNAD Contínua cross-section, translating a scenario's GDP, employment and
   tax/transfer effects into the Gini coefficient, two poverty lines, and top
   income shares.
4. **Social outcomes (C4).** Health spending linked to infant mortality
   (elasticity -0.126, Szklo, Clarke & Rocha 2024) and life expectancy
   (elasticity 0.04, Gallet & Doucouliagos 2017).
5. **Long-run feedback (C5).** Schooling into human capital, health into output,
   public capital (currently inactive: no sourced Brazilian public-capital stock),
   and a sovereign-risk premium that responds to a scenario's own debt deviation
   from its 2025 level (5bp per pp of GDP, capped at ±50pp).
6. **External block (C6/C7).** Commodity terms-of-trade and exchange-rate shocks,
   applied identically to every scenario within a Monte Carlo draw so that
   differences between scenarios stay attributable to policy, not shared luck.
7. **Governance (G1/G2).** Routine social-spending leakage (2.8-13%, cancels
   between scenarios by construction) and rare major-corruption shocks (3-8% a
   year, calibrated on Collor 1992 and Lava Jato), shared identically across every
   scenario and both 2026 candidate programmes within a draw.
8. **2026 programme mapping (W1-W3, P1).** The same machinery, unmodified, maps
   the two filed run-off programmes onto comparable fiscal paths — see Section 7.
9. **Monte Carlo (D1) and back-test (D2/D4).** 1,000 draws propagate parameter
   uncertainty; Section 6 covers validation.

## 4. Headline results at 10 years (default composition, transitory persistence)

Each cell is the median, with the 10th-90th percentile range in brackets, across
1,000 draws, paired against S0 within each draw.

| Indicator | R_mod | R_amb | E_mod |
|---|---:|---:|---:|
| GDP level vs S0 (%) | -0.40 [-0.48, -0.31] | -0.79 [-0.97, -0.62] | +0.40 [+0.31, +0.48] |
| Debt/GDP vs S0 (pp) | -11.6 [-12.4, -10.7] | -23.3 [-24.7, -21.4] | +11.6 [+10.7, +12.4] |
| Unemployment vs S0 (pp) | +0.07 [+0.06, +0.09] | +0.14 [+0.11, +0.17] | -0.07 [-0.09, -0.06] |
| Gini vs S0 (points) | +0.16 [+0.13, +0.57] | +0.36 [+0.33, +1.27] | -0.10 [-0.46, -0.08] |
| Poverty below R$759 vs S0 (pp) | +2.13 [+2.07, +2.41] | +2.87 [+2.68, +3.74] | n.a.* |
| Infant mortality vs S0 (per 1,000) | +0.035 [+0.017, +0.055] | +0.069 [+0.034, +0.110] | -0.035 [-0.056, -0.017] |
| Life expectancy vs S0 (years) | -0.066 [-0.095, -0.035] | -0.133 [-0.190, -0.071] | +0.067 [+0.036, +0.096] |

\* E_mod's poverty figure is omitted here for space; see `outputs/results_brazil.md` (it is negative, i.e. poverty falls, consistent with the sign pattern above).

Three things stand out:

- **The GDP cost of a given reduction depends enormously on how long the
  multiplier effect is assumed to last.** Under `persistent` multipliers instead
  of `transitory`, R_amb's 10-year GDP cost roughly quintuples (-0.79% becomes
  -1.96%; by 20 years, -6.85%). No single "the cost of consolidation" figure is
  defensible without stating this assumption.
- **Every reduction scenario raises the Gini coefficient and infant mortality;
  every expansion lowers both**, in a direction consistent with the independent
  literature each block draws on (Ball, Furceri, Leigh & Loungani 2013 for the
  distributional channel; Szklo, Clarke & Rocha 2024 for the health channel) —
  reassuring in direction, though the two blocks were not calibrated to match
  each other, so the magnitudes should not be read as a joint estimate.
- **Debt falls roughly in line with the arithmetic of the reduction itself**: an
  ambitious, sustained 4pp-of-GDP cut removes about 23pp of GDP of debt by 2035,
  which is the mechanical consequence of the debt identity, not a sign that
  consolidation "pays for itself" through growth.

## 5. What the model says about S0 itself, with no policy change

Independent of any reduction or expansion, S0's own debt path rises from 78.6% of
GDP (2025) to a central 145.5% by 2035, because the interest-growth differential
(central real rate 5.05%, central potential growth under 1%) dominates even a
widening ageing-driven primary deficit. This is not a statement that Brazil is
heading for a debt crisis by 2035; it is a statement that **a baseline with no
fiscal reaction to rising debt is explosive by construction**, which is exactly
what such baselines are designed to show (the IMF, European Commission and CBO's
own long-run baselines share this property). Section 6's D4 diagnostics quantify
what a typical country's historical fiscal reaction would imply instead.

## 6. The back-test, read honestly

Before anything above is treated as fit to use, the model's own equations are
checked against Brazil's recent history (`outputs/backtest.md`). Two tiers:

**Tier 1 (differences vs S0): PASS.** Three independent checks: the debt
identity's one-step error (MAE 2.05pp, 2011-2024); the growth-accounting block,
on a genuinely out-of-sample TFP window (mean error -0.04pp/yr, 2006-2019 — fixed
2026-10-24, see the box below); and the external-shock channel's held-out forecast
(RMSE 3.00 vs a naive benchmark of 3.88, 2015-2024). All three pass. **This is the
gate for publishing the scenario-comparison results in Sections 4-5.**

> **A defect, found and fixed.** The growth-accounting check originally used a
> TFP rate estimated over 2000-2019 to test 2006-2019 — a window containing the
> test period, so its PASS showed internal consistency, not genuine predictive
> skill. A second statistic, using a TFP rate from 1996-2005 (strictly before the
> test period), was added on 2026-10-24 and is now what the gate rates. It still
> passes, and more comfortably than the flawed original (-0.04pp/yr vs the old
> 0.17pp/yr) — a result, not an assumption.

**Tier 2 (absolute debt/GDP levels): FAIL, and expected to stay FAIL.** A debt
projection anchored in 2017 and run forward six years misses observed 2024 debt
by 12.5pp of GDP even with the best available historical correction. The
dominant source is discretionary Treasury-to-BNDES lending and BNDES
early-repayment/Central Bank result-transfer operations (2011-2022) — political
and administrative decisions with no relationship to growth, interest rates or
the terms of trade, so **no amount of better modelling turns this into a
point-forecastable quantity.** The model's response is not to chase a better
point estimate but to represent the uncertainty honestly: a stochastic
stock-flow-adjustment term, bootstrapped from Brazil's own 2011-2024 history,
widens every published debt-*level* band (it does not change the Tier-1-gated
*differences* in Sections 4-5, which is why those remain publishable).

**What the follow-up diagnostics add (`outputs/debt_level_diagnostics.md`, D4,
2026-10-24).** Rather than leave the debt-level question at "FAIL, move on," a
dedicated 300-draw analysis answers it with ranges instead of a point:

| | 10 years | 20 years |
|---|---:|---:|
| P(S0 debt/GDP > 90% of GDP) | 95.0% | 100.0% |
| P(S0 debt/GDP > 100% of GDP) | 86.3% | 100.0% |
| Fiscal gap (further adjustment needed to stabilise debt at that year's own rates) | +7.4pp of GDP | +15.6pp of GDP |
| Debt/GDP if Brazil's primary balance reacted the way a typical emerging economy's has historically (`frf_emerging`) | 124.0 [99.3, 145.6] | 206.7 [146.4, 270.9] |
| Debt/GDP if it reacted the way Brazil's own history suggests instead (`frf_brazil_robustness`, opposite sign) | 138.9 [104.8, 168.8] | 308.8 [184.8, 441.8] |

Brazil's own estimated fiscal-reaction coefficient is *negative* (primary balance
has historically worsened as debt rose, the opposite of the stabilising pattern
seen in most emerging economies) — which is itself informative: S0's "no
reaction" assumption is, if anything, more optimistic than Brazil's own recent
history, not a worst case.

## 7. The 2026 candidate programmes: method only, no results

The same unmodified machinery translates the two run-off candidates' filed
programmes into comparable fiscal paths. The incumbent's path follows the
constitutional spending-growth rule already in force (Complementary Law
200/2023: real spending growth capped at 70% of real revenue growth, bounded
0.6-2.5% a year). The challenger's path follows an explicit debt-stabilising
primary-balance rule, moving linearly over an assumed 2-6 year horizon to the
balance that would stabilise (not reduce) the 2026 debt ratio.

**This report does not publish a headline comparison of the two**, for two
reasons stated plainly in the project's own method note (`docs/p1_programmes.md`):
neither programme specifies the exact composition of its implied cuts, so the
model's own default-composition assumption does most of the work in determining
the result; and this project's internal protocol withholds any debt-level result,
programme-specific or otherwise, until the Tier 2 gate above is cleared or
explicitly caveated — which this report has now done for the methodology, not
for a specific programme comparison. Producing that comparison, reviewed against
this standard, remains future work.

## 8. Limitations, stated once rather than scattered

- **This is a comparative-statics accounting exercise, not a general-equilibrium
  model.** Prices, wages and expectations do not adjust except through the
  specific, named channels above.
- **Governance parameters are identical across every scenario and both
  programmes by design**, because the available perception indices (WGI, CPI)
  cannot distinguish recent Brazilian governments within their own measurement
  uncertainty. The model cannot and does not estimate any candidate's corruption
  propensity.
- **Percentile ranges describe parameter uncertainty only** — not forecast error,
  not model misspecification, and (outside the explicitly labelled `*_with_external`
  and D4 columns) not external shocks or major-corruption risk.
- **Debt *levels* are not validated** (Section 6); only paired *differences*
  against S0 are.
- Public-capital feedback is inactive (no sourced Brazilian stock); schooling,
  physician-access and the composite HDI are not modelled for want of a credible
  Brazilian elasticity; distributional (C3) results are reported only for the
  default composition.

## 9. Where to look for more

| Question | File |
|---|---|
| Full numeric results, every scenario/horizon/variant | `outputs/results_brazil.md` |
| Back-test detail | `outputs/backtest.md` |
| Debt-level diagnostics (D4) | `outputs/debt_level_diagnostics.md` |
| Interactive exploration | `dashboard/brazil.html` |
| Every parameter, its source and vintage | `config/parameters.yaml` |
| Per-block method notes | `docs/c1_baseline.md` … `docs/c7_external_v2.md`, `docs/governance.md`, `docs/corruption.md`, `docs/w1_wiring.md` … `docs/w3_anticorruption.md`, `docs/d1_montecarlo.md`, `docs/d4_debt_level_diagnostics.md` |
| 2026 programme mapping | `docs/p1_programmes.md` |
| Academic write-up with full literature review | `paper/minimum_state_brazil.tex` |
