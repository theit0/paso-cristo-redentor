from datetime import date, timedelta

import httpx
from fastapi import APIRouter, HTTPException

from app import live, predict

router = APIRouter(prefix="/api")

# Rojo solo si P(cerrado) > 50%; el 50% justo queda verde.
# (Con 35% se detectaban 73% de los cierres en vez de 63%, a costa de más rojos falsos.)
UMBRAL_CERRADO = 0.5


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/snowmap")
def snowmap():
    """Nieve nueva y lluvia por día en la zona del paso, próximos 8 días (para el mapita del hover)."""
    try:
        return live.snow_map()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"No se pudo obtener el mapa de nieve: {e}") from e


def prob_closed(target: date, today: date, status: dict, obs: dict, fc: dict) -> float:
    """Modelo con pronóstico, para 1 a 7 días."""
    return predict.probability(predict.features_row(status, obs, fc, today, (target - today).days))


@router.get("/year")
def year():
    """Todos los días del año en curso: pasados = real, hoy = estado oficial, 1–7 días = predicción,
    más adelante = sin dato (null): no hay pronóstico a esa distancia."""
    today = live.today()
    try:
        official = live.official_status()
        status = {**live.status_history(), today: live.current_status(official, live.mendoza_report())}
        obs, fc = live.weather()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"No se pudo obtener datos en vivo: {e}") from e

    days, d = [], date(today.year, 1, 1)
    while d.year == today.year:
        prob = None  # solo los días predichos tienen probabilidad; pasado y hoy son dato real
        if d <= today:
            cerrado = status.get(d, "abierto") != "abierto"
        elif (d - today).days <= predict.MAX_HORIZON:
            prob = prob_closed(d, today, status, obs, fc)
            cerrado = prob > UMBRAL_CERRADO
        else:
            cerrado = None
        days.append({"fecha": d.isoformat(), "cerrado": cerrado, "prob_cerrado": None if prob is None else round(prob, 3)})
        d += timedelta(days=1)
    return {"hoy": today.isoformat(), "dias": days}
