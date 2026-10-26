"""DIS1: a climate/natural-disaster tail-shock diagnostic.

A wider literature benchmark of this project's own debt-sustainability methodology (2026-10-26,
`reports/Debt model methodology and journal fit.md`) found that the IMF's Natural Disaster Debt
Dynamics Tool (ND-DDT) is now institutionalised into both the Market-Access and Low-Income-Country
debt-sustainability frameworks, and that a November 2025 academic application to Croatia and Slovenia (Draganic,
Srdelic and Davila-Fernandez, 2025) calibrates a disaster shock at the 5th percentile of historical
outcomes, hitting both real GDP growth and the primary balance within an otherwise familiar Monte
Carlo. This model already has a structurally near-
identical mechanism for a different tail risk -- the G2 major-corruption-shock process
(`src.corruption`): a stochastic annual event indicator, a triangularly-distributed magnitude, and
a build-up/decay GDP-level path, applied identically to every scenario within a draw so it widens
uncertainty without favouring any policy. DIS1 reuses that exact machinery for a climate/disaster
shock instead of building a new one, and extends it with the one genuine addition the literature
calls for: a direct, shared-draw primary-balance hit (emergency relief spending), since a disaster
shock is not GDP-level-only the way the corruption shock is.

**Calibration and its limits, stated plainly.** No general-purpose, Brazil-specific disaster-
fiscal-cost dataset was identified. The standard international disaster database (EM-DAT) is
independently documented to understate Brazilian disaster losses by roughly an order of magnitude
relative to Brazil's own national S2iD system (36 EM-DAT-recorded hydrometeorological events
totalling R$9.2 billion for 2010-2014, against 4,070 S2iD-recorded events totalling R$331.4 billion
over the same window) -- using a cross-country EM-DAT-calibrated shock would therefore plausibly
understate Brazilian disaster risk specifically. Rather than adopt an uncalibrated cross-country
figure, this diagnostic anchors its primary-balance-shock magnitude on a single, large, well-
documented, federal-level Brazilian event: the 2024 Rio Grande do Sul floods, whose federal fiscal
cost is reported at R$7.7 billion (direct emergency-credit guarantees) rising to at least R$13.4
billion once the broader aid package is included, against Brazil's own roughly R$11 trillion 2024
GDP -- approximately 0.07-0.12% of GDP. This is one severe event, not an estimated distribution; the
low/central/high range sampled below treats it as the central case and brackets it with a
proportionate, explicitly judgemental low/high band, in the same spirit as -- and with the same
single-estimate caveat already attached to -- CYC1's state-dependence ratio and FX1's depreciation
elasticity. The annual event probability is similarly a judgement call, not an estimated hazard
rate: one federal-fiscal-scale climate event (2024) occurred within the roughly twenty-year window
this project's own back-test (Section 7) already covers, which is far too thin a sample to estimate
a probability from directly; the sampled range is stated as a judgement anchored loosely on that
one observation, not a fitted frequency.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src import external
from src.corruption import level_path, sample_events, sample_magnitudes
from src.macro import run_corner
from src.montecarlo import central_draw, inputs_for_draw, load_context, parameters_for_draw, sample_draw

DEFAULT_PATHS = {
    "data": Path("data/brazil/dis1_disaster_shock.csv"),
    "report": Path("outputs/dis1_disaster_shock.md"),
}
N_DRAWS = 300
SEED = 20261026
STREAM_INDEX = 17  # unused by run()'s streams (1-9), D4's (10), CYC1's (11), DC1's (12), IY1's (13),
                   # MR1's (14), FX1's (15), JMC1's (16)
SCENARIOS = ("S0", "R_mod", "R_amb", "E_mod", "E_amb")
# Annual event probability: a judgement, not a fitted hazard rate (see module docstring).
EVENT_PROBABILITY_CFG = {"low": 0.03, "high": 0.12}
# GDP-level loss, triangular, reusing src.corruption's own build-up/decay convention (same order of
# magnitude as the published G2 corruption shock, since both are "a bad year disrupts real activity"
# mechanisms): low 0.5%, mode 1.25%, high 3.0% of GDP level.
GDP_LEVEL_LOSS_CFG = {"low": 0.5, "mode": 1.25, "high": 3.0}
BUILD_UP_YEARS = 1
RECOVERY_HALF_LIFE_YEARS = 2.0
# Primary-balance hit (emergency relief spending), anchored on the 2024 Rio Grande do Sul floods'
# federal fiscal cost (~0.07-0.12% of GDP): triangular, low/central/high.
PRIMARY_BALANCE_HIT_CFG = {"low": 0.05, "mode": 0.10, "high": 0.30}
RELIEF_DECAY_YEARS = 2  # emergency spending is front-loaded, unlike the slower GDP-level recovery


def sample_primary_balance_hits(
    rng: np.random.Generator, n: int, low: float, mode: float, high: float,
) -> np.ndarray:
    """Draw `n` positive primary-balance costs (pp of GDP) for the shared disaster events."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if not 0.0 <= low <= mode <= high:
        raise ValueError("primary-balance hit bounds must satisfy 0 <= low <= mode <= high")
    return rng.triangular(low, mode, high, size=n)


