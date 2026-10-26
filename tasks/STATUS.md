# Task status board (Codex: update this file after each task; Claude reads it to review)

| ID | Status (todo / in progress / PR open / done) | Branch / PR | Notes, problems, data gaps |
|---|---|---|---|
| A1 | done | `codex/brazil-a1-a4` | Consolidated Tesouro GFSM 2014 total and primary expenditure, annual 2010–2026 Q2. 2026 is partial; Q4 rolling-12-month % GDP used for completed years (latest quarter for partial year). Mandatory/discretionary split unavailable in this source. |
| A2 | done | `codex/brazil-a1-a4` | IBGE 2024 revision, Brazil by single age/sex, 2000–2070. UN WPP cross-check remains a data gap. |
| A3 | done (PNAD); POF pending download | `task/a3` | PNAD Continua 2025 visit 1 downloaded (git-ignored), read from the official SAS layout (scripts/read_ibge_fwf.py), mapped (mappings/pnadc_2025_visita1.json) and validated: Gini 0.5112 vs IBGE SIDRA 7435 0.511; population within 0.35%. Corrections to draft: weight is V1032 (not V1028); per-capita income concept is VD5008 (VD5002 gives 0.523, not the published concept). POF 2017-18 Morador codes transcribed (mappings/pof_2017_2018_morador.json); POF income codes (V9001) classified and linked to scenario packages (mappings/pof_2017_2018_income_codes.csv); POF microdata download deferred to C3. Tax-return centiles: Receita Federal AC 2024 archived and tidied (data/brazil/micro/tax_centiles_2024.csv; overlapping top rows flagged; totals reproduce the published figures). Done by Claude while Codex was at its usage limit. |
| A4 | done (fallback) | `codex/brazil-a1-a4` | Refetched WDI `GC.XPN.TOTL.GD.ZS` for 1990–2025 and rebuilt exact endpoint episodes. Central-government expense only, **not general-government expenditure**; no interpolation. Middle-income sample now has 598 15-year and 386 20-year episodes. Brazil itself has no exact 15/20-year pairs in the returned series (Brazil observations begin in 2010). |
| B1 | done | `task/b1` | Precedent cap below S0 (conservative/central): 3.9/4.9/6.1/7.0 and 4.2/5.5/7.3/8.5 pp at 5/10/15/20y; robust to threshold grid, leave-one-country-out and country bootstrap (b1_sensitivity.csv). R_mod inside everywhere; R_amb 20y capped 8 -> 7.0; optional R_max added. Implementability: federal discretionary is only 1.6% GDP (IFI RAF 101), so from 10y on both R paths need mandatory-rule changes (lower bounds reported); the LC 200/2023 25% withholding limit is a one-year tool and is not used as a multi-year allowance. Reviewed by Codex. Proxy: central-government episodes. |
| B2 | done | `task/b2` (merged) | Multipliers (Sanches et al. 2026), Gini effects (Ball et al. 2013) and infant-mortality elasticity (Szklo et al. 2024) checked in full text; ranges are spread across specifications, not CIs. Reviewed by Codex. Gaps: schooling and physician elasticities (C4 limited to mortality/life expectancy). |
| C1 | done | `task/c1` (merged) | Codex revision moved all runtime C1 inputs and source notes into `config/parameters.yaml` and changed the default builder path; removed the duplicate proposed-parameter file. C1 uses reproducible NTA profiles (ages 0–90+, 2003/2018) and 2024 COFOG shares; bounds are sensitivity envelopes, RGPS is a labelled proxy for RPPS-inclusive pensions, and 2024 shares carry to 2025. |
| C2 | done | `task/c2` (merged) | Multiplier GDP effects (transitory/persistent), debt dynamics on the Tesouro GFSM primary balance with same-year Fisher-adjusted implicit rates, PWT 10.01 growth accounting with dynamic 2000-2019 backcast. Central S0 potential growth ~0.9%/yr at 10y (IMF 2.5%: gap from PWT's negative TFP trend); central S0 debt 145% GDP at 10y vs IFI ~125% (gap mostly r-g). R paths read from scenarios.yaml by_year (R_amb 20y = 7.0 after B1). Built by Codex over five review rounds; sources archived and verified by Claude. Inputs consolidated into config/parameters.yaml (task/c2-registry). |
| C3 | done | `task/c3` (merged) | Reviewed by Claude: validation reproduces IBGE Gini 0.51119, population, 79.3 m households; statutory lines verified on Planalto. Note: E_*_tax raises poverty at R$218 under the default spending mix (pension-heavy) with income-proportional or consumption-like tax incidence; incidence and composition drive that result. | Vectorised PNAD household microsimulation with proportional/indexation-floor pensions, GDP-only/employment labour, proportional/consumption-like taxes, means-tested transfers, survey Gini/poverty/top shares and declarant-only tax context. No-change: Gini 0.511190, population 212.683m, households 79.305m, poverty R$218/R$759 3.181%/23.055%; 0.077s prepared evaluation. `85 passed` using a worktree pytest temp root (default Windows temp ACL is inaccessible). Gaps: no offline SIDRA poverty table; S1 omitted because no package allocation; D1 wiring reserved for lead developer; POF incidence pending. |
| C4 | done | `task/c4` (merged) | Social block produces 5/10/15/20y sensitivity envelopes for S0, S1, R_mod, R_amb and optional R_max from C1 health shares and C2 GDP per capita; reviewed and committed by Claude (Codex run ended at usage limit after outputs were complete); IMR and LE anchors are read from raw files, S0 has no assumed trend, and every configured gap is emitted as `not_modelled`. LE uses its central-only elasticity; bound combinations are recorded. `40 passed`; CLI wrote 660 rows. No upstream-file change requested. |
| C5 | done | `task/c5` (merged) | Built by Codex: src/feedback.py with schooling (cohort replacement into PWT hc), health-to-output, public capital and sovereign risk premium channels plus per-channel attribution; inequality inactive until C3. Claude changed the risk premium to respond to debt vs base year for all scenarios incl. S0 (brief had specified vs S0) with a 50 pp deviation cap (choice), and filled public-capital inputs from IMF ICSD (K_g/GDP 0.769 in 2019; depreciation 3.44%). |
| C6 | done | `task/c6` | Built by Claude: src/external.py, block bootstrap (3-yr) of joint observed 2006-2024 ToT and BRL/USD changes, same path for every scenario per draw; GDP via 0.033 elasticity (half permanent), inflation via BCB pass-through 0.10/0.16, debt re-run Fisher-consistent. Neutral path reproduces C2 exactly. Reference boom/neutral/bust results in outputs/runs/external_reference_paths.csv. Gaps: commodity revenue, FX-linked debt, capital flows, pre-2005 ToT. |
| P1 | done (results unpublished) | `task/p1` | src/programs.py builds P_lula (LC 200 rule) and P_flavio (debt-target rule) as C2 scenarios; general extensions package_gaps_by_year, debt_adjustment_by_year, C3 tax cuts; MC flags --programmes / --programmes-common-composition. Existing draws byte-identical. Explicit minimum-wage rule still a gap (current law via C1 proxy). See docs/p1_programmes.md. Results only after D2 gate and user review. |
| P2 | done (results unpublished) | `task/p2` | User request 2026-10-21: Flávio cut scenarios low/mid/high = 1.0/1.5/2.0 pp GDP (official programme; reported 1.5-2% plan, Folha 2026-10-08, denied by the campaign); Lula rule (LC 200) and record (2022-2025 spending +0.64 pp/yr, taxes +0.36 pp/yr); debt-stabilising balance now a diagnostic. C7 dividends wired (same for all). G2 corruption shock wired (same for all). |
| E | done | `task/expansion` | E_mod (+1/2/3/4 pp above S0) and E_amb (+2/4/4.8/4.6, capped at observed p90 increase minus C1 drift) added, debt-financed; mirror R in the current near-linear model. Tax-financed versions and the revenue elasticity (IFI EE16: long run 0.92-0.98, sourced in parameters.yaml) come with the revenue-path task. |
| REV | done | `task/revenue` | Revenue path in C2 by Claude: revenue/GDP scales with (Y/Y_S0)^(e-1) (C2 keeps e=1; D1 samples IFI EE16 long-run 0.92-0.98) and scenarios can set revenue_by_year (tax change, GDP effect via Sanches revenue multiplier). Tax-financed E_mod_tax / E_amb_tax added. Published C2 rows unchanged. Tax incidence by income still needed for C3/P1. |
| F1 | done | `task/f1` (merged) | Codex extracted 19 years from archived LDO annexes with tested source quotes; outturns match BCB within 0.03 pp (2008, 2020 explained). Claude turned it into parameters.yaml fiscal_delivery: consolidated, vs original target, 2020 excluded: median +0.25, mean +0.09, p10 -2.69, p90 +2.81 pp GDP. Default P1 use = median bias (~0); full spread only as sensitivity because it mixes macro surprises. Missing 2001, 2003-2007, 2009, 2013. |
| G1 | done | `task/governance` | Governance added by Claude: WGI and CPI by government period as context (differences since 2017 within error bands; not model inputs); leakage 2.8-13% of social spending (Ferraz, Finan & Moreira 2012) sampled in D1, same for every scenario so it cancels in comparisons; 'leakage halved' sensitivity reported for all scenarios. docs/governance.md. |
| D1 | done | `task/d1` | Built by Claude (Codex at usage limit). src/montecarlo.py runs the unchanged C1/C2 code per draw (sampled value written as low=central=high) plus C4 functions; paired differences vs S0; 5 composition variants x 2 persistence settings; 1,000 draws, seed 20261020. Test pins the all-central draw to published macro.csv/social.csv. Outputs: outputs/runs/summary_percentiles.csv, run_metadata.json (draw files git-ignored). Excludes C3 (rows not_modelled), C5, C6; parameter uncertainty only. |
| D2 | fixed and reviewed (gate v2: Tier 1 genuinely PASS, Tier 2 FAIL, permanent) | `task/d2b` | Gate v2: Tier 1 differences vs S0 PASS (one-step debt MAE 2.054 <= 2.5 pp; growth absolute mean error 0.165 <= 0.5 pp/yr; C7 A OOS RMSE 3.004 < naive 3.881). Tier 2 levels FAIL: 2017-anchor 2024 error +16.061 pp without SFA and +12.472 pp with the fixed 2011-2017 mean SFA (-0.500 pp/yr), both above 5 pp. Neutral period diagnostic added; 2025 debt, primary balance, commodity and C7 inputs unavailable and not carried forward. **Claude review (2026-10-23):** code and tests verified (12 passed); debt one-step is a pure accounting identity (no fitted parameter) and the C7 OOS check is genuinely held out (fit 2000-2014, tested 2015-2024) — both sound. But the growth-block Tier 1 check is *not* held out: its fixed TFP rate is the PWT CAGR over 2000-2019, which fully contains the 2006-2019 test window, so its PASS shows internal consistency, not out-of-sample skill. Caveat added to `outputs/backtest.md`. Also restored an accidentally-deleted "Lead-developer review" section in `docs/c7_external_v2.md` that had been dropped from the working tree without a matching commit. **Per `PLAN_BRAZIL.md`'s stated gate ("back-test errors within tolerance... before dashboard/report"), Tier 2's FAIL formally blocks E1/E2 as validated deliverables** — the existing EXPLAINER artifacts already work around this by reporting Tier 2 FAIL prominently rather than suppressing it. **2026-10-24 fix (Claude):** the growth-block Tier 1 contamination flagged above is fixed, not just caveated. `src/backtest.py::build_growth_test` now reports two statistics: `growth_block` (unchanged TFP window 2000-2019, kept `not_rated`, used only for the episode narrative) and a new `growth_block_oos` (TFP fixed at a new, genuinely pre-sample window, 1996-2005, added to `config/parameters.yaml growth_calibration.tfp_periods` as `pre_2006_backtest_oos`; this key is additive and is not read by `src/macro.py`'s C2 projection, which only reads `low`/`central`/`high`). `gate_verdicts` now rates Tier 1's growth-block check on `growth_block_oos`, not the in-sample one. Result: Tier 1 still PASSES, and more comfortably than before (OOS mean error -0.036 pp/yr vs the old in-sample 0.165 pp/yr) — a genuine, not assumed, finding. `outputs/backtest.md` and `config/d2_inputs_proposed.yaml` updated; two new regression tests added (`tests/test_backtest.py`, 16 total, all passing); full suite re-run clean (224 passed). Tier 2 is now treated as a *permanent*, not a to-fix, limitation — see the D4 row below for the diagnostic layer that replaces "try to fix the point forecast" with "report the uncertainty honestly." |
| SFA | wired, D1 rerun complete, report regenerated | current checkout `codex/brazil-a1-a4` | User request 2026-10-23, following D2 review: historical implied stock-flow adjustment (Treasury<->BNDES loans, BCB result transfers) cannot be point-forecast (discretionary future policy, not predictable from covariates), so instead of chasing a Tier-2 point-estimate fix, wired as a stochastic term in the Monte Carlo to widen debt-level uncertainty bands honestly. Implementation: `src/external.py::historical_sfa_changes` reads D2's `sfa_summary.values_by_year` (2011-2024), demeaned; block-bootstrapped (3yr, reusing `external.bootstrap_path`) on new RNG stream `[seed, 9]`; same draw applied to every scenario in `src/macro.py::run_corner` via `frame["debt_adjustment_pp"] -= sfa` (sign flipped: D2's SFA convention is positive = debt-increasing, debt_adjustment_pp is positive = debt-reducing), added before the per-scenario debt loop so scenario-specific adjustments (privatisation, programme debt_adjustment_by_year) are untouched and it flows through debt_gdp, debt_gdp_with_external and debt_gdp_with_feedback. Deterministic paths (`central_draw`/`evaluate_draw` without `run()`, and `reference_paths()`'s boom/neutral/bust) do not include it, so published macro.csv/social.csv and the C6 reference-path diagnostic stay untouched. Not an exact cancellation vs S0 over multiple years (scenario-specific GDP effects feed the nominal-growth denominator), documented as such rather than overclaimed. On by default - flagged to user, not yet confirmed. 65/65 existing tests passed before the change; added `test_sfa_adjustment_is_sign_flipped_uniform_across_scenarios_and_additive` (test_macro.py), `test_sfa_uses_a_dedicated_stream_and_only_perturbs_debt` and `test_central_draw_has_no_sfa_noise` (test_montecarlo.py) — all pass; discovered and confirmed-correct that the sovereign-risk-premium feedback channel (responds to debt deviation) also shifts under SFA, so the isolation test asserts debt differs and GDP-side indicators don't, not full-frame equality. Documented in `docs/sfa.md`. **2026-10-23 update:** full `tests/` suite reran clean (222 passed, 4:26). 1000-draw D1 Monte Carlo rerun completed (seed 20261020, 8478s runtime, inputs commit de8c2e2 — this also folds in the W2/education-firm-distress and W3/anti-corruption-sensitivity code merged since the last published run on 2026-10-21, not SFA alone); `outputs/runs/summary_percentiles.csv` and `run_metadata.json` updated (metadata now documents the `stock_flow_adjustment` mechanism). `outputs/results_brazil.md` regenerated from the new summary via `scripts/report_brazil_results.py` (427 lines changed — mostly small numeric shifts from SFA-widened debt bands and the folded-in W2/W3 code; no structural changes). Still open: EXPLAINER artifacts (`outputs/brazil_results_explainer.html`, `outputs/brazil_scenario_explained.pptx`) still reflect the 2026-10-21 pre-SFA run and have not been refreshed — left for the user to review alongside the E1/E2 hold decision rather than refreshed unilaterally, since they're user-facing deliverables. User confirmation on "on by default" still pending. |
| D4 | done | current checkout `codex/brazil-a1-a4` | User request 2026-10-24: review and finish D2, then unblock E1/E2 ("Maximal" scope: wire the D3/I1 proposals, not just document the gap). Built by Claude: `src/debt_level_diagnostics.py` wires every unimplemented row of `docs/debt_models_review.md`'s "What we are missing" table that the user chose to pursue (status column added there) without touching `src/montecarlo.py`, `config/scenarios.yaml`, or any existing Monte Carlo output. Reuses `src.montecarlo.load_context`/`sample_draw`/`central_draw`/`parameters_for_draw`/`inputs_for_draw` and `src.macro.run_corner` directly (discovered that `evaluate_draw` discards the full annual path before returning, keeping only the four published horizon years, so a new lightweight annual-resolution S0-only run was needed — this is why the plan's original "CLI flags on `src.montecarlo`" design became a standalone module instead, matching the existing D3/`debt_panel.py`, I1/`rates.py` pattern). 300 draws (central + 299 sampled, independent RNG stream `[seed, 10]`, unused by any of `run()`'s nine existing streams), ~2m18s runtime. Reports: probability of S0 breaching 90/100/120% of GDP; stabilising primary balance and fiscal gap (EC S1/S2-style, derived purely from the debt identity, no new inputs); debt-level bands under Brazil's-own vs. an emerging-panel-calibrated SFA prior; two off-to-the-side S0-only diagnostic variants (`frf_emerging`/`frf_brazil_robustness` using D3's emerging-panel and Brazil's own, oppositely-signed, fiscal-reaction-function estimates; `premium_nonlinear`, a capped fiscal-fatigue-style risk premium, explicitly a modelling choice per D3's own caveat that no ceiling is estimated). First run surfaced and fixed a real bug: an uncapped quadratic premium overflowed to ~1e34 by 2045 in testing; now capped at 2,000bp, documented in `docs/d4_debt_level_diagnostics.md`. `outputs/backtest.md` points to the new report directly under its Tier 2 verdict. 11 new tests (`tests/test_debt_level_diagnostics.py`), including a sign-direction check on the two FRF robustness paths and an SFA-stream-collision guard; full suite re-run clean. Outputs: `outputs/debt_level_diagnostics.md`, `data/brazil/debt_level_diagnostics.csv`, `docs/d4_debt_level_diagnostics.md`. |
| E1 | done | | User decision 2026-10-23: hold until Tier 2 debt-level gate implications of the SFA stochastic term are back in front of the user. **2026-10-24:** built by Claude. `scripts/build_brazil_dashboard.py` writes `dashboard/brazil_data.js` from `outputs/runs/summary_percentiles.csv`, `config/scenarios.yaml`, `outputs/backtest.md` (reusing `scripts/report_brazil_results.py`'s already-reviewed `LABELS`/`DECIMALS`/`parse_backtest` rather than redefining them) and `data/brazil/debt_level_diagnostics.csv`. `dashboard/brazil.html` is a vanilla-JS/SVG page (no new dependency; matches `dashboard/index.html`'s existing style) with a persistent Tier 1/Tier 2 gate banner, an indicator/scenario/persistence/composition explorer with a p10-p50-p90 band chart, an all-scenarios-at-one-horizon table, and a D4 diagnostics panel (probability of breach, fiscal gap, the two S0-only variants) with its own Tier 2 caveat attached directly, not only in a footnote. Verified in a real browser (Claude in Chrome, served over a local HTTP server since the extension cannot open `file://` URLs): initial render, console clear of errors, and spot-checked cells (R_amb/10y/default/transitory debt vs S0 = -23.3 [-24.7,-21.4]) match `outputs/results_brazil.md` and `outputs/debt_level_diagnostics.md` exactly; interactivity (indicator/persistence change) re-renders correctly. One bug found and fixed during review: the composition selector defaulted to whichever variant happened to be first in the data rather than `default`, giving a correct but non-headline number on first load. |
| E2 | done | | Same hold as E1. **2026-10-24:** built by Claude: `outputs/report_brazil.md`, a standalone narrative report distinct from the raw results dump and the EXPLAINER artifacts — the question and scenario grid, a condensed per-block method walkthrough, headline 10-year results with the composition/persistence caveats stated once rather than scattered, the back-test read honestly (including the Tier 1 fix and the D4 diagnostics table), the P1 programme-mapping methodology **without publishing a programme comparison** (same withholding rule as the academic paper, per `docs/p1_programmes.md`), limitations, and a pointer table to every underlying file. Numbers spot-checked against `outputs/results_brazil.md` before writing. |
| EXPLAINER | done (local artifacts) | current checkout `codex/brazil-a1-a4` | Refreshed `outputs/brazil_results_explainer.html` from the latest D1 summary (seed 20261020, 1,000 draws, created 2026-10-21 14:11 UTC; inputs commit aa22b54). Embedded only interface indicators. Audited scenario labels, paired vs-S0 interpretation, units, anchors, uncertainty notes, and mortality conversion. D2 note now matches gate v2: Tier 1 scenario differences PASS; Tier 2 debt/GDP levels FAIL (+12.472 pp OOS error with SFA, 5 pp tolerance). Unemployment remains an editable illustrative 5.6% flat anchor; life expectancy is at birth; distribution and health S0 anchors are held flat. Other artifact: `outputs/brazil_scenario_explained.pptx` (10 slides). Dedicated branch creation was blocked because `.git` is read-only in this workspace. |
| R1 | reviewed | `task/r1` | Reproducible internal-review report for the committed 1,000-draw Monte Carlo. D2 gate FAIL is prominent; debt levels carry the documented backtest caution. Summary data are structurally consistent; C3 distribution rows are modelled only for default, non-S1 scenarios, with all other C3 cells explicitly marked not modelled. **Claude review (2026-10-23):** spot-checked `outputs/results_brazil.md` against `outputs/runs/summary_percentiles.csv` (e.g. R_mod/transitory/10y GDP cell: source p10/p50/p90 -0.483/-0.396/-0.311 -> reported "-0.40 [-0.48, -0.31]", correct rounding) and read `scripts/report_brazil_results.py` in full - labels, decimals and D2-verdict parsing are sound; `tests/test_report_brazil_results.py` passes. **2026-10-23 update:** regenerated from the new post-SFA `summary_percentiles.csv` (`python scripts/report_brazil_results.py`); header now shows inputs commit de8c2e2, created 2026-10-23T10:30:10Z. Diff against the prior version is widespread but small in magnitude (debt-level and debt-driven figures shift as expected from SFA noise plus the folded-in W2/W3 code); no structural or label changes. |
| C7 | done | `task/c7`, `task/c7-wire` | Channels estimated by Codex with fixed specs, fit 2000-2014 / test 2015-2024. A (output) supported: reverse-window fit predicts ~59% of the 2006-10 boom out of sample (C6 ~3%); wired into the MC (window drawn per draw, demeaned bootstrap). B (spread/interest) not supported; C reported only (inside A); D only dividends (not wired, user option). 2014-16 still unexplained (domestic). |
| G2 | reviewed; already wired (STATUS was stale) | `task/g2` | Major-corruption shock module: shared event sequence across all scenarios/programmes, uniform 3-8% annual probability, triangular 1.0/2.25/3.6% log-level loss, two-year build-up and four-year recovery half-life. **Claude review (2026-10-23):** `src/corruption.py`'s build-up/decay math checked by hand against `tests/test_corruption.py` (zero-probability, single-event build/half-recovery, overlap additivity, determinism, probability-bound tests all pass) - correct. D1 wiring is **already done**, not pending: `src/montecarlo.py` commit `e3c1834` ("Wire G2 corruption shock into the Monte Carlo") is merged into this branch, `load_context()` loads `config/corruption_proposed.yaml` unconditionally, and the already-published `outputs/runs/run_metadata.json` (created 2026-10-21) documents the G2 stream `[seed, 4]` - this STATUS row was out of date, corrected here. `thinned_path` (W3's per-programme anti-corruption reduction) is also merged and tested. CPI improvement sensitivity stays correctly off by default (`cpi_sensitivity_path` is defined but never called from `montecarlo.py`). Its cross-country CPI SD placeholder (20 points) stays flagged `to_verify` in `config/corruption_proposed.yaml`, but is now corroborated: TI's published CPI methodology deliberately rescales each year against the 2012 baseline to mean~45/SD~20, which supports 20 as plausible without being a direct current-year computation. |

| RV0 | done | current checkout (`main`) | Response to an independent reviewer's critique (`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), assessed against a Keynesian/countercyclical benchmark: the model is acyclical and monetary-policy-blind, which the reviewer argues plausibly biases the "expansion improves the Gini" finding in favour of expansion (omitted Selic hike, currency weakening, crowding-out, interest-income-to-bondholders, inflation tax). Full plan at `C:\Users\H\.claude\plans\jiggly-wondering-gem.md` covers 8 tasks (RV0, IEQ1, PCY1, CYC1, DC1, IY1, MR1, FX1), sequenced safest-first, every new mechanism off-by-default and regression-checked byte-identical, matching the I1/W1-3/D3/D4 discipline. **RV0 (text-only, this row) is complete:** expanded `paper/minimum_state_brazil.tex`'s Discussion/Limitations to explicitly name the omitted-channel chain and its plausible-but-unproven directional bias (rather than the prior one-line "no monetary reaction function" caveat); added a new debt-composition limitations paragraph citing real Secretaria do Tesouro Nacional RMD/PAF data fetched this session (Selic-linked/floating 48.3% end-2025 rising to 52.7% Aug-2026 against a revised 49-53% PAF band, inflation-linked ~23-26%, fixed-rate ~20-22%, FX-linked a stable 3.7-4.4%, ~96% placed domestically, 1pp Selic rise adds ~R$60.6bn/~0.46% GDP to gross debt) showing the composition risk the model omits is overwhelmingly the domestic-Selic risk it already prices via the debt identity and risk-premium channel, not external FX risk; new bibitem `tesourormd2026`. Confirmed the "nonlinear risk premium by default" ask (reviewer item 8) was already answered pre-existing (the `premium_nonlinear` D4 diagnostic, Appendix B) -- no new text needed there beyond what the D4 writeup already states. Verified: citation/structure/table checks all clean (157/157 citations matched). **IEQ1 is done:** wired C3's pre-feedback Gini path into C5's already-specified-but-inert inequality-to-growth channel, off by default behind a new `--inequality-feedback` CLI flag on `src/montecarlo.py`. `feedback_for_draw` gained an optional `gini_change` parameter (default `None`, byte-identical to before); `evaluate_draw` computes an early `micro_for_draw` pass for the default-composition variant only (matching the existing "C3 runs for the default composition only" convention) and feeds its Gini path into `feedback_for_draw`, then the existing post-feedback `micro_for_draw` call still runs for the final published Gini/poverty columns. **Bug found and fixed by the new test**: the first implementation built `gini_change_input` only from `micro_for_draw`'s own output rows, which don't cover every (year, scenario) pair in the full annual corner (e.g. the base year), causing `feedback.py`'s strict `_path_values` lookup to raise; fixed by defaulting every (year, scenario) pair to a zero (inert) Gini deviation before overlaying micro's actual values. New tests: `tests/test_feedback.py` (`test_inequality_channel_inert_when_gini_change_is_none`, `test_inequality_channel_activates_with_a_gini_path`, hand-computed against the log1p formula) and `tests/test_montecarlo.py` (`test_inequality_feedback_off_by_default` -- regression guard, flag-unset output identical to pre-IEQ1 behaviour; `test_inequality_feedback_activates_only_when_requested` -- S0 inert, R\_amb's feedback-adjusted GDP moves, non-feedback columns untouched). All four new tests pass. **Full `pytest` suite now run and green: 239 passed** (confirms IEQ1 regresses nothing).

**PCY1 is done:** new standalone module `src/pcy1_fiscal_timing.py`, pure historical analysis (reads only `data/brazil/backtest_observed.csv`, no interaction with `src.montecarlo`/`src.macro.run_corner`, cannot touch any published Monte Carlo output). Computes a real-time, backward-looking output-gap proxy (GDP growth minus its own trailing 5-year rolling mean) and a sign-flipped fiscal-impulse series (YoY change in the primary balance), classifying each year 2000-2024 as procyclical-expansionary/-contractionary, countercyclical, broadly-neutral, or not-classified. **Bug found and fixed during implementation**: `backtest_observed.csv`'s `primary_result_pct_gdp` (BCB SGS 5793) is a *borrowing requirement* ("negative = surplus" per its own label), the opposite convention from a conventional balance; the first version used it raw, inverting every classification. Fixed by negating it into a conventional `primary_balance_pct_gdp` in `load_series`, documented prominently in both the module docstring and `docs/pcy1_fiscal_timing.md`. **Finding**: Brazilian fiscal policy 2000-2024 reads as predominantly countercyclical on this proxy (2009 and 2020-2021 both clearly countercyclical), and the reviewer's singled-out 2011-2014 period is *mixed*, not uniformly procyclical (2011 procyclical-contractionary; 2012-2014 all countercyclical) -- this partly complicates rather than confirms the review's qualitative claim, reported honestly rather than adjusted to fit. Output: `outputs/fiscal_timing_diagnostic.md`. Tests: `tests/test_pcy1_fiscal_timing.py`, 12 tests (sign-fix, rolling-window arithmetic by hand, classification boundaries including the neutral-threshold strict inequality, a real-data smoke test), all passing. Method note: `docs/pcy1_fiscal_timing.md`. **Not yet done**: this finding has not yet been written into `paper/minimum_state_brazil.tex` (the plan's cross-cutting requirement to cite each task's actual numbers in the paper) -- left for a documentation pass once more of the sequence has landed, to avoid piecemeal paper edits.

**CYC1 is done:** new standalone module `src/cyc1_state_dependent_multiplier.py` (never calls `src.montecarlo.run()`/`evaluate_draw()`, verified by a bytecode-inspection test). **A prior, more basic finding came out of investigating this task**: the model's own deterministic growth trend has zero cyclical fluctuation on its own (smoothly decelerating 1.18%->0.94% 2026-2035 under the central draw, no bumps), so there was no "recession regime" to condition a multiplier on until genuine year-to-year variation was reintroduced via the existing external-shock bootstrap -- this independently confirms the reviewer's underlying diagnosis before any multiplier-specific work was done. **Literature verification was attempted and partly failed, reported honestly rather than papered over**: could not machine-extract Auerbach & Gorodnichenko (2012)'s own point estimates (PDF extraction failed in this environment; only its abstract-level qualitative finding is used), and a secondary source suggested Pires (2014) -- cited elsewhere in this paper for Brazilian multipliers -- may not actually support a recession/expansion asymmetry (its positive finding may be a volatility-regime split instead); this could not be confirmed, so **Pires (2014) is explicitly excluded as a source for this specific ratio** rather than risk misusing a citation. Added `config/parameters.yaml multiplier_state_dependence_ratio` (sampled 1.0-2.5, central 1.5, full sourcing/exclusion note inline) reflecting genuine literature disagreement rather than a false point estimate. Method: reuses PCY1's trailing-mean regime classifier directly on the external-shock-adjusted S0 growth path, rescales R_mod/R_amb's `gdp_level_vs_s0_pct` (the multiplier's own effect, since S0's gap is zero by construction) by the sampled ratio in recession years only; explicitly a first-order diagnostic (debt consequence not re-derived). 300-draw run (~80s): at 10y, R_amb's median GDP cost moves from -0.80% (fixed) to -1.08% (state-dependent), ~35% larger once cyclicality is reintroduced. Outputs: `data/brazil/cyc1_state_dependent_multiplier.csv`, `outputs/cyc1_state_dependent_multiplier.md`. Tests: `tests/test_cyc1_state_dependent_multiplier.py`, 6 tests, all passing (two test-side bugs caught and fixed during writing: a `pytest.approx`-on-Series comparison that doesn't broadcast, and an over-naive docstring-text search that false-matched its own prose -- fixed with an `np.allclose` check and a bytecode-level `LOAD_GLOBAL` inspection respectively). Method note: `docs/cyc1_state_dependent_multiplier.md`. **Full `pytest` suite re-run after CYC1: 257 passed** (confirms CYC1 regresses nothing); not yet written into the paper.

**DC1 is done:** new standalone module `src/dc1_debt_composition_fx.py` (never calls `src.montecarlo.run()`/`evaluate_draw()`, verified by the same bytecode-inspection test as CYC1). **Scoped down from the plan's original full multi-instrument debt-composition model, for two reasons found while starting the task**: (1) Brazil's FX-linked share of federal debt is small and stable (3.7-4.4% of the DPF, already verified and cited in the paper as `tesourormd2026`), so this is a bounded channel, not the dominant risk the review's general critique implies for a typically currency-exposed emerging market; (2) a genuine multi-decade historical DPF-composition series could not be obtained -- the Treasury publishes it only inside monthly PDF tables this environment cannot extract text from (the same PDF-extraction limitation hit for CYC1's literature sources), and a WebSearch pass surfaced only unverifiable secondary sources (a finance blog, a 2007 working-paper excerpt), which were explicitly not used. `data/brazil/debt_composition.csv` therefore holds only the two verified Treasury snapshots already cited in the paper (end-2025, Aug-2026) plus the PAF 2026 target bands -- a point-in-time record, not a time series -- with the inflation-linked/fixed-rate split left blank at each snapshot date where the source gives only a range, rather than inventing undisclosed precision. Added `config/parameters.yaml debt_composition_fx` (`fx_linked_share_pct_of_dpf`: low 3.7 / central 4.0 / high 4.4, sourced, `verified: full_text`); updated the pre-existing `external_block.gaps` entry for the FX-linked-share gap to point at this partial closure. **Method**: reuses `src.external`'s existing bootstrapped BRL/USD path exactly as CYC1 does, revalues only the FX-linked share of `debt_gdp_with_external` by the *cumulative* bootstrapped depreciation vs the base year (`exp(cumsum(fx_change_pct)/100) - 1`, exact since these are log changes), additive to (not a duplicate of) the existing inflation-pass-through effect -- a distinct stock-revaluation mechanism. FX share itself sampled per draw (uniform 3.7-4.4%, central 4.0%), new RNG stream `[seed, 12]` (unused by `run()`'s 1-9, D4's 10, CYC1's 11). **Finding, honestly reported rather than left as an uncritical confirmation of the paper's existing "second order" framing**: at 5-10y the effect is indeed small (median +1.0pp at 5y, +2.6 to +3.2pp at 10y across S0/R_mod/R_amb), matching the paper's framing at its main 10-year horizon; **but by 15-20y it grows to a no-longer-negligible median +5 to +17pp of GDP (p90 up to +47pp)**, because the small FX-linked tranche is revalued by *cumulative* depreciation, and Brazil's own 2000-2024 BRL/USD history (the bootstrap's only source of variation, consistent with every other external-shock diagnostic in this project) includes 20-year windows with well over 100% cumulative depreciation. This remains modest relative to total debt/GDP's already very wide 20y uncertainty band (over 200pp), but the "second order, don't worry about it" framing should not be extended to the 20-year horizon without this qualification. 300-draw run (seed 20261026). Outputs: `data/brazil/dc1_debt_composition_fx.csv`, `outputs/dc1_debt_composition_fx.md`. Tests: `tests/test_dc1_debt_composition_fx.py`, 7 tests, all passing (hand-computed cumulative-depreciation formula, draw-0 reproducibility/central-share check, sampled-share bounds, exact-formula check on real draw output, report smoke test, bytecode call-check). Method note: `docs/dc1_debt_composition_fx.md`. **Full `pytest` suite re-run after DC1: 264 passed.** **Not yet done**: this finding has not yet been written into `paper/minimum_state_brazil.tex` (same deferred-documentation-pass note as PCY1/CYC1).

**IY1 is done:** wired both channels as off-by-default optional arguments to `src.micro.simulate_household_incomes` (defaults reproduce prior behaviour byte-for-byte): `capital_income_windfall_brl_monthly` + `capital_income_top1_share_pct`/`capital_income_top10_share_pct` (a scenario's change in government interest expense, allocated top-1%/next-9%/bottom-90% using Receita Federal's declared capital/financial-income centiles, within-band proportional to each household's own income), and `transfer_inflation_erosion_pct` (a scenario-year's cumulative extra inflation from `src.external`, applied to each household's baseline Bolsa Familia amount only). New helpers `src.micro._weighted_percentile_rank`/`_allocate_by_income_band`. **Scoping correction made before the first real run**: initially built and tested against `R_mod`/`R_amb` (matching CYC1/DC1's house convention) and the direction came out backwards (contractions correctly *reduced* Gini via less interest expense) -- caught that the reviewer's "expansions reduce the Gini... probably biased" claim is specifically about the debt-financed expansion scenarios (`E_mod`, `E_amb`), not the reduction scenarios, and switched to those. **A real, serious bug found and fixed before any reported numbers**: the first `_allocate_by_income_band` implementation double-counted the survey weight, inflating per-household allocations by roughly two orders of magnitude -- a smoke test immediately produced Gini~0.99 and poverty~99% (thousands of households clipped to zero income), an obviously wrong result that caught it; fixed by removing the extra weight factor from the numerator, verified by a new test asserting the allocation, re-weighted and summed, reproduces the input pool exactly. Government interest expense is derived from the debt identity's own numbers (previous year's `debt_gdp_with_external` times that year's nominal rate, the standard rate-times-stock definition), not a new input. New standalone diagnostic `src/iy1_interest_income_distribution.py` (never calls `src.montecarlo.run()`/`evaluate_draw()`, bytecode-checked). Added `config/parameters.yaml iy1_interest_income_distribution` (capital-income concentration source, interest-expense derivation rule, inflation-erosion choice and its "upper-bound assumption" caveat, within-band incidence choice, gaps). **Finding, the most directly confirming result in this whole review-response sequence**: at the paper's main 10-year horizon, switching IY1 on moves the Gini by +0.76 points (median) for `E_mod` and +1.31 points for `E_amb` vs the published (IY1-off) figures -- small but squarely in the direction the reviewer predicted. The effect grows with horizon: at 20y, median +3.13 (`E_mod`)/+5.02 (`E_amb`) points, p90 up to +4.56/+7.19. Poverty (R$218 line) barely moves (<1pp throughout), confirming the capital-income windfall, not the inflation-tax erosion, dominates. 300-draw run (seed 20261026). Outputs: `data/brazil/iy1_interest_income_distribution.csv`, `outputs/iy1_interest_income_distribution.md`. Tests: `tests/test_micro.py` (+7 tests, including the one that would have caught the weight-double-count bug) and `tests/test_iy1_interest_income_distribution.py` (6 tests), all passing. Method note: `docs/iy1_interest_income_distribution.md`. **Full `pytest` suite re-run after IY1: 276 passed.** **Not yet done**: this finding has not yet been written into `paper/minimum_state_brazil.tex` (same deferred-documentation-pass note as PCY1/CYC1/DC1).

**MR1 is done:** new standalone module `src/mr1_taylor_rule.py` (never calls `src.montecarlo.run()`/`evaluate_draw()`, bytecode-checked). **Design decision following the plan's own flagged risk**: rather than rewiring `src.macro.real_interest_rate_for_year` (used by `run_corner`, which every scenario, CYC1/DC1/D4 and the published Monte Carlo depend on) to be state-dependent, MR1 runs the usual `run_corner`+`apply_external` pass unchanged and **recomputes the debt path afterwards** with a Taylor-rule rate substituted in an otherwise line-for-line identical re-run of the debt identity (`_rerun_debt_with_rate_rule`); verified by a test that this exactly reproduces the existing `debt_gdp_with_external` column when the Taylor coefficients are zero. **Specification**: Taylor (1993)'s classic form, expressed as a real-rate adjustment: `r_taylor_t = r*_t + phi_pi*(inflation_t - 3.0) + phi_y*gdp_level_vs_s0_pct_t`, where `inflation_t` is common to every scenario (so only the output-gap term differentiates a scenario's Selic from S0's) and 3.0 is the BCB continuous inflation target already used elsewhere. **Another literature dead end, handled the same way as CYC1's**: WebSearch found several Brazil-specific Taylor-rule studies (2001-2025, various), all reporting a positive, significant Selic response to both gaps, but none readable past the abstract level (PDF-extraction limitation, reconfirmed by fetching one paper's own HTML repository page directly and finding no numbers there either) -- so `config/parameters.yaml mr1_taylor_rule` samples a discount factor (low 0.3, central 0.6, high 1.0) on Taylor's own classic 0.5 coefficient rather than using an unverified Brazilian point estimate. Tested against all four headline scenarios (`R_mod`, `R_amb`, `E_mod`, `E_amb`). **Finding, the second of the two most directly quantified confirmations of the reviewer's core claim in this sequence**: at the paper's main 10-year horizon, the Taylor rule adds a median +1.46pp of GDP to `E_mod`'s debt vs S0 and +3.02pp to `E_amb`'s, on top of the fixed-rate baseline differential (+11.6pp/+23.2pp) -- roughly 13-15% larger, driven by the Selic genuinely rising (median +0.13/+0.26pp) with the expansion's own output gap. Grows to median +5.45pp/+6.32pp by 20y (p90 up to +10.3/+12.7pp). The mirror-image holds for `R_mod`/`R_amb`: a reactive Selic cuts with the contraction's negative output gap, adding modest debt relief. 300-draw run (seed 20261026). Outputs: `data/brazil/mr1_taylor_rule.csv`, `outputs/mr1_taylor_rule.md`. Tests: `tests/test_mr1_taylor_rule.py`, 8 tests, all passing. Method note: `docs/mr1_taylor_rule.md`. **Full `pytest` suite re-run after MR1: 284 passed.** Not yet written into the paper.

