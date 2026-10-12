"""Valida datasets/closures.csv: es curado a mano, así que un error de tipeo tiene que fallar acá."""
import csv
from datetime import date
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "datasets" / "closures.csv"
SCOPES = {"total", "solo_cargas"}
CAUSES = {"nieve", "lluvia_aludes", "viento", "otro"}
CONFIDENCE = {"alta", "media", "baja"}


def rows():
    with PATH.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_fields_are_valid():
    for r in rows():
        start, end = date.fromisoformat(r["start"]), date.fromisoformat(r["end"])
        assert end > start, r
        assert r["scope"] in SCOPES, r
        assert r["cause"] in CAUSES, r
        assert r["confidence"] in CONFIDENCE, r
        assert r["source"].startswith("http"), r


def test_periods_do_not_overlap():
    rs = sorted(rows(), key=lambda r: r["start"])
    for a, b in zip(rs, rs[1:]):
        assert a["end"] <= b["start"], (a, b)
