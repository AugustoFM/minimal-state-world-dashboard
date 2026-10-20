from __future__ import annotations

import csv
import importlib.util
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_fiscal_delivery", ROOT / "scripts/build_fiscal_delivery.py"
)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def csv_rows() -> list[dict[str, str]]:
    with (ROOT / "data/brazil/fiscal_delivery.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def number(value: str) -> float | None:
    return None if value == "" else float(value)


def test_every_manual_quote_occurs_in_its_extracted_source() -> None:
    texts = {
        filename: builder.extract_text(builder.RAW / filename)
        for filename in builder.FILES.values()
    }
    for row in csv_rows():
        quote = row["source_quote"]
        assert row["extraction_method"] == "manual"
        assert 0 < len(quote) <= 400
        assert quote in texts[row["source_file"]]


def test_sign_convention_and_known_surplus_deficit_examples() -> None:
    rows = {(int(r["evaluated_year"]), r["concept"]): r for r in csv_rows()}
    # Annex surplus values are positive under the output convention.
    assert number(rows[(2008, "consolidated public sector")]["outturn_brl_bn"]) == 118.0
    assert number(rows[(2022, "consolidated public sector")]["outturn_pct_gdp"]) == 1.27
    # Annex deficit values are negative under the same convention.
    assert number(rows[(2020, "central government")]["outturn_brl_bn"]) == -745.266
    assert number(rows[(2023, "consolidated public sector")]["outturn_pct_gdp"]) == -2.29
    # The BCB borrowing-requirement input is sign-flipped for cross-checking.
    assert builder.bcb_values()[2022] == 1.25
    assert builder.bcb_values()[2020] == -9.24


def test_misses_equal_outturn_minus_target() -> None:
    for row in csv_rows():
        outturn = number(row["outturn_pct_gdp"])
        for target_column, miss_column in (
            ("original_target_pct_gdp", "miss_vs_original_pp_gdp"),
            ("final_target_pct_gdp", "miss_vs_final_pp_gdp"),
        ):
            target = number(row[target_column])
            miss = number(row[miss_column])
            if outturn is None or target is None:
                assert miss is None
            else:
                assert miss is not None
                assert math.isclose(miss, outturn - target, abs_tol=0.00011)


def test_one_row_per_evaluated_year_and_concept() -> None:
    rows = csv_rows()
    keys = [(int(r["evaluated_year"]), r["concept"]) for r in rows]
    assert len(keys) == len(set(keys)) == 38
    assert {year for year, _ in keys} == set(builder.FILES)
    for year in builder.FILES:
        assert {concept for row_year, concept in keys if row_year == year} == {
            "consolidated public sector",
            "central government",
        }


def test_years_and_government_mapping_are_exact() -> None:
    expected = {
        1999: "FHC II (PSDB)", 2000: "FHC II (PSDB)", 2002: "FHC II (PSDB)",
        2008: "Lula I-II (PT)", 2010: "Lula I-II (PT)",
        2011: "Dilma (PT)", 2012: "Dilma (PT)", 2014: "Dilma (PT)", 2015: "Dilma (PT)",
        2016: "2016 transition",
        2017: "Temer (MDB)", 2018: "Temer (MDB)",
        2019: "Bolsonaro (PSL/PL)", 2020: "Bolsonaro (PSL/PL)",
        2021: "Bolsonaro (PSL/PL)", 2022: "Bolsonaro (PSL/PL)",
        2023: "Lula III (PT)", 2024: "Lula III (PT)", 2025: "Lula III (PT)",
    }
    assert set(expected) == set(builder.FILES)
    for row in csv_rows():
        year = int(row["evaluated_year"])
        assert row["government"] == expected[year] == builder.government_for_year(year)


def test_special_events_and_archived_year_gaps() -> None:
    rows = csv_rows()
    flags = {
        int(row["evaluated_year"]): row["special_event"]
        for row in rows
        if row["special_event"]
    }
    assert flags == {
        1999: "devaluation",
        2008: "global crisis",
        2020: "pandemic; fiscal targets suspended under state of calamity",
    }
    assert set(range(1999, 2026)) - set(builder.FILES) == {
        2001, 2003, 2004, 2005, 2006, 2007, 2009, 2013
    }


def test_checked_in_csv_is_reproducible() -> None:
    expected = builder.build_rows()
    actual = csv_rows()
    assert len(actual) == len(expected)
    for csv_row, built_row in zip(actual, expected, strict=True):
        for column in builder.COLUMNS:
            expected_value = built_row[column]
            rendered = "" if expected_value is None else str(expected_value)
            assert csv_row[column] == rendered
