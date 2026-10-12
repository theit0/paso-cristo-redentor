"""Features para predecir, en el día de emisión t, si el paso estará cerrado en t+h.

Regla anti-trampa: en t solo se usa (a) el estado del paso hasta t, (b) clima observado hasta t-1
y (c) pronósticos emitidos durante t (lead = días entre emisión y día pronosticado).
La predicción se considera emitida al final del día t.
"""
import numpy as np
import pandas as pd

from app.ml.data import DATASETS

HORIZONS = range(1, 8)  # hay pronóstico archivado hasta 7 días
FORECAST_MODEL = "jma_seamless"  # el único con historia desde 2022; usar el mismo al predecir en vivo


def load_weather() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clima diario combinando ambos puntos: el peor de los dos lados (más nieve, más viento, más frío)."""
    worst = {"snowfall_sum": "max", "precipitation_sum": "max", "wind_speed_10m_max": "max",
             "temperature_2m_min": "min", "temperature_2m_max": "min"}
    obs = pd.read_csv(DATASETS / "weather_observed.csv", parse_dates=["date"])
    obs = obs.groupby("date").agg({**worst, "snow_depth_max": "max"}).asfreq("D")
    fc = pd.read_csv(DATASETS / "weather_forecast.csv", parse_dates=["date"])
    fc = fc[fc["model"] == FORECAST_MODEL].groupby(["date", "lead"]).agg(worst)
    return obs, fc


def state_features(status: pd.Series) -> pd.DataFrame:
    closed = status != "abierto"
    run = closed.groupby((closed != closed.shift()).cumsum()).cumcount() + 1
    return pd.DataFrame({
        "closed_t": closed.astype(int),
        "solo_cargas_t": (status == "solo_cargas").astype(int),
        "dias_en_estado": run.clip(upper=60),
    })


def past_weather_features(obs: pd.DataFrame) -> pd.DataFrame:
    snow = obs["snowfall_sum"]
    big_snow = snow >= 5
    since = big_snow.groupby(big_snow.cumsum()).cumcount()
    f = pd.DataFrame({
        "nieve_3d": snow.rolling(3).sum(),
        "nieve_7d": snow.rolling(7).sum(),
        "nieve_14d": snow.rolling(14).sum(),
        "nieve_suelo": obs["snow_depth_max"],
        "dias_sin_nevada": since.where(big_snow.cumsum() > 0).clip(upper=60),
        "temp_min_ayer": obs["temperature_2m_min"],
    })
    return f.shift(1)  # en t solo se conoce hasta t-1


def forecast_features(fc: pd.DataFrame, index: pd.DatetimeIndex, h: int) -> pd.DataFrame:
    """Pronóstico emitido en t para t+1..t+h: el día objetivo y lo acumulado hasta él."""
    def day(k: int) -> pd.DataFrame:  # pronóstico para t+k emitido k días antes, indexado por t
        return fc.xs(k, level="lead").reindex(index + pd.Timedelta(days=k)).set_axis(index)

    target = day(h)
    window = [day(k) for k in range(1, h + 1)]
    return pd.DataFrame({
        "fc_nieve": target["snowfall_sum"],
        "fc_precip": target["precipitation_sum"],
        "fc_viento": target["wind_speed_10m_max"],
        "fc_temp_min": target["temperature_2m_min"],
        "fc_temp_max": target["temperature_2m_max"],
        "fc_nieve_acum": sum(d["snowfall_sum"] for d in window),
        "fc_nieve_max_dia": pd.concat([d["snowfall_sum"] for d in window], axis=1).max(axis=1),
    }, index=index)


def build(status: pd.Series) -> pd.DataFrame:
    """Tabla de entrenamiento: una fila por (t, h), con y = cerrado en t+h."""
    obs, fc = load_weather()
    idx = status.index
    closed = status != "abierto"
    base = state_features(status).join(past_weather_features(obs).reindex(idx))
    doy = idx.dayofyear
    rows = []
    for h in HORIZONS:
        target_doy = (doy + h - 1) % 365 + 1
        f = base.join(forecast_features(fc, idx, h)).assign(
            h=h,
            estacion_sin=np.sin(2 * np.pi * target_doy / 365),
            estacion_cos=np.cos(2 * np.pi * target_doy / 365),
            y=closed.shift(-h),
            target_date=idx + pd.Timedelta(days=h),
        )
        rows.append(f.dropna(subset=["y"]))
    out = pd.concat(rows)
    out["y"] = out["y"].astype(bool)
    # La misma tormenta pesa distinto si el paso ya está cerrado (demora la reapertura) y según la anticipación.
    out["x_cerrado_precip"] = out["closed_t"] * out["fc_precip"]
    out["x_cerrado_nieve_acum"] = out["closed_t"] * out["fc_nieve_acum"]
    out["x_cerrado_dias"] = out["closed_t"] * out["dias_en_estado"]
    out["x_h_precip"] = out["h"] * out["fc_precip"]
    return out


FEATURES = ["closed_t", "solo_cargas_t", "dias_en_estado", "nieve_3d", "nieve_7d", "nieve_14d",
            "nieve_suelo", "dias_sin_nevada", "temp_min_ayer", "fc_nieve", "fc_precip", "fc_viento",
            "fc_temp_min", "fc_temp_max", "fc_nieve_acum", "fc_nieve_max_dia", "h",
            "estacion_sin", "estacion_cos",
            "x_cerrado_precip", "x_cerrado_nieve_acum", "x_cerrado_dias", "x_h_precip"]
