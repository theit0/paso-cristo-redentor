"""Parte diario del Gobierno de Mendoza "Estado del tiempo y pasos internacionales".

Es más fresco que el aviso del feed del Ministerio de Seguridad (que quedó días con un
"solo cargas" viejo). Se lee por la API REST pública del WordPress de prensa.
"""
import html
import re

import httpx

URL = "https://prensa.mendoza.gob.ar/wp-json/wp/v2/posts"
POINTS = ("Uspallata", "Punta de Vacas", "Puente del Inca", "Las Cuevas")


def classify(text: str) -> str | None:
    """Texto del parte → 'total' / 'solo_cargas' / 'abierto' (None si no se entiende)."""
    t = text.lower()
    if "cerrad" in t:
        return "total"
    if "carga" in t and ("solo" in t or "exclusiv" in t):
        return "solo_cargas"
    if "habilitad" in t or "abiert" in t:
        return "abierto"
    return None


def parse(post: dict) -> dict:
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", post["content"]["rendered"])))
    m = re.search(r"Cristo Redentor\s*:\s*(.+?)(?=\s+Paso\s|\s+Sistema\s|$)", text)
    aviso = m.group(1).strip() if m else None
    temps = {}
    for name in POINTS:
        t = re.search(rf"{name}\s*:\s*(-?\d+(?:[.,]\d+)?)\s*°", text)
        if t:
            temps[name] = float(t.group(1).replace(",", "."))
    return {
        "publicado": post["modified"],  # hora de Mendoza, AAAA-MM-DDTHH:MM:SS
        "link": post["link"],
        "aviso": aviso,
        "estado": classify(aviso) if aviso else None,
        "temperaturas": temps,
    }


def fetch(client: httpx.Client) -> dict:
    r = client.get(URL, params={
        "search": "Estado del tiempo y pasos internacionales", "per_page": 1,
        "orderby": "date", "order": "desc", "_fields": "date,modified,link,content",
    }, headers={"User-Agent": "Mozilla/5.0 (paso-cristo-redentor)"})
    r.raise_for_status()
    posts = r.json()
    if not posts:
        raise ValueError("No hay parte publicado")
    return parse(posts[0])
