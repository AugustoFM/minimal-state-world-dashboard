# Education, programmes, entrepreneurship and crime: evidence review (lead developer)

Lead developer (Claude), 2026-10-22, at the user's request. Companion to ED (`outputs/education.md`). Neutral: the
same evidence and the same channels apply to any scenario that changes education spending, up or down.

## 1. What changed, by period (facts; sources in `data/raw/SOURCES.md` and below)
| Item | Facts |
|---|---|
| Federal technical network (Rede Federal / IFs) | 140 units in 2002; Lei 11.892/2008 created 38 Institutos Federais; 661 units in 2019; 682 in 2024; 100 new campi announced March 2024 (Novo PAC, R$ 3.9 bn, works due end-2026); 30 advanced units converted in 2025 (686 units) |
| Federal universities | Reuni expansion (2007 onward); total executed budget peaked in 2019 (R$ 69.8 bn, Sou Ciência/Unifesp series) and was 9.5% lower in real terms in 2024; discretionary budget (real): R$ 5.5 bn 2019, 4.7 bn 2020, 3.5 bn 2021, about 5 bn 2024 (Poder360); the MEC reports a 22% increase under the current government (different basis). Measures differ (total vs discretionary vs investment): the module uses Tesouro COFOG "tertiary education" consistently |
| ProUni (2005) | private-university scholarships; offers rose to a record in 2024-26, but take-up fell (industry reports ~30% of 2024 offers used) |
| Fies | new contracts rose from ~76 k (2010) to a peak of ~733 k (2014), were cut from 2015 (fiscal adjustment) to ~47 k (2020); ~112 k places offered in 2025 |
| Pé-de-Meia (2024) | savings incentive for public secondary students; ~R$ 12 bn a year; ex-ante evaluation (Paes de Barros et al., Insper/CEEI, March 2026): composite dropout among vulnerable students 26.4% -> 19.9% (-6.5 pp); MEC administrative figure (-43% dropout 2024-25) is not a causal estimate; secondary enrolment fell 5.4% 2024-25 |
| Programme proposals 2026 | Lula: keep and expand (IF campi, Pé-de-Meia, university budget inside the fiscal rule). Flávio (TSE plan, chapter "Preparar para o Brasil que existe"): move federal universities' governance from the MEC to the MCTI, MEC focused on basic education, research oriented to "productive impact"; the plan states no budget figure and does not say whether IFs move |

The cuts and expansions do not map cleanly onto presidencies: Fies contracts and university discretionary budgets
fell from 2015 (fiscal adjustment) and fell further in 2019-2021; the 2023-2026 recomposition is partial on some
measures. The module uses one consistent spending series and lets each scenario's own spending path drive results.

## 2. Evidence on the channels
1. **Schooling -> earnings and productivity (strong evidence).** Returns to schooling in Brazil are high (Mincerian
   returns around 10% per year, higher for tertiary). Already in the model: C4 adult schooling -> C5 human capital.
2. **Education -> entrepreneurship (descriptive gradient; weak causal evidence).** PNAD shows the employer share of
   workers rises with education (tables 7193/7195/7196). But the best Brazilian quasi-experiment on the federal
   expansion (Bergmann, Ribeiro, Niquito & Teixeira 2020, municipal difference-in-differences 2000-2010, 5,507
   municipalities) finds **no significant effect of new IF or university campuses on the local employer rate** (e.g.
   IF effect on employer rate, ages 18+, -0.045 pp, SE 0.042) and positive effects on formalisation for some groups
   (IF, ages 50+: +0.58 pp, SE 0.32). So the entrepreneurship channel starts at zero, with a small positive
   sensitivity, and works mainly through the composition of the workforce, not local campus effects.
3. **Demand effect of university spending (input-output, not causal).** Vinhais & Guilhoto: the 2004-2010 federal
   university expansion added ~0.36% of 2004 GDP through demand. In the model, that is the existing spending
   multiplier, not a separate channel.
4. **Education -> crime (causal evidence, mostly via incentives).** Chioda, De Mello & Soares (2016): extending Bolsa
   Família to ages 16-17 (2008) significantly reduced crime around São Paulo schools (instrument: timing x school
   composition; magnitude to be read from the paper before use). A compulsory-schooling amendment without cash (2009)
   had negligible effects except in non-poor municipalities (J. Development Studies 2023). Lochner & Moretti (2004,
   US): schooling lowers incarceration and arrests; social savings from crime reduction = 14-26% of the private return
   to high-school graduation. Implication: programmes that keep poor youths in school with an income incentive
   (Pé-de-Meia, conditional transfers) have the clearest crime evidence; budget for universities affects crime little.
5. **Hope and expectations.** Survey evidence on youth expectations is qualitative; the module does not quantify it.

## 3. Modelling consequences
- Default for every scenario: current-law education spending from S0 (C1/C2), scenario changes through the existing
  package mechanics.
