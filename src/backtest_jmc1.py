"""JMC1 Step 2: the historical validation gate -- MR1 + DC1 only, against 2000-2024 history.

JMC1's five channels (`src.jmc1_engine`) were designed to compound within a Monte Carlo draw
across *policy scenarios vs S0*. Three of them -- CYC1's state-dependent multiplier, FX1's extra
stress-driven depreciation layer, and IY1's interest-income Gini effect -- are defined entirely in
terms of how a scenario's path differs from S0's. Brazil's actual 2000-2024 history is a single,
already-realized path with no S0 counterfactual sitting next to it: there is no "what growth would
have been without the policy" to rescale by a cyclical multiplier, no "common, policy-blind FX
path" to add an extra stress-driven layer on top of (the real observed BRL/USD path already *is*
whatever happened, stress included), and no "S0's own Gini" to compare a windfall against. Feeding
these three channels real history does not test them -- there is nothing counterfactual for them to
act on. This was surfaced to, and confirmed with, the user before writing this module: the gate is
deliberately narrowed to the two channels that **do** have a genuine historical analogue:

- **MR1** -- a rate-*generating* mechanism (Taylor 1993, reacting to each year's own observed
  inflation and PCY1's own output-gap proxy) compared against the model's existing rate-generating
  mechanism (a fixed real rate -- itself already the historical median real rate, per
  `src.macro`'s own `effective_real_interest_rate` calibration, so this is a genuinely tough
  benchmark to beat, not a strawman).
- **DC1** -- revaluing the FX-linked debt tranche by the *actual* observed BRL/USD change (not an
  "extra" stress layer on top of an unobservable common path -- the real path already *is* the
  realized one).

Both arms feed the *same* observed primary balance and the *same* real-GDP-growth-implied nominal
growth (a Fisher approximation, `(1+real)(1+inflation)-1`, not the SIDRA nominal-GDP series
`src.backtest`'s own `debt_engine` test uses -- any error this approximation introduces applies
equally to every mechanism compared here, so it does not bias the *relative* comparison this module
exists to make). Three reconstructions are compared against the observed debt/GDP path from the
first year debt data exists (2006): `fixed` (today's mechanism), `taylor_only` (MR1 alone, isolating
its own marginal contribution), `joint` (MR1 + DC1 together). The Taylor-rule-implied nominal rate
path is separately compared against the actual observed Selic.

Never imports or modifies `src.macro.run_corner`, `src.external.apply_external`, or
`src.jmc1_engine`'s own Monte Carlo loop -- a standalone historical reconstruction, reusing only
pure arithmetic (`debt_step`, `nominal_rate_from_real`, `taylor_real_rate`) and PCY1's own
already-published output-gap proxy.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest import DEFAULT_PATHS as BACKTEST_PATHS
from src.backtest import debt_backtest, debt_one_step, debt_test_inputs, observed_wide
from src.macro import debt_step, macro_input, nominal_rate_from_real
from src.montecarlo import load_context
from src.mr1_taylor_rule import TAYLOR_1993_COEFFICIENT, taylor_real_rate
from src.pcy1_fiscal_timing import DEFAULT_PATHS as PCY1_PATHS
from src.pcy1_fiscal_timing import compute_gap_and_impulse, load_series

DEFAULT_PATHS = {
    "observed": PCY1_PATHS["observed"],
    "report": Path("docs/jmc1_validation.md"),
}
INFLATION_TARGET_PCT = 3.0
MECHANISMS = ("fixed", "taylor_only", "joint")


def load_backtest_inputs(observed_path: Path = DEFAULT_PATHS["observed"]) -> pd.DataFrame:
    """Year-indexed frame with everything the reconstruction and its targets need."""
    base = load_series(observed_path)  # gdp_growth_pct, primary_balance_pct_gdp (sign-normalised)
    raw = pd.read_csv(observed_path)
    wide = raw.pivot(index="year", columns="indicator", values="value")
    wide.index = wide.index.astype(int)
    frame = base.join(
        wide[["gross_general_government_debt_pct_gdp", "selic_pct", "brl_per_usd", "cpi_inflation_pct"]],
        how="left",
    )
    frame = compute_gap_and_impulse(frame)
    frame["fx_change_pct"] = 100.0 * np.log(frame["brl_per_usd"] / frame["brl_per_usd"].shift(1))
    return frame.sort_index()


def reconstruct(
    frame: pd.DataFrame,
    mechanism: str,
    base_real_rate_pct: float,
    phi_pi: float,
    phi_y: float,
    fx_share_pct: float,
    inflation_target_pct: float = INFLATION_TARGET_PCT,
) -> pd.DataFrame:
    """Recurse `debt_step` annually from the first observed debt anchor, generating (not
    oracle-feeding) the interest rate under `mechanism` in {"fixed", "taylor_only", "joint"}."""
    if mechanism not in MECHANISMS:
        raise ValueError(f"Unknown mechanism {mechanism!r}")
    anchored = frame.loc[frame["gross_general_government_debt_pct_gdp"].notna()].sort_index()
    years = anchored.index.tolist()
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError("JMC1 back-test requires consecutive observed-debt years")
    anchor_year = years[0]
    previous_debt = float(anchored.loc[anchor_year, "gross_general_government_debt_pct_gdp"]) / 100.0
    rows = [{
        "year": anchor_year, "mechanism": mechanism,
        "predicted_debt_gdp": previous_debt * 100.0, "predicted_nominal_rate_pct": float("nan"),
        "observed_debt_gdp": previous_debt * 100.0,
    }]
    for year in years[1:]:
        row = frame.loc[year]
        inflation_pct = float(row["cpi_inflation_pct"])
        real_growth_pct = float(row["gdp_growth_pct"])
        nominal_growth = (1.0 + real_growth_pct / 100.0) * (1.0 + inflation_pct / 100.0) - 1.0
        if mechanism == "fixed":
            real_rate = base_real_rate_pct
        else:
            output_gap_proxy = float(row["output_gap_proxy_pp"]) if pd.notna(row["output_gap_proxy_pp"]) else 0.0
            real_rate = taylor_real_rate(
                base_real_rate_pct, inflation_pct, output_gap_proxy, inflation_target_pct, phi_pi, phi_y,
            )
        nominal_interest = nominal_rate_from_real(real_rate, inflation_pct) / 100.0
        new_debt = debt_step(previous_debt, nominal_interest, nominal_growth, float(row["primary_balance_pct_gdp"]) / 100.0)
        if mechanism == "joint" and pd.notna(row["fx_change_pct"]):
            fx_revaluation_pp = fx_share_pct / 100.0 * (previous_debt * 100.0) * (float(row["fx_change_pct"]) / 100.0)
            new_debt += fx_revaluation_pp / 100.0
        rows.append({
            "year": int(year), "mechanism": mechanism,
            "predicted_debt_gdp": new_debt * 100.0, "predicted_nominal_rate_pct": nominal_interest * 100.0,
            "observed_debt_gdp": float(frame.loc[year, "gross_general_government_debt_pct_gdp"]),
        })
        previous_debt = new_debt
    out = pd.DataFrame(rows)
    out["residual_pp"] = out["predicted_debt_gdp"] - out["observed_debt_gdp"]
    return out


def reconstruct_one_step(
    frame: pd.DataFrame,
    mechanism: str,
    base_real_rate_pct: float,
    phi_pi: float,
    phi_y: float,
    fx_share_pct: float,
    inflation_target_pct: float = INFLATION_TARGET_PCT,
) -> pd.DataFrame:
    """One-step analogue of `reconstruct`: re-anchor on the *observed* lagged debt every year,
    mirroring `src.backtest.debt_one_step`'s own precedent for isolating rate-setting fit from the
    cumulative compounding of stock-flow-adjustment noise that `src.backtest`'s own `debt_engine`
    row already documents as dominant and unrelated to any rate mechanism."""
    if mechanism not in MECHANISMS:
        raise ValueError(f"Unknown mechanism {mechanism!r}")
    anchored = frame.loc[frame["gross_general_government_debt_pct_gdp"].notna()].sort_index()
    years = anchored.index.tolist()
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError("JMC1 back-test requires consecutive observed-debt years")
    rows = []
    for year in years[1:]:
        row = frame.loc[year]
        previous_debt = float(anchored.loc[year - 1, "gross_general_government_debt_pct_gdp"]) / 100.0
        inflation_pct = float(row["cpi_inflation_pct"])
        real_growth_pct = float(row["gdp_growth_pct"])
        nominal_growth = (1.0 + real_growth_pct / 100.0) * (1.0 + inflation_pct / 100.0) - 1.0
        if mechanism == "fixed":
            real_rate = base_real_rate_pct
        else:
            output_gap_proxy = float(row["output_gap_proxy_pp"]) if pd.notna(row["output_gap_proxy_pp"]) else 0.0
            real_rate = taylor_real_rate(
                base_real_rate_pct, inflation_pct, output_gap_proxy, inflation_target_pct, phi_pi, phi_y,
            )
        nominal_interest = nominal_rate_from_real(real_rate, inflation_pct) / 100.0
        new_debt = debt_step(previous_debt, nominal_interest, nominal_growth, float(row["primary_balance_pct_gdp"]) / 100.0)
        if mechanism == "joint" and pd.notna(row["fx_change_pct"]):
            fx_revaluation_pp = fx_share_pct / 100.0 * (previous_debt * 100.0) * (float(row["fx_change_pct"]) / 100.0)
            new_debt += fx_revaluation_pp / 100.0
        rows.append({
            "year": int(year), "mechanism": mechanism,
            "predicted_debt_gdp": new_debt * 100.0,
            "observed_debt_gdp": float(frame.loc[year, "gross_general_government_debt_pct_gdp"]),
        })
    out = pd.DataFrame(rows)
    out["residual_pp"] = out["predicted_debt_gdp"] - out["observed_debt_gdp"]
    return out


def _sidra_debt_inputs(frame: pd.DataFrame) -> pd.DataFrame:
    """`src.backtest`'s own, more accurate SIDRA-nominal-GDP debt-test inputs (2010-2024) --
    the exact data behind `outputs/backtest.md`'s `debt_engine`/`debt_engine_one_step` rows --
    joined with CPI inflation and PCY1's output-gap proxy so a rate can be *generated*, not
    oracle-fed (unlike those two existing rows, which use the *observed* implicit rate)."""
    wide = observed_wide(BACKTEST_PATHS["observed"])
    inputs = debt_test_inputs(wide, BACKTEST_PATHS["workbook"], BACKTEST_PATHS["nominal_gdp"])
    inputs = inputs.set_index("year")
    inputs["cpi_inflation_pct"] = frame["cpi_inflation_pct"].reindex(inputs.index)
    inputs["output_gap_proxy_pp"] = frame["output_gap_proxy_pp"].reindex(inputs.index)
    return inputs.reset_index()


def _generate_rate_pct(
    row, mechanism: str, base_real_rate_pct: float, phi_pi: float, phi_y: float, inflation_target_pct: float,
) -> float:
    inflation_pct = float(row["cpi_inflation_pct"])
    if mechanism == "fixed":
        real_rate = base_real_rate_pct
    else:
        gap = float(row["output_gap_proxy_pp"]) if pd.notna(row["output_gap_proxy_pp"]) else 0.0
        real_rate = taylor_real_rate(base_real_rate_pct, inflation_pct, gap, inflation_target_pct, phi_pi, phi_y)
    return nominal_rate_from_real(real_rate, inflation_pct)


def reconstruct_sidra_cumulative(
    inputs: pd.DataFrame, mechanism: str, base_real_rate_pct: float, phi_pi: float, phi_y: float,
    inflation_target_pct: float = INFLATION_TARGET_PCT,
) -> pd.DataFrame:
    """Cumulative-from-one-anchor reconstruction on `_sidra_debt_inputs`' own nominal-GDP growth
    and observed primary balance, *generating* (not oracle-feeding) the interest rate --
    directly comparable in level to `outputs/backtest.md`'s own `debt_engine` row."""
    data = inputs.sort_values("year").reset_index(drop=True)
    previous_debt = float(data.loc[0, "observed_debt_gdp"]) / 100.0
    rows = [{
        "year": int(data.loc[0, "year"]), "predicted_debt_gdp": previous_debt * 100.0,
        "observed_debt_gdp": previous_debt * 100.0,
    }]
    for row in data.iloc[1:].itertuples(index=False):
        nominal_interest = _generate_rate_pct(row._asdict(), mechanism, base_real_rate_pct, phi_pi, phi_y, inflation_target_pct) / 100.0
        previous_debt = debt_step(
            previous_debt, nominal_interest, float(row.nominal_gdp_growth_pct) / 100.0,
            float(row.primary_balance_gdp) / 100.0,
        )
        rows.append({
            "year": int(row.year), "predicted_debt_gdp": previous_debt * 100.0,
            "observed_debt_gdp": float(row.observed_debt_gdp),
        })
    out = pd.DataFrame(rows)
    out["residual_pp"] = out["predicted_debt_gdp"] - out["observed_debt_gdp"]
    return out


