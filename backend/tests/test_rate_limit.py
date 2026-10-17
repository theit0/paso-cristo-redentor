from fastapi.testclient import TestClient

from app import main


def test_blocks_after_limit(monkeypatch):
    # contador propio: si no, los demás tests reciben 429
    monkeypatch.setattr(main, "_hits", {})
    monkeypatch.setattr(main, "_window_start", 0.0)
    client = TestClient(main.app)
    codes = [client.get("/api/health").status_code for _ in range(main.RATE_MAX + 1)]
    assert codes[:-1] == [200] * main.RATE_MAX
    assert codes[-1] == 429
