# Method: presidential travel, costs and external outcomes

## Scope and invariants

The build is offline and deterministic. It uses only frozen repository inputs, treats every president identically, retains value-year pairs, and never interpolates a missing observation. Presidential labels are FHC (1995-2002), Lula I-II (2003-2010), Dilma Rousseff (to 30 August 2016), Michel Temer (from 31 August 2016), Jair Bolsonaro (2019-2022), and Lula III (2023-2026).

## Trips and days

Year-specific wikitext tables are parsed. Country cells come from flag templates; dates accept English and Portuguese month names and same- or cross-month ranges. Primary sources are Portuguese for FHC and Lula and English for the other presidents. A table's explicit trip number groups multi-country legs. Where a source has no trip number, rows whose date intervals overlap or are directly contiguous are grouped as one departure-return itinerary. A trip's day count is the inclusive union span from earliest start through latest end; country-visits are unique countries in that trip. Primary/cross-check differences are retained as flags rather than silently reconciled.

This grouping assumes a shared explicit number or overlapping/directly contiguous listed dates identifies one continuous itinerary. It can undercount separately ticketed trips on the same or consecutive days or overstate days if a source omits an intervening return to Brazil. Listed days are explicitly a lower bound because stop dates can exclude outbound and return travel days. Press/page-lead counts are context only: differences can arise from list completeness, trip-versus-stop counting, travel-day rules and snapshot cut-off dates. The original rows remain recoverable from the cited raw files.

## Costs and prices

For each Portal record, nominal net cost is `per diem + tickets + other - refund`; the source field is Portal “Valor devolução” (money returned). Each component is multiplied by cumulative monthly IPCA after its start month through September 2026. Thus September 2026 has factor 1; dates without a price factor remain missing.

A presidential-trip support record must (1) be flagged international, (2) overlap a listed trip date interval, and (3) have at least one destination country matching that trip. Matching normalises Portuguese/English country names and common three-letter flag codes. Other Presidency international travel is reported separately. Spouse-related records use the pre-fixed motive terms “FAMILIAR DO SR PRESIDENTE”, “PRIMEIRA-DAMA”, or “CONJUGE”; these are staff/security support costs, not an itemised spouse bill.

Every matched-support amount is labelled a **lower bound**. The travel system covers Presidency bodies, selected Defence support, and other organs citing presidential missions. It excludes Air Force aircraft, payment-card hotel/expense items, and unitemised costs of the President and spouse. Optional `presidency_cpgf_2013_2026.csv.gz` is a separate card series: conservatively identified foreign transactions are reported separately and never mixed into travel-system costs. Published figures in `cited_figures_press.csv` are context only and retain their source basis.

## Aggregate association

The annual 1995-2025 frame contains trips, days, monthly BCB FDI and goods exports summed to annual values, WDI FDI as percent of GDP from the existing observed-data build, and the annual FUNCEX export quantum index. For each outcome, travel measure, lag 0-2 and transformation:

`y_t = a + b travel_(t-lag) + controls_t + trend + error_t`

Level models contain a linear trend; first-difference models difference outcomes, travel and controls and omit the trend. Controls are the local commodity terms-of-trade index, world GDP growth, China GDP growth, and BRL/USD. Coefficient intervals use Newey-West covariance with lag 2. A two-sided permutation p-value shuffles travel year labels 10,000 times after partialling the other regressors (seed 20261022 plus lag). Missing controls are listwise deleted and n is reported per model. These low-powered time-series associations begin with only 31 years and are vulnerable to global cycles, simultaneity and destination selection. A levels coefficient is not treated as robust unless it survives first differences; the exports-per-trip result does not.

## Bilateral association

The 1997-2025 panel uses log positive FOB exports to each ComexStat partner. Separate models estimate visits at t, t-1 and t-2:

`log(exports_ct) = country FE + year FE + b visit_c,t-lag + error_ct`

Standard errors are clustered by country. Robustness adds country-specific linear trends. The placebo moves actual visits two years earlier, so a visit at t+2 predicts exports at t. Log coefficients and confidence bounds are reported as `100*(exp(b)-1)`. Each timing is estimated separately. The placebo is about as large and significant as t−1, while no coefficient survives country trends; this supports the reading that visits tend to follow already-growing trade partners, not a causal export effect.

## Reproducibility and output interpretation

Run `python -m src.presidential_travel`. The CSVs are machine-readable sources for the report and embedded HTML. Empty/missing means unavailable, never zero, except visit indicators and annual trip counts in a known covered list where no listed trip is zero. The HTML contains inline CSS, JavaScript, SVG and embedded JSON and makes no request.
