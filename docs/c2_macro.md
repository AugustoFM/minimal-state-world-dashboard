# C2 macro block

## Scope

`src/macro.py` converts the annual C1 primary-spending paths into macro paths
and reports sensitivity envelopes at 5, 10, 15 and 20 years. These are not
forecasts or probability intervals. The base year is 2025; a five-year result is
2030 and contains five debt transitions.

S0 keeps the C1 ageing drift. S1 holds primary spending at its base share.
Reform sizes come only from each scenario's `config/scenarios.yaml` `by_year`
mapping: the code adds a zero in 2025 and linearly interpolates between the
configured horizons. `pace_pp_gdp_per_year_below_S0` is descriptive and is not
used. Any optional `R_max` with a `by_year` mapping is handled the same way.

## Fiscal identity and debt anchor

The Tesouro workbook supplies primary revenue and spending on one GFSM basis.
For 2025-IV, primary revenue is total revenue less interest receivable and
primary spending is total expense less interest payable.

| Item | % GDP |
|---|---:|
| Total revenue | 41.4557 |
| Less interest receivable | 2.4858 |
| Primary revenue | 38.9699 |
| Total expense | 50.0366 |
| Less interest payable | 10.2746 |
| Primary spending | 39.7620 |
| Calculated / reported primary balance | -0.7921 |

Revenue remains 38.9699% of GDP under the unit-elasticity assumption in
`config/parameters.yaml`, while S0 primary spending continues to follow C1.
Thus ageing is intentionally allowed to worsen the primary balance.

The untouched BCB SGS 13762 JSON supplies exact December debt observations and
the 2025 anchor, 78.64% of GDP. Tesouro interest payable divided by same-year
December debt gives the nominal rate. It is converted using same-year IBGE
GDP-deflator inflation: `r_t = (1+i_t)/(1+pi_t)-1`.

| Year | Debt (% GDP) | Nominal rate (%) | GDP deflator (%) | Real rate (%) |
|---:|---:|---:|---:|---:|
| 2021 | 77.31 | 10.6923 | 13.00 | -2.0422 |
| 2022 | 71.68 | 11.1931 | 8.60 | 2.3877 |
| 2023 | 73.83 | 10.5127 | 5.20 | 5.0501 |
| 2024 | 76.27 | 11.2703 | 3.80 | 7.1968 |
| 2025 | 78.64 | 13.0654 | 5.73 | 6.9379 |

The real-rate minimum / median / maximum is **-2.0422 / 5.0501 / 7.1968%**.
Each projection corner uses `i=(1+r)(1+projected deflator)-1`, giving nominal
rates of **0.8966 / 8.2016 / 11.2703%**. The old direct nominal calibration is
available only through `use_legacy_nominal_rate_fallback`, which defaults false.

## Growth accounting

All supply-side capital quantities now come from one internally consistent
source and price basis: Penn World Table 10.01, Brazil (`BRA`), at constant
2017 national prices. The IBGE population projection remains the labour source.
The production function is

`Y = A K^alpha (hc * L)^(1-alpha)`.

The loader reads the Stata file directly. For projection, `alpha = 1-labsh`,
depreciation is `delta`, and initial `K/Y = rnna/rgdpna`, all from the 2019 row.
Labour is employment (`emp`, not hours): the 2019 PWT employment level divided
by the 2019 IBGE population aged 15-64 fixes the employment rate, which is then
held constant while labour follows the C1 working-age-population helper. Human
capital and TFP grow at the PWT sub-period rates below.

Capital accumulates rather than using a fixed capital-growth shortcut:

`K[t] = (1-delta) K[t-1] + investment_rate * Y[t-1]`.

Annual output growth is the discrete change implied by the production function.
The investment rate is inferred annually from PWT on the same basis as capital:
`(rnna[t] - (1-delta[t])*rnna[t-1]) / rgdpna[t]`. The 16.8% IBGE 2025 nominal
investment rate is retained in the register only as context and is **not used:
different price basis**.