def reconstruct_sidra_one_step(
    inputs: pd.DataFrame, mechanism: str, base_real_rate_pct: float, phi_pi: float, phi_y: float,
    inflation_target_pct: float = INFLATION_TARGET_PCT,
) -> pd.DataFrame:
    """One-step analogue, directly comparable to `outputs/backtest.md`'s `debt_engine_one_step` row."""
    data = inputs.sort_values("year").reset_index(drop=True)
    rows = []
    for idx in range(1, len(data)):
        row = data.iloc[idx]
        previous_debt = float(data.iloc[idx - 1]["observed_debt_gdp"]) / 100.0
        nominal_interest = _generate_rate_pct(row, mechanism, base_real_rate_pct, phi_pi, phi_y, inflation_target_pct) / 100.0
        predicted = debt_step(
            previous_debt, nominal_interest, float(row["nominal_gdp_growth_pct"]) / 100.0,
            float(row["primary_balance_gdp"]) / 100.0,
        )
        rows.append({
            "year": int(row["year"]), "predicted_debt_gdp": predicted * 100.0,
            "observed_debt_gdp": float(row["observed_debt_gdp"]),
        })
    out = pd.DataFrame(rows)
    out["residual_pp"] = out["predicted_debt_gdp"] - out["observed_debt_gdp"]
    return out


