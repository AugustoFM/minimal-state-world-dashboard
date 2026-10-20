# C4 social outcomes block

## Scope and interpretation

`src/social.py` links C1 health-spending shares and C2 real GDP per capita to
infant mortality, life expectancy and the HDI health index. It emits
sensitivity envelopes at 5, 10, 15 and 20 years for S0, S1, R_mod, R_amb and
the optional R_max. These are not forecasts or probability intervals.

S0 infant mortality and life expectancy are held at their latest observed
levels because no sourced S0 trend is available. Every policy outcome is an
effect relative to that flat S0 anchor and is labelled `S0 no trend assumed`.
This deliberately avoids extending the historical improvement as an invented
trend.

## Equations

For C1 variant `c`, C2 variant `m`, C2 persistence choice `p`, service-loss
choice `s`, scenario `j` and horizon `h`, real public health spending per
capita is

```
H[j,h,c,m,p,s] = (q[j,h,c] - R[j,h] * w_eff * a_health * s) / 100
                 * GDPpc[j,h,m,p]
```

where `q` is the C1 health share of GDP, `R` is the reduction below S0 from
`config/scenarios.yaml`, `w_eff = 0.20` is the
`efficiency_health_education_admin` package share, and
`a_health = health_2025 / (health_2025 + education_2025)`. The C1 base shares
give `a_health = 0.4965568563`. Ignoring administration over-allocates the
efficiency package to health and education and is conservative for adverse
service outcomes. S0 has `R=0`. S1 uses its direct C1 health path because it
has no `by_year` reduction in the scenario file.

The two reported spending changes are

```
Delta_base = 100 * (H[j,h] / H[S0,2025] - 1)
Delta_S0   = 100 * (H[j,h] / H[S0,h]    - 1).
```

For outcome base `Y0`, elasticity `e`, and `b(h)=min(h/10,1)`, the symmetric
policy effect is

```
Y[j,h] = Y0 * (1 + e * Delta_S0/100 * b(h)).
```

Infant mortality reports the level per 1,000 live births and its difference
from S0. Life expectancy reports the level in years and its difference from
S0. The HDI health index and its difference from S0 are

```
I_health = (life_expectancy - 20) / (85 - 20).
```

## Envelopes and bound provenance

The low and high rows are the minimum and maximum over every available infant
mortality elasticity, all three service-cut fractions, all C1 variants, all C2
GDP-per-capita variants, and both C2 persistence choices. The central row uses
central parameters and C1/C2 variants with C2's default transitory persistence.
`bound_combination` records the exact corner behind every row. C2 variants are
included because GDP per capita is part of the specified health-spending
measure. D1 will replace this deterministic corner envelope with Monte Carlo
draws.

The life-expectancy source supplies only its central elasticity. Consequently
all life-expectancy and HDI health-index bounds say `elasticity=central_only`;
their remaining width comes from the spending, C1 and C2 choices. Health
spending rows say `elasticity=not_applicable`.

## Parameter and input register

| Input or parameter | Value/range | Status | Source |
|---|---:|---|---|
| Health-spending measure | C1 health share adjusted for service loss, times C2 real GDP per capita | choice | `social_modelling_choices.health_spending_measure` |
| Efficiency package share | 0.20 | scenario choice | `config/scenarios.yaml` `package_shares` |
| Health allocation within health + education | 0.4965568563 | calculated from sourced inputs using specified choice | 2025 C1 health 5.0319033180 and education 5.1016861266% GDP; proportional rule in `social_modelling_choices` |
| Service-cut fraction | 0 / 0.5 / 1 | choice | `social_modelling_choices.reduction_hitting_health_education.service_cut_fraction`; pure efficiency / partial loss / one-for-one service loss |
| Elasticity build-up | linear to full effect at 10 years, then flat | choice with empirical timing basis | `social_modelling_choices.elasticity_build_up`; Szklo, Clarke & Rocha (2024) |
| Cuts versus increases | same elasticity in both directions | choice/extrapolation | `social_modelling_choices.cuts_vs_increases` |
| Infant-mortality elasticity | -0.206 / -0.126 / -0.071 | estimate range across specifications | Szklo, Clarke & Rocha (2024), IZA DP 16829, Table B.2 and section 5.2.3; full text verified |
| Life-expectancy elasticity | null / 0.04 / null | point estimate only | Gallet & Doucouliagos (2017), *Social Science & Medicine* 179; abstract verified; mostly cross-country total health spending |
| HDI health goalposts | 20 and 85 years | UNDP method | `social_modelling_choices.life_expectancy_to_hdi`; UNDP HDR technical notes |
| Infant-mortality base | 12.3 in 2024 | latest raw observation | World Bank WDI `SP.DYN.IMRT.IN`, UN IGME estimate, read from `data/raw/brazil/social/worldbank_bra_infant_mortality.json` |
| Life-expectancy base | 75.848 years in 2023 | latest raw observation | UNDP HDR indicator code `le`, read from `data/raw/hdr-data.json` |
| Base real GDP per capita | R$59,687.49 in 2025 prices | C2 point input | IBGE Quarterly National Accounts; `config/c2_inputs_proposed.yaml` |
| C1 health paths | low/central/high, 2025-2045 | C1 sensitivity paths | `data/brazil/baseline.csv`, category `health` |
| C2 GDP-per-capita paths | low/central/high, transitory/persistent | C2 sensitivity paths | `data/brazil/macro.csv`, indicator `gdp_per_capita` |

Raw-file paths, fields and selection rules for the two outcome anchors are in
`config/c4_inputs_proposed.yaml`. The CLI reads the latest non-null matching
record; neither year nor value is hand-entered in runtime configuration.

## Not modelled

The following configured gaps are emitted for every horizon, scenario and
variant with an empty `value` and `status = not_modelled: <reason>`:

- mean and expected years of schooling: no sourced elasticity;
- physicians per 1,000 and other health-access measures: no sourced elasticity;
- the HDI education index and overall HDI: both depend on the unmodelled
  schooling outcomes. Only the health index is produced.

## Caveats

Szklo et al. identify spending increases around Brazil's EC 29/2000 and find a
noisy indication that mortality responds more to increases than declines. C4
applies their elasticity symmetrically to spending cuts, as required by the
lead-developer choice; this may overstate harm from cuts. The life-expectancy
elasticity is a cross-country meta-regression estimate for total rather than
public health spending and has no sourced uncertainty range. The model captures
only spending-mediated outcomes and does not model service quality, allocation
within health, epidemiological change or feedback from mortality to GDP.

## CLI

From the repository root:

```
python -m src.social
```

This writes `data/brazil/social.csv`. Missing required parameters fail with
`MissingSocialParameter`; missing or duplicate C1/C2 rows fail rather than being
filled or interpolated.
