"""Registrador: guarda una foto del estado del paso (Ministerio) y del parte de Mendoza.

Uso: python -m app.collect [status] [mendoza]   (sin argumentos: todos)
Sale con código 1 si alguna fuente falló, después de guardar las que funcionaron.
"""
import argparse
import logging
import sys
from datetime import datetime, timezone

import httpx

from app import store
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


# El pronóstico no se guarda: Open-Meteo ya lo archiva (Previous Runs API, de ahí sale el entrenamiento).
COLLECTORS = {"status": collect_status, "mendoza": collect_mendoza}


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
