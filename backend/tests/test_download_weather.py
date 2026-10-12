import math

import pytest

pytest.importorskip("pandas")  # solo con requirements-ml.txt
from scripts.download_weather import daily  # noqa: E402


def test_daily_aggregates_and_never_turns_missing_hours_into_zero():
    hours = [f"2024-06-12T{i:02d}:00" for i in range(24)] + ["2024-06-13T00:00"]
    d = daily({
        "time": hours,
        "snowfall": [1.0] * 24 + [None],
        "temperature_2m": list(range(-12, 13)),
        "wind_gusts_10m": [None] * 25,
    }).reset_index()

    assert d.loc[0, "snowfall_sum"] == 24
    assert math.isnan(d.loc[1, "snowfall_sum"])  # hora faltante → NaN, no 0
    assert (d.loc[0, "temperature_2m_min"], d.loc[0, "temperature_2m_max"]) == (-12, 11)
    assert math.isnan(d.loc[0, "wind_gusts_10m_max"])