- New outputs (ED): attainment path by cohort, employer-share change through workforce composition (gradient x
  attainment, with a zero-to-small local effect per Bergmann), youth-homicide change through secondary completion
  (literature range, with Pé-de-Meia-type incentive programmes treated separately from general spending).
- The Flávio university move: governance change with no stated budget -> default current law; sensitivity of a real
  university budget cut (range stated as an assumption, symmetric with any increase), never presented as the plan.

## 4. International benchmarks (user request 2026-10-22: Germany, Switzerland, USA, India, peers)
| Country / study | Design | Finding (as published) | Use in the model |
|---|---|---|---|
| 78 countries, ~15,000 universities, 1,500 regions, 1950-2010 (Valero & Van Reenen 2019, *Economics of Education Review* 68; NBER w22501) | regional panel, region FE and year dummies (association; authors find no sign of reverse causality or pure demand effects) | +10% universities in a region -> about +0.4% GDP per capita; spillovers to neighbouring regions; channels: human capital supply and innovation | upper bound for a long-run level effect of higher-education capacity on GDP per capita: elasticity 0.04, phased in over 10-20 years |
| USA, new colleges and land-grant colleges (Andrews, NBER w26235 and later versions) | winners vs runner-up counties (diff-in-diff) | +40% to +62% patents per year in the winning county; mostly through attracting people (migration); only ~12% of local patents from the college's own alumni/faculty; land-grant counties' population +45% by 1940 | local innovation gains are partly relocation: national effect smaller than local -> haircut the regional elasticity (central = half) |
| Germany, Switzerland, Denmark: dual apprenticeship (Hanushek, Schwerdt, Woessmann & Zhang 2017, *J. Human Resources*) | life-cycle comparison, IALS data | vocational graduates enter work more easily, but employment advantage reverses at older ages (less adaptable skills); attempts to export the German system mostly show little long-term effect (Bertelsmann review) | IF/technical expansion raises youth formal employment early; long-run productivity effect no larger than general schooling; no extra premium assumed |
| OECD growth (Hanushek & Woessmann; Hanushek & Kim 1995) | cross-country growth regressions | cognitive skills (quality), not years or tertiary headcount, explain growth differences; 1 s.d. of test scores ~ +1 pp annual growth | quantity effects through schooling years only (existing C5 PWT mapping); quality not modelled (no Brazilian test-score scenario) |
| India: engineering-college and IT growth (time-series studies; state timing of private engineering colleges) | cointegration and state comparisons (association) | higher-education enrolment moves with IT/software exports in the long run; early-opening states kept an advantage for ~15 years | supports a competitiveness channel in skill-intensive services; not quantified separately (inside the regional elasticity) |
| Schooling -> entrepreneurship (IZA DP 14655, IV with cohort maternal schooling) | instrumental variables | more schooling raises incorporated self-employment and self-employment in high-growth industries | supports the PNAD composition channel (employer share rises with attainment) |
| Schooling -> crime (Lochner & Moretti 2004, USA) | compulsory-schooling-law IV | schooling lowers arrest and incarceration; crime savings = 14-26% of the private return to high-school graduation | social benefit of secondary completion (Pé-de-Meia-type incentives), reported as an indicator |

Reading across countries: higher-education capacity is associated with higher regional income and innovation over
decades, but part of the local gain is relocation, quality matters more than headcounts, and vocational systems ease
entry rather than raising long-run productivity. Effects take 10-20 years and are small relative to fiscal and
interest-rate effects within the 2045 horizon, but they compound beyond it.

## 5. How the programmes enter (identical rules)
- **Every scenario:** the education channels are driven by that scenario's own education spending path (C2/C5), so any
  cut to education in a cut package lowers schooling and capacity, and any increase raises them, symmetrically.
- **Lula programme:** current-law floors plus the stated measures (100 new IF campi under Novo PAC, Pé-de-Meia
  maintained, university budget inside the LC 200 rule). Pé-de-Meia enters as secondary completion (ex-ante -6.5 pp
  dropout among vulnerable students; sensitivity at half), IF campi as higher-education capacity.
- **Flávio programme:** universities moved to the MCTI; the plan states no budget. Default: current law for university
  spending (only what the cut package itself implies). Sensitivity, labelled as an assumption and never as the plan:
  real university budget -10% and -20% from 2028. If the plan's applied-research focus raised innovation per real
  of spending, that is not quantified (no evidence of size); stated as an unmodelled upside.

