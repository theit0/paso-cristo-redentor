import pytest

from app.collectors.pass_status import parse

SAMPLE = [
    {"id": 27, "nombre_paso": "Agua Negra", "estado_prioridad": "CERRADO"},
    {
        "id": 29,
        "nombre_paso": "Sistema Cristo Redentor",
        "estado_prioridad": "ABIERTO",
        "estado_vialidad": "HABILITADA",
        "fecha_schema": "Mo-Su 09:00-21:00 open",
        "fecha_schema_cancilleria": "Mo-Su 09:00-19:00 open \"Habilitado solo para transporte de cargas.\"",
        "fecha_hora_consulta": "2026-10-12 14:27:03",
    },
]


def test_parse_picks_cristo_redentor():
    s = parse(SAMPLE)
    assert s["estado"] == "ABIERTO"
    assert s["estado_vialidad"] == "HABILITADA"
    assert "solo para transporte de cargas" in s["horario_cancilleria"]
    assert s["raw"]["id"] == 29


def test_parse_fails_loudly_if_pass_missing():
    with pytest.raises(ValueError):
        parse(SAMPLE[:1])
