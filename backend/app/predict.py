"""Predicción en producción, en Python puro (sin pandas/sklearn).

Replica exactamente app/ml/features.py; tests/test_predict.py verifica que ambos den lo mismo.
"""
import json
import math
from datetime import date, timedelta
from functools import cache
from pathlib import Path

MODEL_PATH = Path(__file__).with_name("model.json")
MAX_HORIZON = 7  # más allá no hay pronóstico en el entrenamiento → climatología

Daily = dict[date, dict]  # día → {"snowfall_sum": ..., ...}


@cache
def model() -> dict:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def run_length(status: dict[date, str], today: date, cap: int = 60) -> int:
    """Días consecutivos (incluido hoy) en el mismo estado abierto/cerrado. Días sin dato = abierto."""
    closed = lambda d: status.get(d, "abierto") != "abierto"
    state, n, d = closed(today), 0, today
    while n < cap and closed(d) == state:
        n += 1
        d -= timedelta(days=1)
    return n


def _sum(values):
    return None if any(v is None for v in values) else sum(values)


def features_row(status: dict[date, str], obs: Daily, fc: Daily, today: date, h: int) -> dict:
    """status: estado por día hasta hoy. obs: clima observado por día (hasta ayer).
    fc: pronóstico emitido hoy, por día pronosticado (today+1 … today+7)."""
    past = lambda var, k: [obs.get(today - timedelta(days=i), {}).get(var) for i in range(1, k + 1)]
    snow = past("snowfall_sum", 61)
    big = [i for i, s in enumerate(snow) if s is not None and s >= 5]  # i=0 es ayer
    window = [fc.get(today + timedelta(days=k), {}) for k in range(1, h + 1)]
    target = window[-1]
    window_snow = [d.get("snowfall_sum") for d in window]
    target_doy = (today.timetuple().tm_yday + h - 1) % 365 + 1

    current = status.get(today, "abierto")
    closed_t = int(current != "abierto")
    dias = run_length(status, today)
    row = {
        "closed_t": closed_t,
        "solo_cargas_t": int(current == "solo_cargas"),
        "dias_en_estado": dias,
        "nieve_3d": _sum(snow[:3]),
        "nieve_7d": _sum(snow[:7]),
        "nieve_14d": _sum(snow[:14]),
        "nieve_suelo": past("snow_depth_max", 1)[0],
        "dias_sin_nevada": min(big[0], 60) if big else 60,
        "temp_min_ayer": past("temperature_2m_min", 1)[0],
        "fc_nieve": target.get("snowfall_sum"),
        "fc_precip": target.get("precipitation_sum"),
        "fc_viento": target.get("wind_speed_10m_max"),
        "fc_temp_min": target.get("temperature_2m_min"),
        "fc_temp_max": target.get("temperature_2m_max"),
        "fc_nieve_acum": _sum(window_snow),
        "fc_nieve_max_dia": max((s for s in window_snow if s is not None), default=None),
        "h": h,
        "estacion_sin": math.sin(2 * math.pi * target_doy / 365),
        "estacion_cos": math.cos(2 * math.pi * target_doy / 365),
    }
    mult = lambda a, b: None if a is None or b is None else a * b
    row["x_cerrado_precip"] = mult(closed_t, row["fc_precip"])
    row["x_cerrado_nieve_acum"] = mult(closed_t, row["fc_nieve_acum"])
    row["x_cerrado_dias"] = closed_t * dias
    row["x_h_precip"] = mult(h, row["fc_precip"])
    return row


def probability(row: dict) -> float:
    """Imputa con la mediana, estandariza y aplica la regresión logística exportada."""
    m = model()
    z = m["intercepto"]
    for name, med, mu, sd, w in zip(m["features"], m["medianas"], m["media"], m["escala"], m["coef"]):
        x = row[name] if row[name] is not None else med
        z += w * (x - mu) / sd
    return 1 / (1 + math.exp(-z))


def climatology(target: date) -> float:
    return model()["climatologia"][target.timetuple().tm_yday - 1]
