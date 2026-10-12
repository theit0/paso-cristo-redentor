"""Registrador: guarda una foto del estado del paso y del pronóstico.

Uso: python -m app.collect   (correrlo cada hora)
"""
import json
import logging
from datetime import datetime, timezone

import httpx

from app import db
from app.collectors import forecast, pass_status

log = logging.getLogger("collect")


def run() -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with httpx.Client(timeout=30, follow_redirects=True) as client, db.connect() as conn:
        # Cada fuente por separado: si una falla, la otra igual se guarda.
        try:
            s = pass_status.fetch(client)
            conn.execute(
                "INSERT INTO pass_status (fetched_at, source_time, estado, estado_vialidad, horario, horario_cancilleria, raw)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (now, s["source_time"], s["estado"], s["estado_vialidad"], s["horario"],
                 s["horario_cancilleria"], json.dumps(s["raw"], ensure_ascii=False)),
            )
            log.info("estado: %s / %s", s["estado"], s["estado_vialidad"])
        except Exception:
            log.exception("falló estado del paso")
        try:
            for loc, data in forecast.fetch(client).items():
                conn.execute("INSERT INTO forecast (fetched_at, location, raw) VALUES (?, ?, ?)",
                             (now, loc, json.dumps(data)))
            log.info("pronóstico guardado")
        except Exception:
            log.exception("falló pronóstico")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
