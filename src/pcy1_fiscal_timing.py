"""PCY1: historical fiscal-timing (procyclicality) diagnostic.

An independent review of this project's academic paper
(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`) argued the model, being
forward-looking and acyclical, cannot show whether Brazil's past fiscal policy
was itself procyclical -- expansionary while the economy was already running
hot, or contractionary while it was already slack -- and singled out
2011-2014 as a period worth checking. This module answers that question
directly, using only data already in the repository
(`data/brazil/backtest_observed.csv`): it is a pure historical diagnostic,
has no interaction with `src.macro.run_corner` or `src.montecarlo`, and so
cannot change any existing published Monte Carlo output.

Method (deliberately simple and stated plainly, following this project's own
"report the honest finding, even if it complicates the existing narrative"
discipline):

- Output-gap proxy: a real-time, backward-looking proxy -- each year's
  observed GDP growth rate (`gdp_growth_pct`) minus the trailing
  `TREND_WINDOW_YEARS`-year (including the current year) rolling mean of the
  same series. Chosen explicitly over a two-sided (HP or similar) filter to
  avoid end-of-sample revision; the acknowledged cost is that it lags during
  a structural acceleration or deceleration.
- Fiscal impulse: the year-over-year change in the primary balance
  (`primary_result_pct_gdp`), sign-flipped so a *positive* impulse means
  *expansionary* (balance falling) and a *negative* impulse means
  *contractionary* (balance rising).
- Classification: `procyclical_expansionary` (expansionary impulse while the
  gap is already positive), `procyclical_contractionary` (contractionary
  impulse while the gap is already negative), `countercyclical` (the
  opposite pairings), or `broadly_neutral` (|impulse| below
  `NEUTRAL_IMPULSE_THRESHOLD_PP`).

This is not a structural/cyclically-adjusted balance in the OECD/IMF sense
(no output-elasticity-of-revenue correction is applied); it is a transparent,
stated proxy answering the specific question the review raised, not a
replacement for a proper structural-balance estimate.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_PATHS = {
    "observed": Path("data/brazil/backtest_observed.csv"),
    "report": Path("outputs/fiscal_timing_diagnostic.md"),
}

TREND_WINDOW_YEARS = 5
NEUTRAL_IMPULSE_THRESHOLD_PP = 0.1


def load_series(observed_path: Path = DEFAULT_PATHS["observed"]) -> pd.DataFrame:
    """Return a year-indexed frame of gdp_growth_pct and primary_balance_pct_gdp.

    ``backtest_observed.csv``'s ``primary_result_pct_gdp`` (BCB SGS 5793) is a
    *borrowing requirement*, not a balance: its own label states "negative =
    surplus". We negate it immediately into a conventional, surplus-positive
    ``primary_balance_pct_gdp`` (matching how the rest of this project, e.g.
    ``src.macro``'s ``primary_balance_gdp``, defines the primary balance) so
    every downstream calculation in this module uses the familiar sign.
    """
    raw = pd.read_csv(observed_path)
    wide = raw.pivot(index="year", columns="indicator", values="value")
    frame = wide[["gdp_growth_pct", "primary_result_pct_gdp"]].dropna(how="all")
    frame.index = frame.index.astype(int)
    frame["primary_balance_pct_gdp"] = -frame.pop("primary_result_pct_gdp")
    return frame.sort_index()


def compute_gap_and_impulse(
    frame: pd.DataFrame, trend_window_years: int = TREND_WINDOW_YEARS
) -> pd.DataFrame:
    """Add an output-gap proxy and a sign-flipped fiscal-impulse column."""
    out = frame.copy()
    out["trend_growth_pct"] = (
        out["gdp_growth_pct"].rolling(trend_window_years, min_periods=trend_window_years).mean()
    )
    out["output_gap_proxy_pp"] = out["gdp_growth_pct"] - out["trend_growth_pct"]
    out["fiscal_impulse_pp"] = -out["primary_balance_pct_gdp"].diff()
    return out


def classify_year(
    output_gap_proxy_pp: float,
    fiscal_impulse_pp: float,
    neutral_impulse_threshold_pp: float = NEUTRAL_IMPULSE_THRESHOLD_PP,
) -> str:
    if pd.isna(output_gap_proxy_pp) or pd.isna(fiscal_impulse_pp):
        return "not_classified"
    if abs(fiscal_impulse_pp) < neutral_impulse_threshold_pp:
        return "broadly_neutral"
    if fiscal_impulse_pp > 0 and output_gap_proxy_pp > 0:
        return "procyclical_expansionary"
    if fiscal_impulse_pp < 0 and output_gap_proxy_pp < 0:
        return "procyclical_contractionary"
    return "countercyclical"


def classify(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["classification"] = [
        classify_year(row.output_gap_proxy_pp, row.fiscal_impulse_pp) for row in out.itertuples()
    ]
    return out


def render_report(frame: pd.DataFrame) -> str:
    classified = frame.dropna(subset=["output_gap_proxy_pp", "fiscal_impulse_pp"])
    procyclical_years = classified.loc[
        classified["classification"].isin(["procyclical_expansionary", "procyclical_contractionary"])
    ]

    def fmt(value: float) -> str:
        return "n.a." if pd.isna(value) else f"{value:+.2f}"

    lines = [
        "# PCY1: historical fiscal-timing (procyclicality) diagnostic",
        "",
        "Built in direct response to an independent review of this project's academic paper "
        "(`paper/Reviewer/Brazil_Fiscal_Model_Review.pdf`), which argued the forward-looking "
        "scenario model cannot show whether past Brazilian fiscal policy was itself "
        "procyclical. This is a pure historical diagnostic: it reads only "
        "`data/brazil/backtest_observed.csv`, has no interaction with `src.montecarlo` or "
        "`src.macro.run_corner`, and cannot change any existing published Monte Carlo output.",
        "",
        "**Method** (stated plainly; not a structural/cyclically-adjusted balance in the "
        "OECD/IMF sense): a real-time, backward-looking output-gap proxy (observed GDP growth "
        f"minus its own trailing {TREND_WINDOW_YEARS}-year rolling mean, a one-sided choice "
        "made explicitly to avoid the end-of-sample revision a two-sided HP-style filter would "
        "introduce, at the acknowledged cost of lagging during a structural acceleration or "
        "deceleration), and a sign-flipped year-over-year change in the primary balance as the "
        f"fiscal-impulse measure (impulses inside ±{NEUTRAL_IMPULSE_THRESHOLD_PP}pp are "
        "reported as broadly neutral rather than forced into a cyclical category).",
        "",
        "## Year-by-year classification",
        "",
        "| Year | GDP growth (%) | Trailing trend (%) | Output-gap proxy (pp) | "
        "Primary balance (% GDP, surplus positive) | Fiscal impulse (pp) | Classification |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in frame.itertuples():
        lines.append(
            f"| {row.Index} | {fmt(row.gdp_growth_pct)} | {fmt(row.trend_growth_pct)} | "
            f"{fmt(row.output_gap_proxy_pp)} | {fmt(row.primary_balance_pct_gdp)} | "
            f"{fmt(row.fiscal_impulse_pp)} | {row.classification} |"
        )
    lines += ["", "## Reading the 2011-2014 period the review singled out", ""]
    review_years = classified.loc[classified.index.isin([2011, 2012, 2013, 2014])]
    if len(review_years):
        by_year = "; ".join(f"{int(y)}: {c}" for y, c in review_years["classification"].items())
        n_proc = review_years["classification"].isin(
            ["procyclical_expansionary", "procyclical_contractionary"]
        ).sum()
        n_counter = review_years["classification"].eq("countercyclical").sum()
        lines.append(f"Year by year on this proxy -- {by_year}.")
        lines.append("")
        if n_proc and n_proc == len(review_years):
            lines.append(
                "Every year in 2011-2014 classifies as procyclical on this proxy, directly "
                "consistent with the review's reading of the period as a whole."
            )
        elif n_proc == 0:
            lines.append(
                "No year in 2011-2014 classifies as procyclical on this proxy -- the review's "
                "qualitative reading of the period as fiscally procyclical is not confirmed "
                "here, which is itself a finding worth taking seriously rather than suppressing "
                "because it complicates the critique."
            )
        else:
            lines.append(
                f"The period is mixed on this proxy: {n_proc} of {len(review_years)} years "
                f"classify as procyclical and {n_counter} as countercyclical, so the review's "
                "characterisation of 2011-2014 as a whole as procyclical is only partly borne "
                "out -- this proxy's more precise reading should be taken over the review's "
                "broader-brush one where they disagree, since the review did not itself compute "
                "a year-by-year series."
            )
    else:
        lines.append("Insufficient data to classify 2011-2014 on this proxy.")
    lines += ["", "## All years classified procyclical", ""]
    if len(procyclical_years):
        for year, row in procyclical_years.iterrows():
            lines.append(
                f"- {int(year)}: {row['classification']} (output-gap proxy "
                f"{row['output_gap_proxy_pp']:+.2f}pp, fiscal impulse "
                f"{row['fiscal_impulse_pp']:+.2f}pp)"
            )
    else:
        lines.append("No year in the available sample classifies as procyclical on this proxy.")
    lines += [
        "",
        "## Limitations",
        "",
        "- This is a proxy output gap (trailing realised-growth deviation), not a structural/"
        "potential-GDP-based output gap; it will systematically lag true turning points.",
        "- The fiscal impulse uses the headline primary balance, not one adjusted for one-off "
        "items (e.g. the 2021-2022 commodity-revenue windfalls already flagged in "
        "`data/brazil/fiscal_delivery.csv`), so part of a measured impulse may reflect revenue "
        "surprises rather than discretionary policy.",
        "- The classification thresholds (five-year trailing window, "
        f"±{NEUTRAL_IMPULSE_THRESHOLD_PP}pp neutral band) are stated choices, not "
        "estimated or optimised; a different reasonable choice could relabel a small number of "
        "close-to-threshold years.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed", type=Path, default=DEFAULT_PATHS["observed"])
    parser.add_argument("--report", type=Path, default=DEFAULT_PATHS["report"])
    parser.add_argument("--trend-window-years", type=int, default=TREND_WINDOW_YEARS)
    args = parser.parse_args(argv)
    frame = load_series(args.observed)
    frame = compute_gap_and_impulse(frame, args.trend_window_years)
    frame = classify(frame)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(frame), encoding="utf-8")
    print(frame.to_string(float_format=lambda v: f"{v:.3f}"))
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
