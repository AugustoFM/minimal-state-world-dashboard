# Governance and corruption in the Brazil model

## What the data can and cannot say
Two standard perception indices are archived in `data/raw/brazil/governance/` and combined in `data/brazil/governance_brazil.csv`:

- World Bank WGI Control of Corruption (estimate, about -2.5 to +2.5; higher = less corruption perceived), Brazil 1996-2025;
- Transparency International CPI (0-100; higher = less corruption perceived), Brazil 2012-2025 with standard errors (comparable series starts in 2012).

Averages by government period (calendar years):

| Period | WGI Control of Corruption | CPI |
|---|---|---|
| FHC II (PSDB) 1999-2002 | +0.10 (2 obs.) | n/a |
| Lula I-II (PT) 2003-2010 | -0.12 (range -0.29 to +0.05) | n/a |
| Dilma (PT) 2011-2015 | -0.10 (range -0.35 to +0.22) | 41.5 |
| Temer (MDB) 2016-2018 | -0.41 | 37.3 |
| Bolsonaro (PL) 2019-2022 | -0.39 | 37.2 |
| Lula III (PT) 2023-2025 | -0.41 | 35.0 |

Reading it fairly:
- The largest change is the fall in 2014-2017, when the Lava Jato investigations exposed corruption schemes. Perception indices measure perceived corruption, so they also move when corruption is uncovered and prosecuted, and with a lag; a fall can reflect exposure as much as new corruption.
- Since 2017 the indices are flat across Temer, Bolsonaro and Lula III. The differences between these periods (WGI -0.39 to -0.41; CPI 35-38) are smaller than the indices' measurement error (CPI standard errors 1.5-2.8 points), so the data do not rank these governments.
- Calendar-year averages do not map cleanly to governments (mandates start in January, scandals surface years after the acts, Dilma's term ended in 2016).

For these reasons the indices are context only and are not model inputs.

## How corruption enters the model
As leakage: a share of social-service spending that is diverted before it becomes services (`config/parameters.yaml` -> `governance`).

- Range 2.8%-13%, sampled uniformly in D1. The low bound is the expected diversion in audited municipal education transfers (Ferraz, Finan & Moreira 2012: corruption found in 35% of audited municipalities, 8% of audited resources diverted there); the high bound is the lower end of an older CGU-based estimate for FUNDEF (13-55%, 2001-03, cited in the same paper).
- The same leakage applies to every scenario and both 2026 programmes: the evidence does not say how any future government would change it.
- Consequence: leakage cancels out of every scenario-vs-S0 comparison (each scenario loses the same share of each real). `tests/test_montecarlo.py` checks this.
- It matters only if a policy changes leakage. D1 therefore reports a "leakage halved" sensitivity for every scenario (including S0) for health services, infant mortality and life expectancy. Both programmes promise anti-fraud action; neither quantifies it, so the sensitivity is not attributed to either.

Not modelled: corruption's effect on investment, growth or interest rates, and the learning loss associated with corruption (-0.35 SD in test scores, an association) - both recorded as context in `parameters.yaml`.