## 6. Productivity, innovation, new products, industry and technology (user request 2026-10-22)
| Item | Evidence | Use in the model |
|---|---|---|
| Schooling -> worker productivity | Mincerian returns (Brazil high); PWT human-capital mapping already in C5 | existing channel, driven by each scenario's education spending |
| Higher-education capacity -> regional income, patents, new industries | Valero & Van Reenen (0.4% GDP pc per +10% universities, association); Andrews (patents +40-62% locally, mostly relocation); land-grant colleges raised long-run manufacturing productivity; India's engineering-college supply moved with IT-services exports | one "capacity" channel (elasticity 0-0.04, central 0.02, 15-year phase-in) that stands for innovation, new products and skill-intensive industry together; not added again separately (avoids double counting) |
| Public R&D and technology programmes (incl. the AI plan) | Brazil firm-level R&D-to-TFP elasticity small or insignificant (USP dissertations, Lei do Bem 2003-2013: below international median; 0.014, n.s., with common factors); public agricultural R&D (Embrapa) associated with high TFP growth (simulation evidence); internationally, social returns to R&D exceed private returns (Jones & Williams 1998) | separate small "innovation capacity" sub-channel: output elasticity 0.01 (central) to 0.02 (high) per log of the public R&D stock (perpetual inventory, 15% depreciation), low 0, applied to the change in real public R&D spending of each scenario |
| Brazilian AI Plan (PBIA, 2024-2028) | R$ 23 bn over 2024-2028 (MCTI); national AI supercomputer led by the LNCC in Macaíba (RN), announced Aug 2026, contract value reported at R$ 0.96-1.06 bn, procurement postponed to 4 Nov 2026, operation expected 2027; 5,000 people to be trained over five years | enters as public R&D/technology spending in the innovation sub-channel (Lula: as planned; Flávio: current law unless the plan states otherwise). At ~R$ 4.6 bn a year (~0.035% of GDP) its measurable GDP effect within 2045 is small; reported, not overstated |
| Industrial expansion and competitiveness | export quantum and skill-intensive exports are outcomes, not separate inputs; competitiveness is captured through GDP/TFP in the channels above | no additional channel |

## 7. Treating education as an investment (both programmes, same accounting)
Education and R&D spending are costs today (they lower the primary balance and raise debt, as in C2) and returns
later (schooling of cohorts, capacity, innovation stock, through C5/ED). The model shows both sides for every scenario:
- **Lula programme:** higher education spending (Pé-de-Meia, 100 IF campi, university budget inside the rule, PBIA)
  costs fiscal space now; gains arrive gradually (secondary completion within ~5 years; capacity and innovation over
  10-20 years) and continue beyond 2045. Revenue on the higher GDP is counted (revenue/GDP held, so revenue rises with
  GDP), so part of the cost pays back.
- **Flávio programme:** cuts in the package's education share (and the -10%/-20% university sensitivities) save money
  now and lower schooling, capacity and innovation later. The move of universities to the MCTI with an applied-research
  focus could raise research effectiveness, but no evidence gives a size: it is listed as an unquantified upside, and
  a symmetric sensitivity (+/-10% effectiveness of the capacity channel) is reported.
- **Reporting:** for each scenario, the present value (3% real discount) of the fiscal cost or saving vs the GDP gain or
  loss from these channels to 2045 and to 2060 (beyond-horizon tail stated separately), so neither side's long-run
  effects are hidden or overstated.

## 8. The 2019-2022 record for universities and science (lead computation, Tesouro COFOG, 2024 prices, IPCA)
| R$ bn, 2024 prices | 2018 | 2019 | 2022 | 2024 | 2018->2022 | 2022->2024 |
|---|---:|---:|---:|---:|---:|---:|
| Federal universities, total (incl. personnel) | 65.9 | 66.3 | 57.0 | 59.7 | -13.5% | +4.7% |
| Federal universities, excluding personnel and benefits | 7.8 | 7.1 | 5.6 | 6.2 | -28.5% | +10% |
| MCTI budget units | 12.2 | 10.5 | 8.4 | 11.8 | -31% | +40% |
| COFOG tertiary education (central government) | 58.7 | 58.8 | 48.8 | 50.3 | -17% | +3% |

Context: the 2016 spending cap (EC 95), the 2020-21 pandemic and the 2021-22 inflation (nominal freezes became real
cuts) all contributed; total education spending rose in 2021-22 because of the constitutional Fundeb top-up
(EC 108/2020), so the fall is specific to higher education and science. Personnel is ~90% of university spending and
is sticky; most of the cut fell on operations, investment and research.

**Calibration for the Flávio programme (sensitivities, never the plan):** the plan moves universities to the MCTI and
states no budget. Three cases, applied from 2027 and ramped over the 2027-2030 term:
- `current_law` (default): no change beyond the package's own education share;
- `record_repeat` (central sensitivity, the lead's best guess as requested by the user): repeat the 2018-2022 real
  changes over the term: federal universities -13.5% total (non-personnel -28.5%), MCTI R&D -31%, held after 2030;
- `half_record`: half of those changes.
Symmetric reading for the Lula programme: `current_law` plus its stated measures (2022-2024 recomposition continues:
universities +4.7%, MCTI +40% on the record, PBIA). The cascade then runs through the capacity, innovation and
schooling channels with the same parameters.
