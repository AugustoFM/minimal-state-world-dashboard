# C6 External block

`src/external.py` adds the external environment (commodity terms of trade and the BRL/USD exchange rate) as an exogenous, uncertain input. It is not a policy lever: in every Monte Carlo draw all scenarios receive the same external path, so differences between scenarios remain attributable to policy, and external luck is not credited to or blamed on a policy (the 2003-2010 lesson: exports, reserves and the exchange rate moved with a ~37% terms-of-trade rise while the primary surplus stayed at 3.2-3.7% of GDP).

## Paths
- Stochastic (D1): moving-block bootstrap (3-year blocks) of joint observed annual log changes of the WDI net barter terms of trade and the official BRL/USD rate, 2006-2024 (`data/brazil/backtest_observed.csv`). Resampling the pair together keeps their co-movement (correlation -0.64: commodity booms strengthen the real). Only observed changes are used; nothing is invented. Separate random stream `[seed, 1]`, so parameter draws are unchanged.
- Reference: `boom` = observed 2005-2011 changes then flat; `bust` = observed 2011-2016 changes then flat; `neutral` = no change. Results for the central parameter draw are in `outputs/runs/external_reference_paths.csv`.

## Equations
- GDP: impulse_t = beta x terms-of-trade change_t, beta = 0.033 (`external_block.gdp_wrt_commodity_prices`, derived from Gruss 2014). Half of each impulse is permanent (potential output; actual output co-moves about twice as strongly as potential, IMF WEO 2015) and half is cyclical, decaying with a 2-year half-life (choice).
- Inflation: extra inflation_t = 0.10 x depreciation_t + 0.06 x depreciation_(t-1) (BCB pass-through 0.10 at 12 months, 0.16 cumulative at 24 months).
- Debt: re-run with `src.macro.debt_step` on nominal GDP including the external level effect and extra inflation. The nominal rate is kept Fisher-consistent with the C2 real rate, so inflation by itself does not erode debt.

With the neutral path the block reproduces C2's debt and GDP per capita exactly (`tests/test_external.py`).

## Outputs added to D1
`external_gdp_level_pct`, `gdp_per_capita_with_external_vs_s0_pct`, `debt_gdp_with_external`, `debt_gdp_with_external_vs_s0_pp`, `inflation_with_external_pct`. Sampled paths' cumulative terms-of-trade and FX changes are saved per draw in `outputs/runs/draws/sampled_parameters.csv`.

## Choices and gaps
- Choices: 3-year blocks, 2-year half-life of the cyclical part, potential share 0.5, beta held at its point estimate (no sourced range).
- Gaps (from `external_block.gaps`): commodity revenue beyond revenue moving with GDP (oil royalties); the FX-linked share of public debt (so depreciation has no valuation effect on debt here); capital flows and FDI; a terms-of-trade series before 2005 (FUNCEX) for the 2003-2004 back-test years.

## First results and a warning for D2
With beta = 0.033 the external block is small: repeating the observed 2005-2011 boom moves the GDP level by about +0.6% and debt/GDP by under 1 pp at 10 years (central parameters, `external_reference_paths.csv`); bootstrap paths give p10-p90 of -0.3% to +0.8% at 10 years. This follows from the sourced estimate (Brazil responds much less than its LAC peers, Gruss 2014), but it is hard to square with 2003-2010, when exports tripled, reserves rose eightfold and the real appreciated strongly. The channels C6 lacks (capital inflows, appreciation lowering inflation and interest rates, commodity revenue, FX-linked debt) are the likely reason. D2 must test this first: if the back-test cannot reproduce 2003-2010 with observed external paths, the block understates external effects and must be extended before any projection is published.
