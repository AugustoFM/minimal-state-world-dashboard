from __future__ import annotations

import copy

import numpy as np
import pytest

from src import montecarlo as mc
from src.macro import revenue_elasticity, run_corner


@pytest.fixture(scope="module")
def context() -> dict:
    return mc.load_context(variants=["default"])


def _run(context, parameters=None, scenarios=None, persistence="transitory"):
    draw = mc.central_draw(context["parameters"], context["inputs"])
    annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
    return run_corner(annual, context["population"], scenarios or context["variant_configs"]["default"],
                      parameters or context["parameters"], context["inputs"], "central", persistence).set_index(["year", "scenario"])


def test_c2_rule_is_unit_elasticity(context) -> None:
    assert revenue_elasticity(context["parameters"], "central") == 1.0
    frame = _run(context)
    s0 = frame.xs("S0", level="scenario")
    assert np.allclose(s0["revenue_gdp"], s0["revenue_gdp"].iloc[0])


def test_tax_financed_expansion_keeps_primary_balance_of_s0(context) -> None:
    frame = _run(context)
    for year in frame.index.get_level_values("year").unique():
        assert frame.loc[(year, "E_mod_tax"), "primary_balance_gdp"] == pytest.approx(frame.loc[(year, "S0"), "primary_balance_gdp"])


def test_tax_increase_lowers_gdp_relative_to_debt_financing(context) -> None:
    frame = _run(context)
    final = frame.index.get_level_values("year").max()
    assert frame.loc[(final, "E_mod_tax"), "gdp_level_vs_s0_pct"] < frame.loc[(final, "E_mod"), "gdp_level_vs_s0_pct"]
    assert frame.loc[(final, "E_mod_tax"), "gdp_level_vs_s0_pct"] > 0


def test_elasticity_below_one_softens_revenue_loss_from_cuts(context) -> None:
    params = copy.deepcopy(context["parameters"])
    for corner in ("low", "central", "high"):
        params["revenue_elasticity_to_gdp"][corner] = 0.92
    unit, below = _run(context, persistence="persistent"), _run(context, params, persistence="persistent")
    final = unit.index.get_level_values("year").max()
    # Lower GDP in R_amb raises revenue/GDP when elasticity < 1, so the primary balance improves.
    assert below.loc[(final, "R_amb"), "primary_balance_gdp"] > unit.loc[(final, "R_amb"), "primary_balance_gdp"]
    assert below.loc[(final, "S0"), "primary_balance_gdp"] == pytest.approx(unit.loc[(final, "S0"), "primary_balance_gdp"])
