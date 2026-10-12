from itertools import islice

from fastapi import APIRouter, HTTPException, Query

from app import store

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


@router.get("/forecast/{location}")
def latest_forecast(location: str):
    f = next((f for f in store.newest_first("forecast") if f["location"] == location), None)
    if f is None:
        raise HTTPException(404, f"Sin pronóstico para {location}")
    return {"fetched_at": f["fetched_at"], **f["data"]}
