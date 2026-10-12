from datetime import date, timedelta
from itertools import islice

import httpx
from fastapi import APIRouter, HTTPException, Query

from app import live, predict, store

router = APIRouter(prefix="/api")


def public(status: dict) -> dict:
    return {k: v for k, v in status.items() if k != "raw"}


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/status")
def latest_status():
    latest = next(store.newest_first("status"), None)
    if latest is None:
        raise HTTPException(404, "Sin datos todavía: ver README (rama data)")
    return public(latest)


@router.get("/status/history")
def status_history(limit: int = Query(168, ge=1, le=5000)):
    return [public(s) for s in islice(store.newest_first("status"), limit)]


def verdict(p: float) -> str:
    return "cerrado" if p >= 0.65 else "abierto" if p <= 0.35 else "incierto"


def predict_one(target: date, today: date, official: dict, status: dict, obs: dict, fc: dict) -> dict:
    h = (target - today).days
    if h == 0:  # hoy: manda el estado oficial
        p, fuente, confianza = (1.0 if live.to_status(official["estado"]) != "abierto" else 0.0), "estado_oficial", "alta"
    elif h <= predict.MAX_HORIZON:
        p = predict.probability(predict.features_row(status, obs, fc, today, h))
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
    }


@router.get("/predict")
def predict_endpoint(date_: date | None = Query(None, alias="date", description="AAAA-MM-DD; sin fecha: próximos 8 días")):
    today = live.today()
    if date_ is not None and not 0 <= (date_ - today).days <= 365:
        raise HTTPException(422, "La fecha tiene que estar entre hoy y dentro de un año")
    try:
        official = live.official_status()
        status = {**live.status_history(), today: live.to_status(official["estado"])}
        obs, fc = live.weather()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"No se pudo obtener datos en vivo: {e}") from e
    targets = [date_] if date_ else [today + timedelta(days=k) for k in range(8)]
    return {
        "hoy": today.isoformat(),
        "estado_actual": {k: official[k] for k in ("estado", "estado_vialidad", "horario", "horario_cancilleria", "source_time")},
        "modelo": predict.model()["version"],
        "predicciones": [predict_one(t, today, official, status, obs, fc) for t in targets],
    }


@router.get("/forecast/{location}")
def latest_forecast(location: str):
    f = next((f for f in store.newest_first("forecast") if f["location"] == location), None)
    if f is None:
        raise HTTPException(404, f"Sin pronóstico para {location}")
    return {"fetched_at": f["fetched_at"], **f["data"]}
