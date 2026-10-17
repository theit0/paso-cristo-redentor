from app.collectors.mendoza_report import classify, parse

POST = {
    "modified": "2026-10-13T10:24:45",
    "link": "https://prensa.mendoza.gob.ar/estado-del-tiempo-y-pasos-internacionales/",
    "content": {"rendered": (
        "<p>Pronóstico...</p><h3>Pasos internacionales</h3><p>Uspallata: 1 °<br>Punta de Vacas: -9 °<br>"
        "Puente del Inca: -12 °<br>Las Cuevas: -13 °</p><p><strong>Sistema Integrado Cristo Redentor:</strong> "
        "Habilitado las 24 horas para todo tipo de vehículos.</p><p>Paso Pehuenche: Cerrado.</p>"
    )},
}


def test_parse_real_report():
    r = parse(POST)
    assert r["aviso"] == "Habilitado las 24 horas para todo tipo de vehículos."
    assert r["estado"] == "abierto"  # el "Cerrado" de Pehuenche no se mezcla
    assert r["temperaturas"] == {"Uspallata": 1, "Punta de Vacas": -9, "Puente del Inca": -12, "Las Cuevas": -13}
    assert r["publicado"] == "2026-10-13T10:24:45"


def test_current_status_combines_sources():
    from app.live import current_status

    report = lambda estado, hoy=True: {"estado": estado, "es_de_hoy": hoy}
    assert current_status({"estado": "ABIERTO"}, report("abierto")) == "abierto"
    assert current_status({"estado": "ABIERTO"}, report("solo_cargas")) == "solo_cargas"
    assert current_status({"estado": "ABIERTO"}, report("solo_cargas", hoy=False)) == "abierto"  # parte viejo
    assert current_status({"estado": "CERRADO"}, report("abierto")) == "total"  # el Ministerio está en vivo
    assert current_status({"estado": "ABIERTO"}, None) == "abierto"  # sin parte


def test_classify():
    assert classify("Cerrado por nevadas.") == "total"
    assert classify("Habilitado solo para transporte de cargas.") == "solo_cargas"
    assert classify("Habilitado exclusivamente para cargas de Argentina a Chile") == "solo_cargas"
    assert classify("Habilitado las 24 horas para todo tipo de vehículos.") == "abierto"
    assert classify("Se evaluará mañana") is None
    assert classify("Cerrado para vehículos livianos. Habilitado solo para cargas.") == "solo_cargas"
