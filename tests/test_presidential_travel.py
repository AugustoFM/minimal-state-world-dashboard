from datetime import date

import numpy as np
import pandas as pd

from src.presidential_travel import (
    SUPPORT_LOWER_BOUND_LABEL,
    _group_visits,
    _press_cost_context,
    bilateral_fe_regression,
    deflate_to_constant,
    is_international,
    parse_date_range,
    parse_wikitext,
    permutation_test,
)


def test_wikitext_parsing_and_multicountry_trip_counting():
    text = """
== 2020 ==
{| class="wikitable"
! No. !! Country !! Dates
|-
| rowspan=2 | 1
| {{flag|Argentina}}
| 2–3 March
|-
| {{flag|Chile}}
| 3–5 March
|-
| 2
| {{USA}}
| 10 March
|}
"""
    rows = parse_wikitext(text)
    trips = _group_visits(rows, "Example", "synthetic", "primary")
    assert len(rows) == 3
    assert len(trips) == 2
    first = trips.iloc[0]
    assert first.country_visits == 2
    assert first.days_abroad == 4
    assert first.start_date == "2020-03-02"
    assert first.end_date == "2020-03-05"


def test_portuguese_and_cross_month_dates():
    assert parse_date_range("15 e 16 de janeiro de 2003", 2003) == (date(2003, 1, 15), date(2003, 1, 16))
    assert parse_date_range("30 May–1 June", 2003) == (date(2003, 5, 30), date(2003, 6, 1))


def test_international_flag_variants():
    assert is_international(True)
    assert is_international("SIM")
    assert is_international("1")
    assert not is_international(False)
    assert not is_international("não")


def test_deflation_uses_month_specific_factor():
    factors = pd.Series({pd.Period("2025-01", "M"): 1.10, pd.Period("2026-09", "M"): 1.0})
    got = deflate_to_constant([100.0, 50.0], ["15/01/2025", "01/09/2026"], factors)
    np.testing.assert_allclose(got, [110.0, 50.0])


def test_permutation_test_reproducible():
    y = np.array([1, 2, 1, 4, 5, 8, 7, 9], dtype=float)
    x = np.arange(8, dtype=float)
    one = permutation_test(y, x, draws=250, seed=77)
    two = permutation_test(y, x, draws=250, seed=77)
    assert one == two
    assert 0 < one[1] <= 1


def test_bilateral_fe_recovers_planted_effect():
    rng = np.random.default_rng(4)
    countries = [f"C{i}" for i in range(30)]
    years = range(2000, 2020)
    rows = []
    country_effect = {c: rng.normal(scale=0.5) for c in countries}
    for c in countries:
        for year in years:
            visit = rng.binomial(1, 0.18)
            log_exports = 10 + country_effect[c] + 0.025 * (year - 2000) + 0.30 * visit + rng.normal(scale=0.08)
            rows.append((c, year, np.exp(log_exports), visit))
    panel = pd.DataFrame(rows, columns=["country", "year", "exports_usd", "visit"])
    result = bilateral_fe_regression(panel)
    assert abs(result["coefficient"] - 0.30) < 0.04
    assert result["std_error"] < 0.03


def test_press_cost_context_stays_separate_and_label_is_explicit():
    cited = pd.DataFrame([
        {"item": "international_trip_cost_2025", "value": 44.4, "basis": "press estimate"},
        {"item": "presidency_travel_spending_2023_2025", "value": 150.5, "basis": "all destinations"},
    ])
    context = _press_cost_context(2025, cited)
    assert "R$ 44.4m" in context
    assert "R$ 150.5m total for 2023–2025 (not allocable by year" in context
    assert SUPPORT_LOWER_BOUND_LABEL.startswith("LOWER BOUND")
    assert "payment-card hotel/expense items" in SUPPORT_LOWER_BOUND_LABEL
