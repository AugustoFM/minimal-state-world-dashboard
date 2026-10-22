import json
from io import StringIO
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.bankruptcy import (
    cumulative_response,
    exclude_pandemic,
    ols_newey_west,
    read_ipeadata,
    read_serasa_annual,
    read_sidra_events,
    twelve_month_changes,
)


def test_read_ipeadata_parses_month_and_missing_value():
    payload = json.dumps({"value": [
        {"VALDATA": "2020-01-01T00:00:00-03:00", "VALVALOR": 2.5},
        {"VALDATA": "2020-02-01T00:00:00-03:00", "VALVALOR": None},
    ]})
    with patch("pathlib.Path.read_text", return_value=payload):
        result = read_ipeadata("synthetic.json", "x")
    assert result.name == "x"
    assert result.index.tolist() == [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-02-01")]
    assert result.iloc[0] == 2.5
    assert np.isnan(result.iloc[1])


def test_read_sidra_events_pivots_event_series():
    payload = [{"resultados": [{
        "classificacoes": [{"categoria": {"1": "Saída de atividade"}}],
        "series": [{"serie": {"2020": "10", "2021": "12"}}],
    }, {
        "classificacoes": [{"categoria": {"2": "Total de empresas ativas"}}],
        "series": [{"serie": {"2020": "100", "2021": "110"}}],
    }]}]
    with patch("pathlib.Path.read_text", return_value=json.dumps(payload, ensure_ascii=False)):
        result = read_sidra_events("synthetic.json")
    assert result.loc[2021, "saida de atividade"] == 12
    assert result.loc[2020, "total de empresas ativas"] == 100


def test_twelve_month_difference_and_lag_alignment():
    frame = pd.DataFrame({"x": np.arange(20.0)})
    changed = twelve_month_changes(frame, ["x"])
    changed["d12_x_lag6"] = changed["d12_x"].shift(6)
    assert changed["d12_x"].iloc[:12].isna().all()
    assert changed.loc[12, "d12_x"] == 12
    assert np.isnan(changed.loc[17, "d12_x_lag6"])
    assert changed.loc[18, "d12_x_lag6"] == changed.loc[12, "d12_x"]


def test_newey_west_recovers_simulated_slope_and_has_positive_se():
    rng = np.random.default_rng(41)
    n = 500
    x = rng.normal(size=n)
    innovation = rng.normal(scale=0.25, size=n)
    error = np.empty(n)
    error[0] = innovation[0]
    for i in range(1, n):
        error[i] = 0.55 * error[i - 1] + innovation[i]
    y = 1.0 + 0.7 * x + error
    result = ols_newey_west(y, np.column_stack([np.ones(n), x]), lag=18)
    assert abs(result["beta"][1] - 0.7) < 0.06
    assert result["se"][1] > 0


def test_cumulative_response_uses_covariances():
    beta = np.array([9.0, 1.0, 2.0])
    covariance = np.array([[1.0, 0.0, 0.0], [0.0, 4.0, 1.0], [0.0, 1.0, 9.0]])
    estimate, se, low, high = cumulative_response(beta, covariance, [1, 2])
    assert estimate == 3.0
    assert se == np.sqrt(15.0)
    assert low < estimate < high


def test_serasa_method_flag_is_preserved():
    buffer = StringIO()
    pd.DataFrame({
        "year": [2024, 2025], "falencias_requeridas": [10, 11],
        "rj_requeridas": [20, 21], "basis": ["old method", "new method: CNPJs"],
        "source_url": ["a", "b"],
    }).to_csv(buffer, index=False)
    buffer.seek(0)
    result = read_serasa_annual(buffer)
    assert result["serasa_method"].tolist() == ["old method", "new method: CNPJs"]


def test_pandemic_window_exclusion_is_inclusive():
    frame = pd.DataFrame({
        "month": pd.to_datetime(["2020-02-01", "2020-03-01", "2021-12-01", "2022-01-01"]),
        "value": [1, 2, 3, 4],
    })
    result = exclude_pandemic(frame)
    assert result["month"].tolist() == [pd.Timestamp("2020-02-01"), pd.Timestamp("2022-01-01")]