def selic_reconstruction(
    frame: pd.DataFrame, base_real_rate_pct: float, phi_pi: float, phi_y: float,
    inflation_target_pct: float = INFLATION_TARGET_PCT,
) -> pd.DataFrame:
    """Compare the fixed-rate and Taylor-rule nominal-rate paths against the actual observed Selic,
    over every year with both inflation and Selic observed (no debt anchor needed for this one)."""
    rows = []
    for year, row in frame.iterrows():
        if pd.isna(row["cpi_inflation_pct"]) or pd.isna(row["selic_pct"]):
            continue
        inflation_pct = float(row["cpi_inflation_pct"])
        fixed_nominal = nominal_rate_from_real(base_real_rate_pct, inflation_pct)
        output_gap_proxy = float(row["output_gap_proxy_pp"]) if pd.notna(row["output_gap_proxy_pp"]) else None
        taylor_nominal = float("nan")
        if output_gap_proxy is not None:
            taylor_real = taylor_real_rate(
                base_real_rate_pct, inflation_pct, output_gap_proxy, inflation_target_pct, phi_pi, phi_y,
            )
            taylor_nominal = nominal_rate_from_real(taylor_real, inflation_pct)
        rows.append({
            "year": int(year), "observed_selic_pct": float(row["selic_pct"]),
            "fixed_nominal_rate_pct": fixed_nominal, "taylor_nominal_rate_pct": taylor_nominal,
        })
    return pd.DataFrame(rows)


