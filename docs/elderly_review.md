# Older people: pensions, BPC, poverty and health costs (evidence review)

Lead developer (Claude), 2026-10-21, at the user's request. Companion to E3 (`outputs/elderly.md`). Measures are
assessed identically whichever programme proposes them: cuts and increases use the same channels.

## 1. Facts (PNAD Contínua 2025, visit 1; lead-developer computation, reproduced by E3)

- Per-capita household income below R$ 759: 40.6% (ages 0-14), 25.5% (15-29), 18.9% (30-64), **6.0% (65+)**.
  Below R$ 218: 5.0%, 3.3%, 2.8%, 1.5%.
- 24.6 million people are 65+; 80.2% receive a pension, 7.2% BPC; 59.2% of 65+ pensions are at about 1 minimum wage.
- Without pension and BPC income, 65+ poverty below R$ 759 would be **63.5%** (47.6% below R$ 218). Pensions and BPC are
  the main reason older Brazilians are the least-poor age group, and they also support the children and adults who live
  with them (Camarano/IPEA, 2020: deaths of older providers in the pandemic put ~4 million adults and ~1 million
  children at risk of poverty; secondary report).

## 2. How a benefit-indexation change works

- Current law: the minimum wage, and with it most INSS benefits and BPC, gets INPC plus a real gain of 0.6-2.5% a year
  (2025-2030 rule). INPC-only indexation (reported mid/high scenarios; not in the TSE programme; denied by the campaign)
  keeps the real value of benefits **constant** but stops the real gain. The constitution bars benefits below the
  minimum wage, so de-linking requires a constitutional amendment.
- Effect on poverty: against a fixed real poverty line, an older person whose benefit keeps its real value does not
  become poorer than today; the effect is **relative to the current-law path** (S0): with real gains of 0.6-2.5% a year from 2027, current-law
  benefits would be 2.4-10.4% higher in real terms by 2030 and 5.5-24.9% higher by 2035 than INPC-only benefits
  (if INPC-only starts in 2027; E3 item 3 compounds from 2026: 3.0-13.1% by 2030 and 6.2-28.0% by 2035). Households near the line,
  typically one benefit supporting several members, are the ones that cross it. BPC households are poor by
  construction (eligibility: household income below 1/4 minimum wage per person), so BPC changes move poverty most.
- The same channel applies in reverse to real minimum-wage gains (Lula scenarios): they lower poverty among older
  people and those living with them, and raise pension spending (C1/C2) and therefore debt and, through I1, rates.

## 3. Health costs of older people

- **Prices (IBGE, 2012-Sep 2026, annualised):** INPC general 5.65%; health group 6.03%; **medicines 5.33% (below INPC;
  CMED-regulated)**; medical and dental services 6.83%; **health plans 8.49%**. An INPC-indexed benefit loses purchasing
  power for health mainly for plan holders and users of private services; for low-income older people relying on SUS and
  medicines the price erosion is small (medicines are also partly free under Farmácia Popular).
- **Burden:** POF 2017-18 (Cadernos de Saúde Pública, 2022): individual health-plan spending rises from 4.5% of per-capita
  household income (under 19) to 10.6% (79+); the probability of spending over 40% of income on health falls with income,
  rises with age and is higher for plan payers; plans alone push 5.6% of people 60+ above that 40% threshold. Older
  evidence (PNAD 1998): medicines took ~23% of the income of half the older population.
- **Public provision:** older people use SUS most (C1 health age profile). If health spending is held constant in real
  terms (reported mid/high measure: floors indexed to inflation only) while the 65+ share rises from 11.6% to 20.5% by
  2045, real public health spending per age-weighted person falls (E3 item 5 quantifies it). C4 already maps
  services-package cuts to infant mortality and life expectancy. An older-people-specific outcome elasticity is not
  estimated in the model (gap; listed).

## 4. Channels the model will report (E3 + Claude wiring)

1. Poverty for ages 0-14 and 65+, and for people living with a 65+ pension/BPC recipient (C3 microsimulation, every scenario).
2. BPC follows the indexation package together with pensions (both are minimum-wage linked; symmetric for cuts and increases).
3. Indexation arithmetic: real benefit paths under current law and INPC-only.
4. Health-adjusted purchasing power of an INPC-indexed benefit (plan holders vs SUS users).
5. Real SUS spending per age-weighted person under the S0, inflation-only and revenue-linked floor paths.

Not modelled (stated as gaps): behavioural responses (later retirement, family transfers), health outcomes of older
people from income changes, long-term care costs.

## 5. What E3 found (`outputs/elderly.md`)

- **Profile reproduced:** 65+ poverty (R$ 759) 5.98%; 63.5% without pensions/BPC; 61% of the income of people 65+ comes
  from pensions/BPC. **41.2 million people of all ages** live with a 65+ pension/BPC recipient: their poverty is 6.8%,
  and would be 58.5% without that income.
- **Knife-edge at the poverty line.** R$ 759 is half the 2025 minimum wage, so a two-person household living on one
  minimum-wage benefit sits exactly on the line. In the stylised C3 check, a cut of only 0.1% of GDP concentrated on
  minimum-wage benefits raises 65+ poverty from 5.98% to 8.4% (8.9% when BPC follows the same indexation) and poverty
  among people living with an older recipient to 9.5-10.0%. The same mechanism works in reverse: real minimum-wage gains
  lift these households above the line. Older-age poverty is therefore very sensitive to the minimum-benefit
  indexation in either direction; results at this line should be read together with the R$ 218 line, which barely moves.
- **Health prices:** an INPC-indexed benefit loses ~0.35%/yr of health purchasing power on average (health group),
  ~2.6%/yr for health-plan holders, ~1.1%/yr for private medical services; it *gains* ~0.1%/yr on medicines (regulated
  prices). Low-income older people relying on SUS and medicines are least exposed through prices; plan holders most.
- **SUS per age-weighted person by 2045** (2025 = 100): S0 path 115; current-law floor with revenue/GDP constant 92;
  spending frozen in real terms (proxy for an inflation-only floor) 78. Ageing raises health need by 28.5%; a real
  freeze cuts resources per unit of need by about a fifth.
- **Model change:** BPC now follows the pension/indexation package (option `bpc_follows_pension_indexation`, default on,
  symmetric), and the microsimulation reports poverty for ages 0-14, 65+ and people living with an older recipient.
