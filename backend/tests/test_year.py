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
    # futuro: cerrado solo si la probabilidad supera el umbral; 50% justo es abierto
    probs = {date(2026, 10, 14): 0.51, date(2026, 10, 16): 0.5}
    monkeypatch.setattr(routes, "prob_closed", lambda d, *a: probs.get(d, 0.2))

    r = TestClient(app).get("/api/year").json()
    by = {d["fecha"]: d["cerrado"] for d in r["dias"]}
    assert r["hoy"] == "2026-10-13" and len(r["dias"]) == 365
    assert by["2026-07-20"] and by["2026-08-20"]  # real; solo camiones cuenta como cerrado
    assert not by["2026-07-21"]
    assert not by["2026-10-13"]  # hoy: estado oficial
    assert by["2026-10-14"] and not by["2026-10-15"] and not by["2026-10-16"]
    assert by["2026-10-20"] is not None and by["2026-10-21"] is None  # más de 7 días: sin dato
    prob = {d["fecha"]: d["prob_cerrado"] for d in r["dias"]}
    assert prob["2026-10-14"] == 0.51 and prob["2026-10-13"] is None and prob["2026-10-21"] is None


def test_registrador_days_combines_ministry_and_mendoza():
    status = [
        {"fetched_at": "2026-07-01T12:00:00+00:00", "estado": "CERRADO"},
        {"fetched_at": "2026-07-02T02:00:00+00:00", "estado": "ABIERTO"},  # 23 h del 1/7 en Mendoza: el último manda
        {"fetched_at": "2026-07-02T15:00:00+00:00", "estado": "ABIERTO"},
        {"fetched_at": "2026-07-03T15:00:00+00:00", "estado": "ABIERTO"},
    ]
    mendoza = [
        {"fetched_at": "2026-07-02T14:00:00+00:00", "publicado": "2026-07-02T09:00:00", "estado": "solo_cargas"},
        {"fetched_at": "2026-07-03T14:00:00+00:00", "publicado": "2026-07-02T09:00:00", "estado": "solo_cargas"},  # parte viejo
    ]
    assert live.registrador_days(status, mendoza) == {
        date(2026, 7, 1): "abierto", date(2026, 7, 2): "solo_cargas", date(2026, 7, 3): "abierto"}