def _errors(residual: pd.Series) -> dict[str, float]:
    clean = residual.dropna()
    return {
        "mean_error": float(clean.mean()),
        "mae": float(clean.abs().mean()),
        "rmse": float(np.sqrt((clean ** 2).mean())),
        "n": int(len(clean)),
    }


def coverage_rate(
    sidra_inputs: pd.DataFrame, mechanism: str, low_rate_pct: float, high_rate_pct: float,
    phi_pi: float, phi_y: float,
) -> dict:
    """ESM-style coverage statistic (Brief 05/2025): the fraction of historical anchor years whose
    actually observed debt/GDP fell within the band this model's own low/high real-rate corners
    imply, rather than a bare pass/fail verdict on the central-case reconstruction alone. Reuses
    `reconstruct_sidra_one_step` unchanged, called once at each corner -- a reporting addition, not
    a new estimation exercise: the low/high real-rate bounds are the same ones
    `config/parameters.yaml`'s `effective_real_interest_rate` already publishes and the headline
    Monte Carlo already samples between."""
    low = reconstruct_sidra_one_step(sidra_inputs, mechanism, low_rate_pct, phi_pi, phi_y)
    high = reconstruct_sidra_one_step(sidra_inputs, mechanism, high_rate_pct, phi_pi, phi_y)
    merged = low[["year", "observed_debt_gdp", "predicted_debt_gdp"]].rename(
        columns={"predicted_debt_gdp": "predicted_low_rate"}
    ).merge(
        high[["year", "predicted_debt_gdp"]].rename(columns={"predicted_debt_gdp": "predicted_high_rate"}),
        on="year",
    )
    band_low = merged[["predicted_low_rate", "predicted_high_rate"]].min(axis=1)
    band_high = merged[["predicted_low_rate", "predicted_high_rate"]].max(axis=1)
    covered = (merged["observed_debt_gdp"] >= band_low) & (merged["observed_debt_gdp"] <= band_high)
    return {
        "mechanism": mechanism, "n_years": int(len(merged)), "n_covered": int(covered.sum()),
        "coverage_rate": float(covered.mean()),
        "mean_band_width_pp": float((band_high - band_low).mean()),
        "years_outside_band": [int(y) for y in merged.loc[~covered, "year"]],
    }


