# C7 external block v2

`src.external_v2` estimates the prespecified annual Brazilian external-channel equations using only checked-in files. It has no network path and no global estimated state.

## Public API

- `load_prepare_data()` reads and transforms Pcx, CTOT, US rates, EMBI, macro outcomes, GFS revenue codes 1412/1415, and the GFS implicit interest rate.
- `estimate_channels(window)` returns coefficients, Newey-West standard errors, fit statistics, exact estimation years and fit means for `primary`, `robustness`, `reverse`, or `all`.
- `predict(data, model)` applies one returned model.
- `historical_changes_v2()` returns the complete observed 2000-2024 joint path of `dlnP`, `dUS`, and world GDP growth for a later block bootstrap.
- `effects_from_path(path, coefficients)` returns GDP-level, EMBI, real-rate, debt-rate, commodity-revenue and investment-rate effects. It removes intercepts and centers world growth on A's fit mean, so a zero path produces zero effects.

## Units and dynamics

`dlnP` is a percent log change, `dUS` is a percentage-point change, and `dEMBI` is basis points. B2 receives `dEMBI / 100`. A's annual growth deviations compound to a GDP-level deviation. C's predicted annual changes cumulate to the investment-rate level. D is evaluated relative to the projection base-year Pcx level. B3 applies contemporaneous and lagged real-rate changes.

## Estimation and wiring boundary

The point estimates are proposals, not runtime parameters: `config/parameters.yaml` is untouched. The lead developer should wire only mechanically supported channels. Current supported primary equations: A_output, B2_real_rate, C_investment, D_dividends. See `config/c7_proposed.yaml` for exact proposed mappings and `outputs/c7_backtest.md` for the full limitations and robustness table.

The prediction equations are associations. In particular, EMBI and Selic endogeneity prevents a causal reading, and no Monte Carlo integration is performed in C7.
