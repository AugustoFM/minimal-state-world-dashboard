# D3 debt-panel method

`python -m src.debt_panel` reads only archived files and deterministically rebuilds the six CSVs, report, method note, and proposed-calibration YAML.

## Data and panel

The sample is the fixed list of 24 advanced and 26 emerging economies for 1975-2024. IMF Public Finances in Modern History supplies debt, primary balance, interest and primary expenditure. WEO, HPDD and GDD debt fields are cross-check columns only. WDI supplies real growth, GDP-deflator inflation and ageing measures. Rows with missing observations remain missing; nothing is interpolated. The archived JST file has an `.xlsx` suffix but Stata 118 content, so it is read with `pandas.read_stata`.

## Accounting

For exact annual lags, nominal growth is `(1+g)(1+pi)-1`. Contributions follow the formulas fixed in `tasks/D3.md`; SFA is the residual that makes their sum equal the observed debt change. Effective interest and r-g are missing when lagged debt is below 5% of GDP. Large SFA means absolute SFA above 10 points. Calibration summaries restrict the sample to years with GDP-deflator inflation below 15% and to 2000-2024 because the FPP interest/SFA split is not comparable in high-inflation years.

## Trajectories and episodes

A 20-year window requires observed debt at both exact endpoints. Cumulative primary balance and decomposition contributions report their observation counts and are never gap-filled. Local peaks require a complete +/-5-year debt neighborhood. Reductions use the lowest subsequent debt within ten years from a peak and require a 15-point fall. Increases retain every start year whose maximum debt within ten years is at least 30 points higher; overlaps are intentionally visible.

## Estimation

The output gap is the log real-GDP index reconstructed from WDI growth minus an HP trend (lambda 100) within uninterrupted segments. Panel FRFs use within-country demeaning and country-clustered covariance with finite-sample correction. Brazil uses OLS with an intercept and Bartlett Newey-West covariance with two lags. Robustness rows add debt squared/cubed, omit lagged primary balance, start in 1990, restrict current observations to inflation below 15%, or restrict the period to 2000-2024. Long-run response is rho/(1-phi). Cubic fatigue is the lowest real zero of the marginal debt response inside the observed estimation range.

For the Brazil 2000-2024 robustness, the BCB primary-result series is converted from NFSP signs (positive is a deficit) to primary-balance signs and paired with FPP debt. The FPP primary-balance version is retained as a direct comparison. No balance observation is interpolated. Stabilisation thresholds are arithmetic comparisons of long-run FRF responses with `(r-g)/(1+g)` and do not alter the debt model.

The ageing regressions use all exact-endpoint 20-year windows with an advanced-economy dummy and country-clustered uncertainty. A fixed 1995-2024 long difference is labelled robustness. These regressions are descriptive because ageing, spending and fiscal balances respond to common shocks and institutions.

## Important limitations

Country definitions and fiscal perimeters can change. WDI macro series need not share the fiscal data denominator, making SFA partly a source-alignment residual. Fixed-effects dynamic-panel estimates may have Nickell bias. Cluster inference has only 24 or 26 clusters in group estimates, and Brazil HAC inference is small-sample. HP gaps are endpoint-sensitive. The panel has no default/restructuring flag, so it cannot identify a maximum non-default debt observation. Overlapping windows and episodes are not independent. JST long rates are market yields, whereas the main panel uses an effective debt-service rate.
