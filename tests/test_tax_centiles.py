from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_brazil_tax_centiles as tax  # noqa: E402

OUTPUT = ROOT / "data/brazil/micro/tax_centiles_2024.csv"


def test_partition_rows_tile_the_population_exactly() -> None:
    bounds = [tax.row_bounds(r) for r in range(1, 121)]
    parts = sorted((lo, hi) for lo, hi, part in bounds if part)
    assert parts[0][0] == 0 and parts[-1][1] == pytest.approx(100)
    for (_, hi), (lo, _) in zip(parts, parts[1:]):
        assert lo == pytest.approx(hi)
    # Overlapping aggregate rows are excluded from the partition.
    assert not tax.row_bounds(100)[2] and not tax.row_bounds(110)[2]


@pytest.mark.skipif(not OUTPUT.exists(), reason="tidy output not built")
def test_partition_reproduces_published_totals() -> None:
    wide = pd.read_csv(OUTPUT)
    v = wide.loc[wide["table"].eq("V")]
    count = next(c for c in wide.columns if c.startswith("Quantidade de Contribu"))
    total = next(c for c in wide.columns if "Soma de RB4" in c)
    accumulated = next(c for c in wide.columns if "RB4 Acumulado" in c)
    assert v.loc[v["partition"], count].sum() == v.loc[v["row"] <= 100, count].sum()
    published = v.loc[v["row"].eq(100), accumulated].item()
    assert v.loc[v["partition"], total].sum() == pytest.approx(published, rel=1e-9)
