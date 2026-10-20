from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_pof_income_codes as pof  # noqa: E402


def test_each_code_has_one_category() -> None:
    seen: dict[str, str] = {}
    for category, (_, codes) in pof.CATEGORIES.items():
        for code in codes:
            assert code not in seen, f"{code} in {seen.get(code)} and {category}"
            seen[code] = category


def test_register_classification_is_complete_and_linked() -> None:
    codes = pof.build()
    assert codes["category"].notna().all()
    assert set(codes["quadro"]) == pof.INCOME_QUADROS
    pensions = codes.loc[codes["code"].isin({"5400401", "5400601"}), "scenario_package"]
    assert set(pensions) == {"pension_and_indexation"}
    assert codes.loc[codes["code"].eq("5400102"), "category"].item() == "bolsa_familia"
    assert codes.loc[codes["code"].eq("5502101"), "category"].item() == "not_current_income"
