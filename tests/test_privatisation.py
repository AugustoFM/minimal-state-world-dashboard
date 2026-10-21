from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import yaml

from src import privatisation, programs
from src.macro import build_spending_paths, debt_step


def inventory(*rows: dict) -> pd.DataFrame:
    defaults = {
        "company": "Synthetic", "short_name": "SYN", "tier": "A",
        "status_2026": "verify", "valuation_mid_brl_million": 100.0,
        "cycle_average_dividends_2025_brl_million": 10.0,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def synthetic_s0() -> pd.DataFrame:
    return pd.DataFrame([
        {"year": year, "spending_pct_gdp": 40.0, "real_gdp": 100.0,
         "real_growth": 0.0 if year > 2025 else np.nan,
         "nominal_growth": 0.03 if year > 2025 else np.nan,
         "interest": 0.08, "revenue_gdp": 39.0,
         "primary_balance_gdp": -1.0, "debt_gdp": 80.0}
        for year in range(2025, 2036)
    ])


def programme_draw(**updates) -> dict:
    draw = {
        "lula_transfers_pp": 0.0, "lula_revenue_pp": 0.0,
        "flavio_revenue_pp": 0.0, "flavio_privatisation_pp": 0.0,
        "flavio_new_programmes_pp": 0.0, "delivery_bias_pp": 0.0,
    }
    draw.update(updates)
    return draw


def test_proceeds_retire_debt_in_sale_year_and_dividends_stop_next_year() -> None:
    paths = privatisation.sale_paths(
        inventory({}), "f5", np.random.default_rng(4), 1_000.0,
        f5_target_pp=10.0, end_year=2031,
    )
    proceeds, lost = paths["debt_adjustment_by_year"], paths["non_tax_revenue_by_year"]
    assert proceeds[2] > 0 and proceeds[5] > 0
    assert lost[2] == 0.0
    assert lost[3] < 0.0
    assert lost[6] == pytest.approx(-1.0)  # R$10m / R$1bn = 1 pp after all tranches


def test_empty_package_reproduces_zero_current_paths() -> None:
    empty = inventory({"tier": "C"})
    paths = privatisation.sale_paths(empty, "f5", np.random.default_rng(1), 1_000.0,
                                    f5_target_pp=2.0, end_year=2030)
    assert not paths["companies"]
    assert set(paths["debt_adjustment_by_year"].values()) == {0.0}
    assert set(paths["non_tax_revenue_by_year"].values()) == {0.0}


def test_non_tax_revenue_changes_debt_but_not_tax_or_package_incidence() -> None:
    baseline = pd.DataFrame([
        {"year": year, "scenario": scenario, "variant": "central", "category": "total",
         "spending_pct_gdp": 40.0}
        for year in (2025, 2026) for scenario in ("S0", "S1")
    ])
    scenarios = {
        "package_shares": {"other_current": 1.0}, "protected": [],
        "scenarios": {"P": {"by_year": {1: 0.0}, "non_tax_revenue_by_year": {1: -1.0}}},
    }
    totals, gaps = build_spending_paths(baseline, scenarios, "central")
    row = totals.set_index(["year", "scenario"]).loc[(2026, "P")]
    assert row.revenue_change_pp == 0.0
    assert row.non_tax_revenue_pp == -1.0
    assert gaps.loc[(gaps.year == 2026) & (gaps.scenario == "P") & (gaps.package == "revenue"),
                    "gap_below_s0_pp"].item() == 0.0
    without = debt_step(0.8, 0.08, 0.05, -0.01)
    with_lost_dividend = debt_step(0.8, 0.08, 0.05, -0.02)
    assert with_lost_dividend > without


def test_petrobras_state_stake_is_selected_once() -> None:
    frame = inventory(
        {"company": "Petrobras", "short_name": "PETROBRAS", "tier": "B", "valuation_mid_brl_million": 296.0},
        {"company": "Banco do Brasil", "short_name": "BB", "tier": "B", "valuation_mid_brl_million": 69.0},
    )
    members = privatisation.package_members(frame, "broad_bb_petrobras")
    assert members.short_name.tolist().count("PETROBRAS") == 1
    assert members.loc[members.short_name.eq("PETROBRAS"), "valuation_mid_brl_million"].sum() == 296.0


def test_petrobras_lost_dividends_use_same_stake_share_as_value() -> None:
    direct_dividends = 100.0
    lost_dividends = privatisation.dividend_loss_measure("PETROBRAS", direct_dividends)

    assert privatisation.PETROBRAS_UNION_DIRECT_STAKE_PCT == pytest.approx(28.67)
    assert lost_dividends == pytest.approx(direct_dividends * 36.61 / 28.67)
    assert lost_dividends / direct_dividends == pytest.approx(
        privatisation.PETROBRAS_STATE_STAKE_PCT
        / privatisation.PETROBRAS_UNION_DIRECT_STAKE_PCT
    )
    assert privatisation.dividend_loss_measure("BNDES", direct_dividends) == direct_dividends


def test_lula_scenarios_are_unaffected_by_privatisation_paths() -> None:
    config = yaml.safe_load(open("config/programs_2026.yaml", encoding="utf-8"))
    base = programs.build_programme_scenarios(synthetic_s0(), config, programme_draw())
    changed = programs.build_programme_scenarios(
        synthetic_s0(), config,
        programme_draw(privatisation_debt_adjustment_by_year={1: 0.5},
                       privatisation_non_tax_revenue_by_year={2: -0.1}),
    )
    for scenario in ("P_lula_rule", "P_lula_record"):
        assert changed[scenario] == base[scenario]
    for scenario in ("P_flavio_low", "P_flavio_mid", "P_flavio_high"):
        assert changed[scenario]["debt_adjustment_by_year"] == {1: 0.5}
        assert changed[scenario]["non_tax_revenue_by_year"] == {2: -0.1}


def test_inventory_has_46_direct_companies_and_required_exclusions() -> None:
    frame = pd.read_csv(privatisation.INVENTORY_PATH)
    assert len(frame) == 46
    assert set(frame.loc[frame.tier.eq("D"), "dependent"]) == {True}
    broad = set(privatisation.package_members(frame, "broad").short_name)
    assert not broad.intersection({"PETROBRAS", "BB", "CAIXA", "BNDES", "BNB", "BASA"})
