# Major-corruption shock module (G2)

## Purpose and interpretation

G2 adds rare major-corruption scandals to Monte Carlo uncertainty as GDP level paths. It does not forecast whether a named person or party will be corrupt. In each draw, one annual event sequence and one set of loss magnitudes are drawn and applied identically to every policy scenario and both 2026 programmes. Events may overlap; their GDP level effects add in log terms.

The same annual probability applies to every candidate. Brazil's Transparency International CPI was 34-38 during 2019-2025, and TI says changes of about +/-1 point are statistically insignificant. World Bank WGI Control of Corruption confidence intervals for the recent governments overlap. These data therefore do not distinguish the corruption likelihood of recent governments or candidates. They also measure perceptions, can react when corruption is exposed rather than committed, and cannot assign a future scandal to a candidate.

## Method and parameters

| Input | Proposed value | Basis | Source flag |
|---|---:|---|---|
| Annual event probability | uniform(3%, 8%) | Two federal episodes with measurable macro effects in 1990-2025: the 1992 Collor impeachment crisis and 2014-2016 Lava Jato. Two divided by 36 years is 5.6%; the range is a modelling choice. | historical count + choice |
| Full GDP level loss | triangular(1.0%, 2.25%, 3.6%) | Low: smaller episodes. Mode: reported 2-2.5% Lava Jato contribution to the 2015-2016 GDP fall. High: 3.6% of GDP over 2014-2017. | low choice; mode secondary; high contested |
| Build-up | 2 years | Linear from the event year to the full loss. | choice |
| Recovery half-life | 4 years | Construction and investment effects persisted after Lava Jato. | choice |

The mode comes from GO Associados and Tendencias estimates reported secondhand, not from a checked primary study. The high estimate is Dieese for CUT (2024); it is contested by economists cited by Folha because it does not account adequately for Petrobras problems that predated Lava Jato. These flags must accompany reported results.

Mensalao (2005), the 2025 INSS benefit-deduction fraud, and similar cases are excluded from the event count because no measurable GDP effect was identified. Exclusion does not imply that they had no social, fiscal, legal, or distributional cost.

For an event of magnitude `m`, the loss is `m / 2` in its first year, reaches `m` in year two, and then decays exponentially with a four-year half-life. The output is a non-positive log-level deviation in percent. The deterministic central path contains no event; stochastic paths are generated with a caller-provided NumPy generator for reproducibility.

## What the module changes

The shock changes GDP levels and widens uncertainty bands. Because the identical path is shared within a draw, it does not mechanically change scenario or programme differences versus S0. Differences can still arise after the lead developer integrates the path through nonlinear channels, notably the C5 sovereign-risk-premium/debt feedback.

The module cannot estimate candidate-specific corruption probabilities, identify who caused an event, value ordinary leakage, or model legal and institutional benefits from enforcement. The existing G1 spending-leakage channel remains conceptually separate.

## Optional CPI improvement sensitivity

An off-by-default sensitivity answers explicit questions such as "what if Brazil's CPI rose to X?" Gründler and Potrafke (2019, ifo Working Paper 309; later *European Journal of Political Economy*) estimate that a one-standard-deviation improvement in the reversed CPI corresponds to roughly a 17% cumulative long-run real-GDP-per-capita level effect. G2 scales that effect by CPI points and phases it in linearly over 20 years, identically for all scenarios.

The cross-country CPI standard deviation is currently a 20-point placeholder on the modern 0-100 scale and is marked `to_verify` in `config/corruption_proposed.yaml`. No result from this sensitivity should be reported until that input and the paper's CPI scale conversion have been verified. This is a long-run illustrative association, not a candidate forecast or a short-run scandal effect.