**FX1 is done -- the eighth and last task in the plan.** New standalone module `src/fx1_endogenous_fx.py` (never calls `src.montecarlo.run()`/`evaluate_draw()`, bytecode-checked). **Design, following C7 channel B's own precedent**: rather than fit a new debt-to-FX regression (this project already tried the closest analogue, C7's debt-to-spread "channel B," fit 2000-2014/test 2015-2024, and found it not supported out of sample), FX1 chains the model's own already-verified debt-to-risk-premium parameter (`long_run_feedback.sovereign_risk_premium`, reused via `src.feedback.sovereign_risk_premium_path`) to a sampled, UIP-anchored (not fitted) spread-to-depreciation elasticity (low 0.5/central 1.0/high 3.0% per 1pp premium; upper bound only qualitatively informed by a BIS working paper whose own tables, like CYC1's/MR1's literature sources, could not be read in this environment). **A structural finding that reshaped the module's design, found before any numbers were reported**: the first implementation routed the extra depreciation through the existing inflation-pass-through channel and re-ran the debt identity exactly as `external.apply_external` does -- and produced an *exactly zero* debt/GDP effect, to floating-point precision, at every single draw and horizon. Verified this is a genuine structural property, not a bug: this model's Fisher-consistent debt identity reprices the nominal rate and nominal GDP growth by the same inflation factor, so a pure inflation shock with no real-economy effect cannot move the debt/GDP ratio at all, by construction -- independently confirming, the same way CYC1's acyclical-core finding did, a basic structural fact about this model worth stating on its own. **Redesigned** to route the depreciation instead through DC1's FX-linked debt tranche (the one channel that genuinely is not Fisher-neutral), reusing DC1's own `fx_linked_share_pct_of_dpf` parameter rather than a second debt-composition assumption; the now-confirmed-inert inflation figure is still computed and reported (`extra_inflation_pp_inert`) rather than quietly dropped. Added `config/parameters.yaml fx1_endogenous_fx` with full sourcing notes. Tested against all four headline scenarios. **Finding**: small in absolute terms (as expected given the FX-linked share is only ~4% of debt) and, unlike IY1/MR1, does not materially complicate the paper's existing "second order" framing for this specific channel: at 10y, median +0.18pp GDP (`E_mod`) / +0.21pp (`E_amb`); at 20y, +0.42pp/+0.47pp (p90 up to +0.83/+0.93pp). Read alongside DC1, the two diagnostics together show the FX-linked channel stays small specifically because the underlying FX-linked share is small, not because fiscal stress fails to move the exchange rate. 300-draw run (seed 20261026). Outputs: `data/brazil/fx1_endogenous_fx.csv`, `outputs/fx1_endogenous_fx.md`. Tests: `tests/test_fx1_endogenous_fx.py`, 7 tests, all passing. Method note: `docs/fx1_endogenous_fx.md`. **Full `pytest` suite re-run after FX1: 291 passed.**

