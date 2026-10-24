from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import calibrate_b1 as b1  # noqa: E402


def _series(values: dict[str, list[float]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"iso3": iso3, "year": 2000 + i, "value": v}
            for iso3, vs in values.items()
            for i, v in enumerate(vs)
        ]
    )


def test_weighted_quantile_gives_each_country_equal_weight() -> None:
    # Country A has 9 episodes at +1, country B one at -5: B must carry half the weight.
    changes = pd.Series([1.0] * 9 + [-5.0])
    countries = pd.Series(["A"] * 9 + ["B"])
    assert b1.weighted_quantile(changes, countries, 0.10) == -5.0
    assert b1.weighted_quantile(changes, countries, 0.60) == 1.0


def test_spike_start_flags_jump_above_prior_mean() -> None:
    flags = b1.spike_starts(_series({"A": [20, 20, 20, 25, 20]}))
    assert flags.loc[flags["year"].eq(2003), "spike"].item()
    assert not flags.loc[flags["year"].eq(2004), "spike"].item()


def test_break_window_detects_jump_inside_episode_only() -> None:
    series = _series({"A": [60, 20, 20, 20, 20, 20]})
    episodes = pd.DataFrame(
        {"iso3": ["A", "A"], "start_year": [2000, 2001], "end_year": [2005, 2005]}
    )
    assert b1.break_windows(series, episodes).tolist() == [True, False]


def test_classify_uses_conservative_then_central_bound() -> None:
    assert b1.classify(3.0, conservative=3.5, central=4.0) == "inside"
    assert b1.classify(3.8, conservative=3.5, central=4.0) == "borderline"
    assert b1.classify(4.5, conservative=3.5, central=4.0) == "outside"


def test_one_year_withholding_is_not_subtracted_from_multi_year_reductions() -> None:
    # Only the full discretionary stock (1.6 pp) bounds what can avoid mandatory rules;
    # the 25% one-year withholding limit must not shrink the mandatory requirement.
    assert b1.mandatory_lower_bound(1.0) == 0.0
    assert b1.mandatory_lower_bound(4.0) == 4.0 - b1.DISCRETIONARY_PCT_GDP
