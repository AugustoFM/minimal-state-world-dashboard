# C5 long-run feedback block

## Scope and API

`src.feedback.apply_feedback` consumes one complete annual DataFrame returned by
`src.macro.run_corner`. It preserves every input column and adds:

- `gdp_level_vs_s0_pct_with_feedback`, `gdp_per_capita_with_feedback`, and
  `debt_gdp_with_feedback`;
- GDP-level contributions named `<channel>_contribution_pct`;
- debt contributions named `<channel>_debt_contribution_pp`;
- the adult mean-schooling change and explicit public-capital/inequality status.

Contributions follow `long_run_feedback_choices.attribution`: each is the
with-all result minus a complete rerun with that channel switched off. This
captures interactions in debt dynamics. S0 is exactly neutral in every channel.

The core function performs no file or configuration reads. Every coefficient,
choice, stock, rate, and package share is an argument, so D1 can pass sampled
values. `load_feedback_defaults` is a convenience loader only. It reads C1/C2/C5
defaults, derives the C2 raw-file-backed central inputs through the existing C2
loader, and reads the latest Brazil UNDP `mys` observation. It deliberately
returns `None` for the health central value and both IMF public-capital inputs.
D1 must sample health uniformly on [0, 4]; it must not invent a central value.

## Channels

### Schooling and human capital

For scenario spending gap `G = spending - spending_S0` (percentage points of
GDP), the education-service change is

```
G_edu = G * package_efficiency * education/(education + health) * service_fraction.
```

The proportional change uses the sourced base education share. Each cohort age
6–17 in year `t` receives one twelfth of the full school-age dose:

```
delta_schooling_cohort,t = MYS_base * elasticity * ln(1 + G_edu/education_share) / 12.
```

The division by 12 prevents a 12-year exposure from applying the published
elasticity twelve times. Gains follow birth cohorts. In each projection year,
the change in adult mean years is the population-weighted mean among ages 25+,
using `data/brazil/population.csv`. It is zero in 2025 and until an exposed
cohort reaches age 25.

The PWT mapping is `hc = exp(phi(s))`, where the slopes of `phi` are 0.134 up to
four years, 0.101 from four to eight, and 0.068 above eight. Brazil's latest
UNDP mean schooling is 8.425371752 years (2023), read from the raw JSON, so the
local marginal slope is 0.068. The output log effect is
`(1 - capital_share) * delta ln(hc)`.

### Health

The caller supplies the annual life-expectancy change versus S0. The level
effect is exactly linear when this is the only channel:

```
output change = health_to_output * LE change / 100.
```

The configured coefficient has no central estimate. D1 samples
`uniform[0, 4]` percent output per additional life-expectancy year. A missing LE
path is neutral, and supplied S0 observations are forced to zero.

### Public capital

The investment-flow gap is `G * public_investment_package_share`. Initial
public capital/GDP and depreciation are required. Given those two inputs, the
S0 maintenance flow is the transparent implied flow
`depreciation * initial K_g/Y * current S0 GDP`; scenario and S0 stocks are then
accumulated separately. The output log effect is
`public_capital_elasticity * ln(K_g,scenario/K_g,S0)`.

No Brazil IMF ICSD values are in the repository. The proposed register keeps
both null in `config/c5_inputs_proposed.yaml`. The function raises
`MissingFeedbackInput` even if the default package protects investment. With
`allow_missing=True`, this channel is exactly zero and every row is flagged
`skipped: missing IMF public-capital input`. It must not be presented as an
estimated zero.

### Sovereign risk premium and debt

For year `t`, the real-rate premium is based only on the previous year's debt
deviation:

```
premium_t = bp_per_pp / 10,000 * (debt_scenario,t-1 - debt_S0,t-1 in pp).
```

The premium is added to the C2 real rate, reinflated with the C2 deflator, and
the recursion calls `src.macro.debt_step`. Nominal GDP uses the C2 real-GDP
path, the C2 GDP-level effect, and channels 1–3 (plus inequality if active).
The lag resolves circularity year by year. Zero basis points and zero supply
effects preserve the input debt column exactly.

### Inequality

When a net-Gini change path is supplied, the configured percentage-point growth
effect is compounded annually. With `None`, the effect is zero and status is
`inactive: no Gini path (until C3)`, matching the parameter register. This is
off by default.

## Inputs and sources

| Input | Value used by central loader | Source/status |
|---|---:|---|
| Adult mean years of schooling | 8.425371752 (2023) | Latest Brazil `mys`, untouched UNDP HDR JSON |
| Schooling elasticity | 0.35 | Litschig & Morrison (2013) / Litschig (2012); proxy based on total municipal spending |
| PWT schooling returns | 0.134 / 0.101 / 0.068 | Feenstra, Inklaar & Timmer, *Human capital in PWT 9.0* |
| Capital share | 0.4220046401 | PWT 10.01 Brazil 2019, `1-labsh`, through C2 loader |
| Education / health shares | 5.1016861266 / 5.0319033180% GDP | Tesouro COFOG 2024, carried to 2025 in C1 |
| Efficiency package share | 0.20 default; 0.16 stress | `config/scenarios.yaml` choices |
| Service-cut fraction | 0.5 central (0–1 range) | `social_modelling_choices`, explicit choice |
| Health-to-output | no central; uniform [0, 4] | Acemoglu & Johnson (2007) / Bloom, Canning & Sevilla (2001) |
| Public-capital elasticity | 0.106 central (0.083–0.122) | Bom & Ligthart (2014) |
| Initial public capital/GDP | **null** | IMF ICSD download required |
| Public-capital depreciation | **null** | IMF ICSD download required |
| Public-investment package share | 0 default; 0.20 stress | `config/scenarios.yaml` choices |
| Sovereign premium | 5 bp/pp central (2–7) | Baldacci & Kumar (2010) |
| C2 real rate / deflator / initial debt | 5.050117% / 3% / 78.64% GDP | Tesouro + BCB + IBGE inputs, through C2 loader |
| Inequality-to-growth | -0.1 pp/yr per Gini point; inactive | Ostry, Berg & Tsangarides (2014) |
| Population weights | IBGE 2024 revision, annual single age | `data/brazil/population.csv` |

