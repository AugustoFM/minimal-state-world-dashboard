from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import yaml

from src import programs
from src.macro import build_spending_paths

CONFIG = yaml.safe_load(open("config/programs_2026.yaml", encoding="utf-8"))
PARAMETERS = yaml.safe_load(open("config/parameters.yaml", encoding="utf-8"))


def synthetic_s0(years=range(2025, 2036), growth=0.02, inflation=0.03, interest=0.08) -> pd.DataFrame:
    rows = []
    for k, year in enumerate(years):
        spending = 40.0 + 0.3 * k
        rows.append({
            "year": year, "spending_pct_gdp": spending, "real_gdp": 100 * (1 + growth) ** k,
            "real_growth": np.nan if k == 0 else growth,
            "nominal_growth": np.nan if k == 0 else (1 + growth) * (1 + inflation) - 1,
            "interest": interest, "revenue_gdp": 39.0, "primary_balance_gdp": 39.0 - spending,
            "debt_gdp": 80.0,
        })
    return pd.DataFrame(rows)


def draw(**overrides) -> dict:
    values = {
        "lula_transfers_pp": 0.0, "lula_revenue_pp": 0.0,
        "flavio_revenue_pp": 0.0, "flavio_privatisation_pp": 0.0, "flavio_new_programmes_pp": 0.0,
        "delivery_bias_pp": 0.0,
    }
    values.update(overrides)
    return values


def total(definition: dict, horizon: int) -> float:
    return sum(programs.package_gaps(definition, horizon).values())


MODEL = CONFIG["model_parameters"]


def test_every_programme_scenario_is_built_and_nothing_changes_before_the_term() -> None:
    defs = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw(lula_revenue_pp=0.5, flavio_revenue_pp=-1))
    assert set(defs) == set(programs.PROGRAMMES)
    for definition in defs.values():
        assert total(definition, 1) == 0.0
        assert definition["revenue_by_year"][1] == 0.0


def test_lc200_rule_grows_federal_spending_at_70_percent_of_revenue_growth() -> None:
    s0 = synthetic_s0()
    defs = programs.build_programme_scenarios(s0, CONFIG, draw())
    share = MODEL["federal_share_of_general_government_primary"]["value"]
    federal = share * 40.3  # 2026 S0 spending
    for year in range(2027, 2031):
        federal *= 1.014 / 1.02  # 0.7 x 2% real revenue growth, deflated by 2% GDP growth
        expected = share * float(s0.set_index("year").loc[year, "spending_pct_gdp"]) - federal
        assert total(defs["P_lula_rule"], year - 2025) == pytest.approx(expected)
    assert total(defs["P_lula_rule"], 10) == pytest.approx(total(defs["P_lula_rule"], 5))


def test_lc200_floor_binds_when_growth_is_low() -> None:
    defs = programs.build_programme_scenarios(synthetic_s0(growth=0.0), CONFIG, draw())
    share = MODEL["federal_share_of_general_government_primary"]["value"]
    assert total(defs["P_lula_rule"], 2) == pytest.approx(share * 40.6 - share * 40.3 * 1.006)


def test_lula_record_continues_the_2022_2025_trends() -> None:
    defs = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw(delivery_bias_pp=0.25))
    record = MODEL["lula_record_trend"]
    spending, tax = record["spending_pp_gdp_per_year"]["value"], record["tax_revenue_pp_gdp_per_year"]["value"]
    # synthetic S0 rises 0.3 pp a year; the record trend is above it, so the gap is negative; no bias added
    assert total(defs["P_lula_record"], 5) == pytest.approx(0.3 * 4 - spending * 4)
    assert defs["P_lula_record"]["revenue_by_year"][5] == pytest.approx(tax * 4)
    assert total(defs["P_lula_record"], 10) == pytest.approx(total(defs["P_lula_record"], 5))


def test_flavio_cut_scenarios_reach_their_sizes_by_the_end_of_the_term() -> None:
    defs = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw(flavio_revenue_pp=-0.8))
    for name, scenario in MODEL["flavio_cut_scenarios"].items():
        if not isinstance(scenario, dict):
            continue
        definition = defs[f"P_flavio_{name}"]
        assert total(definition, 5) == pytest.approx(scenario["cut_pp_gdp_by_end_of_term"])
        assert total(definition, 3) == pytest.approx(scenario["cut_pp_gdp_by_end_of_term"] / 2)
        assert definition["revenue_by_year"][5] == pytest.approx(-0.8)
    mid = programs.package_gaps(defs["P_flavio_mid"], 5)
    assert mid["pension_and_indexation"] == pytest.approx(0.5 * 1.5)


