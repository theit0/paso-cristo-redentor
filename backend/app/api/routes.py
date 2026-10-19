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


def forecast() -> tuple[date, dict, dict[date, float]]:
    """Hoy, historial de estados y P(cerrado) para los próximos 1–7 días. La usan /year y el registrador."""
    today = live.today()
    official = live.official_status()
    status = {**live.status_history(), today: live.current_status(official, live.mendoza_report())}
    obs, fc = live.weather()
    days = (today + timedelta(days=h) for h in range(1, predict.MAX_HORIZON + 1))
    return today, status, {d: prob_closed(d, today, status, obs, fc) for d in days}


@router.get("/year")
def year(anio: int | None = None):
    """Todos los días de `anio` (por defecto, el en curso): pasados = real, hoy = estado oficial,
    1–7 días = predicción, más adelante = sin dato (null): no hay pronóstico a esa distancia.
    Pasado y hoy traen `predicho` (lo que se había predicho, si el registrador lo guardó) y `acerto`;
    `aciertos` cuenta todos los días con predicción desde que existe la app."""
    try:
        today, status, probs = forecast()
        made = live.past_predictions()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"No se pudo obtener datos en vivo: {e}") from e
    anio = anio or today.year
    first = min(status).year  # closures.csv tiene el histórico real desde antes de la app (sin predicciones)
    if not first <= anio <= today.year:
        raise HTTPException(404, f"Sin datos para {anio}")

    def hit(d: date) -> bool:
        return (made[d] > UMBRAL_CERRADO) == (status.get(d, "abierto") != "abierto")

    checked = [hit(d) for d in made if d <= today]
    days, d = [], date(anio, 1, 1)
    while d.year == anio:
        prob = predicho = acerto = None  # prob: solo los días predichos; pasado y hoy son dato real
        if d <= today:
            cerrado = status.get(d, "abierto") != "abierto"
            predicho = made.get(d)
            acerto = None if predicho is None else hit(d)
        elif d in probs:
            prob = probs[d]
            cerrado = prob > UMBRAL_CERRADO
        else:
            cerrado = None
        days.append({"fecha": d.isoformat(), "cerrado": cerrado, "prob_cerrado": None if prob is None else round(prob, 3),
                     "predicho": predicho, "acerto": acerto})
        d += timedelta(days=1)
    return {"hoy": today.isoformat(), "anio": anio, "primer_anio": first, "dias": days,
            "aciertos": {"acertados": sum(checked), "total": len(checked)}}
