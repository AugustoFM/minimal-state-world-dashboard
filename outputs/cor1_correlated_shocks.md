# COR1: jointly-correlated macro-fiscal shock diagnostic

Built in response to a wider literature benchmark of this project's own methodology, which found that two 2025 institutional debt-sustainability papers (Banque de France; the ESM's own operational fan-chart engine) replace independent parameter sampling with a jointly-correlated shock structure, both finding this *widens* uncertainty bands relative to simpler approaches. COR1 tests the same question against Brazil's own 2002-2024 history: a joint 3-year block bootstrap of growth, inflation, the primary balance and the exchange rate together (preserving whatever correlation they actually had), compared against the published Monte Carlo's own independent-sampling band width at the same scenario/horizon. See the module docstring for why a block bootstrap, not a fitted VAR, was used (23 years of overlapping data is too thin to fit a multi-variable VAR with confidence).

Draws: 300 (seed 20261026, central draw -- zero shock -- plus 299 sampled).
Band width wider than the published Monte Carlo's own: 16 of 20 scenario-horizon cells.

## Debt/GDP vs S0: band width, correlated-shock diagnostic vs published Monte Carlo (pp)

| Scenario | Horizon | Published width | COR1 (correlated) width | Wider? |
|---|---:|---:|---:|---|
| E_amb | 5 | 0.369 | 0.593 | yes |
| E_amb | 10 | 3.378 | 5.740 | yes |
| E_amb | 15 | 13.206 | 25.646 | yes |
| E_amb | 20 | 33.596 | 69.709 | yes |
| E_mod | 5 | 0.186 | 0.296 | yes |
| E_mod | 10 | 1.690 | 2.868 | yes |
| E_mod | 15 | 6.479 | 12.400 | yes |
| E_mod | 20 | 17.216 | 36.089 | yes |
| R_amb | 5 | 0.378 | 0.591 | yes |
| R_amb | 10 | 3.381 | 5.726 | yes |
| R_amb | 15 | 12.947 | 24.799 | yes |
| R_amb | 20 | 34.773 | 72.688 | yes |
| R_mod | 5 | 0.188 | 0.296 | yes |
| R_mod | 10 | 1.690 | 2.865 | yes |
| R_mod | 15 | 6.476 | 12.400 | yes |
| R_mod | 20 | 17.214 | 36.084 | yes |
| S0 | 5 | 0.000 | 0.000 | no |
| S0 | 10 | 0.000 | 0.000 | no |
| S0 | 15 | 0.000 | 0.000 | no |
| S0 | 20 | 0.000 | 0.000 | no |

## Limitations

- A joint historical block bootstrap, not a fitted VAR or Bayesian VAR -- a deliberate choice given the thin (23-year) overlapping sample, not a claim this fully replicates the Banque de France/ESM methodology, only that it tests the same underlying question (correlated vs. independent shocks) with a technique this project already uses elsewhere.
- The FX-linked revaluation reuses DC1's own formula and config parameter rather than introducing a new assumption; growth and inflation shocks are applied additively to the already-external-adjusted corner, the same first-order-diagnostic simplification CYC1, DC1, FX1, MR1 and JMC1 already document.
- The shared joint shock path is common to every scenario within a draw (like the external and corruption shock blocks already are), so this diagnostic widens uncertainty without mechanically favouring any policy path.
