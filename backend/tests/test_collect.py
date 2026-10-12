from app import collect


def test_one_source_failing_still_runs_the_other_and_reports_failure(monkeypatch):
    ran = []

    def broken(client, now):
        raise RuntimeError("fuente caída")

    monkeypatch.setitem(collect.COLLECTORS, "status", broken)
    monkeypatch.setitem(collect.COLLECTORS, "forecast", lambda client, now: ran.append("forecast"))

    assert collect.run(["status", "forecast"]) is False
    assert ran == ["forecast"]
