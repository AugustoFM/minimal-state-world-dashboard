from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import pytest

from src import external
from src import montecarlo as mc
from src.macro import run_corner


@pytest.fixture(scope="module")
def context() -> dict:
    return mc.load_context(variants=["default"])


@pytest.fixture(scope="module")
def corner(context) -> pd.DataFrame:
    draw = mc.central_draw(context["parameters"], context["inputs"])
    annual = context["grid"][(draw["profile_year"], draw["pension_gdp_per_worker_weight"])]
    return run_corner(annual, context["population"], context["variant_configs"]["default"],
                      context["parameters"], context["inputs"], "central", "transitory")


@pytest.fixture(scope="module")
def changes() -> pd.DataFrame:
    return external.historical_changes()


def test_neutral_path_reproduces_c2_debt(context, corner, changes) -> None:
    years = int(corner["year"].max() - corner["year"].min())
    effects = external.gdp_and_inflation_effects(external.reference_path("neutral", changes, years), context["parameters"])
    out = external.apply_external(corner, effects, context["inputs"])
    np.testing.assert_allclose(out["debt_gdp_with_external"], out["debt_gdp"], rtol=1e-12)
    np.testing.assert_allclose(out["gdp_per_capita_with_external"], out["gdp_per_capita"], rtol=1e-12)


def test_boom_raises_gdp_and_lowers_debt_relative_to_bust(context, corner, changes) -> None:
    years = int(corner["year"].max() - corner["year"].min())
    results = {}
    for name in ("boom", "bust"):
        effects = external.gdp_and_inflation_effects(external.reference_path(name, changes, years), context["parameters"])
        results[name] = external.apply_external(corner, effects, context["inputs"])
    final = corner["year"].max()
    boom = results["boom"].loc[results["boom"]["year"].eq(final)].set_index("scenario")
    bust = results["bust"].loc[results["bust"]["year"].eq(final)].set_index("scenario")
    assert (boom["gdp_per_capita_with_external"] > bust["gdp_per_capita_with_external"]).all()
    assert (boom["debt_gdp_with_external"] < bust["debt_gdp_with_external"]).all()


def test_same_external_path_for_every_scenario(context, corner, changes) -> None:
    years = int(corner["year"].max() - corner["year"].min())
    effects = external.gdp_and_inflation_effects(external.reference_path("boom", changes, years), context["parameters"])
    out = external.apply_external(corner, effects, context["inputs"])
    per_year = out.groupby("year")["external_gdp_level_pct"].nunique()
    assert (per_year == 1).all()


def test_external_debt_uses_same_annual_rate_offset_for_every_scenario(context, corner, changes) -> None:
    years = int(corner["year"].max() - corner["year"].min())
    effects = external.gdp_and_inflation_effects(external.reference_path("neutral", changes, years), context["parameters"])
    inputs = copy.deepcopy(context["inputs"])
    inputs["derived"]["real_rate_path_offset_pp"] = {year: 1.0 for year in range(2026, 2046)}
    raised = copy.deepcopy(context["inputs"])
    for key in ("low", "central", "high"):
        raised["macro"]["effective_real_interest_rate"][key] += 1.0
    with_offset = external.apply_external(corner, effects, inputs)
    with_scalar = external.apply_external(corner, effects, raised)
    np.testing.assert_allclose(with_offset["debt_gdp_with_external"], with_scalar["debt_gdp_with_external"])


def test_permanent_share_and_pass_through(context) -> None:
    path = pd.DataFrame({"step": [1, 2, 3], "tot_change_pct": [10.0, 0.0, 0.0], "fx_change_pct": [10.0, 0.0, 0.0]})
    effects = external.gdp_and_inflation_effects(path, context["parameters"], elasticity=0.1)
    # impulse 1.0%: half permanent, half cyclical decaying with a 2-year half-life
    assert effects.loc[0, "external_gdp_level_pct"] == pytest.approx(1.0)
    assert effects.loc[0, "external_potential_level_pct"] == pytest.approx(0.5)
    assert effects.loc[2, "external_gdp_level_pct"] == pytest.approx(0.5 + 0.5 * 0.5)
    assert effects.loc[0, "external_extra_inflation_pp"] == pytest.approx(1.0)
    assert effects.loc[1, "external_extra_inflation_pp"] == pytest.approx(0.6)
    assert effects.loc[2, "external_extra_inflation_pp"] == pytest.approx(0.0)


def test_bootstrap_uses_observed_changes_only(changes) -> None:
    path = external.bootstrap_path(np.random.default_rng(3), changes, 20)
    assert len(path) == 20
    observed = {tuple(np.round(r, 9)) for r in changes.to_numpy()}
    assert all(tuple(np.round(r, 9)) in observed for r in path[["tot_change_pct", "fx_change_pct"]].to_numpy())


def test_c7_changes_are_demeaned_and_complete() -> None:
    changes = external.historical_changes_v2()
    assert list(changes.index) == list(range(2001, 2025))
    assert changes[["dlnp_pct", "world_growth_dev_pp"]].mean().abs().max() < 1e-9


def test_c7_one_off_price_shock_follows_channel_a(context) -> None:
    coefficients = external.channel_a_coefficients(context["parameters"], "reverse_2010_2024")
    path = pd.DataFrame({"step": [1, 2, 3], "dlnp_pct": [10.0, 0.0, 0.0],
                         "world_growth_dev_pp": 0.0, "fx_change_pct": 0.0})
    effects = external.gdp_and_inflation_effects(path, context["parameters"], channel_a=coefficients)
    first = coefficients["dlnP"] * 10
    second = (1 + first / 100) * (1 + coefficients["dlnP_lag"] * 10 / 100) * 100 - 100
    assert effects["external_gdp_level_pct"].tolist() == pytest.approx([first, second, second])
    assert effects["external_extra_inflation_pp"].abs().max() == 0.0


def test_c7_central_is_the_average_of_both_windows(context) -> None:
    central = external.channel_a_coefficients(context["parameters"])
    primary = external.channel_a_coefficients(context["parameters"], "primary_2000_2014")
    reverse = external.channel_a_coefficients(context["parameters"], "reverse_2010_2024")
    assert central["dlnP"] == pytest.approx((primary["dlnP"] + reverse["dlnP"]) / 2)


def test_c7_is_the_default_mc_external_input(context) -> None:
    assert "dlnp_pct" in context["external_changes"].columns


def test_corruption_shock_combines_with_external_level(context, corner) -> None:
    years = int(corner["year"].max() - corner["year"].min())
    effects = external.gdp_and_inflation_effects(
        external.reference_path("neutral", external.historical_changes_v2(), years), context["parameters"])
    effects["corruption_gdp_level_pct"] = -2.0
    out = external.apply_external(corner, effects, context["inputs"])
    later = out.loc[out["year"] > out["year"].min()]
    assert later["external_gdp_level_pct"].tolist() == pytest.approx([-2.0] * len(later))
    assert (later["gdp_per_capita_with_external"] < later["gdp_per_capita"]).all()
