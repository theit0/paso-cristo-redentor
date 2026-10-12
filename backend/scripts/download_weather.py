"""Baja el clima histórico de Open-Meteo y lo resume por día (hora de Mendoza).

- weather_observed.csv: Historical Forecast API (primeras horas de cada corrida ≈ lo que pasó).
- weather_forecast.csv: Previous Runs API, lo que se pronosticaba con 1–7 días de anticipación.
  Esto es lo que el modelo puede usar sin hacer trampa.

Uso (desde backend/): python -m scripts.download_weather
"""
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import httpx
import pandas as pd

from app.config import LOCATIONS

OUT = Path(__file__).resolve().parents[2] / "datasets"
TZ = "America/Argentina/Mendoza"
START = date(2022, 1, 1)
CHUNK = timedelta(days=90)
LEADS = range(1, 8)

OBSERVED_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
OBSERVED_VARS = ["temperature_2m", "precipitation", "snowfall", "snow_depth", "wind_speed_10m",
                 "wind_gusts_10m", "freezing_level_height", "visibility", "cloud_cover"]

PREVIOUS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
FORECAST_VARS = ["temperature_2m", "precipitation", "snowfall", "wind_speed_10m", "wind_gusts_10m", "cloud_cover"]
# jma_seamless es el único con nieve/precipitación archivada desde 2022 (no trae ráfagas);
# best_match es mejor pero arranca en 2024.
FORECAST_MODELS = {"jma_seamless": date(2022, 1, 1), "best_match": date(2024, 1, 1)}


def strict_sum(s: pd.Series) -> float:
    return s.sum(min_count=len(s))  # si falta alguna hora, NaN en vez de subestimar


AGG = {
    "precipitation": [strict_sum], "snowfall": [strict_sum],
    "temperature_2m": ["min", "max"], "wind_speed_10m": ["max"], "wind_gusts_10m": ["max"],
    "cloud_cover": ["mean"], "freezing_level_height": ["min"], "snow_depth": ["max"], "visibility": ["min"],
}


def daily(hourly: dict) -> pd.DataFrame:
    df = pd.DataFrame(hourly)
    df["date"] = pd.to_datetime(df.pop("time")).dt.date
    out = df.groupby("date").agg({c: AGG[c] for c in df.columns if c in AGG})
    out.columns = [f"{v}_{'sum' if f == 'strict_sum' else f}" for v, f in out.columns]
    return out.round(2)


def get(client: httpx.Client, url: str, params: dict) -> dict:
    for attempt in range(5):
        try:
            r = client.get(url, params=params)
            if r.status_code == 429:
                raise httpx.HTTPStatusError("429", request=r.request, response=r)
            r.raise_for_status()
            return r.json()["hourly"]
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            wait = 30 * (attempt + 1)
            print(f"  reintento en {wait}s ({e})", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"falló {url} {params}")


def chunks(start: date, end: date):
    while start <= end:
        yield start, min(start + CHUNK - timedelta(days=1), end)
        start += CHUNK


def main() -> None:
    end = date.today() - timedelta(days=1)
    observed, forecast = [], []
    with httpx.Client(timeout=120) as client:
        for loc, (lat, lon) in LOCATIONS.items():
            base = {"latitude": lat, "longitude": lon, "timezone": TZ}
            for a, b in chunks(START, end):
                print(f"{loc} observado {a}", file=sys.stderr)
                h = get(client, OBSERVED_URL, {**base, "hourly": ",".join(OBSERVED_VARS), "start_date": a, "end_date": b})
                observed.append(daily(h).assign(location=loc))

            for model, model_start in FORECAST_MODELS.items():
                cols = [f"{v}_previous_day{n}" for v in FORECAST_VARS for n in LEADS]
                for a, b in chunks(model_start, end):
                    print(f"{loc} pronóstico {model} {a}", file=sys.stderr)
                    h = get(client, PREVIOUS_URL, {**base, "models": model, "hourly": ",".join(cols),
                                                   "start_date": a, "end_date": b})
                    for n in LEADS:
                        lead = {v: h[f"{v}_previous_day{n}"] for v in FORECAST_VARS}
                        forecast.append(daily({"time": h["time"], **lead}).assign(location=loc, model=model, lead=n))
                    time.sleep(1)

    obs = pd.concat(observed).reset_index()
    obs.insert(1, "location", obs.pop("location"))
    obs.to_csv(OUT / "weather_observed.csv", index=False)

    fc = pd.concat(forecast).reset_index()
    for i, c in enumerate(["location", "model", "lead"], start=1):
        fc.insert(i, c, fc.pop(c))
    fc.to_csv(OUT / "weather_forecast.csv", index=False)
    print(f"observado: {len(obs)} filas, pronóstico: {len(fc)} filas", file=sys.stderr)


if __name__ == "__main__":
    main()