def primary_balance_path(event_steps: np.ndarray, hits: np.ndarray, years: int, decay_years: int) -> np.ndarray:
    """Return the shared primary-balance deduction path (pp of GDP, positive = cost), linearly
    phased out over `decay_years` from the event year -- front-loaded, unlike the GDP-level channel's
    slower exponential recovery, since emergency relief spending is concentrated near the event."""
    if years < 0:
        raise ValueError("years must be non-negative")
    if decay_years < 1:
        raise ValueError("decay_years must be at least one")
    events = np.asarray(event_steps, dtype=bool)
    costs = np.asarray(hits, dtype=float)
    if events.ndim != 1 or len(events) != years:
        raise ValueError("event_steps must be a one-dimensional array of length years")
    if costs.ndim != 1 or len(costs) != int(events.sum()):
        raise ValueError("hits must contain one value per event")
    path = np.zeros(years, dtype=float)
    for event_index, cost in zip(np.flatnonzero(events), costs):
        remaining = decay_years - np.arange(years - event_index)
        contribution = np.clip(remaining, 0, decay_years) / decay_years * cost
        path[event_index:] += contribution[: years - event_index]
    return path


def run_draws(n_draws: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    context = load_context(variants=["default"])
    params = context["parameters"]
    base_year = context["base_year"]
    target_years = context["target_years"]
    steps = max(target_years) - base_year
    rng = np.random.default_rng(seed)
    event_rng = np.random.default_rng([seed, STREAM_INDEX])
    magnitude_rng = np.random.default_rng([seed, STREAM_INDEX, 1])
    balance_rng = np.random.default_rng([seed, STREAM_INDEX, 2])
    external_rng = np.random.default_rng([seed, STREAM_INDEX, 3])
    changes = external.historical_changes()

    rows: list[dict] = []
    for index in range(n_draws):
        draw = (
            central_draw(params, context["inputs"]) if index == 0 else sample_draw(rng, params, context["inputs"])
        )
        probability = (
            0.5 * (EVENT_PROBABILITY_CFG["low"] + EVENT_PROBABILITY_CFG["high"]) if index == 0
            else float(event_rng.uniform(EVENT_PROBABILITY_CFG["low"], EVENT_PROBABILITY_CFG["high"]))
        )
        events = sample_events(event_rng, steps, probability)
        n_events = int(events.sum())
        gdp_magnitudes = (
            np.full(n_events, GDP_LEVEL_LOSS_CFG["mode"]) if index == 0
            else sample_magnitudes(
                magnitude_rng, n_events, GDP_LEVEL_LOSS_CFG["low"], GDP_LEVEL_LOSS_CFG["mode"], GDP_LEVEL_LOSS_CFG["high"],
            )
        )
        balance_hits = (
            np.full(n_events, PRIMARY_BALANCE_HIT_CFG["mode"]) if index == 0
            else sample_primary_balance_hits(
                balance_rng, n_events, PRIMARY_BALANCE_HIT_CFG["low"], PRIMARY_BALANCE_HIT_CFG["mode"], PRIMARY_BALANCE_HIT_CFG["high"],
            )
        )
        gdp_level_pct = level_path(events, gdp_magnitudes, steps, BUILD_UP_YEARS, RECOVERY_HALF_LIFE_YEARS)
        balance_hit_pp = primary_balance_path(events, balance_hits, steps, RELIEF_DECAY_YEARS)

        annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
        draw_parameters = parameters_for_draw(params, draw)
        draw_inputs = inputs_for_draw(context["inputs"], draw)
        corner = run_corner(
            annual, context["population"], context["variant_configs"]["default"],
            draw_parameters, draw_inputs, "central", "transitory",
        )
        bootstrapped = external.bootstrap_path(external_rng, changes, steps)
        effects = external.gdp_and_inflation_effects(bootstrapped, params)
        corner = external.apply_external(corner, effects, draw_inputs)

        gdp_by_step = {0: 0.0, **{i + 1: float(v) for i, v in enumerate(gdp_level_pct)}}
        balance_by_step = {0: 0.0, **{i + 1: float(v) for i, v in enumerate(balance_hit_pp)}}

        for scenario in SCENARIOS:
            scen = corner.loc[corner["scenario"].eq(scenario)].sort_values("year")
            for row in scen.itertuples():
                year = int(row.year)
                if year not in target_years:
                    continue
                step = year - base_year
                extra_gdp_pct = gdp_by_step.get(step, 0.0)
                extra_balance_pp = balance_by_step.get(step, 0.0)
                baseline_debt = float(row.debt_gdp_with_external)
                # First-order diagnostic, same convention as DC1/FX1: the GDP-level shock revalues
                # debt/GDP through the denominator, and the primary-balance shock adds directly to
                # the numerator -- both applied to the already-external-adjusted baseline, not
                # re-run through the full debt recursion, to stay a standalone, additive diagnostic.
                denominator_effect_pp = baseline_debt * (1.0 / (1.0 + extra_gdp_pct / 100.0) - 1.0)
                additional_pp = denominator_effect_pp + extra_balance_pp
                rows.append({
                    "draw": index, "scenario": scenario, "year": year, "horizon": step,
                    "probability_sampled": probability,
                    "extra_gdp_level_pct": extra_gdp_pct,
                    "extra_primary_balance_cost_pp": extra_balance_pp,
                    "debt_gdp_baseline": baseline_debt,
                    "additional_debt_gdp_pp_from_disaster": additional_pp,
                    "debt_gdp_with_disaster": baseline_debt + additional_pp,
                })
    return pd.DataFrame(rows)


def summarise(draws: pd.DataFrame) -> pd.DataFrame:
    sampled = draws.loc[draws["draw"] > 0]
    records = []
    for (scenario, horizon), group in sampled.groupby(["scenario", "horizon"], sort=False):
        record = {"scenario": scenario, "horizon": int(horizon)}
        for column in ("debt_gdp_baseline", "additional_debt_gdp_pp_from_disaster", "debt_gdp_with_disaster"):
            record[f"{column}_p10"] = float(np.nanpercentile(group[column], 10))
            record[f"{column}_p50"] = float(np.nanpercentile(group[column], 50))
            record[f"{column}_p90"] = float(np.nanpercentile(group[column], 90))
        records.append(record)
    return pd.DataFrame(records).sort_values(["scenario", "horizon"]).reset_index(drop=True)


def render_report(draws: pd.DataFrame, summary: pd.DataFrame, n_draws: int, seed: int) -> str:
    prob = draws.loc[draws["draw"] > 0, "probability_sampled"]
    lines = [
        "# DIS1: climate/natural-disaster tail-shock diagnostic",
        "",
        "Built in response to a wider literature benchmark of this project's own debt-sustainability "
        "methodology, which found the IMF's Natural Disaster Debt Dynamics Tool (ND-DDT) is now "
        "institutionalised in its debt-sustainability frameworks and is structurally close to this "
        "model's own existing major-corruption-shock mechanism (`src.corruption`). DIS1 reuses that "
        "exact machinery for a climate/disaster shock, adding a shared-draw primary-balance hit "
        "(emergency relief spending) alongside the existing GDP-level channel. Calibration is "
        "anchored on a single, well-documented Brazilian event (the 2024 Rio Grande do Sul floods, "
        "federal fiscal cost ~0.07-0.12% of GDP), not an estimated distribution -- see the module "
        "docstring for the full sourcing note and its limits, including why a generic cross-country "
        "(EM-DAT) calibration was not used (it is independently documented to understate Brazilian "
        "disaster losses by roughly an order of magnitude relative to Brazil's own S2iD system).",
        "",
        f"Draws: {n_draws} (seed {seed}, central draw plus {n_draws - 1} sampled). Sampled annual "
        f"event probability: median {float(np.nanpercentile(prob, 50)):.3f} "
        f"[{float(np.nanpercentile(prob, 10)):.3f}, {float(np.nanpercentile(prob, 90)):.3f}].",
        "",
        "## Additional debt/GDP from the disaster-shock channel",
        "",
        "| Scenario | Horizon | Baseline (p50 [p10,p90]) | Additional pp from disaster shock (p50 [p10,p90]) |",
        "|---|---:|---|---|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.horizon} | "
            f"{row.debt_gdp_baseline_p50:.2f} [{row.debt_gdp_baseline_p10:.2f}, {row.debt_gdp_baseline_p90:.2f}] | "
            f"{row.additional_debt_gdp_pp_from_disaster_p50:+.3f} "
            f"[{row.additional_debt_gdp_pp_from_disaster_p10:+.3f}, {row.additional_debt_gdp_pp_from_disaster_p90:+.3f}] |"
        )
    lines += [
        "",
        "## Limitations",
        "",
        "- Both the event probability and the magnitude bands are judgement calls anchored on a "
        "single severe Brazilian event (2024), not an estimated hazard rate or loss distribution -- "
        "the ~20-year window this project's own back-test covers contains exactly one federal-fiscal-"
        "scale climate event, far too thin a sample to fit a frequency to.",
        "- The GDP-level and primary-balance channels are applied as a direct, first-order "
        "revaluation of the already-external-adjusted baseline, not re-run through the full debt "
        "recursion -- the same simplification CYC1, DC1 and FX1 already document.",
        "- The same drawn event sequence and magnitudes are applied identically to every scenario "
        "within a draw, exactly as the G2 corruption-shock module already does, so this channel "
        "widens uncertainty without mechanically favouring any policy path.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=N_DRAWS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--data", type=Path, default=DEFAULT_PATHS["data"])
    parser.add_argument("--report", type=Path, default=DEFAULT_PATHS["report"])
    args = parser.parse_args(argv)
    draws = run_draws(args.draws, args.seed)
    summary = summarise(draws)
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    draws.to_csv(args.data, index=False, float_format="%.6f")
    args.report.write_text(render_report(draws, summary, args.draws, args.seed), encoding="utf-8")
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print(f"Wrote {len(draws)} draw-horizon rows to {args.data} and {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
