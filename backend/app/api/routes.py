from datetime import date, timedelta

import httpx
from fastapi import APIRouter, HTTPException

from app import live, predict

router = APIRouter(prefix="/api")

# Rojo si P(cerrado) >= 35%. Con el mismo % de aciertos que 50%, detecta 73% de los cierres
# en vez de 63%: un verde equivocado (viajar y encontrarlo cerrado) cuesta más que un rojo equivocado.
UMBRAL_CERRADO = 0.35


@router.get("/health")
def health():
    return {"ok": True}


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
        if d <= today:
            cerrado = status.get(d, "abierto") != "abierto"
        elif (d - today).days <= predict.MAX_HORIZON:
            cerrado = prob_closed(d, today, status, obs, fc) >= UMBRAL_CERRADO
        else:
            cerrado = None
        days.append({"fecha": d.isoformat(), "cerrado": cerrado})
        d += timedelta(days=1)
    return {"hoy": today.isoformat(), "dias": days}