The source URLs, verification levels, and licences for established parameters
are in `config/parameters.yaml` and `data/raw/SOURCES.md`.

## Central C2 transitory-corner diagnostic

These are deterministic diagnostics, not forecasts or Monte Carlo percentiles.
They use central C2 inputs, central schooling/risk parameters, the central
service fraction, no Gini path, and `allow_missing=True`. Because health has no
central value, “with feedback” is shown as a range from its configured 0 and 4
endpoints. The annual LE path is calculated with the documented C4 equation and
its central 0.04 elasticity, not interpolated. Public capital is skipped.

### Default package

| Scenario | Horizon | GDP vs S0 without | GDP vs S0 with feedback [health 0, 4] | Debt without | Debt with feedback [health 0, 4] |
|---|---:|---:|---:|---:|---:|
| R_mod | 10 | -0.4013% | [-0.6615, -0.4015]% | 133.5269% | [131.3599, 131.7432]% |
| R_mod | 20 | -0.4013% | [-0.8430, -0.4133]% | 243.2942% | [199.0567, 200.5531]% |
| R_amb | 10 | -0.8027% | [-1.3191, -0.8029]% | 121.5694% | [117.5183, 118.2368]% |
| R_amb | 20 | -0.4013% | [-1.1409, -0.4254]% | 190.0886% | [126.5880, 128.3516]% |

GDP attribution ranges (percentage points) are: human capital -0.0001 to
-0.0003 at 10 years and -0.0119 to -0.0241 at 20; health 0 to -0.2600/-0.5162
at 10 and 0 to -0.4297/-0.7155 at 20 for R_mod/R_amb; public capital, sovereign
risk, and inactive inequality contribute zero directly to GDP. Debt attribution
is interaction-sensitive: sovereign risk contributes -2.17/-4.05 pp at 10
years and about -44.3/-63.5 pp at 20 for R_mod/R_amb; the adverse health effect
adds up to +0.38/+0.72 pp at 10 and +1.50/+1.76 pp at 20. Human-capital debt
effects are at most +0.04 pp here.

### Investment-also-cut stress-like package

This in-memory case uses the configured 32/20/16/12/20 package shares and lets
C2 apply its public-investment multiplier. It is only “stress-like,” not a full
C5 public-capital stress, because the missing IMF stock and depreciation force
that feedback contribution to be skipped.

| Scenario | Horizon | GDP vs S0 without | GDP vs S0 with feedback [health 0, 4] | Debt without | Debt with feedback [health 0, 4] |
|---|---:|---:|---:|---:|---:|
| R_mod | 10 | -0.5377% | [-0.7715, -0.5378]% | 133.6872% | [131.5966, 131.9438]% |
| R_mod | 20 | -0.5377% | [-0.9163, -0.5473]% | 243.5408% | [199.6912, 201.0018]% |
| R_amb | 10 | -1.0755% | [-1.5386, -1.0757]% | 121.8924% | [117.9806, 118.6332]% |
| R_amb | 20 | -0.5377% | [-1.1540, -0.5569]% | 190.3250% | [127.2601, 128.7862]% |

Human-capital GDP contributions are -0.0001/-0.0002 pp at 10 years and
-0.0095/-0.0192 pp at 20 for R_mod/R_amb. Health contributions range from zero
to -0.2336/-0.4629 pp at 10 and -0.3690/-0.5971 pp at 20. Public-capital GDP and
debt contributions are flagged skipped, not zero estimates. Sovereign-risk debt
contributions range roughly from -2.09/-3.91 pp at 10 to -43.9/-63.1 pp at 20,
with small endpoint interactions from health.

## Downloads needed

- IMF Investment and Capital Stock Dataset: latest non-null Brazil public
  capital stock as a share of GDP and the corresponding public-capital
  depreciation rate, retaining the observation years and dataset licence.
  Until archived and registered, channel 3 cannot be activated.

## Tests and limitations

`tests/test_feedback.py` covers zero-channel identity, S0 neutrality, cohort
replacement and the PWT slope, health linearity, public-capital accumulation,
lagged risk/debt monotonicity, first-order symmetry, and fail-closed missing IMF
inputs. Schooling uses adult MYS as the cohort dose scale because the source
does not publish a Brazil-wide school-age baseline. The elasticity itself is a
municipal-total-spending proxy. Public-capital maintenance investment is
implied from the two requested IMF inputs; it should be revisited if the ICSD
download supplies a consistent investment-flow series.