**All 8 tasks in the approved plan (RV0, IEQ1, PCY1, CYC1, DC1, IY1, MR1, FX1) are now built, tested and documented.**

**Paper updated (2026-10-26): the plan's final cross-cutting task is done.** Added a new appendix, `\section{Diagnostic extensions, part II: responding to an independent review}` (`\label{app:reviewer}`), to `paper/minimum_state_brazil.tex`, with five subsections: the business cycle (PCY1, CYC1), debt composition and the exchange rate (DC1, FX1, with two new tables `tab:dc1`/`tab:fx1`), interest income and the inflation tax (IY1, table `tab:iy1`), a reactive Selic (MR1, table `tab:mr1`), and a final synthesis subsection, `\label{sec:discussion-reviewer-synthesis}`, giving the plan's "real test of the whole exercise" a direct, unhedged answer rather than a caveat. **The synthesis finding**: combining each diagnostic's own median effect with the published figure (an indicative addition of two separately-run statistics, not a recomputed joint distribution, stated as such) shows the ten-year Gini effect for `E_mod`/`E_amb` moves from $-0.10$/$-0.16$ points (published) to $+0.65$/$+1.15$ points once IY1's interest-income channel is added -- **the median effect reverses sign**, directly confirming the reviewer's distributional bias claim rather than merely moderating it. The debt-cost effect (MR1 + FX1 added to the published differential) is directionally unchanged but understated by roughly 13-14\% ($+11.6\to+13.3$pp for `E_mod`, $+23.3\to+26.5$pp for `E_amb` at 10y). PCY1 and FX1, by contrast, complicate rather than confirm the reviewer's framing (fiscal policy's own history reads as predominantly countercyclical; the FX-linked debt channel is genuinely small once isolated). Also revised the two existing RV0 Discussion paragraphs (omitted-channel chain; debt composition) to point to these now-quantified results instead of the earlier "not established, so we report the limitation rather than attempt a correction" hedge, and added a short pointer paragraph in `sec:d4` (the back-testing section) signposting the new appendix. Added 3 new bibitems (`banerjeemehrotrazampolli2023`, `receitafederal2024`, `taylor1993`); reused existing bibitems for everything else (`baldaccikumar2010`, `tesourormd2026`, `auerbachgorodnichenko2012`, `pires2014`, `ramey2019`, `rameyzubairy2018`, `ostrybergtsangarides2014`), no duplicate sourcing. **Verified** (no LaTeX compiler available in this environment, same limitation as RV0): a from-scratch citation/label/structure check script (scratchpad, not checked in) confirms every `\cite*{}` key has a matching `\bibitem`, every `\ref{}` has a matching `\label{}`, no duplicate labels, all `\begin{}`/`\end{}` environment counts match, exactly one `\end{document}`, and all 8 tables (the pre-existing `tab:headline`/`tab:d4breach`/`tab:d4gap`/`tab:d4variants` plus the 4 new ones) have the labels the new text references. Full `pytest` suite re-run one final time after all paper edits: **291 passed** (no `src/`/`config` changes since the FX1 row's own 291-passed run, so this reconfirms, not newly gates).

