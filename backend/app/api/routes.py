from datetime import date, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Query

from app import live, predict

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/status")
def official_status():
    """Estado oficial en vivo (caché de 10 min). El historial completo está en la rama `data`."""
    try:
        s = live.official_status()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"No se pudo obtener el estado oficial: {e}") from e
    return {k: v for k, v in s.items() if k != "raw"}


def verdict(p: float) -> str:
    return "cerrado" if p >= 0.65 else "abierto" if p <= 0.35 else "incierto"


def _r(x: float | None, nd: int = 1) -> float | None:
    return None if x is None else round(x, nd)


def weather_of(day: dict | None) -> dict | None:
    """Pronóstico JMA del día (el mismo que usa el modelo), peor de los dos lados del paso."""
    if not day:
        return None
    return {
        "nieve_cm": _r(day.get("snowfall_sum")), "precip_mm": _r(day.get("precipitation_sum")),
        "viento_kmh": _r(day.get("wind_speed_10m_max"), 0),
        "temp_min": _r(day.get("temperature_2m_min"), 0), "temp_max": _r(day.get("temperature_2m_max"), 0),
    }


def predict_one(target: date, today: date, official: dict, status: dict, obs: dict, fc: dict) -> dict:
    h = (target - today).days
    factores = []
    if h == 0:  # hoy: manda el estado oficial
        p, fuente, confianza = (1.0 if status[today] != "abierto" else 0.0), "estado_oficial", "alta"
    elif h <= predict.MAX_HORIZON:
        row = predict.features_row(status, obs, fc, today, h)
        p, factores = predict.probability(row), predict.top_factors(row)
        fuente, confianza = "modelo", "alta" if h <= 3 else "media"
    else:  # sin pronóstico útil: tasa histórica de cierre para esa fecha
        p, fuente, confianza = predict.climatology(target), "climatologia", "baja"
    metricas = predict.model()["metricas_invierno"].get(str(h))
    return {
        "fecha": target.isoformat(),
        "dias_adelante": h,
        "prob_cerrado": round(p, 3),
        "prob_abierto": round(1 - p, 3),
        "veredicto": verdict(p),
        "confianza": confianza,
        "fuente": fuente,
        "aciertos_historicos_invierno": metricas and metricas["aciertos"],
        "clima": weather_of(fc.get(target)) if h <= predict.MAX_HORIZON else None,
        "factores": factores,
        "base_abierto": round(1 - predict.base_probability(), 3) if factores else None,
    }


def context(today: date, status: dict, obs: dict, fc: dict) -> dict:
    """Lo que el modelo sabe de hoy y de los días pasados."""
    row = predict.features_row(status, obs, fc, today, 1)
    suelo = row["nieve_suelo"]
    return {
        "dias_en_estado": row["dias_en_estado"],
        "nieve_3d_cm": _r(row["nieve_3d"]),
        "nieve_7d_cm": _r(row["nieve_7d"]),
        "nieve_14d_cm": _r(row["nieve_14d"]),
        "nieve_suelo_cm": None if suelo is None else round(suelo * 100),  # Open-Meteo da metros
        "dias_sin_nevada": row["dias_sin_nevada"],
        "temp_min_ayer": _r(row["temp_min_ayer"], 0),
    }


@router.get("/predict")
def predict_endpoint(date_: date | None = Query(None, alias="date", description="AAAA-MM-DD; sin fecha: próximos 8 días")):
    today = live.today()
    if date_ is not None and not 0 <= (date_ - today).days <= 365:
        raise HTTPException(422, "La fecha tiene que estar entre hoy y dentro de un año")
    try:
        official = live.official_status()
        report = live.mendoza_report()
        status = {**live.status_history(), today: live.current_status(official, report)}
        obs, fc = live.weather()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"No se pudo obtener datos en vivo: {e}") from e
    targets = [date_] if date_ else [today + timedelta(days=k) for k in range(8)]
    return {
        "hoy": today.isoformat(),
        "estado_actual": {
            **{k: official[k] for k in ("estado", "estado_vialidad", "horario", "horario_cancilleria", "source_time")},
            "estado_hoy": status[today],  # abierto / solo_cargas / total, combinando ambas fuentes
            "parte_mendoza": report,
        },
        "modelo": predict.model()["version"],
        "contexto": context(today, status, obs, fc),
        "predicciones": [predict_one(t, today, official, status, obs, fc) for t in targets],
    }

