from app import config, store


def test_newest_first_crosses_months(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    for ts in ["2026-09-30T23:00:00+00:00", "2026-10-01T00:00:00+00:00", "2026-10-01T01:00:00+00:00"]:
        store.append("status", {"fetched_at": ts})

    got = [r["fetched_at"][:13] for r in store.newest_first("status")]
    assert got == ["2026-10-01T01", "2026-10-01T00", "2026-09-30T23"]
    assert sorted(p.name for p in (tmp_path / "status").iterdir()) == ["2026-09.jsonl", "2026-10.jsonl"]


def test_empty_store(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    assert next(store.newest_first("status"), None) is None