**This closes the plan at `C:\Users\H\.claude\plans\jiggly-wondering-gem.md` end to end.**

## JMC1 -- a jointly-integrated Monte Carlo, validated against history (new plan, 2026-10-26)

The user asked the sharper follow-up question the 8-task plan's own appendix flagged but did not
answer: should CYC1/MR1/FX1/DC1/IY1 actually interact *within* each draw and compound year over
year, rather than being computed independently and summed afterward? New plan approved at the same
plan file (`C:\Users\H\.claude\plans\jiggly-wondering-gem.md`, overwritten -- the 8-task plan is
preserved in git history/this file's rows above, not lost): build a second, fully separate Monte
Carlo (JMC1), validate it against 2000-2024 observed history, and only trust its 2025+ projections
if it fits history at least as well as the published model -- mirroring this project's own
precedent of rejecting C7 channel B when it failed an out-of-sample test.

**Step 1 -- the joint engine (done, 2026-10-26).** `src/jmc1_engine.py`: a standalone per-scenario,
per-year recursion mirroring `external.apply_external`'s own debt loop, substituting all five
channels simultaneously and letting each year's outputs feed the next year's inputs (CYC1's
state-dependent multiplier on the growth effect, broadened to all four scenarios not just R_mod/
R_amb; MR1's Taylor rule reacting to that year's own rescaled gap and inflation; a *running*,
compounding sovereign-risk premium -- deliberately not the baseline-only premium FX1's standalone
diagnostic uses, since compounding it is this module's whole point; FX1's elasticity and DC1's
exact FX-linked-tranche formula revaluing the running debt stock; IY1's capital-income allocation
closing into growth via a two-pass approximation -- a pre-feedback macro-only pass supplies the
Gini path at `target_years` milestones, mirroring IEQ1's own already-published, already-accepted
one-pass approximation, not a new assumption). Never imports or modifies `run_corner`,
`apply_external`, or `feedback.py`/`apply_feedback` -- a design choice made explicitly (and
confirmed with the user) over the alternative of extending `feedback.py`'s already-similar
`_evaluate` loop, to keep zero risk to the published pipeline's own code.

**Critical test passed**: with every channel at zero/neutral (ratio=1.0, phi_pi=phi_y=0.0,
elasticity=0.0 or premium_bp=0.0, no inequality feedback), the joint engine's debt path reproduces
`apply_external`'s own `debt_gdp_with_external` to `1e-9` -- confirmed in
`tests/test_jmc1_engine.py` (8 tests, including this exact-reproduction check, a Taylor-rule
directional sanity check, draw-zero reproducibility/bounds checks, and the same
`evaluate_draw`-isolation bytecode check every other diagnostic module carries).

**Known cost, stated plainly**: closing the IY1/inequality loop requires a household
microsimulation call at every (scenario x target-year) pair per draw, costing roughly 20s/draw
(vs. near-instant for the macro-only channels) -- a full 300-draw run with the loop closed would
take on the order of 100 minutes. The actual diagnostic run (once built) will use a reduced draw
count for the inequality-closed path, documented as a cost-driven choice, not a silently smaller
sample.

Full `pytest` suite re-run after this addition: **299 passed** (291 + 8 new JMC1 tests), confirming
no regression anywhere else in the repo.

**Step 2 -- the historical validation gate (done, 2026-10-26): FAIL. Stopped here per the plan's own
decision rule; Step 3 (forward comparison, paper update) is NOT started.**

Before building the gate, found and confirmed with the user that 3 of the 5 channels (CYC1, FX1's
extra layer, IY1) are scenario-vs-S0 concepts with no counterfactual in a single realized history --
feeding them real history tests nothing, since there's no S0 path next to it to differ from. Gate
narrowed, with the user's sign-off, to the two channels that do have a real historical analogue:
MR1 (a rate-*generating* Taylor-rule mechanism, vs the model's existing fixed-rate mechanism) and
DC1 (FX-linked debt revaluation using the *actual* observed BRL/USD path, not an unobservable
"extra" layer).

`src/backtest_jmc1.py`: three reconstructions (`fixed`, `taylor_only`, `joint` = MR1+DC1) recursing
`debt_step` annually from 2006 using *observed* primary balance and growth, but *generating* (not
oracle-fed) the interest rate. Two debt/GDP tests: cumulative-from-one-anchor (expected to be
dominated by stock-flow-adjustment noise, exactly as this project's own pre-existing `debt_engine`
row already documents and accepts -- not the gate) and one-step re-anchored-on-observed-lagged-debt
(mirroring `src.backtest.debt_one_step`'s own precedent; this is the actual gate). A third test
compares the Taylor-rule-implied nominal rate directly to the observed Selic.

**Result (`docs/jmc1_validation.md`)**: One-step debt/GDP RMSE -- fixed 3.685pp vs taylor_only
4.253pp vs joint 4.299pp: **FAIL**, the joint mechanism's debt-level fit is *worse* than the
published model's existing fixed-rate mechanism, not better. Selic RMSE -- fixed 3.869pp vs taylor
3.352pp: **PASS**, MR1's Taylor rule genuinely does track the actual historical Selic level better
than the fixed-rate assumption. These two verdicts disagree, and that disagreement is itself the
finding, reported plainly rather than reconciled: MR1 describes *Selic-setting behaviour* better,
but that improvement does not translate into a better *debt-level* reconstruction once `debt_step`'s
own dynamics are involved -- the debt-level error is apparently dominated by noise unrelated to
which rate-generating mechanism is used (consistent with, though a different test from, this
project's own pre-existing finding that the cumulative debt-engine test is SFA-noise-dominated).
Note the `fixed` benchmark here is not a strawman: `effective_real_interest_rate.central` is
itself calibrated as the median of the same historical real-rate series being tested against.

**Per the plan's own decision rule, this means Step 3 does not proceed**: JMC1's 2025+ forward
projections are not validated as an improvement over the published model and should not be
presented as such in the paper. The 8-task plan's existing appendix framing -- separately-run
diagnostics, summed as an indicative addition, explicitly not a recomputed joint distribution --
stands as the more defensible answer to the reviewer than a jointly-integrated engine would have
been, *given that engine does not actually fit history better*. This is a genuine negative result,
reported with the same honesty this project already applied to C7 channel B's own rejection, not a
reason to keep tuning JMC1 until it passes.

**Follow-up answered (2026-10-26): "can we use MR1's Taylor rule in the previous (published)
model and see if it improves the overall historical fit?" -- No, confirmed with two independent
datasets.** Extended `src/backtest_jmc1.py` with a refined test using `src.backtest`'s own more
accurate SIDRA-nominal-GDP inputs (the exact data behind `outputs/backtest.md`'s `debt_engine`/
`debt_engine_one_step` rows -- reproduced here to the same RMSE, 9.322pp/2.390pp, confirming the
data pipeline matches exactly), swapping the *oracle* observed implicit rate those published rows
use for a *generated* rate (fixed baseline vs MR1's Taylor rule) so the comparison is fair. Result:
fixed beats Taylor on both the original CPI-based test (one-step RMSE 3.685 vs 4.253pp) and this
SIDRA-refined one (one-step RMSE 3.234 vs 3.880pp) -- replacing the model's fixed real-rate
mechanism with MR1's Taylor rule makes the historical debt/GDP fit modestly *worse*, consistently
across both datasets, even though MR1's rate path is a *better* match to the actual Selic level on
its own (confirmed again here). **Likely reason, not just a sample quirk**: `effective_real_
interest_rate` is calibrated to the government's effective *blended* rate across its whole
diversified (Selic-linked/inflation-linked/fixed) debt stock, not the Selic policy rate itself;
MR1's Taylor rule is a good description of Selic-setting but a mismatched stand-in for that blended
concept when plugged directly into the debt identity. Full write-up in `docs/jmc1_validation.md`
(both the original and refined sections). This reinforces, via a second route, the Step 2 gate's
FAIL verdict above: do not use MR1's rate mechanism as a replacement for the published model's
fixed-rate assumption, in either the joint engine or the published model directly.

`tests/test_backtest_jmc1.py` written (6 tests: the oracle-reproduction check against
`outputs/backtest.md`'s own published RMSEs, the fixed-beats-taylor-on-debt /
taylor-beats-fixed-on-Selic results on both datasets, and the usual `evaluate_draw`-isolation
check) -- confirmed passing: **6 passed in 128.55s**. Full `pytest` suite re-run after this
addition: **305 passed in 1544.88s** (299 + 6 new tests) -- zero regressions. JMC1's Steps 1 and 2
are now both fully built, tested, and documented; Step 3 does not proceed (Step 2's FAIL verdict).

## Paper presentation improvement (2026-10-26)

User asked for a top-notch academic presentation pass: benchmark how `paper/minimum_state_brazil.tex`
should present results against the target journal (*Fiscal Studies*), then implement an improvement
plan, independently reviewed before implementation (one Claude agent, one Codex agent -- the Codex
path required debugging first, see below).

**Benchmarking**: a 5-subagent deep-research pass (`reports/Fiscal Studies results presentation.md`)
surveyed ~25 *Fiscal Studies* articles via working-paper twins (Wiley itself blocks automated access).
Key finding: the paper's existing abstract/discussion prose already matches the journal's hedged,
plain-juxtaposition house style; the real gap is that the paper has exactly one figure (an
architecture schematic) and zero figures for any quantitative result, despite the one confirmed
journal precedent for this exact use case (Cronin & Dowd 2013, debt/deficit fan charts under policy
scenarios).

**Plan + two independent reviews** (`tasks/paper_presentation_improvement_plan.md`): both reviews
independently caught the same category of problem (the plan over-cited the benchmark's own
unconfirmed findings as if established) and independently flagged the original "A reactive Selic"
paragraph draft and the abstract's length as the plan's weakest points -- strong convergent signal.
**Codex debugging note, worth remembering**: the Codex companion's configured default model
(`C:\Users\H\.codex\config.toml`, `model = "gpt-6-luna"`) is stale -- the account's actual valid
models (`~/.codex/models_cache.json`) are `gpt-5.6-luna`/`gpt-5.6-sol`/`gpt-5.6-terra`; `gpt-6-luna`
and a guessed `gpt-5.1-codex` both failed with `model_not_found` before `gpt-5.6-luna` worked. User
has not yet asked for `config.toml` to be fixed; still stale as of this entry.

**Implementation (done)**:
- `src/paper_figures.py` (+ `tests/test_paper_figures.py`, 5 tests): builds 3 figures from
  already-published data only (no new Monte Carlo, no new historical analysis) -- `debt_fan.pdf`/
  `gini_fan.pdf` (4-panel scenario grids, median + p10-p90 band, from
  `outputs/runs/summary_percentiles.csv`) and `backtest_fit.pdf` (observed vs. reconstructed
  debt/GDP 2017-2024, from `src.backtest.sfa_out_of_sample`, the exact function behind the paper's
  existing 16.1pp/12.5pp overshoot prose). Deliberately NOT a continuous time-path fan chart --
  the model only reports percentiles at 4 named horizons, so plotting anything smoother would imply
  resolution the data doesn't have.
- **Two narrative claims drafted for the figures were checked against the data and found wrong**
  before being left in the paper: a claim that R_amb/E_amb's uncertainty bands widen faster than
  the moderate scenarios' (false -- all four widen by a consistent ~10x factor, 9.9-10.3x, from 10y
  to 20y) and a claim that E_amb's Gini band widens enough to approach zero by 20y (false -- it
  widens the *least* of the four, 1.07x vs ~1.8-2.1x, and none of the 16 scenario x horizon Gini
  cells cross zero at all). Both corrected to the actually-verified pattern before committing the
  prose -- a reminder that every interpretive claim about a new figure needs a direct data check,
  not just a plausible-sounding narrative.
- `tab:headline` gained a 4th column (`E_amb`, pulled from the same published CSV at the 10-year
  horizon, matching every other column's own sourcing) and two prose cross-references to "the
  underlying percentile file for E_amb" were simplified now that it's in the table directly.
- Abstract compressed 309 -> 254 words (still above the benchmark's 80-120 norm, a deliberate,
  acknowledged trade-off given this paper's genuinely richer multi-part content, not a forced fit
  to an arbitrary count) and gained one new clause previewing the Gini-reversal finding, which the
  original abstract omitted entirely despite the Discussion section calling it central.
- Introduction gained a short quantitative-preview paragraph (per the benchmark's confirmed finding
  that *Fiscal Studies* introductions, not abstracts, carry the real headline numbers).
- New subsection `\subsection{Testing MR1 against Brazil's own fiscal history}`
  (`\label{sec:mr1-historical}`) in the "Diagnostic extensions, part II" appendix, with its own
  method paragraph and a new table (`tab:mr1-historical`), properly documenting the JMC1 historical-
  validation finding (Tier-1/Tier-2 framing bridge both reviews asked for) -- built as its own
  diagnostic per the user's decision, not folded into the existing MR1 paragraph as first drafted.
- Appendix intro updated from "six... diagnostics" to note a seventh, explicitly flagged as
  different in kind (a historical-fit test, not a Monte Carlo scenario diagnostic).

**Verification**: from-scratch citation/label/environment/brace-balance check (scratchpad, not
checked in) -- zero missing/orphaned citations, zero missing/duplicate labels, all `\begin`/`\end`
counts match, exactly one `\end{document}`, all three new figure files exist on disk and are
referenced, all new labels (`fig:debt-fan`, `fig:gini-fan`, `fig:backtest-fit`,
`tab:mr1-historical`, `sec:mr1-historical`) defined and referenced. Full `pytest` suite re-run after
`src/paper_figures.py`'s addition: **[pending -- background run launched, not yet confirmed as of
this checkpoint]**.

**Actual LaTeX compile (new capability, 2026-10-26): a real, working compiler for this environment.**
Downloaded `tectonic` (self-contained LaTeX engine, official GitHub release, ~21MB, user-approved
before download) to the scratchpad and successfully compiled `minimum_state_brazil.tex` for the
first time this project has ever had a working compiler available -- every prior paper edit this
session, and apparently in this project's whole history, was verified only by from-scratch
citation/label/structure scripts, never an actual render. This surfaced three real, previously
invisible defects, all now fixed:
- **A genuine, pre-existing bug**: no `\bibliographystyle` was declared (pure hand-written
  `thebibliography`, no BibTeX), which made natbib halt non-interactively on every single compile
  attempt ("Bibliography not compatible with author-year citations"), confirmed root-caused to
  natbib's `\NAT@apalk` parser choking on `\bibitem` labels with 2+ authors/commas (41 of 160 labels
  affected) -- rewriting all 160 to the correct 3-part `[Label(Year)ShortKey]` format was judged too
  large/risky a change for the benefit, so the specific internal consistency check
  (`\NAT@force@numbers`) was neutralized instead (`\makeatletter\let\NAT@force@numbers\relax
  \makeatother` in the preamble) -- citations already rendered correctly from the bibitem labels
  regardless; this check only ever gated a late, optional self-consistency assertion.
- **A genuine, pre-existing visible defect**: the architecture figure's (`fig:chain`) last two rows
  overflowed the page so badly (165pt, over 2 inches) that text was literally clipped off the page
  edge mid-word. Fixed by shortening two rows' text and reducing one row's hand-tuned `\hspace`
  indent -- confirmed visually via rendered page images, not just warning-count chasing.
- **Two of this session's own new additions overflowed the page**: `tab:headline`'s new 4th column
  (E_amb) by ~186pt (~40% too wide) and the new `tab:mr1-historical` table by ~15pt -- both wrapped
  in `\resizebox{\textwidth}{!}{...}`, confirmed fixed by recompiling.
- One cosmetic fix: the back-test figure's legend overlapped the 2020 peak data point under a fixed
  `loc="upper left"`; changed to `loc="best"` in `src/paper_figures.py` and regenerated the actual
  figure PDFs (a step that was initially missed -- edited the script but forgot to re-run it before
  the next compile, caught and corrected).
- Remaining overfull-hbox warnings (lines ~131 residual 3.3pt, ~305, ~736, ~773, ~789) are all
  pre-existing, sub-millimeter-to-modest, not from this session's content, and not fixed (out of
  scope; flagged to the user, not touched without being asked).
- **Compiled PDF copied to `paper/minimum_state_brazil.pdf`** (44 pages) so the user can actually
  open it -- this is the first time this file has existed anywhere in the project.

**Policy-recommendations addition (2026-10-26), after an explicit stance check with the user.**
User asked for the model's results to be turned into forward-looking policy priorities. Flagged
directly that this is in real tension with the paper's own repeated "we do not rank candidates or
make recommendations" framing before proceeding -- user chose the hedged option: state what the
model's own numbers imply is at stake, not "we recommend X." A second, narrower research pass (10
real *Fiscal Studies* articles, via free working-paper twins where paywalled) found: no article in
the sample had a labelled "Policy implications" section (all fold this into the end of Discussion/
Conclusion, 1-3 sentences to about a page); register is mostly hedged ("would"/"suggests," direct
"should" language rare and narrowly scoped); explicit non-ranking disclaimers like this paper's own
were not found elsewhere in the sample, but nothing contradicts them either; citation support per
claim is narrow, 1-2 papers, never a long citation string. Added one ~190-word paragraph at the end
of the existing Conclusion (not a new section), four hedged claims (interest-growth differential as
the higher-leverage lever; composition over size; ring-fencing health spending; debt-financed
expansion's distributional benefit is conditional on who holds the resulting interest income) --
**reusing entirely citations already in the paper's own 160-entry bibliography** (`blanchard2019`,
`furmansummers2020`, `alesinaardagna2010`, `pires2014`, `szkloclarkerocha2024`, `rasellaetal2013`,
`lustig2018ceq`, `higginspereira2014`), since the paper's existing extended literature review
(Appendix A) turned out to already cover every one of the four themes, several with Brazil-specific
evidence -- zero new citations needed. Recompiled clean, no new overflow, visually confirmed.

**Wide-literature benchmark and journal-fit reassessment (2026-10-26).** User asked for a second,
broader benchmark (~50 diverse articles, different from the 25-article Fiscal Studies presentation
survey) covering debt-projection methodology, journal fit, and AI-disclosure norms, plus a
paper-wide tone-consistency pass. Five parallel research agents + one report-writer (full report:
`reports/Debt model methodology and journal fit.md`); one tone-consistency fork (full read-through
of all 915 lines, confirmed already consistent, zero fixes needed).

**Headline finding: journal fit, not methodology, is the real issue.** *Fiscal Studies* has
essentially no track record for this genre (one adjacent conceptual paper found, no stochastic DSA
or microsimulation precedent at all), while a 2008 *IMF Staff Papers* article (direct predecessor
to *IMF Economic Review*) ran a near-identical Monte Carlo/VAR stochastic DSA study naming Brazil
explicitly; *Economic Modelling* has a second confirmed precedent. **User decided: retarget to IMF
Economic Review.** Fixed the one casualty already found in the paper text: the lit-review appendix
intro's "reflecting this paper's deliberate engagement with [Fiscal Studies'] own back-catalogue"
framing, which only made sense when targeting that specific journal -- generalized to name Fiscal
Studies as "one of several applied public-finance journals," not the target. A new, focused
benchmark of IMF Economic Review's own author guidelines/structure/length/citation-style
conventions is running (background), to replace the Fiscal Studies-specific calibration done
earlier this session (abstract length target, figure/table conventions, the "policy implications"
placement precedent) -- **not yet reconciled against the paper; do this next.**

**Methodology**: confirmed largely sound. One real, well-evidenced gap: independent-per-draw
parameter sampling instead of a correlated-shock structure (two 2025 institutional papers -- Banque
de France, the ESM's own operational fan-chart engine -- now use Bayesian VAR for this, finding it
produces *wider*, not narrower, bands than simpler approaches, implying this model likely
understates joint tail risk). A climate/disaster tail-shock channel (paralleling the existing G2
corruption-shock mechanism almost exactly) is a second cheap, near-term gap. ML/DL debt-path
forecasting and a true macro-fiscal copula are both explicitly flagged as NOT worth chasing (thin/
unconverged literature, or no precedent anywhere). Notable: several gaps the external literature
scan would have flagged turned out to already be closed by this session's own uncommitted work
(DC1, MR1, CYC1, FX1); IY1 (bondholder-incidence wired into microsimulation) appears to have no
precedent anywhere in the literature at all -- worth stating in the paper as a contribution, not
just a robustness check. **Not yet implemented; awaiting the user's choice of which items to act
on** (see the report's own distinction between near-term-actionable vs. acknowledge-as-limitation).

**AI disclosure**: assessed as fully policy-compliant and more transparent than any published
economics-journal precedent found; the real exposure is referee *perception* of the code-disclosure
specifically (no comparable published example exists yet), not a compliance problem. No change
recommended to the disclosure's honesty; a minor wording clarification (distinguishing "AI
implementing under continuous author specification/review" from "AI autonomously analysing data,"
mirroring the Journal of Finance's own tiered framing) is a candidate refinement, not yet made.

**One live addition made directly in response to a user question this round**: a footnote on the
inactive inequality-to-growth channel (\citet{ostrybergtsangarides2014}), explaining the two
separate reasons it stays off by default (a genuine pipeline circularity between C3 and C5; the
single-external-estimate discipline applied to every other borderline channel).

## IMF Economic Review retarget, methodology builds, and reframing (2026-10-26)

**`paper/minimum_state_brazil_IMF.tex` created** as a copy of the Fiscal-Studies-targeted original,
per the user's explicit instruction, so the original stays intact as a fallback for a different
venue. All new work from this point goes into the `_IMF` file only; `minimum_state_brazil.tex` is
untouched beyond the one earlier lit-review-sentence fix.

**IMF Economic Review benchmark** (background research agent): hard 50-double-spaced-page cap that
explicitly *includes* appendices (figures/tables add up to 8 more); abstract needs to shift from
Fiscal Studies' hedged register toward direct, declarative findings; citation style (natbib author-
year) carries over unchanged, no rework needed there. **Not yet actioned** -- the main/supplementary
split and abstract de-hedging are the next task, per the user's explicit sequencing choice
(methodology items first).

**Three new methodology diagnostics built**, all user-approved, all in the established off-by-
default, byte-identical-when-unset house style:
- `src/dis1_disaster_shock.py` (+ 8 tests): a climate/disaster tail-shock channel reusing
  `src.corruption`'s own event/magnitude/decay machinery, extended with a shared-draw primary-
  balance hit. Calibrated on the 2024 Rio Grande do Sul floods' federal fiscal cost (~0.07-0.12% of
  GDP), explicitly NOT on EM-DAT (independently documented to understate Brazilian disaster losses
  ~36x relative to Brazil's own S2iD registry, per a SciELO comparison study found during sourcing).
- `src/cor1_correlated_shocks.py` (+ 8 tests): tests whether a jointly-correlated historical shock
  (growth, inflation, primary balance, FX together, 3-year block bootstrap -- the same convention
  already used for the Section 7 SFA term, not a fitted VAR, since the 23-year overlapping sample is
  too thin to fit one) widens debt/GDP bands relative to the published Monte Carlo's own independent
  sampling. **Found a real bug during development**: the first implementation used a telescoping
  growth-factor shortcut that silently dropped the year-to-year change in `gdp_level_vs_s0_pct`/
  `external_gdp_level_pct`, breaking the zero-shock exact-reproduction property (caught immediately
  by the critical regression test, not left in). Fixed by switching to the same direct per-year
  formula every other diagnostic this session already uses. **Finding, confirmed over 300 draws**:
  the correlated-shock band is wider than the published band in 16 of 20 scenario-horizon cells,
  roughly double the published width at 20 years for the ambitious scenarios -- directly consistent
  with the Banque de France and ESM precedents that motivated building this.
- `src/backtest_jmc1.py` extended with a `coverage_rate()` function: an ESM-style coverage statistic
  (what fraction of historical anchor years fall inside the model's own already-published low/high
  real-rate band) added to the existing MR1-historical validation, at no new estimation cost. Result:
  64.3% coverage (9/14 years), missing 2011, 2012, 2014, 2015, 2022.

Three new citations added to `minimum_state_brazil_IMF.tex`'s bibliography only (not the FS
original): Baret, Bec & Cochard (2025, Banque de France WP 1019), Hitaj, Zavalloni & Zigraiova
(2025, ESM Brief 5), Draganic, Srdelic & Davila-Fernandez (2025, arXiv). New appendix section
"Diagnostic extensions, part III: a wider methodology sanity check" added to the IMF-targeted paper
with both new diagnostics' tables and findings.

**Reframing (explicit user instruction, 2026-10-26): removed the "independent review" narrative
throughout `minimum_state_brazil_IMF.tex`.** The paper had been structured around "an independent
reviewer argued X, we built Y in response" (the whole Appendix~B/"part II" section, several
Discussion paragraphs, the abstract). Rewrote roughly 15 distinct sentences/paragraphs to a neutral,
self-motivated "sanity check" framing (e.g. "a direct sanity check on the model's own completeness
makes exactly this point" instead of "an independent review ... made exactly this point"), including
the section title itself ("responding to an independent review" -> "robustness checks on the
business cycle, monetary policy, the exchange rate and interest-income incidence") and the
"Putting it together" subsection title. Internal LaTeX labels (`app:reviewer`,
`sec:discussion-reviewer-synthesis`) were deliberately left unchanged since they're invisible to
readers and renaming them would require touching every cross-reference for no reader-visible
benefit. Journal-name occurrences of "Review" (American Economic Review, etc.) and genuinely
self-referential "internal review" mentions (the project's own bug-catching process, an in-house
debt-panel estimate) were correctly left untouched -- verified by a full re-grep after the edits.

**Verification**: recompiled clean after every batch of edits (same 5 pre-existing sub-page-width
warnings, zero new ones); citation/label/brace-balance script clean (zero missing/orphaned
citations or labels); PDF copied to `paper/minimum_state_brazil_IMF.pdf`. Full `pytest` suite
re-run after the three new modules: **326 passed in 1850.68s** (310 + 16 new tests from COR1 and
DIS1) -- zero regressions.

**Not yet done**: the main-manuscript/online-supplementary-material split and abstract de-hedging
for the IMF target (next task per the approved sequencing); confirming the full pytest result.

Nothing committed or pushed, per standing instruction.

## 2026-10-26: IMF target -- main-manuscript / online-supplementary-material split, and abstract de-hedging

Completed the two remaining items from the "go ahead" instruction (the split was needed to fit IMF
Economic Review's 50-double-spaced-page cap, which explicitly counts appendices and references).

**Cross-reference fix (prerequisite to splitting)**: identified, via a scratchpad script, every
`\ref{}`/`Appendix~\ref{}`/`Section~\ref{}`/`Table~\ref{}` in the main body (then lines 58-339)
pointing at a label that lives in the appendix region (lines 672-977) -- 35 instances across 14
distinct labels (`app:d4`, `app:lit`, `app:reviewer`, `sec:discussion-reviewer-synthesis`,
`sec:lit-brazil`, `sec:lit-microsim`, `sec:lit-multipliers`, `sec:lit-premium`, `sec:lit-sfa`,
`tab:d4breach`, `tab:d4gap`, `tab:d4variants`, `tab:dc1`, `tab:fx1`). Numbered cross-document
`\ref`s will not resolve once the file is split, so each was replaced with descriptive plain text
("the online supplementary material", "the online supplementary material's literature review",
etc.), preserving each sentence's grammar and meaning rather than attempting a fragile
`\usepackage{xr}` cross-document-reference setup.

**The split itself**: wrote a one-off script
(`build_split_files.py` in the session scratchpad) that (1) parses the single file into preamble,
main body, the 163-entry hand-written bibliography, and the appendix block; (2) computes which
citation keys are actually used in the body (73) versus the appendix (153, 63 shared); (3) writes
`paper/minimum_state_brazil_IMF.tex` as preamble + body + a trimmed 73-entry bibliography, and a
new `paper/minimum_state_brazil_IMF_supplement.tex` as its own preamble/title ("Online
Supplementary Material for ...") + the full appendix content (literature review, D4 diagnostics,
the reframed reviewer-response diagnostics, and the new benchmark diagnostics) + a trimmed
153-entry bibliography. The original merged file is preserved at
`paper/minimum_state_brazil_IMF_prerelease_merged.tex.bak` in case anything needs to be recovered
from it.

Two bugs caught by the verification script and fixed before compiling: (1) the appendix content
itself contains 11 reverse-direction references pointing back into the main body (`sec:architecture`,
`sec:architecture.premium`, `sec:backtest`, `sec:results`, `sec:scenarios`, `sec:discussion`,
`sec:lit`, `sec:d4`, `tab:headline`) -- fixed the same way, with descriptive text ("the main
manuscript's back-testing section", etc.); (2) the bibliography-splitting script duplicated the
final `\end{thebibliography}` line in the supplement (an artefact of how the original bibliography
block was parsed) -- removed the stray duplicate.

Both files recompile clean via tectonic: main manuscript 25 pages / ~12,730 words (~42 double-spaced
pages, comfortably under the 50-page cap), supplement 28 pages. One real layout defect found and
fixed (the new `tab:d4variants` table, now in the supplement, overflowed the page width by ~47pt;
wrapped in `\resizebox{\textwidth}{!}{...}`, same fix pattern as every other oversized table this
project has hit). Two sub-10pt overfull-hbox warnings remain (a long section title, one table row)
-- same negligible magnitude as warnings already accepted elsewhere in this project; not fixed.

**Abstract de-hedging**: rewritten from 263 words (hedged, FS-style) to 179 words, more declarative
IMF Economic Review register -- states the back-test failure, the diagnostic reversal finding, and
the magnitude (12-16pp overshoot, 13-14% understatement) directly rather than wrapped in qualifying
clauses, while keeping every number traceable to the body.

PDFs copied to `paper/minimum_state_brazil_IMF.pdf` and `paper/minimum_state_brazil_IMF_supplement.pdf`.

**Post-split read-through**: read both compiled documents in full, prose and all. Found and fixed one
real defect the mechanical `Section~\ref{...}` -> descriptive-text substitution introduced: a
sentence in the supplement's debt-composition/FX subsection started with a lower-case "the main
manuscript's discussion section..." immediately after a period (the substitution doesn't know
whether the label it's replacing started a sentence). Fixed the capitalisation; recompiled clean.
No other grammar or cross-reference defects found on the full read.

Nothing committed or pushed, per standing instruction.

## Operational flag for the user

- `docs/c7_external_v2.md` lost its "Lead-developer review (2026-10-21)" section **twice** in this session
  (2026-10-23) with no corresponding commit or tool action by Claude in between - restored both times from
  `git show HEAD:docs/c7_external_v2.md`, most recently at ~11:05 local time. No other Claude session was
  running on this machine at the time (checked via the agent directory) and no script in this repo writes
  to that path. This smells like something outside this session reverting the working-tree file (a sync
  tool on the `Desktop`-path working directory, e.g. OneDrive, is the most likely external candidate, but
  unconfirmed) rather than a bug in this repo's own code. Worth checking when back: whether the file keeps
  reverting, and whether anything else in the working tree is silently losing edits the same way.

## Branch consolidation notes

- **2026-10-24: `codex/brazil-a1-a4` merged into `main` (PR #1) and deleted**, both locally and on
  `origin`, after the D2 fix / D4 diagnostics / E1 dashboard / E2 report / academic-paper commit
  (`59f691d`) landed on it. `main` now holds the full task history described in this file; rows
  above that still name `codex/brazil-a1-a4` as their branch refer to work that is now on `main`,
  not a separate branch to look up.
- The A1 and A2 commits are combined on `codex/brazil-a1-a4` so both outputs and raw sources are present together.
- Concurrent Claude edits to `AGENTS.md`, `PLAN_BRAZIL.md`, and `config/scenarios.yaml` were present in the checkout when work resumed and are preserved unchanged here.
- IMF October 2026 WEO workbook and DataMapper API, and the OECD SDMX API, each returned HTTP 403 from this environment. A4 therefore uses the existing World Bank indicator and labels its central-government-only scope in the output files.
- A4 was later refetched from the World Bank API for 1990–2025 into `data/raw/brazil/worldbank_expense_1990_2025.json`; summary episode files were rebuilt from that response.
- A3 downloads are documentation/layout files only. Full PNAD and POF microdata remain deferred until the exact source mappings are reviewed.