| Calibration | Low | Central | High | Basis |
|---|---:|---:|---:|---|
| TFP growth (%/yr) | -2.0553 | -0.9276 | -0.0655 | PWT CAGR: 2010-19 / 2000-19 / 2004-13 |
| Human-capital growth (%/yr) | 2.1682 | 2.1982 | 2.5092 | PWT CAGR: 2004-13 / 2000-19 / 2010-19 |
| Capital share `alpha` | 0.4220 | 0.4220 | 0.4220 | `1-labsh`, 2019 |
| Depreciation (%/yr) | 4.9330 | 4.9330 | 4.9330 | `delta`, 2019 |
| Initial K/Y | 4.1896 | 4.1896 | 4.1896 | `rnna/rgdpna`, 2019 |
| Investment/GDP (%) | 25.4092 | 27.8048 | 29.3136 | PWT implied-rate averages: 2015-19 / 2000-19 / 2004-13 |

### Historical validation

The dynamic backcast starts from PWT capital in 2000 and thereafter accumulates
capital using each year's PWT-implied investment rate and depreciation; it does
not feed actual subsequent capital into the projection. Actual average capital
growth is 2.5277627% and dynamically accumulated growth is 2.5277633%, an
average growth error of **+0.0000006 pp** (floating-point precision). Feeding
that accumulated capital into growth accounting gives average actual output
growth of 2.2546% and fitted growth of 2.3718%, a fitted-minus-actual average
error of **+0.1172 pp**; mean absolute annual output-growth error is 0.2809 pp.

## S0 results and external benchmarks

| Horizon | Year | Potential growth low / central / high (%) | Debt low / central / high (% GDP) |
|---:|---:|---:|---:|
| 5 | 2030 | -0.357 / 1.122 / 2.424 | 79.98 / 104.46 / 108.53 |
| 10 | 2035 | -0.614 / 0.936 / 2.329 | 88.93 / 145.49 / 155.62 |
| 15 | 2040 | -0.942 / 0.659 / 2.122 | 105.79 / 207.48 / 227.06 |
| 20 | 2045 | -1.290 / 0.348 / 1.862 | 130.85 / 298.94 / 333.77 |

The correction raises central S0 growth to 1.12%, 0.94%, 0.66% and 0.35% at the
four horizons, but a material gap remains. At ten years the model is still
about **1.56 pp below** the IMF 2.5% benchmark. This result is not tuned: weak
PWT TFP history and later working-age decline still offset much of the capital
and human-capital contribution.

The IFI baseline cited in the lead-developer review is approximately 125% of GDP
by 2035. No underlying IFI RAF file or exact table is present in the offline
source set, so this is explicitly a secondary benchmark pending verification.
Central S0 is 145.49% in 2035, about **20.49 pp above** that benchmark; it should
not be described as an IFI-consistent baseline.

### Ten-year S0 debt-change decomposition

The exact annual identity is decomposed as `Delta d = -primary balance +
d[-1]*((1+i)/(1+nominal g)-1)`. Summing the ten transitions from the 78.64%
2025 anchor to the 145.49% central result gives:

| Contribution, 2025-2035 | Percentage points of GDP | Share of increase |
|---|---:|---:|
| Primary balance, including C1 ageing drift | 25.97 | 38.8% |
| Interest-growth | 40.88 | 61.2% |
| Total S0 debt change | 66.85 | 100.0% |

The S0 primary deficit widens from 1.11% of GDP in 2026 to 4.11% in 2035. The
larger interest-growth component reflects an 8.20% central nominal rate while
nominal GDP growth declines from about 4.21% to 3.96%; it explains most of the
remaining gap to the secondary IFI benchmark. The model-versus-IFI difference
cannot itself be decomposed exactly until the underlying IFI path is available.

## Ten-year reform results

The checked-in scenario file currently gives R_mod and R_amb reductions of 2
and 4 percentage points of GDP below S0 in year 10. Values below are
`low / central / high`.

### Transitory multiplier effects, 2035

| Indicator | R_mod | R_amb |
|---|---:|---:|
| GDP level vs S0 (%) | -0.635 / -0.401 / -0.160 | -1.270 / -0.803 / -0.320 |
| GDP per capita (2025 BRL) | 55,673 / 64,386 / 73,052 | 55,584 / 64,126 / 72,585 |
| Debt/GDP (%) | 78.53 / 133.53 / 143.71 | 68.14 / 121.57 / 131.81 |
| Primary balance/GDP (%) | -2.199 / -2.115 / -1.651 | -0.199 / -0.115 / 0.349 |
| Unemployment change vs S0 (pp) | 0.022 / 0.075 / 0.130 | 0.045 / 0.151 / 0.261 |

