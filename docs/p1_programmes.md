# P1 - 2026 government programmes as model scenarios

Status: implemented, **results unpublished**. Programme results are not committed to `outputs/` while the
D2 publication gate fails (`outputs/backtest.md`) and until the user has reviewed the method. Nothing here
ranks candidates; the model compares policy mechanisms that the two filed programmes describe.

## What is built

`src/programs.py` turns the item mapping in `config/programs_2026.yaml` into two ordinary C2 scenarios,
`P_lula` and `P_flavio`. They run through the same C2 -> C6 -> C4 -> C5 -> C3 chain, with the same
parameter draws and external paths as every other scenario, and are compared with S0 in each draw.

Three general model extensions, usable by any scenario, were needed:

| Extension | Where | Effect on existing scenarios |
|---|---|---|
| `package_gaps_by_year`: per-package gap paths instead of total x shares | `src/macro.py` build_spending_paths; C4/C5/C3 hooks in `src/montecarlo.py` | none (byte-identical draws checked) |
| `debt_adjustment_by_year`: debt retired outside the primary balance (privatisation) | C2, C6 and C5 debt recursions | none |
| negative `revenue_change_pp` (tax cuts) in C3, relief allocated by the same incidence score as a rise | `src/micro.py` | none |

## How each programme becomes a path (2027-2030 term, gaps held after 2030)

**P_lula** - L1 LC 200/2023 rule on the federal share (0.48) of general-government primary spending:
real spending growth = 0.7 x real revenue growth, bounded to [0.6%, 2.5%]; revenue growth is S0 GDP
growth plus the L5 revenue ramp. The gap is the rule's federal path below 0.48 x S0. Cuts fall in an
assumed composition (other current 0.5, subsidies 0.25, services 0.25); L3 transfers rise by 0-0.2 pp
inside the cap; L5 revenue +0-0.5 pp.

**P_flavio** - F1 debt-target rule: the planned primary balance moves linearly from its 2026 S0 level to
the level that stabilises the 2026 debt ratio, d(i - g)/(1 + g) on S0 rates and growth, over T = 2-6
years. Spending gap = planned primary-balance change minus the F3 revenue change (0 to -1 pp). Cuts in
the F2 composition (services 0.5, other current 0.25, subsidies 0.25); F8 new programmes (0-0.3 pp) are
financed inside the path; F5 privatisation retires 0-2 pp of GDP of debt over the term.

Both: the F1 pooled median delivery bias (+0.25 pp, outturn minus original target) is added to the
planned gap from 2027; unstated sizes are sampled uniformly over their ranges on a separate random
stream `[seed, 2]`, so all other draws are unchanged; the central run uses midpoints (T = 4).

Run: `python -m src.montecarlo --programmes --output-dir <dir>`; sensitivity with the same default
package shares for both programmes: `--programmes-common-composition`.

## Known limits (same for both)

- Paths are ex ante, evaluated on the S0 GDP path; realised balances then move with the multipliers.
- The federal/subnational split is proportional, so the LC 200 squeeze from RGPS ageing is understated.
- The debt-stabilising target uses S0 growth (about 1.1-1.2% a year) and the C2 real rate, which makes the
  required primary balance high (about 3.2% of GDP); the implied 2030 cut is larger than the B1
  precedent caps (R_max). It is reported, not capped.
- Cut compositions are assumptions for both programmes; the efficiency package has a zero central
  multiplier in C2, so composition drives the GDP results. The common-composition run isolates size and
  timing from that assumption and must be shown next to the main run.
- Not modelled for either: labour regulation (6x1, negotiated over legislated), off-budget investment
  and BNDES/guarantee costs, lost dividends after privatisation, anti-fraud savings, the 50% LC 200
  growth factor after a missed target.