def test_new_programmes_are_financed_inside_the_cut() -> None:
    base = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw())
    extra = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw(flavio_new_programmes_pp=0.3))
    services = "efficiency_health_education_admin"
    for name in ("low", "high"):
        key = f"P_flavio_{name}"
        assert total(extra[key], 5) == pytest.approx(total(base[key], 5))
        share = MODEL["flavio_cut_scenarios"][name]["composition"][services]
        expected = (total(base[key], 5) + 0.3) * share - 0.3
        assert programs.package_gaps(extra[key], 5)[services] == pytest.approx(expected)


def test_privatisation_retires_debt_over_the_term_only() -> None:
    defs = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw(flavio_privatisation_pp=2.0))
    path = defs["P_flavio_mid"]["debt_adjustment_by_year"]
    assert sum(path.values()) == pytest.approx(2.0)
    assert path[2] == pytest.approx(0.5) and path[6] == 0.0


def test_delivery_bias_applies_to_plans_and_common_composition_to_all() -> None:
    s0 = synthetic_s0()
    base = programs.build_programme_scenarios(s0, CONFIG, draw())
    biased = programs.build_programme_scenarios(s0, CONFIG, draw(delivery_bias_pp=0.25))
    for name in programs.PROGRAMMES:
        expected = 0.0 if name == "P_lula_record" else 0.25
        assert total(biased[name], 5) - total(base[name], 5) == pytest.approx(expected)
    common = {"pension_and_indexation": 0.4, "other_current": 0.6}
    defs = programs.build_programme_scenarios(s0, CONFIG, draw(), common)
    for name in programs.PROGRAMMES:
        gaps = programs.package_gaps(defs[name], 5)
        assert gaps["pension_and_indexation"] == pytest.approx(0.4 * total(defs[name], 5))


def test_debt_stabilising_primary_balance_is_a_diagnostic() -> None:
    s0 = synthetic_s0()
    g = 1.02 * 1.03 - 1
    assert programs.debt_stabilising_primary_balance(s0, 2029, 2026) == pytest.approx(80.0 * (0.08 - g) / (1 + g))


def test_sampling_stays_inside_the_stated_ranges() -> None:
    rng = np.random.default_rng(1)
    for _ in range(200):
        d = programs.sample_programme_draw(rng, CONFIG, PARAMETERS)
        assert 0 <= d["lula_revenue_pp"] <= 0.5 and -1 <= d["flavio_revenue_pp"] <= 0
        assert d["delivery_bias_pp"] == PARAMETERS["fiscal_delivery"]["summary"]["median"]
    central = programs.central_programme_draw(CONFIG, PARAMETERS)
    assert central["lula_transfers_pp"] == pytest.approx(0.1)


def test_package_paths_feed_c2_totals_and_debt_adjustment() -> None:
    years = range(2025, 2028)
    baseline = pd.DataFrame(
        [{"year": y, "scenario": s, "variant": "central", "category": "total", "spending_pct_gdp": 40.0}
         for y in years for s in ("S0", "S1")]
    )
    scenarios = {
        "package_shares": {"pension_and_indexation": 1.0},
        "protected": [],
        "scenarios": {"P": {
            "package_gaps_by_year": {"other_current": {1: 1.0, 2: 2.0}, "means_tested_transfers": {1: -0.5, 2: -0.5}},
            "revenue_by_year": {1: -0.2, 2: -0.4},
            "debt_adjustment_by_year": {1: 0.5, 2: 0.5},
        }},
    }
    totals, gaps = build_spending_paths(baseline, scenarios, "central")
    row = totals.set_index(["year", "scenario"]).loc[(2027, "P")]
    assert row.gap_below_s0_pp == pytest.approx(1.5)
    assert row.spending_pct_gdp == pytest.approx(38.5)
    assert row.revenue_change_pp == pytest.approx(-0.4)
    assert row.debt_adjustment_pp == pytest.approx(0.5)
    packages = gaps.loc[gaps["scenario"].eq("P") & gaps["year"].eq(2027)].set_index("package")["gap_below_s0_pp"]
    assert packages.to_dict() == pytest.approx({"revenue": 0.4, "other_current": 2.0, "means_tested_transfers": -0.5})