### Persistent multiplier effects, 2035

| Indicator | R_mod | R_amb |
|---|---:|---:|
| GDP level vs S0 (%) | -3.426 / -2.064 / -0.345 | -6.852 / -4.128 / -0.690 |
| GDP per capita (2025 BRL) | 55,570 / 63,311 / 71,000 | 55,378 / 61,977 / 68,481 |
| Debt/GDP (%) | 78.67 / 135.64 / 147.60 | 68.39 / 125.74 / 139.61 |
| Primary balance/GDP (%) | -2.199 / -2.115 / -1.651 | -0.199 / -0.115 / 0.349 |
| Unemployment change vs S0 (pp) | 0.048 / 0.388 / 0.704 | 0.097 / 0.775 / 1.408 |

## Input register

Exact URLs, file paths, locators and range rules are in
`config/parameters.yaml` (C2 sections: `fiscal_calibration`, `interest_rate_calibration`, `growth_calibration`, `macro`, `published_potential_growth_benchmark`); raw-file hashes and licences are in
`data/raw/SOURCES.md`.

| Input | Low / central / high | Vintage or period | Range basis |
|---|---|---|---|
| Initial GGGD | 78.64 / 78.64 / 78.64% GDP | Dec. 2025 | BCB SGS point observation |
| Primary revenue | 38.9699 / 38.9699 / 38.9699% GDP | 2025-IV | Tesouro workbook point observation |
| Historical nominal implicit interest | 10.5127 / 11.1931 / 13.0654% | 2021-25 | descriptive min / median / max; not projected directly |
| Effective real interest | -2.0422 / 5.0501 / 7.1968% | 2021-25 | min / median / max of same-year Fisher conversions |
| Projected nominal interest | 0.8966 / 8.2016 / 11.2703% | projection | real rate reinflated by projected deflator per corner |
| GDP deflator growth | 3.0 / 3.0 / 3.8% | current target; 2024 observation | BCB target is the low/central proxy; IBGE observed deflator is high |
| TFP growth | -2.0553 / -0.9276 / -0.0655% | 2010-19 / 2000-19 / 2004-13 | PWT sub-period CAGRs |
| Human-capital growth | 2.1682 / 2.1982 / 2.5092% | 2004-13 / 2000-19 / 2010-19 | PWT sub-period CAGRs |
| Capital share | 0.4220 | 2019 | PWT `1-labsh` point value |
| Capital/output | 4.1896 | 2019 | PWT `rnna/rgdpna` point value |
| Depreciation | 4.9330% | 2019 | PWT `delta` point value |
| Investment/GDP | 25.4092 / 27.8048 / 29.3136% | 2015-19 / 2000-19 / 2004-13 | PWT implied-rate averages, same constant-price basis as K |
| IBGE nominal investment/GDP (context only) | 16.8% | 2025 | **Not used: different price basis** |
| Okun coefficient | 0.140473 / 0.1878 / 0.2055 | studies through 2015Q2 | range across two studies |
| GDP anchor | R$12,738.6bn | 2025 | IBGE point observation |
| GDP-per-capita anchor | R$59,687.49 | 2025 | IBGE point observation |

The GDP-deflator assumption uses the CPI target as a labelled long-run proxy;
the two concepts are not identical. Aligned deterministic corners are
sensitivity envelopes. D1 will replace them with parameter draws.

IBGE SIDRA responses for the 2021-2023 deflators, 2024-2025 current-price GDP and
2025 real growth are archived in `data/raw/brazil/macro/` (checked by Claude). The
2025 deflator derived from them is 5.71%, against 5.73% used (rounding of the
published 2.3% real growth). The 2024 deflator (3.8%) is from the IBGE yearbook
PDF, not archived.

## Limitations

Federal-government multipliers are transferred to general-government spending
reductions. S1's offset is allocated using the default reform package because C1
does not assign a package. PWT ends in 2019, so its factor and implied-investment
calibrations are held fixed in projection. Constant
employment rates omit participation and unemployment trends. Debt omits
stock-flow adjustments, valuation effects and endogenous interest rates. The
GFSM primary balance should not be compared mechanically with the BCB
consolidated-public-sector headline, which has different coverage.

Required null inputs fail clearly. With `--allow-missing`, only dependent
outputs are omitted and the skipped-output mapping is recorded.
