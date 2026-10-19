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
    monkeypatch.setattr(live, "past_predictions", lambda: {date(2026, 7, 20): 0.8, date(2026, 7, 21): 0.6})
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
    acerto = {d["fecha"]: d["acerto"] for d in r["dias"]}
    assert acerto["2026-07-20"] is True and acerto["2026-07-21"] is False  # predijo cerrado y estuvo abierto
    assert acerto["2026-07-22"] is None and acerto["2026-10-14"] is None  # sin predicción guardada / futuro
    assert r["aciertos"] == {"acertados": 1, "total": 2}


def test_year_past_year_and_out_of_range(monkeypatch):
    monkeypatch.setattr(live, "today", lambda: date(2027, 3, 1))
    monkeypatch.setattr(live, "official_status", lambda: {"estado": "ABIERTO"})
    monkeypatch.setattr(live, "mendoza_report", lambda: None)
    monkeypatch.setattr(live, "status_history", lambda: {date(2026, 11, 5): "total"})
    monkeypatch.setattr(live, "weather", lambda: ({}, {}))
    monkeypatch.setattr(live, "past_predictions", lambda: {date(2026, 11, 5): 0.9, date(2027, 2, 1): 0.9})
    monkeypatch.setattr(routes, "prob_closed", lambda *a: 0.2)

    c = TestClient(app)
    r = c.get("/api/year?anio=2026").json()
    assert r["anio"] == 2026 and len(r["dias"]) == 365
    assert all(d["prob_cerrado"] is None for d in r["dias"])  # año pasado: todo es dato real
    assert {d["fecha"]: d["acerto"] for d in r["dias"]}["2026-11-05"] is True
    assert r["aciertos"] == {"acertados": 1, "total": 2}  # el total cruza años
    assert r["primer_anio"] == 2026  # el primer año con historial
    assert c.get("/api/year?anio=2025").status_code == 404
    assert c.get("/api/year?anio=2028").status_code == 404


def test_past_predictions_uses_the_last_one_before_noon_of_the_day_before(monkeypatch):
    monkeypatch.setattr(live, "_collected_records", lambda kind: [
        {"fetched_at": "2026-07-01T14:59:00+00:00", "prob_cerrado": {"2026-07-02": 0.9}},  # 11:59 del 1/7: vale
        {"fetched_at": "2026-06-30T20:00:00+00:00", "prob_cerrado": {"2026-07-02": 0.1, "2026-07-03": 0.4}},
        {"fetched_at": "2026-07-01T15:00:00+00:00", "prob_cerrado": {"2026-07-02": 0.5}},  # mediodía del 1/7: tarde
        {"fetched_at": "2026-07-02T15:00:00+00:00", "prob_cerrado": {"2026-07-03": 0.7}},  # mediodía del 2/7: tarde
    ])
    assert live.past_predictions.__wrapped__() == {date(2026, 7, 2): 0.9, date(2026, 7, 3): 0.4}


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



def test_collected_records_reads_every_month_since_launch(monkeypatch):
    asked = []

    class Resp:
        status_code, text = 404, ""

    monkeypatch.setattr(live.config, "GITHUB_TOKEN", "x")
    monkeypatch.setattr(live, "today", lambda: date(2027, 1, 10))
    monkeypatch.setattr(live.HTTP, "get", lambda url, **kw: asked.append(url.rsplit("/", 1)[1]) or Resp())
    live._collected_records("prediccion")
    assert asked == ["2026-10.jsonl", "2026-11.jsonl", "2026-12.jsonl", "2027-01.jsonl"]
