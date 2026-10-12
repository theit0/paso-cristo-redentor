from datetime import date

from fastapi.testclient import TestClient

from app import live
from app.main import app

client = TestClient(app)


def test_history_by_year_covers_jan_1_to_yesterday(monkeypatch):
    monkeypatch.setattr(live, "today", lambda: date(2026, 3, 10))
    monkeypatch.setattr(live, "status_history", lambda: {date(2026, 2, 1): "total", date(2026, 2, 2): "solo_cargas"})

    days = client.get("/api/history?year=2026").json()
    assert days[0] == {"fecha": "2026-01-01", "estado": "abierto"}
    assert days[-1]["fecha"] == "2026-03-09"  # hasta ayer
    assert [d["estado"] for d in days[31:33]] == ["total", "solo_cargas"]

    full = client.get("/api/history?year=2025").json()
    assert len(full) == 365 and full[-1]["fecha"] == "2025-12-31"

    assert client.get("/api/history?year=2027").status_code == 422
    assert client.get("/api/history?year=2021").status_code == 422
