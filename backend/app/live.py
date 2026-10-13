"""Datos en vivo para predecir: estado oficial, historial de estados, clima reciente y pronóstico JMA."""
import csv
import json
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from functools import wraps

import httpx

from app import config, store
from app.collectors import mendoza_report as mza
from app.collectors import pass_status

# ponytail: Mendoza es UTC-3 fijo (sin horario de verano desde 2009); zoneinfo en Windows exige tzdata.
TZ = timezone(timedelta(hours=-3))
HTTP = httpx.Client(timeout=30, follow_redirects=True)


def today() -> date:
    return datetime.now(TZ).date()


def ttl_cache(seconds: int):
    """Cachea el último resultado de una función sin argumentos durante `seconds`."""
    def deco(fn):
        slot = {"at": 0.0, "value": None}

        @wraps(fn)
        def wrapper():
            if time.monotonic() - slot["at"] > seconds:
                slot["value"], slot["at"] = fn(), time.monotonic()
            return slot["value"]
        return wrapper
    return deco


@ttl_cache(600)
def official_status() -> dict:
    return pass_status.fetch(HTTP)


def to_status(estado: str | None) -> str:
    # El aviso "solo cargas" del feed del Ministerio quedó días desactualizado (12-13/10/2026):
    # de ese feed solo se usa ABIERTO/CERRADO; el detalle sale del parte de Mendoza.
    return "total" if estado == "CERRADO" else "abierto"


@ttl_cache(600)
def mendoza_report() -> dict | None:
    """Parte diario del Gobierno de Mendoza, con `es_de_hoy`. Fuente secundaria: si falla, None."""
    try:
        r = mza.fetch(HTTP)
    except (httpx.HTTPError, ValueError, KeyError):
        return None
    return {**r, "es_de_hoy": r["publicado"][:10] == today().isoformat()}


def current_status(official: dict, report: dict | None) -> str:
    """Abierto/cerrado lo decide el Ministerio (su estado está al día, en vivo);
    si está abierto, el parte de Mendoza del día dice si es solo para camiones."""
    ministry = to_status(official.get("estado"))
    if ministry == "abierto" and report and report["es_de_hoy"] and report["estado"] == "solo_cargas":
        return "solo_cargas"
    return ministry


def _collected_records() -> list[dict]:
    """Registros del registrador (rama data): de GitHub en producción, del disco en local."""
    if not config.GITHUB_TOKEN:
        return list(store.newest_first("status"))
    t = today()
    months = {t.strftime("%Y-%m"), (t.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")}
    records = []
    for month in months:
        r = HTTP.get(f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/status/{month}.jsonl",
                     params={"ref": "data"},
                     headers={"Authorization": f"Bearer {config.GITHUB_TOKEN}", "Accept": "application/vnd.github.raw"})
        if r.status_code == 404:
            continue
        r.raise_for_status()
        records += [json.loads(line) for line in r.text.splitlines() if line]
    return records


@ttl_cache(3600)
def status_history() -> dict[date, str]:
    """Estado por día: closures.csv (histórico curado) + registrador (último registro de cada día)."""
    status: dict[date, str] = {}
    with (config.REPO_DIR / "datasets" / "closures.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d, end = date.fromisoformat(row["start"]), date.fromisoformat(row["end"])
            while d < end:
                status[d] = row["scope"]
                d += timedelta(days=1)
    for r in sorted(_collected_records(), key=lambda r: r["fetched_at"]):
        day = datetime.fromisoformat(r["fetched_at"]).astimezone(TZ).date()
        status[day] = to_status(r.get("estado"))
    return status


WORST = {"snowfall_sum": max, "precipitation_sum": max, "wind_speed_10m_max": max, "snow_depth_max": max,
         "temperature_2m_min": min, "temperature_2m_max": min}


def daily(hourly: dict) -> dict[date, dict]:
    """Igual que scripts/download_weather.daily: suma estricta (None si falta una hora), min/max del resto."""
    by_day = defaultdict(lambda: defaultdict(list))
    for i, ts in enumerate(hourly["time"]):
        for var, values in hourly.items():
            if var != "time":
                by_day[date.fromisoformat(ts[:10])][var].append(values[i])
    out = {}
    for d, v in by_day.items():
        present = lambda var: [x for x in v.get(var, []) if x is not None]
        out[d] = {
            "snowfall_sum": None if None in v.get("snowfall", [None]) else sum(v["snowfall"]),
            "precipitation_sum": None if None in v.get("precipitation", [None]) else sum(v["precipitation"]),
            "wind_speed_10m_max": max(present("wind_speed_10m"), default=None),
            "snow_depth_max": max(present("snow_depth"), default=None),
            "temperature_2m_min": min(present("temperature_2m"), default=None),
            "temperature_2m_max": max(present("temperature_2m"), default=None),
        }
    return out


def _worst(per_location: list[dict[date, dict]]) -> dict[date, dict]:
    """El peor de los dos lados, como en el entrenamiento."""
    out = {}
    for d in set().union(*per_location):
        out[d] = {}
        for var, pick in WORST.items():
            vals = [loc[d][var] for loc in per_location if d in loc and loc[d].get(var) is not None]
            out[d][var] = pick(vals) if vals else None
    return out


def _open_meteo(lat: float, lon: float, **params) -> dict:
    r = HTTP.get(config.OPEN_METEO_URL, params={"latitude": lat, "longitude": lon,
                                                "timezone": "America/Argentina/Mendoza", **params})
    r.raise_for_status()
    return r.json()["hourly"]


@ttl_cache(3600)
def weather() -> tuple[dict[date, dict], dict[date, dict]]:
    """(observado últimos 61 días con best_match, pronóstico JMA a 7 días) — mismas fuentes que el entrenamiento."""
    obs, fc = [], []
    for lat, lon in config.LOCATIONS.values():
        obs.append(daily(_open_meteo(lat, lon, hourly="snowfall,snow_depth,temperature_2m,precipitation,wind_speed_10m",
                                     past_days=61, forecast_days=1)))
        fc.append(daily(_open_meteo(lat, lon, hourly="snowfall,temperature_2m,precipitation,wind_speed_10m",
                                    models="jma_seamless", forecast_days=8)))
    return _worst(obs), _worst(fc)
