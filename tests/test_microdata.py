from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import load_brazil_microdata as loader  # noqa: E402
import read_ibge_fwf as fwf  # noqa: E402
import validate_brazil_microdata as validation  # noqa: E402

LAYOUT = ROOT / "data/raw/brazil/layouts/pnadc_2025_visita1_input.txt"
MAPPING = ROOT / "data/brazil/micro/mappings/pnadc_2025_visita1.json"


def test_official_layout_positions_match_dictionary() -> None:
    layout = fwf.parse_sas_layout(LAYOUT).set_index("name")
    # Positions and widths as printed in pnadc_2025_visita1_dictionary.xls.
    assert tuple(layout.loc["V1032", ["start", "width"]]) == (57, 15)
    assert tuple(layout.loc["VD5008", ["start", "width"]]) == (673, 8)
    assert tuple(layout.loc["V5004A2", ["start", "width"]]) == (415, 8)
    assert layout.loc["UF", "is_text"] and not layout.loc["V2009", "is_text"]


def test_read_columns_streams_fixed_width_from_zip(tmp_path: Path) -> None:
    layout = pd.DataFrame(
        {"name": ["UF", "AGE", "W"], "start": [0, 2, 5], "width": [2, 3, 6], "is_text": [True, False, False]}
    )
    archive = tmp_path / "data.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("data.txt", "11 3212.500\n35  7  1.25\n")
    frame = fwf.read_columns(archive, layout, ["UF", "W"])
    assert frame["UF"].tolist() == ["11", "35"]
    assert frame["W"].tolist() == [12.5, 1.25]


def test_approved_mapping_has_no_identifiers_or_keys() -> None:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    assert mapping["household_key_columns"] == []
    assert not any(loader.FORBIDDEN_COLUMN.search(c) for c in mapping["columns"])
    assert set(mapping["columns"].values()) <= loader.ALLOWED_CANONICAL
    assert mapping["columns"]["V1032"] == "survey_weight"
    assert mapping["columns"]["VD5008"] == "household_income_per_capita_brl"


def test_loader_rejects_identifier_mapping(tmp_path: Path) -> None:
    export = tmp_path / "export.csv"
    pd.DataFrame({"UPA": ["1"], "Ano": [2025], "V1032": [1.0]}).to_csv(export, index=False)
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({"dataset": "pnadc", "columns": {"UPA": "state_code", "Ano": "year", "V1032": "survey_weight"}}))
    with pytest.raises(ValueError, match="identifier"):
        loader.load_export("pnadc", export, mapping)


def test_weighted_gini_known_cases() -> None:
    assert validation.weighted_gini(np.array([5.0, 5.0, 5.0]), np.ones(3)) == pytest.approx(0.0)
    assert validation.weighted_gini(np.array([0.0, 0.0, 0.0, 1.0]), np.ones(4)) == pytest.approx(0.75)
    # Weights act as replicated observations.
    assert validation.weighted_gini(np.array([1.0, 3.0]), np.array([2.0, 1.0])) == pytest.approx(
        validation.weighted_gini(np.array([1.0, 1.0, 3.0]), np.ones(3))
    )
