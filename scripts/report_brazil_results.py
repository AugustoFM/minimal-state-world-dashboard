"""Build the internal Brazil Monte Carlo results report from committed files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "outputs/runs/summary_percentiles.csv"
METADATA_PATH = ROOT / "outputs/runs/run_metadata.json"
BACKTEST_PATH = ROOT / "outputs/backtest.md"
SCENARIOS_PATH = ROOT / "config/scenarios.yaml"
OUTPUT_PATH = ROOT / "outputs/results_brazil.md"

HEADLINE_INDICATORS = (
    "gdp_level_vs_s0_pct",
    "gdp_level_vs_s0_pct_with_feedback",
    "unemployment_change_pp",
    "debt_gdp_vs_s0_pp",
    "debt_gdp_with_feedback_vs_s0_pp",
    "infant_mortality_difference_vs_s0",
    "life_expectancy_difference_vs_s0_years",
    "gini_change_vs_s0_points",
    "poverty_218_change_vs_s0_pp",
    "poverty_759_change_vs_s0_pp",
    "poverty_218_age_0_14_change_vs_s0_pp",
    "poverty_218_age_65_plus_change_vs_s0_pp",
    "poverty_218_with_65_plus_recipient_change_vs_s0_pp",
    "poverty_759_age_0_14_change_vs_s0_pp",
    "poverty_759_age_65_plus_change_vs_s0_pp",
    "poverty_759_with_65_plus_recipient_change_vs_s0_pp",
)

LABELS = {
    "gdp_level_vs_s0_pct": "GDP level vs S0 (%)",
    "gdp_level_vs_s0_pct_with_feedback": "GDP level vs S0, with C5 feedback (%)",
    "unemployment_change_pp": "Unemployment change vs S0 (pp)",
    "debt_gdp_vs_s0_pp": "Debt/GDP vs S0 (pp)",
    "debt_gdp_with_feedback_vs_s0_pp": "Debt/GDP vs S0, with C5 feedback (pp)",
    "infant_mortality_difference_vs_s0": "Infant mortality difference vs S0 (per 1,000)",
    "life_expectancy_difference_vs_s0_years": "Life expectancy difference vs S0 (years)",
    "gini_change_vs_s0_points": "Gini change vs S0 (points)",
    "poverty_218_change_vs_s0_pp": "Poverty below R$218 change vs S0 (pp)",
    "poverty_759_change_vs_s0_pp": "Poverty below R$759 change vs S0 (pp)",
    "poverty_218_age_0_14_change_vs_s0_pp": "Poverty below R$218, age 0-14, change vs S0 (pp)",
    "poverty_218_age_65_plus_change_vs_s0_pp": "Poverty below R$218, age 65+, change vs S0 (pp)",
    "poverty_218_with_65_plus_recipient_change_vs_s0_pp": "Poverty below R$218, living with a 65+ pension/BPC recipient, change vs S0 (pp)",
    "poverty_759_age_0_14_change_vs_s0_pp": "Poverty below R$759, age 0-14, change vs S0 (pp)",
    "poverty_759_age_65_plus_change_vs_s0_pp": "Poverty below R$759, age 65+, change vs S0 (pp)",
    "poverty_759_with_65_plus_recipient_change_vs_s0_pp": "Poverty below R$759, living with a 65+ pension/BPC recipient, change vs S0 (pp)",
    "debt_gdp": "Debt/GDP level (%)",
    "debt_gdp_with_feedback": "Debt/GDP level with C5 feedback (%)",
}

DECIMALS = {
    "gdp_level_vs_s0_pct": 2,
    "gdp_level_vs_s0_pct_with_feedback": 2,
    "unemployment_change_pp": 2,
    "debt_gdp_vs_s0_pp": 1,
    "debt_gdp_with_feedback_vs_s0_pp": 1,
    "infant_mortality_difference_vs_s0": 3,
    "life_expectancy_difference_vs_s0_years": 3,
    "gini_change_vs_s0_points": 3,
    "poverty_218_change_vs_s0_pp": 2,
    "poverty_759_change_vs_s0_pp": 2,
    "poverty_218_age_0_14_change_vs_s0_pp": 2,
    "poverty_218_age_65_plus_change_vs_s0_pp": 2,
    "poverty_218_with_65_plus_recipient_change_vs_s0_pp": 2,
    "poverty_759_age_0_14_change_vs_s0_pp": 2,
    "poverty_759_age_65_plus_change_vs_s0_pp": 2,
    "poverty_759_with_65_plus_recipient_change_vs_s0_pp": 2,
    "debt_gdp": 1,
    "debt_gdp_with_feedback": 1,
}


def _markdown_rows(text: str) -> dict[str, list[str]]:
    """Return markdown table rows keyed by their first cell."""
    rows: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and cells[0] and not set(cells[0]) <= {"-", ":"}:
            rows[cells[0]] = cells
    return rows


def parse_backtest(backtest: str) -> dict[str, float | str]:
    """Read the gate and requested diagnostics from the committed report text."""
    gate_match = re.search(r"Overall proposed gate:\s*(PASS|FAIL)", backtest)
    if not gate_match:
        raise ValueError("Could not find the D2 gate verdict in the backtest report")
    tier1 = re.search(r"Tier 1 - differences vs S0:\s*(PASS|FAIL)", backtest)
    tier2 = re.search(r"Tier 2 - debt/GDP levels:\s*(PASS|FAIL)", backtest)
    rows = _markdown_rows(backtest)
    debt_start_match = re.search(r"recursion starts from observed (\d{4})", backtest)
    debt_end_match = re.search(r"absolute (\d{4}) debt error", backtest)
    boom_years_match = re.search(r"measures the (\d{4})-(\d{4}) transitions", backtest)
    if not (debt_start_match and debt_end_match and boom_years_match):
        raise ValueError("Could not read diagnostic year ranges from the backtest report")
    try:
        debt_one_step_mean = float(rows["debt_engine_one_step"][1])
        debt_cumulative = float(rows["debt_engine"][5])
        boom = rows["commodity boom (2005 base to 2010; 2003-04 unavailable because ToT starts in 2005)"]
        boom_actual = float(boom[1].rstrip("%"))
        boom_external = float(boom[3].replace("pp", "").replace("+", "").strip())
    except (KeyError, IndexError, ValueError) as exc:
        raise ValueError("Could not read required diagnostics from the backtest tables") from exc
    return {
        "gate": gate_match.group(1),
        "tier1": tier1.group(1) if tier1 else None,
        "tier2": tier2.group(1) if tier2 else None,
        "debt_one_step_mean": debt_one_step_mean,
        "debt_cumulative": debt_cumulative,
        "debt_start_year": debt_start_match.group(1),
        "debt_end_year": debt_end_match.group(1),
        "boom_actual": boom_actual,
        "boom_external": boom_external,
        "boom_start_year": boom_years_match.group(1),
        "boom_end_year": boom_years_match.group(2),
    }


def validate_summary(summary: pd.DataFrame, metadata: dict[str, Any]) -> None:
    required = {
        "variant", "persistence", "scenario", "horizon", "year", "indicator",
        "p10", "p50", "p90", "n_draws", "status",
    }
    missing = required - set(summary.columns)
    if missing:
        raise ValueError(f"Summary is missing columns: {sorted(missing)}")
    keys = ["variant", "persistence", "scenario", "horizon", "indicator"]
    if summary.duplicated(keys).any():
        raise ValueError("Summary has duplicate result keys")
    modelled = summary["status"].str.startswith("modelled")
    if summary.loc[modelled, ["p10", "p50", "p90"]].isna().any().any():
        raise ValueError("A modelled summary row has a missing percentile")
    if ((summary.loc[modelled, "p10"] > summary.loc[modelled, "p50"]) |
            (summary.loc[modelled, "p50"] > summary.loc[modelled, "p90"])).any():
        raise ValueError("Summary percentiles are not ordered")
    if set(summary["n_draws"]) != {metadata["n_draws"]}:
        raise ValueError("Summary draw counts do not match metadata")


def format_cell(row: pd.Series, indicator: str) -> str:
    if pd.isna(row["p50"]):
        return "not modelled"
    decimals = DECIMALS[indicator]
    values = [float(row[column]) for column in ("p50", "p10", "p90")]
    rendered = [f"{value:.{decimals}f}" for value in values]
    return f"{rendered[0]} [{rendered[1]}, {rendered[2]}]"


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(row) + " |" for row in rows),
    ]


def _scalar(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def scenario_table(summary: pd.DataFrame, config: dict[str, Any]) -> list[str]:
    present = set(summary["scenario"])
    rows: list[list[str]] = []
    for code, definition in config["scenarios"].items():
        if code not in present:
            continue
        by_year = definition.get("by_year")
        path = (
            "; ".join(f"{year}y: {_scalar(value)} pp" for year, value in by_year.items())
            if by_year else "not specified"
        )
        direction = definition.get("direction")
        if direction is None and code.startswith("R_"):
            direction = "below_S0"
        elif direction is None and code == "S0":
            direction = "baseline"
        elif direction is None and code == "S1":
            direction = "constant_size"
        financing = definition.get("financing", "not specified")
        details = definition.get("description", definition.get("name", ""))
        rows.append([
            code,
            str(details).replace("|", "\\|"),
            path,
            str(direction).replace("_", " "),
            str(financing),
        ])
    absent = present - set(config["scenarios"])
    if absent:
        raise ValueError(f"CSV scenarios are absent from scenarios.yaml: {sorted(absent)}")
    return _table(["Scenario", "Definition", "By-year path vs S0", "Direction", "Financing"], rows)


def _select_one(summary: pd.DataFrame, **filters: Any) -> pd.Series:
    selected = summary
    for column, value in filters.items():
        selected = selected[selected[column].eq(value)]
    if len(selected) != 1:
        raise ValueError(f"Expected one result for {filters}, found {len(selected)}")
    return selected.iloc[0]


def result_table(
    summary: pd.DataFrame,
    indicator: str,
    scenarios: list[str],
    horizons: list[int],
    *,
    variant: str = "default",
) -> list[str]:
    rows: list[list[str]] = []
    for scenario in scenarios:
        for persistence in ("transitory", "persistent"):
            cells = [
                format_cell(_select_one(
                    summary, variant=variant, persistence=persistence,
                    scenario=scenario, horizon=horizon, indicator=indicator,
                ), indicator)
                for horizon in horizons
            ]
            rows.append([scenario, persistence, *cells])
    years = [str(int(_select_one(
        summary, variant=variant, persistence="transitory", scenario=scenarios[0],
        horizon=horizon, indicator=indicator,
    )["year"])) for horizon in horizons]
    return _table(["Scenario", "Persistence", *years], rows)


def levels_tables(
    summary: pd.DataFrame, scenarios: list[str], horizons: list[int]
) -> list[str]:
    lines: list[str] = []
    for persistence in ("transitory", "persistent"):
        lines.extend([f"### {persistence.capitalize()}", ""])
        headers = ["Scenario"]
        for horizon in horizons:
            year = int(_select_one(
                summary, variant="default", persistence=persistence,
                scenario=scenarios[0], horizon=horizon, indicator="debt_gdp",
            )["year"])
            headers.extend([f"{year} debt", f"{year} with feedback"])
        rows: list[list[str]] = []
        for scenario in scenarios:
            cells: list[str] = []
            for horizon in horizons:
                for indicator in ("debt_gdp", "debt_gdp_with_feedback"):
                    result = _select_one(
                        summary, variant="default", persistence=persistence,
                        scenario=scenario, horizon=horizon, indicator=indicator,
                    )
                    cells.append(format_cell(result, indicator))
            rows.append([scenario, *cells])
        lines.extend([*_table(headers, rows), ""])
    return lines


def composition_tables(summary: pd.DataFrame, variants: list[str]) -> list[str]:
    indicators = (
        "gdp_level_vs_s0_pct",
        "infant_mortality_difference_vs_s0",
        "debt_gdp_vs_s0_pp",
    )
    lines: list[str] = []
    for persistence in ("transitory", "persistent"):
        lines.extend([f"### {persistence.capitalize()}", ""])
        rows: list[list[str]] = []
        for scenario in ("R_mod", "R_amb"):
            for horizon in (10, 20):
                for variant in variants:
                    cells = [format_cell(_select_one(
                        summary, variant=variant, persistence=persistence,
                        scenario=scenario, horizon=horizon, indicator=indicator,
                    ), indicator) for indicator in indicators]
                    rows.append([scenario, str(horizon), variant, *cells])
        lines.extend([*_table(
            ["Scenario", "Horizon (years)", "Variant", "GDP vs S0 (%)",
             "Infant mortality vs S0 (per 1,000)", "Debt/GDP vs S0 (pp)"],
            rows,
        ), ""])
    return lines


def crossing_lines(summary: pd.DataFrame, scenarios: list[str]) -> list[str]:
    lines: list[str] = []
    data = summary[
        summary["variant"].eq("default")
        & summary["horizon"].eq(20)
        & summary["indicator"].isin(HEADLINE_INDICATORS)
        & summary["scenario"].isin(scenarios)
        & summary["p10"].notna()
    ]
    for scenario in scenarios:
        parts: list[str] = []
        for persistence in ("transitory", "persistent"):
            selected = data[
                data["scenario"].eq(scenario)
                & data["persistence"].eq(persistence)
                & data["p10"].le(0)
                & data["p90"].ge(0)
            ]
            names = [LABELS[name] for name in HEADLINE_INDICATORS
                     if name in set(selected["indicator"])]
            parts.append(f"{persistence}: {', '.join(names) if names else 'none'}")
        lines.append(f"- `{scenario}` — " + "; ".join(parts) + ".")
    return lines


def build_report(
    summary_path: Path = SUMMARY_PATH,
    metadata_path: Path = METADATA_PATH,
    backtest_path: Path = BACKTEST_PATH,
    scenarios_path: Path = SCENARIOS_PATH,
) -> str:
    summary = pd.read_csv(summary_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    backtest_text = backtest_path.read_text(encoding="utf-8")
    config = yaml.safe_load(scenarios_path.read_text(encoding="utf-8"))
    validate_summary(summary, metadata)
    diagnostics = parse_backtest(backtest_text)

    horizons = [5, 10, 20]
    scenario_order = [name for name in config["scenarios"] if name in set(summary["scenario"])]
    vs_s0_scenarios = [name for name in scenario_order if name != "S0"]
    choices = "; ".join(metadata["choices"])
    not_modelled = metadata.get("not_modelled", {})
    not_modelled_text = json.dumps(not_modelled, sort_keys=True) if not_modelled else "none listed"
    summary_not_modelled = int(summary["status"].str.startswith("not_modelled").sum())

    lines = [
        "# Brazil scenario results",
        "",
        (f"**Internal review - not for publication: D2 gate v2 - Tier 1 (differences vs S0) {diagnostics['tier1']}, "
         f"Tier 2 (debt/GDP levels) {diagnostics['tier2']}**"
         if diagnostics.get("tier1") else
         f"**Internal review - not for publication: D2 gate {diagnostics['gate']}**"),
        "",
        f"Run seed: `{metadata['seed']}`  ",
        f"Draws: `{metadata['n_draws']}`  ",
        f"Inputs commit: `{metadata['inputs_commit']}`  ",
        f"Created: `{metadata['created_utc']}`  ",
        "D2 verdict and diagnostics: parsed from `outputs/backtest.md`",
        "",
        "## How to read",
        "",
        "Each cell is p50 [p10, p90] across parameter draws. Differences against S0 are paired within each draw. "
        f"The percentiles describe parameter uncertainty only: {choices}. Persistence settings are shown separately. "
        "S0 is a no-policy-change ageing baseline, not a forecast.",
        "",
        "## Scenarios",
        "",
        *scenario_table(summary, config),
        "",
        "## Headline results",
        "",
        "Variant: `default`. S0 is excluded because these indicators are differences against S0. "
        "A missing cell is labelled `not modelled`.",
        "",
    ]
    available = set(summary["indicator"])
    for indicator in (name for name in HEADLINE_INDICATORS if name in available):
        lines.extend([
            f"### {LABELS[indicator]}",
            "",
            *result_table(summary, indicator, vs_s0_scenarios, horizons),
            "",
        ])

    one_step = float(diagnostics["debt_one_step_mean"])
    cumulative = float(diagnostics["debt_cumulative"])
    lines.extend([
        "## Debt/GDP levels",
        "",
        f"**Caution:** these levels carry the D2 debt-engine bias: one-step mean {one_step:+.2f} pp/year "
        f"and cumulative {cumulative:+.1f} pp over {diagnostics['debt_start_year']}-"
        f"{diagnostics['debt_end_year']}. Levels explode in S0 because of the C5 risk "
        "premium; differences against S0 are the meaningful quantity.",
        "",
        *levels_tables(summary, scenario_order, horizons),
        "## Composition variants",
        "",
        f"All {len(metadata['variants'])} committed variants are shown. C3 distribution indicators exist only for "
        "the `default` composition, so they are not included in this cross-variant table.",
        "",
        *composition_tables(summary, metadata["variants"]),
        "## Caveats",
        "",
        "At the 20-year horizon, the following default-variant p10-p90 intervals include zero "
        "(listed by scenario and persistence):",
        "",
        *crossing_lines(summary, vs_s0_scenarios),
        "",
        f"The D2 backtest showed the C6 external block explained about "
        f"{float(diagnostics['boom_external']):.1f} pp of the {float(diagnostics['boom_actual']):.0f}% "
        f"{diagnostics['boom_start_year']}-{diagnostics['boom_end_year']} boom; the runs now use C7 channel A "
        "(commodity prices), which out of sample reproduces about 59% of it (`outputs/c7_backtest.md`). "
        "External paths, commodity-linked dividends and the G2 corruption shock are common to every scenario.",
        "",
        f"Metadata `not_modelled`: {not_modelled_text}. The summary separately contains "
        f"{summary_not_modelled:,} rows explicitly marked not modelled: C3 distribution results are available "
        "only for the `default` composition and exclude S1 because it has no package allocation.",
        "",
        "The report compares policy scenarios; no candidate or party appears in it.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--metadata", type=Path, default=METADATA_PATH)
    parser.add_argument("--backtest", type=Path, default=BACKTEST_PATH)
    parser.add_argument("--scenarios", type=Path, default=SCENARIOS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.summary, args.metadata, args.backtest, args.scenarios)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
