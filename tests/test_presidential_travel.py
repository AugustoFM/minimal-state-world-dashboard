from datetime import date

import numpy as np
import pandas as pd

from src.presidential_travel import (
    SUPPORT_LOWER_BOUND_LABEL,
    _group_visits,
    _press_cost_context,
    bilateral_fe_regression,
    deflate_to_constant,
    efficiency_ratios,
    export_channel_changes,
    is_international,
    parse_date_range,
    parse_wikitext,
    permutation_test,
    term_for_date,
    world_share,
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


def test_term_assignment_uses_monthly_transition_and_partial_cutoff():
    assert term_for_date(date(2016, 8, 31)) == "Dilma II"
    assert term_for_date(date(2016, 9, 1)) == "Temer"
    assert term_for_date(date(2026, 9, 30)) == "Lula III"
    assert term_for_date(date(2026, 10, 1)) is None


def test_world_share_arithmetic():
    assert world_share(25, 1000) == 2.5
    assert np.isnan(world_share(25, 0))


def test_new_and_lost_market_counting_at_thresholds():
    panel = pd.DataFrame([
        (2000, "A", 9_000_000), (2001, "A", 12_000_000),
        (2000, "B", 11_000_000), (2001, "B", 8_000_000),
        (2000, "C", 2_000_000), (2001, "C", 3_000_000),
    ], columns=["year", "country", "exports_usd"])
    ten = export_channel_changes(panel, 2000, 2001, 10_000_000)
    one = export_channel_changes(panel, 2000, 2001, 1_000_000)
    assert (ten["new_markets"], ten["lost_markets"]) == (1, 1)
    assert ten["new_market_names"] == "A"
    assert (one["new_markets"], one["lost_markets"]) == (0, 0)


def test_efficiency_ratios_preserve_missing_costs():
    got = efficiency_ratios({
        "trips": 10, "days_abroad": 50, "matched_cost_brl_2026_09": np.nan,
        "fdi_world_share_change_pp": 0.2, "export_world_share_change_pp": 0.1,
        "new_markets_10m": 5,
    })
    assert got["fdi_share_pp_per_trip"] == 0.02
    assert got["export_share_pp_per_100_days"] == 0.2
    assert got["new_markets_per_trip"] == 0.5
    assert np.isnan(got["fdi_share_pp_per_cost_m"])


def test_prepare_cpgf_keeps_classified_rows_and_splits_organs():
    import pandas as pd
    from src.presidential_travel import prepare_cpgf

    card = pd.DataFrame({
        "NOME ÓRGÃO": ["Presidência da República", "Presidência da República",
                       "Gabinete da Vice-Presidência da República", "Empresa Brasil de Comunicação"],
        "ANO EXTRATO": [2023, 2023, 2023, 2023],
        "MÊS EXTRATO": [5, 5, 5, 5],
        "TRANSAÇÃO": ["Informações protegidas por sigilo", "COMPRA A/V - INT$ - APRES",
                      "COMPRA A/V - R$ - APRES", "COMPRA A/V - R$ - APRES"],
        "DATA TRANSAÇÃO": [None, "10/05/2023", "11/05/2023", "12/05/2023"],
        "VALOR TRANSAÇÃO": [1000.0, 50.0, 20.0, 5.0],
    })
    factors = pd.Series(1.0, index=pd.period_range("2013-01", "2026-09", freq="M"))
    out = prepare_cpgf(card, factors)
    assert len(out) == 4
    classified = out[out.classified]
    assert len(classified) == 1 and bool(classified.dated_by_statement.iloc[0])
    assert classified.date.iloc[0] == pd.Timestamp("2023-05-01")
    assert out.organ_group.tolist() == ["presidency", "presidency", "vice_presidency", "excluded"]
    assert out.foreign.tolist() == [False, True, False, False]
