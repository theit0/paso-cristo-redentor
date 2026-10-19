"""Datos en vivo para predecir: estado oficial, historial de estados, clima reciente y pronóstico JMA."""
import csv
import json
import threading
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
HTTP = httpx.Client(timeout=30, follow_redirects=True, verify=config.SSL)


def today() -> date:
    return datetime.now(TZ).date()


def ttl_cache(seconds: int):
    """Cachea el último resultado de una función sin argumentos durante `seconds`.
    El lock evita que varios pedidos simultáneos con el caché vencido salgan todos a la API externa."""
    def deco(fn):
        slot = {"at": 0.0, "value": None}
        lock = threading.Lock()

        @wraps(fn)
        def wrapper():
            with lock:
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


def _collected_records(kind: str) -> list[dict]:
    """Registros del registrador (rama data): de GitHub en producción (últimos 2 meses), del disco en local."""
    if not config.GITHUB_TOKEN:
        return list(store.newest_first(kind))
    t = today()
    months = {t.strftime("%Y-%m"), (t.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")}
    records = []
    for month in months:
        r = HTTP.get(f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{kind}/{month}.jsonl",
                     params={"ref": "data"},
                     headers={"Authorization": f"Bearer {config.GITHUB_TOKEN}", "Accept": "application/vnd.github.raw"})
        if r.status_code == 404:
            continue
        r.raise_for_status()
        records += [json.loads(line) for line in r.text.splitlines() if line]
    return records


def registrador_days(status_records: list[dict], mendoza_records: list[dict]) -> dict[date, str]:
    """Estado por día según el registrador, con la misma regla que current_status: el último registro
    del Ministerio decide abierto/cerrado y, si está abierto, el parte de Mendoza de ese día dice si es solo cargas.
    Lo usan la app (historial) y el reentrenamiento (app.ml.data), así ven lo mismo."""
    days: dict[date, str] = {}
    for r in sorted(status_records, key=lambda r: r["fetched_at"]):
        days[datetime.fromisoformat(r["fetched_at"]).astimezone(TZ).date()] = to_status(r.get("estado"))
    for r in sorted(mendoza_records, key=lambda r: r["fetched_at"]):
        d = date.fromisoformat(r["publicado"][:10])  # el parte vale para el día en que se publicó
        if days.get(d) == "abierto" and r.get("estado") == "solo_cargas":
            days[d] = "solo_cargas"
    return days


def closures_days() -> dict[date, str]:
    """datasets/closures.csv (histórico curado a mano) → estado por día; los días que faltan son abiertos."""
    status: dict[date, str] = {}
    with (config.REPO_DIR / "datasets" / "closures.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d, end = date.fromisoformat(row["start"]), date.fromisoformat(row["end"])
            while d < end:
                status[d] = row["scope"]
                d += timedelta(days=1)
    return status


@ttl_cache(3600)
def status_history() -> dict[date, str]:
    """Estado por día: closures.csv (histórico curado) + registrador."""
    return {**closures_days(), **registrador_days(_collected_records("status"), _collected_records("mendoza"))}


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


@ttl_cache(3 * 3600)
def snow_map() -> dict:
    """Lo que cae cada día en una grilla alrededor del paso, para los próximos 8 días: nieve nueva (cm) y lluvia (mm).
    (La nieve acumulada en el suelo casi no cambia de un día a otro; lo que cambia, y lo que muestra snow-forecast,
    es lo que cae.) Un solo pedido con todos los puntos; cada punto cuenta como una llamada, por eso el caché largo."""
    lat0, lat1, lon0, lon1 = config.SNOWMAP_BBOX
    rows, cols = config.SNOWMAP_GRID
    pts = [(lat0 + (lat1 - lat0) * r / (rows - 1), lon0 + (lon1 - lon0) * c / (cols - 1))
           for r in range(rows) for c in range(cols)]
    r = HTTP.get(config.OPEN_METEO_URL, params={
        "latitude": ",".join(f"{a:.3f}" for a, _ in pts), "longitude": ",".join(f"{b:.3f}" for _, b in pts),
        "daily": "snowfall_sum,rain_sum", "forecast_days": 8, "timezone": "America/Argentina/Mendoza",
    }, timeout=60)
    r.raise_for_status()
    points = r.json()
    days = {}
    for i, day in enumerate(points[0]["daily"]["time"]):
        days[day] = {
            "nieve": [round(p["daily"]["snowfall_sum"][i] or 0, 1) for p in points],
            "lluvia": [round(p["daily"]["rain_sum"][i] or 0, 1) for p in points],
        }
    return {"bbox": config.SNOWMAP_BBOX, "rows": rows, "cols": cols, "dias": days}


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
