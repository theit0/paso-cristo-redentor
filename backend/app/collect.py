"""Registrador: guarda una foto del estado del paso (Ministerio), del parte de Mendoza
y de la predicción de los próximos 7 días (para después ver si acertó).

Uso: python -m app.collect [status] [mendoza] [prediccion]   (sin argumentos: todos)
Sale con código 1 si alguna fuente falló, después de guardar las que funcionaron.
"""
import argparse
import logging
import sys
from datetime import datetime, timezone

import httpx

from app import config, store
from app.collectors import mendoza_report, pass_status

log = logging.getLogger("collect")


def collect_status(client: httpx.Client, now: str) -> None:
    s = pass_status.fetch(client)
    store.append("status", {"fetched_at": now, **s})
    log.info("estado: %s / %s", s["estado"], s["estado_vialidad"])


def collect_mendoza(client: httpx.Client, now: str) -> None:
    r = mendoza_report.fetch(client)
    store.append("mendoza", {"fetched_at": now, **r})
    log.info("parte Mendoza (%s): %s", r["publicado"], r["aviso"])


def collect_prediccion(client: httpx.Client, now: str) -> None:
    from app.api.routes import forecast  # acá adentro: el registrador no necesita FastAPI para lo demás

    probs = forecast()[2]
    store.append("prediccion", {"fetched_at": now, "prob_cerrado": {d.isoformat(): round(p, 3) for d, p in probs.items()}})
    log.info("predicción: %s", {d.isoformat(): round(p, 2) for d, p in probs.items()})


# El pronóstico no se guarda: Open-Meteo ya lo archiva (Previous Runs API, de ahí sale el entrenamiento).
COLLECTORS = {"status": collect_status, "mendoza": collect_mendoza, "prediccion": collect_prediccion}


def run(kinds: list[str]) -> bool:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ok = True
    with httpx.Client(timeout=30, follow_redirects=True, verify=config.SSL) as client:
        for kind in kinds:
            try:
                COLLECTORS[kind](client, now)
            except Exception:
                log.exception("falló %s", kind)
                ok = False
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("kinds", nargs="*", choices=list(COLLECTORS), default=list(COLLECTORS))
    sys.exit(0 if run(parser.parse_args().kinds) else 1)
