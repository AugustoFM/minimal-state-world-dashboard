"""Figures for `paper/minimum_state_brazil.tex`, built from already-published output only.

Three figures, reusing data this project already computes and already cites in the paper's own
text -- no new Monte Carlo run, no new historical analysis:

1. `debt_fan.pdf` -- debt/GDP-vs-S0 parameter-uncertainty bands (median, p10-p90) for the four
   headline scenarios, at the model's own four reporting horizons (5/10/15/20 years). Data:
   `outputs/runs/summary_percentiles.csv` (`variant=default`, `persistence=transitory`,
   `indicator=debt_gdp_vs_s0_pp`), the same cells `tab:headline` already reports in text.
2. `gini_fan.pdf` -- the same layout for `gini_change_vs_s0_points`.
3. `backtest_fit.pdf` -- the Section 5 Tier-2 back-test: observed debt/GDP 2017-2024 against the
   zero-correction and stock-flow-adjustment-corrected reconstructions. Data:
   `src.backtest.sfa_out_of_sample`, the exact function already producing the 16.1pp/12.5pp
   overshoot figures Section 5's prose cites.

Deliberately NOT a continuous time-path fan chart: the model reports percentiles only at its four
named horizons, not an annual series, so plotting anything smoother than four discrete,
clearly-marked points would imply resolution the data does not have. Each panel is explicitly
labelled "parameter-uncertainty band, not a forecast interval" in its caption text (written into
the LaTeX, not this script), echoing the paper's own existing language (Section 6).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.backtest import DEFAULT_PATHS as BACKTEST_PATHS
from src.backtest import debt_test_inputs, observed_wide, sfa_out_of_sample

DEFAULT_PATHS = {
    "summary": Path("outputs/runs/summary_percentiles.csv"),
    "out_dir": Path("paper/figures"),
}
HORIZONS = (5, 10, 15, 20)
SCENARIOS = ("R_mod", "R_amb", "E_mod", "E_amb")
SCENARIO_LABELS = {
    "R_mod": "R_mod (moderate cut)", "R_amb": "R_amb (ambitious cut)",
    "E_mod": "E_mod (moderate rise)", "E_amb": "E_amb (ambitious rise)",
}
# Two hue families (reduction = blue, expansion = orange), lighter tint for the moderate variant,
# full/darker tone for the ambitious one -- the pairing carries the reduction/expansion polarity,
# the shade carries the moderate/ambitious intensity, matching this scenario grid's own structure
# rather than treating four scenarios as unrelated categorical identities.
SCENARIO_COLORS = {
    "R_mod": "#6da7ec", "R_amb": "#184f95",
    "E_mod": "#f0a37e", "E_amb": "#b84f1f",
}


def load_horizon_percentiles(
    indicator: str, summary_path: Path = DEFAULT_PATHS["summary"],
    variant: str = "default", persistence: str = "transitory",
) -> pd.DataFrame:
    """Median/p10/p90 of `indicator` by scenario and horizon, for the four headline scenarios."""
    data = pd.read_csv(summary_path)
    mask = (
        data["variant"].eq(variant) & data["persistence"].eq(persistence)
        & data["indicator"].eq(indicator) & data["scenario"].isin(SCENARIOS)
        & data["horizon"].isin(HORIZONS)
    )
    out = data.loc[mask, ["scenario", "horizon", "p10", "p50", "p90"]].sort_values(["scenario", "horizon"])
    if len(out) != len(SCENARIOS) * len(HORIZONS):
        raise ValueError(f"Expected {len(SCENARIOS) * len(HORIZONS)} rows for {indicator!r}, got {len(out)}")
    return out.reset_index(drop=True)


def _panel(ax, group: pd.DataFrame, scenario: str, ylabel: str) -> None:
    ordered = group.sort_values("horizon")
    color = SCENARIO_COLORS[scenario]
    ax.axhline(0.0, color="#c3c2b7", linewidth=1.0, zorder=1)
    ax.fill_between(ordered["horizon"], ordered["p10"], ordered["p90"], color=color, alpha=0.25, zorder=2)
    ax.plot(ordered["horizon"], ordered["p50"], color=color, linewidth=2.0, marker="o", markersize=4, zorder=3)
    ax.set_title(SCENARIO_LABELS[scenario], fontsize=9)
    ax.set_xticks(HORIZONS)
    ax.set_xlabel("Horizon (years)", fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def build_scenario_grid(indicator: str, ylabel: str, out_path: Path) -> None:
    percentiles = load_horizon_percentiles(indicator)
    fig, axes = plt.subplots(2, 2, figsize=(6.0, 5.0), sharex=True)
    for ax, scenario in zip(axes.flat, SCENARIOS):
        group = percentiles.loc[percentiles["scenario"].eq(scenario)]
        _panel(ax, group, scenario, ylabel)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def build_backtest_figure(out_path: Path) -> None:
    wide = observed_wide(BACKTEST_PATHS["observed"])
    inputs = debt_test_inputs(wide, BACKTEST_PATHS["workbook"], BACKTEST_PATHS["nominal_gdp"])
    recursion, _ = sfa_out_of_sample(inputs)
    fig, ax = plt.subplots(figsize=(5.0, 3.6))
    ax.plot(recursion["year"], recursion["observed_debt_gdp"], color="#0b0b0b", linewidth=2.0,
            marker="o", markersize=4, label="Observed", zorder=3)
    ax.plot(recursion["year"], recursion["zero_sfa_debt_gdp"], color="#e34948", linewidth=1.6,
            linestyle="--", marker="s", markersize=3, label="Model, no correction", zorder=2)
    ax.plot(recursion["year"], recursion["with_sfa_debt_gdp"], color="#1baf7a", linewidth=1.6,
            linestyle="--", marker="^", markersize=3, label="Model, with stock-flow correction", zorder=2)
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Gross general-government debt (% of GDP)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=7, frameon=False, loc="best")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_PATHS["out_dir"])
    args = parser.parse_args(argv)
    build_scenario_grid(
        "debt_gdp_vs_s0_pp", "Debt/GDP vs. S0 (pp)", args.out_dir / "debt_fan.pdf",
    )
    build_scenario_grid(
        "gini_change_vs_s0_points", "Gini vs. S0 (points)", args.out_dir / "gini_fan.pdf",
    )
    build_backtest_figure(args.out_dir / "backtest_fit.pdf")
    print(f"Wrote 3 figures to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
