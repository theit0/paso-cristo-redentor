"""Lo que más importa de las features: que en t no se use nada que todavía no se sabía."""
import numpy as np
import pytest

pd = pytest.importorskip("pandas")
from app.ml.features import forecast_features, past_weather_features, state_features  # noqa: E402

DAYS = pd.date_range("2024-06-01", periods=10)


def test_past_weather_only_uses_up_to_yesterday():
    snow = np.zeros(10)
    snow[4] = 20  # nevada el 5/6
    obs = pd.DataFrame({"snowfall_sum": snow, "snow_depth_max": snow / 100, "temperature_2m_min": -5.0}, index=DAYS)
    f = past_weather_features(obs)
    assert f.loc["2024-06-05", "nieve_3d"] == 0  # el mismo día todavía no se conoce
    assert f.loc["2024-06-06", "nieve_3d"] == 20
    assert f.loc["2024-06-06", "dias_sin_nevada"] == 0
    assert f.loc["2024-06-08", "dias_sin_nevada"] == 2


def test_forecast_uses_lead_equal_to_days_ahead():
    # pronóstico para el día d con anticipación k: nieve = 10*k + día del mes, para distinguir cada combinación
    rows = [(d, k, 10 * k + d.day) for d in DAYS for k in range(1, 8)]
    fc = pd.DataFrame(rows, columns=["date", "lead", "snowfall_sum"]).assign(
        precipitation_sum=0.0, wind_speed_10m_max=0.0, temperature_2m_min=0.0, temperature_2m_max=0.0,
    ).set_index(["date", "lead"])
    f = forecast_features(fc, DAYS, h=2)
    # emitido el 1/6 para el 3/6 → lead 2 del 3/6 = 23; acumulado = (lead 1 del 2/6 = 12) + 23
    assert f.loc["2024-06-01", "fc_nieve"] == 23
    assert f.loc["2024-06-01", "fc_nieve_acum"] == 12 + 23
    assert np.isnan(f.loc["2024-06-10", "fc_nieve"])  # fuera del rango: NaN, no se inventa


def test_state_counts_days_in_current_state():
    status = pd.Series(["abierto", "total", "total", "solo_cargas", "abierto"], index=DAYS[:5])
    s = state_features(status)
    assert s["closed_t"].tolist() == [0, 1, 1, 1, 0]
    assert s["dias_en_estado"].tolist() == [1, 1, 2, 3, 1]
    assert s["solo_cargas_t"].tolist() == [0, 0, 0, 1, 0]
