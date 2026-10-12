"""Registrador: guarda una foto del estado del paso y/o del pronóstico.

Uso: python -m app.collect [status] [forecast]   (sin argumentos: ambos)
Sale con código 1 si alguna fuente falló, después de guardar las que funcionaron.
"""
import argparse
import logging
import sys
from datetime import datetime, timezone

import httpx

from app import store
from app.collectors import forecast, pass_status

log = logging.getLogger("collect")


def collect_status(client: httpx.Client, now: str) -> None:
    s = pass_status.fetch(client)
    store.append("status", {"fetched_at": now, **s})
    log.info("estado: %s / %s", s["estado"], s["estado_vialidad"])


def collect_forecast(client: httpx.Client, now: str) -> None:
    for loc, data in forecast.fetch(client).items():
        store.append("forecast", {"fetched_at": now, "location": loc, "data": data})
    log.info("pronóstico guardado")


COLLECTORS = {"status": collect_status, "forecast": collect_forecast}


def run(kinds: list[str]) -> bool:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ok = True
    with httpx.Client(timeout=30, follow_redirects=True) as client:
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
