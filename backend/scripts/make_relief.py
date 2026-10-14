"""Genera el relieve del mapita (frontend/src/relief.json) desde las Terrain Tiles públicas de AWS Open Data
(imágenes de elevación gratuitas, sin cuenta ni clave).

Se corre una sola vez: el relieve no cambia. (La API de elevación de Open-Meteo cuenta cada punto
como una llamada y el cupo se agota con una grilla así.)
Uso (desde backend/, con requirements-ml.txt): python -m scripts.make_relief
"""
import io
import json
import math
from pathlib import Path

import httpx
from PIL import Image

from app.config import SNOWMAP_BBOX

OUT = Path(__file__).resolve().parents[2] / "frontend" / "src" / "relief.json"
TILES = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
Z = 8  # ~600 m por píxel: de sobra para un mapa de 180 px
ROWS, COLS = 68, 60  # ~3 km por celda


def tile_xy(lat: float, lon: float) -> tuple[float, float]:
    """Coordenadas de tile (fraccionales) en proyección Web Mercator."""
    n = 2 ** Z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


def main() -> None:
    lat0, lat1, lon0, lon1 = SNOWMAP_BBOX
    tiles: dict[tuple[int, int], Image.Image] = {}
    with httpx.Client(timeout=60) as client:
        def elevation(lat: float, lon: float) -> float:
            fx, fy = tile_xy(lat, lon)
            key = (int(fx), int(fy))
            if key not in tiles:
                r = client.get(TILES.format(z=Z, x=key[0], y=key[1]))
                r.raise_for_status()
                tiles[key] = Image.open(io.BytesIO(r.content)).convert("RGB")
            px = min(255, int((fx - key[0]) * 256)), min(255, int((fy - key[1]) * 256))
            red, green, blue = tiles[key].getpixel(px)
            return red * 256 + green + blue / 256 - 32768  # codificación "terrarium"

        elev = [round(elevation(lat0 + (lat1 - lat0) * r / (ROWS - 1), lon0 + (lon1 - lon0) * c / (COLS - 1)))
                for r in range(ROWS) for c in range(COLS)]
    OUT.write_text(json.dumps({"bbox": SNOWMAP_BBOX, "rows": ROWS, "cols": COLS, "elev": elev}), encoding="utf-8")
    print(f"{OUT.name}: {OUT.stat().st_size // 1024} KB, {len(tiles)} tiles, {min(elev)}–{max(elev)} m")


if __name__ == "__main__":
    main()
