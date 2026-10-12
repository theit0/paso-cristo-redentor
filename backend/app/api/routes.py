import json

from fastapi import APIRouter, HTTPException, Query

from app import db

router = APIRouter(prefix="/api")

STATUS_COLS = "fetched_at, source_time, estado, estado_vialidad, horario, horario_cancilleria"


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/status")
def latest_status():
    with db.connect() as conn:
        row = conn.execute(f"SELECT {STATUS_COLS} FROM pass_status ORDER BY fetched_at DESC LIMIT 1").fetchone()
    if row is None:
        raise HTTPException(404, "Sin datos todavía: correr `python -m app.collect`")
    return dict(row)


@router.get("/status/history")
def status_history(limit: int = Query(168, le=5000)):
    with db.connect() as conn:
        rows = conn.execute(f"SELECT {STATUS_COLS} FROM pass_status ORDER BY fetched_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


@router.get("/forecast/{location}")
def latest_forecast(location: str):
    with db.connect() as conn:
        row = conn.execute(
            "SELECT fetched_at, raw FROM forecast WHERE location = ? ORDER BY fetched_at DESC LIMIT 1", (location,)
        ).fetchone()
    if row is None:
        raise HTTPException(404, f"Sin pronóstico para {location}")
    return {"fetched_at": row["fetched_at"], **json.loads(row["raw"])}
