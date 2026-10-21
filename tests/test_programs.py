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
        "lula_transfers_pp": 0.0, "lula_revenue_pp": 0.0, "flavio_years_to_target": 4,
        "flavio_revenue_pp": 0.0, "flavio_privatisation_pp": 0.0, "flavio_new_programmes_pp": 0.0,
        "delivery_bias_pp": 0.0,
    }
    values.update(overrides)
    return values


def total(definition: dict, horizon: int) -> float:
    return sum(programmes_gap for programmes_gap in programs.package_gaps(definition, horizon).values())


def test_nothing_changes_before_the_term() -> None:
    defs = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw(lula_revenue_pp=0.5, flavio_revenue_pp=-1))
    for definition in defs.values():
        assert total(definition, 1) == 0.0
        assert definition["revenue_by_year"][1] == 0.0


def test_lc200_rule_grows_federal_spending_at_70_percent_of_revenue_growth() -> None:
    s0 = synthetic_s0()
    defs = programs.build_programme_scenarios(s0, CONFIG, draw())
    share = CONFIG["model_parameters"]["federal_share_of_general_government_primary"]["value"]
    federal = share * 40.3  # 2026 S0 spending
    for year in range(2027, 2031):
        federal *= 1.014 / 1.02  # 0.7 x 2% real revenue growth, deflated by 2% GDP growth
        expected = share * float(s0.set_index("year").loc[year, "spending_pct_gdp"]) - federal
        assert total(defs["P_lula"], year - 2025) == pytest.approx(expected)
    # after the term the 2030 gap is held
    assert total(defs["P_lula"], 10) == pytest.approx(total(defs["P_lula"], 5))


def test_lc200_floor_binds_when_growth_is_low() -> None:
    s0 = synthetic_s0(growth=0.0)
    defs = programs.build_programme_scenarios(s0, CONFIG, draw())
    share = CONFIG["model_parameters"]["federal_share_of_general_government_primary"]["value"]
    federal = share * 40.3 * 1.006
    assert total(defs["P_lula"], 2) == pytest.approx(share * 40.6 - federal)


def test_flavio_reaches_the_debt_stabilising_primary_balance_in_t_years() -> None:
    s0 = synthetic_s0()
    tax_cut = -0.8
    defs = programs.build_programme_scenarios(s0, CONFIG, draw(flavio_years_to_target=3, flavio_revenue_pp=tax_cut))
    g = 1.02 * 1.03 - 1
    target = 0.80 * (0.08 - g) / (1 + g) * 100
    row = s0.set_index("year").loc[2029]  # third year of the term
    revenue = defs["P_flavio"]["revenue_by_year"][4]
    planned_pb = row.primary_balance_gdp + revenue + total(defs["P_flavio"], 4)
    assert planned_pb == pytest.approx(target)
    assert revenue == pytest.approx(tax_cut * 3 / 4)


def test_new_programmes_are_financed_inside_the_path() -> None:
    base = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw())
    extra = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw(flavio_new_programmes_pp=0.3))
    assert total(extra["P_flavio"], 5) == pytest.approx(total(base["P_flavio"], 5))
    services = "efficiency_health_education_admin"
    composition = {"efficiency_health_education_admin": 0.5}
    expected = (total(base["P_flavio"], 5) + 0.3) * composition[services] - 0.3
    assert programs.package_gaps(extra["P_flavio"], 5)[services] == pytest.approx(expected)


def test_privatisation_retires_debt_over_the_term_only() -> None:
    defs = programs.build_programme_scenarios(synthetic_s0(), CONFIG, draw(flavio_privatisation_pp=2.0))
    path = defs["P_flavio"]["debt_adjustment_by_year"]
    assert sum(path.values()) == pytest.approx(2.0)
    assert path[2] == pytest.approx(0.5) and path[6] == 0.0


def test_delivery_bias_and_common_composition_treat_both_programmes_alike() -> None:
    s0 = synthetic_s0()
    base = programs.build_programme_scenarios(s0, CONFIG, draw())
    biased = programs.build_programme_scenarios(s0, CONFIG, draw(delivery_bias_pp=0.25))
    for name in programs.PROGRAMMES:
        assert total(biased[name], 5) - total(base[name], 5) == pytest.approx(0.25)
    common = {"pension_and_indexation": 0.4, "other_current": 0.6}
    defs = programs.build_programme_scenarios(s0, CONFIG, draw(), common)
    for name in programs.PROGRAMMES:
        gaps = programs.package_gaps(defs[name], 5)
        assert gaps["pension_and_indexation"] == pytest.approx(0.4 * total(defs[name], 5))


def test_sampling_stays_inside_the_stated_ranges() -> None:
    rng = np.random.default_rng(1)
    for _ in range(200):
        d = programs.sample_programme_draw(rng, CONFIG, PARAMETERS)
        assert 0 <= d["lula_revenue_pp"] <= 0.5 and -1 <= d["flavio_revenue_pp"] <= 0
        assert 2 <= d["flavio_years_to_target"] <= 6
        assert d["delivery_bias_pp"] == PARAMETERS["fiscal_delivery"]["summary"]["median"]
    central = programs.central_programme_draw(CONFIG, PARAMETERS)
    assert central["flavio_years_to_target"] == 4 and central["lula_transfers_pp"] == pytest.approx(0.1)


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
