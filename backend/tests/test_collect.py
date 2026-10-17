from app import collect


def test_one_source_failing_still_runs_the_other_and_reports_failure(monkeypatch):
    ran = []

    def broken(client, now):
        raise RuntimeError("fuente caída")

    monkeypatch.setitem(collect.COLLECTORS, "status", broken)
    monkeypatch.setitem(collect.COLLECTORS, "mendoza", lambda client, now: ran.append("mendoza"))

    assert collect.run(["status", "mendoza"]) is False
    assert ran == ["mendoza"]
