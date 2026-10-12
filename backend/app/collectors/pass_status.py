import httpx

from app.config import PASS_ID, PASSES_URL


def parse(passes: list[dict]) -> dict:
    p = next((x for x in passes if x.get("id") == PASS_ID), None)
    if p is None:
        raise ValueError(f"Paso id={PASS_ID} no está en la respuesta")
    return {
        "source_time": p.get("fecha_hora_consulta"),
        "estado": p.get("estado_prioridad"),
        "estado_vialidad": p.get("estado_vialidad"),
        "horario": p.get("fecha_schema"),
        "horario_cancilleria": p.get("fecha_schema_cancilleria"),
        "raw": p,
    }


def fetch(client: httpx.Client) -> dict:
    r = client.get(PASSES_URL, headers={"User-Agent": "paso-cristo-redentor/0.1"})
    r.raise_for_status()
    return parse(r.json())
