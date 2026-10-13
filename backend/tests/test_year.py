from datetime import date

from fastapi.testclient import TestClient

from app import live
from app.api import routes
from app.main import app


def test_year_past_is_real_and_future_uses_threshold(monkeypatch):
    monkeypatch.setattr(live, "today", lambda: date(2026, 10, 13))
    monkeypatch.setattr(live, "official_status", lambda: {"estado": "ABIERTO"})
    monkeypatch.setattr(live, "mendoza_report", lambda: None)
    monkeypatch.setattr(live, "status_history", lambda: {date(2026, 7, 20): "total", date(2026, 8, 20): "solo_cargas"})
    monkeypatch.setattr(live, "weather", lambda: ({}, {}))
    # futuro: cerrado solo los días con probabilidad >= umbral
    monkeypatch.setattr(routes, "prob_closed", lambda d, *a: 0.5 if d == date(2026, 10, 14) else 0.2)

    r = TestClient(app).get("/api/year").json()
    by = {d["fecha"]: d["cerrado"] for d in r["dias"]}
    assert r["hoy"] == "2026-10-13" and len(r["dias"]) == 365
    assert by["2026-07-20"] and by["2026-08-20"]  # real; solo camiones cuenta como cerrado
    assert not by["2026-07-21"]
    assert not by["2026-10-13"]  # hoy: estado oficial
    assert by["2026-10-14"] and not by["2026-10-15"]
