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

## Lead-developer review (2026-10-21)

- Coefficients for A were re-estimated independently (numpy lstsq) and match to four decimals.
- The 2006-2010 episode lies inside the primary fit window, so the primary "20.9% of 24.5%" is in-sample.
  The genuine out-of-sample check of the boom is the prespecified reverse window (fit 2010-2024):
  dlnP 0.082 (SE 0.035), test RMSE 1.59 vs naive 2.59, sign agreement 10/10, cumulative 2006-2010
  prediction 14.4% vs observed 24.5% (about 59%); C6 gives about 0.7%.
- 2014-2016 stays unexplained by every specification (reverse model -1.2% vs observed -6.2%): the
  recession was mostly domestic.
- Primary A over-predicts 2017-2019 (9.7% vs 4.4%) through its constant and world-growth level: Brazil's
  trend fell after 2014. The model uses A only for shock deviations (no constant), so trend growth still
  comes from C2.
- Wiring decision: A replaces the C6 terms-of-trade-to-GDP coefficient, with the coefficient set drawn per
  Monte Carlo draw from the two prespecified windows (primary or reverse, equal probability), and bootstrap
  inputs demeaned over the sample so draws add shocks, not a trend. C (investment) is already part of A's
  total-GDP response and is reported only, to avoid double counting. B is not supported: interest rates
  stay as in C2/C5. D: only dividends pass, and they mostly reflect Petrobras payout policy; not wired,
  left as an option for the user. *Update 2026-10-21 (P2):* wired at the user's request as a best guess -
  `output_channel_c7.dividend_revenue` (lnP 0.838) adds commodity-linked dividends to the primary balance in
  the external debt path, the same for every scenario.
- In the D2 growth-accounting block (observed investment and labour fed in) A would double count factor
  responses, so A is evaluated by the direct out-of-sample growth test above, not added to D2's block.