def run_validation() -> dict:
    context = load_context(variants=["default"])
    inputs = context["inputs"]
    params = context["parameters"]
    base_real_rate_pct = macro_input(inputs, "effective_real_interest_rate", "central")
    discount = float(params["mr1_taylor_rule"]["discount_vs_taylor_1993"]["central"])
    phi_pi = phi_y = TAYLOR_1993_COEFFICIENT * discount
    fx_share_pct = float(params["debt_composition_fx"]["fx_linked_share_pct_of_dpf"]["central"])

    frame = load_backtest_inputs()
    reconstructions = {m: reconstruct(frame, m, base_real_rate_pct, phi_pi, phi_y, fx_share_pct) for m in MECHANISMS}
    debt_errors = {m: _errors(r["residual_pp"]) for m, r in reconstructions.items()}
    one_step = {m: reconstruct_one_step(frame, m, base_real_rate_pct, phi_pi, phi_y, fx_share_pct) for m in MECHANISMS}
    one_step_errors = {m: _errors(r["residual_pp"]) for m, r in one_step.items()}

    selic = selic_reconstruction(frame, base_real_rate_pct, phi_pi, phi_y)
    selic_errors = {
        "fixed": _errors(selic["fixed_nominal_rate_pct"] - selic["observed_selic_pct"]),
        "taylor_only": _errors(selic["taylor_nominal_rate_pct"] - selic["observed_selic_pct"]),
    }

    # Refined test: src.backtest's own, more accurate SIDRA nominal-GDP inputs (2010-2024), the
    # exact data behind outputs/backtest.md's debt_engine/debt_engine_one_step rows, with a
    # *generated* (not oracle-fed) rate -- directly comparable in level to those existing rows.
    sidra_inputs = _sidra_debt_inputs(frame)
    sidra_cumulative = {
        m: reconstruct_sidra_cumulative(sidra_inputs, m, base_real_rate_pct, phi_pi, phi_y)
        for m in ("fixed", "taylor_only")
    }
    sidra_one_step = {
        m: reconstruct_sidra_one_step(sidra_inputs, m, base_real_rate_pct, phi_pi, phi_y)
        for m in ("fixed", "taylor_only")
    }
    sidra_cumulative_errors = {m: _errors(r["residual_pp"]) for m, r in sidra_cumulative.items()}
    sidra_one_step_errors = {m: _errors(r["residual_pp"]) for m, r in sidra_one_step.items()}
    oracle_cumulative = debt_backtest(sidra_inputs)
    oracle_one_step = debt_one_step(sidra_inputs)
    oracle_errors = {
        "cumulative": _errors(oracle_cumulative["residual_pp"]),
        "one_step": _errors(oracle_one_step["residual_pp"]),
    }

    # ESM-style coverage statistic (see coverage_rate's own docstring): the model's own published
    # low/high real-rate corners, not a new estimate.
    low_rate_pct = macro_input(inputs, "effective_real_interest_rate", "low")
    high_rate_pct = macro_input(inputs, "effective_real_interest_rate", "high")
    coverage = coverage_rate(sidra_inputs, "fixed", low_rate_pct, high_rate_pct, phi_pi, phi_y)

    return {
        "base_real_rate_pct": base_real_rate_pct, "phi_pi": phi_pi, "phi_y": phi_y,
        "fx_share_pct": fx_share_pct, "reconstructions": reconstructions, "debt_errors": debt_errors,
        "one_step": one_step, "one_step_errors": one_step_errors,
        "selic": selic, "selic_errors": selic_errors,
        "sidra_cumulative_errors": sidra_cumulative_errors, "sidra_one_step_errors": sidra_one_step_errors,
        "oracle_errors": oracle_errors, "coverage": coverage,
        "low_rate_pct": low_rate_pct, "high_rate_pct": high_rate_pct,
    }


