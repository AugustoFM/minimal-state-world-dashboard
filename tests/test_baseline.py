from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.baseline import OUTPUT_CATEGORIES, expand_age_profiles, project_baseline, read_yaml


def _fiscal() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2024, 2025, 2026],
            "quarters_observed": [4, 4, 2],
            "primary_spending_pct_gdp": [39.0, 40.0, 38.0],
        }
    )


def _profiles() -> pd.DataFrame:
    values = {
        "pension": [0.0, 0.5, 8.0],
        "health": [1.0, 1.0, 1.0],
        "education": [1.0, 1.0, 1.0],
    }
    return pd.DataFrame(
        [
            {
                "category": category,
                "age_band": band,
                "relative_cost_per_capita": cost,
            }
            for category, costs in values.items()
            for band, cost in zip(("0-14", "15-64", "65+"), costs)
        ]
    )


def _inputs() -> dict:
    params = {
        "pension_gdp_share": 12.0,
        "health_gdp_share": 5.0,
        "education_gdp_share": 5.0,
        "working_age_min": 15,
        "working_age_max": 64,
    }
    baseline = {
        name: {variant: value for variant in ("low", "central", "high")}
        for name, value in params.items()
    }
    baseline["pension_gdp_per_worker_weight"] = {
        "low": 0.0,
        "central": 0.5,
        "high": 1.0,
    }
    return {"baseline": baseline}


def _population(old_2030: int = 20) -> pd.DataFrame:
    rows = []
    for year, counts in (
        (2025, (20, 60, 20)),
        (2030, (20, 60, old_2030)),
    ):
        for age, count in zip((10, 30, 70), counts):
            rows.append(
                {
                    "year": year,
                    "age": age,
                    "population": count,
                    "sex": "Ambos",
                    "iso3": "BR",
                }
            )
    return pd.DataFrame(rows)


def _run(population: pd.DataFrame) -> pd.DataFrame:
    return project_baseline(
        _fiscal(), population, _profiles(), _inputs(), horizons=[5]
    )


def test_s1_is_constant() -> None:
    result = _run(_population(old_2030=35))
    totals = result.loc[
        result["scenario"].eq("S1") & result["category"].eq("total"),
        "spending_pct_gdp",
    ]
    assert totals.eq(40.0).all()


def test_flat_population_makes_s0_equal_s1() -> None:
    result = _run(_population(old_2030=20))
    future = result.loc[result["year"].eq(2030)]
    s0 = future.loc[future["scenario"].eq("S0")].set_index(
        ["variant", "category"]
    )["spending_pct_gdp"]
    s1 = future.loc[future["scenario"].eq("S1")].set_index(
        ["variant", "category"]
    )["spending_pct_gdp"]
    pd.testing.assert_series_equal(s0, s1, check_names=False)


def test_drift_is_positive_when_old_age_share_rises() -> None:
    result = _run(_population(old_2030=35))
    drift = result.loc[
        result["year"].eq(2030)
        & result["scenario"].eq("S0")
        & result["category"].eq("total"),
        "drift_pct_gdp",
    ]
    assert (drift > 0).all()


def test_categories_sum_to_total() -> None:
    result = _run(_population(old_2030=35))
    components = set(OUTPUT_CATEGORIES) - {"total"}
    grouped = result.loc[result["category"].isin(components)].groupby(
        ["year", "scenario", "variant"], observed=True
    )["spending_pct_gdp"].sum()
    totals = result.loc[result["category"].eq("total")].set_index(
        ["year", "scenario", "variant"]
    )["spending_pct_gdp"]
    pd.testing.assert_series_equal(
        grouped.sort_index(), totals.sort_index(), check_names=False
    )


def test_base_year_reproduces_latest_complete_fiscal_year() -> None:
    result = _run(_population(old_2030=35))
    base = result.loc[
        result["year"].eq(2025) & result["category"].eq("total"),
        "spending_pct_gdp",
    ]
    assert base.tolist() == pytest.approx([40.0] * len(base))


def test_single_age_profiles_map_90_plus_to_age_90() -> None:
    profiles = pd.DataFrame(
        [
            {"category": category, "age": age, "relative_cost_per_capita": cost}
            for category in ("pension", "health", "education")
            for age, cost in ((0, 1.0), (90, 9.0))
        ]
    )
    expanded = expand_age_profiles(profiles, [0, 90, 95])
    for category in ("pension", "health", "education"):
        values = expanded.loc[expanded["category"].eq(category)].set_index("age")[
            "cost"
        ]
        assert values.loc[90] == pytest.approx(9.0)
        assert values.loc[95] == pytest.approx(values.loc[90])


def test_profile_vintage_switch_changes_result() -> None:
    rows = []
    for vintage, old_pension_cost in ((2003, 2.0), (2018, 8.0)):
        for category in ("pension", "health", "education"):
            for age in (10, 30, 70):
                cost = old_pension_cost if category == "pension" and age == 70 else 1.0
                rows.append(
                    {
                        "category": category,
                        "age": age,
                        "relative_cost_per_capita": cost,
                        "profile_year": vintage,
                    }
                )
    profiles = pd.DataFrame(rows)
    results = {}
    for vintage in (2003, 2018):
        result = project_baseline(
            _fiscal(),
            _population(old_2030=35),
            profiles.loc[profiles["profile_year"].eq(vintage)],
            _inputs(),
            horizons=[5],
        )
        results[vintage] = result.loc[
            result["year"].eq(2030)
            & result["scenario"].eq("S0")
            & result["variant"].eq("central")
            & result["category"].eq("total"),
            "spending_pct_gdp",
        ].item()
    assert results[2003] != pytest.approx(results[2018])


def test_real_data_smoke() -> None:
    paths = {
        "fiscal": Path("data/brazil/fiscal.csv"),
        "population": Path("data/brazil/population.csv"),
        "profiles": Path("data/brazil/age_profiles.csv"),
        "inputs": Path("config/parameters.yaml"),
    }
    if not all(path.exists() for path in paths.values()):
        pytest.skip("C1 real-data files are absent")
    result = project_baseline(
        pd.read_csv(paths["fiscal"]),
        pd.read_csv(paths["population"]),
        pd.read_csv(paths["profiles"]),
        read_yaml(paths["inputs"]),
        horizons=[5],
    )
    assert len(result) == 60
    assert result["spending_pct_gdp"].notna().all()
    assert set(result["profile_year"].dropna().astype(int)) <= {2003, 2018}