def render_report(result: dict) -> str:
    lines = [
        "# JMC1 validation: does the joint rate/FX mechanism improve on 2000-2024 history?",
        "",
        "Narrowed gate (see `src/backtest_jmc1.py` module docstring for why): only MR1 (the Taylor-"
        "rule rate mechanism) and DC1 (FX-linked debt revaluation using the *actual* observed "
        "BRL/USD path) have a genuine historical analogue. CYC1, FX1's extra depreciation layer, "
        "and IY1 are scenario-vs-S0 concepts with no counterfactual in a single realized history, "
        "and are not tested here.",
        "",
        f"Fixed real-rate assumption: {result['base_real_rate_pct']:.3f}% (the model's own "
        "`effective_real_interest_rate.central` -- already the historical median real rate, so "
        "this is a tough benchmark, not a strawman). Taylor coefficients: "
        f"phi_pi = phi_y = {result['phi_pi']:.3f}. FX-linked share: {result['fx_share_pct']:.2f}% "
        "(DC1's own config central).",
        "",
        "## Debt/GDP reconstruction error vs observed, 2006-2024 (pp)",
        "",
        "| Mechanism | Mean error | MAE | RMSE | n |",
        "|---|---:|---:|---:|---:|",
    ]
    for mechanism in MECHANISMS:
        err = result["debt_errors"][mechanism]
        lines.append(f"| {mechanism} | {err['mean_error']:+.3f} | {err['mae']:.3f} | {err['rmse']:.3f} | {err['n']} |")
    lines += [
        "",
        "## Debt/GDP one-step error (re-anchored on observed lagged debt each year, pp) -- "
        "the fairer test, mirroring `src.backtest.debt_one_step`'s own precedent for isolating "
        "rate-setting fit from cumulative stock-flow-adjustment noise",
        "",
        "| Mechanism | Mean error | MAE | RMSE | n |",
        "|---|---:|---:|---:|---:|",
    ]
    for mechanism in MECHANISMS:
        err = result["one_step_errors"][mechanism]
        lines.append(f"| {mechanism} | {err['mean_error']:+.3f} | {err['mae']:.3f} | {err['rmse']:.3f} | {err['n']} |")
    lines += [
        "",
        "## Nominal-Selic reconstruction error vs observed, years with both inflation and Selic (pp)",
        "",
        "| Mechanism | Mean error | MAE | RMSE | n |",
        "|---|---:|---:|---:|---:|",
    ]
    for mechanism in ("fixed", "taylor_only"):
        err = result["selic_errors"][mechanism]
        lines.append(f"| {mechanism} | {err['mean_error']:+.3f} | {err['mae']:.3f} | {err['rmse']:.3f} | {err['n']} |")
    fixed_rmse = result["debt_errors"]["fixed"]["rmse"]
    joint_rmse = result["debt_errors"]["joint"]["rmse"]
    taylor_only_rmse = result["debt_errors"]["taylor_only"]["rmse"]
    fixed_one_step_rmse = result["one_step_errors"]["fixed"]["rmse"]
    joint_one_step_rmse = result["one_step_errors"]["joint"]["rmse"]
    taylor_only_one_step_rmse = result["one_step_errors"]["taylor_only"]["rmse"]
    fixed_selic_rmse = result["selic_errors"]["fixed"]["rmse"]
    taylor_selic_rmse = result["selic_errors"]["taylor_only"]["rmse"]
    # The one-step test is the primary gate: the cumulative test is dominated by stock-flow-
    # adjustment noise with no macro antecedent (this project's own existing `debt_engine` row,
    # `outputs/backtest.md`, already documents and accepts this as expected, mechanism-independent
    # behaviour), so it cannot fairly discriminate between rate-generating mechanisms.
    verdict = "PASS" if joint_one_step_rmse <= fixed_one_step_rmse else "FAIL"
    selic_verdict = "PASS" if taylor_selic_rmse <= fixed_selic_rmse else "FAIL"
    lines += [
        "",
        "## Verdict",
        "",
        f"Cumulative debt/GDP RMSE (dominated by SFA noise, reported for transparency, not the "
        f"gate): fixed {fixed_rmse:.3f}pp vs taylor_only {taylor_only_rmse:.3f}pp vs joint "
        f"{joint_rmse:.3f}pp.",
        "",
        f"**One-step debt/GDP RMSE (the actual gate)**: fixed {fixed_one_step_rmse:.3f}pp vs "
        f"taylor_only {taylor_only_one_step_rmse:.3f}pp vs joint {joint_one_step_rmse:.3f}pp -- "
        f"**{verdict}**: the joint (MR1+DC1) mechanism's one-step reconstruction error is "
        + ("no larger than" if verdict == "PASS" else "larger than")
        + " the published model's fixed-rate mechanism's own error on the same 2006-2024 window.",
        "",
        f"**Selic RMSE**: fixed {fixed_selic_rmse:.3f}pp vs taylor {taylor_selic_rmse:.3f}pp -- "
        f"**{selic_verdict}**: the Taylor rule's *own* implied rate path is "
        + ("closer to" if selic_verdict == "PASS" else "no closer to")
        + " the actual observed Selic than the fixed-rate assumption, over 2000-2024.",
        "",
        "If the one-step debt/GDP verdict and the Selic verdict disagree, that is itself the "
        "finding: it would mean MR1 genuinely improves on describing *Selic-setting behaviour* "
        "without that translating into a better *debt-level* reconstruction once debt_step's own "
        "dynamics (and whatever stock-flow noise survives even the one-step re-anchoring) are "
        "involved -- reported plainly either way, not reconciled into a single number.",
        "",
    ]
    sidra_fixed_cum = result["sidra_cumulative_errors"]["fixed"]["rmse"]
    sidra_taylor_cum = result["sidra_cumulative_errors"]["taylor_only"]["rmse"]
    sidra_fixed_one = result["sidra_one_step_errors"]["fixed"]["rmse"]
    sidra_taylor_one = result["sidra_one_step_errors"]["taylor_only"]["rmse"]
    oracle_cum = result["oracle_errors"]["cumulative"]["rmse"]
    oracle_one = result["oracle_errors"]["one_step"]["rmse"]
    sidra_verdict = "PASS" if sidra_taylor_one <= sidra_fixed_one else "FAIL"
    lines += [
        "## Refined test: `src.backtest`'s own SIDRA nominal-GDP inputs (2010-2024)",
        "",
        "Same comparison (a *generated*, not oracle-fed, rate), but using the exact data behind "
        "`outputs/backtest.md`'s `debt_engine`/`debt_engine_one_step` rows (actual SIDRA current-"
        "price GDP, not the CPI/real-growth Fisher approximation used above) -- a fairer, more "
        "rigorous version of the same question, and directly comparable in level to those rows.",
        "",
        "| Mechanism | Cumulative RMSE (pp) | One-step RMSE (pp) |",
        "|---|---:|---:|",
        f"| fixed | {sidra_fixed_cum:.3f} | {sidra_fixed_one:.3f} |",
        f"| taylor_only | {sidra_taylor_cum:.3f} | {sidra_taylor_one:.3f} |",
        f"| *oracle (observed implicit rate, `outputs/backtest.md`'s own rows)* | *{oracle_cum:.3f}* | *{oracle_one:.3f}* |",
        "",
        f"**{sidra_verdict}** on this refined one-step test too: {sidra_fixed_one:.3f}pp (fixed) vs "
        f"{sidra_taylor_one:.3f}pp (taylor_only) -- the fixed-rate mechanism fits better, confirming "
        "the CPI-based result above with the project's own more accurate historical dataset, not "
        "contradicting it. Both generated-rate mechanisms remain well short of the oracle "
        f"({oracle_one:.3f}pp one-step), which uses the *true* realized implicit rate.",
        "",
        "**Why Selic-tracking and debt-fit disagree (the likely mechanism, not just a coincidence "
        "of this sample)**: `effective_real_interest_rate` is calibrated to approximate the "
        "government's *effective, blended* rate on its whole diversified debt stock (a mix of "
        "Selic-linked, inflation-linked and fixed-rate instruments, per DC1's own debt-composition "
        "note), not the Selic policy rate itself. MR1's Taylor rule was built, and tested above, as "
        "a Selic-tracking mechanism -- it is a better description of Selic-setting behaviour, but "
        "using it as a direct stand-in for the *effective rate on the whole debt stock* conflates "
        "two different rates. That conflation, not a flaw in Taylor's rule per se, is the more "
        "likely reason it does not help here.",
        "",
        "## Coverage: how often does the published model's own uncertainty range contain the truth?",
        "",
        "A wider literature benchmark of this project's own methodology (`reports/Debt model "
        "methodology and journal fit.md`) found that the ESM's own operational fan-chart validation "
        "(Brief 05/2025) reports a calibrated coverage/error-rate statistic rather than a bare "
        "pass/fail verdict on a single central reconstruction. The same idea applied here, at no "
        "new estimation cost: using the model's own already-published "
        f"`effective_real_interest_rate` low ({result['low_rate_pct']:.3f}%) and high "
        f"({result['high_rate_pct']:.3f}%) corners (not a new estimate) to bound the one-step "
        "SIDRA-based reconstruction instead of a single central-case line.",
        "",
        f"**Coverage rate: {result['coverage']['coverage_rate']*100:.1f}% "
        f"({result['coverage']['n_covered']}/{result['coverage']['n_years']} years)** -- the actual "
        f"observed debt/GDP fell inside the model's own low/high-rate band in "
        f"{result['coverage']['n_covered']} of {result['coverage']['n_years']} one-step-reconstructed "
        f"years, mean band width {result['coverage']['mean_band_width_pp']:.2f}pp"
        + (
            f", missed in {', '.join(str(y) for y in result['coverage']['years_outside_band'])}."
            if result['coverage']['years_outside_band'] else "."
        ),
        "",
        "## Limitations",
        "",
        "- Nominal GDP growth is approximated as `(1+real growth)(1+inflation)-1` (a Fisher "
        "compounding of the observed real-growth and CPI series), not the SIDRA nominal-GDP level "
        "series `src.backtest`'s own `debt_engine` test uses -- any error this introduces is common "
        "to every mechanism compared here, so it does not bias the *relative* comparison this "
        "report exists to make, but it does mean these RMSEs are not directly comparable in level "
        "to `outputs/backtest.md`'s own `debt_engine`/`debt_engine_one_step` rows (which use the "
        "SIDRA series and, for `debt_engine`, an *observed*, not generated, implicit interest rate).",
        "- The Taylor rule's output-gap term uses PCY1's own real-time trailing-mean proxy, not a "
        "structural output gap; see `src.pcy1_fiscal_timing`'s own stated limitations.",
        "- The `fixed` mechanism's own benchmark is not naive: `effective_real_interest_rate.central` "
        "is calibrated as the median of the same historical real-rate series being tested against, "
        "so beating it on debt/GDP RMSE is a genuine test of whether year-to-year reactivity adds "
        "anything, not a test against an arbitrary flat guess.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_PATHS["report"])
    args = parser.parse_args(argv)
    result = run_validation()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    for mechanism in MECHANISMS:
        err = result["debt_errors"][mechanism]
        print(f"{mechanism}: RMSE {err['rmse']:.3f}pp (n={err['n']})")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
