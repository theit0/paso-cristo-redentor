import os
import ssl
from pathlib import Path

import certifi

REPO_DIR = Path(__file__).resolve().parents[2]
# Worktree de la rama `data` (ver README). En Actions se pasa por variable de entorno.
DATA_DIR = Path(os.getenv("PASO_DATA_DIR", REPO_DIR / "data"))

# Ministerio de Seguridad: estado de los 156 pasos internacionales (JSON).
PASSES_URL = "https://www.argentina.gob.ar/seguridad/pasosinternacionales/listado"
PASS_ID = 29  # Sistema Cristo Redentor

# prensa.mendoza.gob.ar (CloudFront) no manda la cadena completa desde el certificado del 13/10/2026:
# Windows baja los intermedios solo, OpenSSL no. Se agregan YR1 y Root YR (firmado por ISRG Root X1).
SSL = ssl.create_default_context(cafile=certifi.where())
SSL.load_verify_locations(Path(__file__).with_name("le-yr1.pem"))

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
# Un punto de cada lado: el paso cierra si cualquiera de los dos no está transitable.
LOCATIONS = {
    "las_cuevas": (-32.811, -70.050),  # lado argentino, ~3150 m
    "portillo": (-32.835, -70.130),    # lado chileno (Caracoles), ~2880 m
}

# Zona del mapita (lat norte, lat sur, lon oeste, lon este): de la costa del Pacífico a Mendoza, como snow-forecast.
SNOWMAP_BBOX = (-31.0, -35.0, -72.0, -68.5)
SNOWMAP_GRID = (16, 12)  # filas, columnas de puntos de pronóstico (~28 km); cada punto cuenta como llamada en Open-Meteo

# En producción el historial del registrador se lee de la rama `data` vía API (token de solo lectura).
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "theit0/paso-cristo-redentor")

# Frontend compilado: si existe, lo sirve el mismo servicio (ver main.py).
STATIC_DIR = Path(os.getenv("PASO_STATIC_DIR", REPO_DIR / "frontend" / "dist"))
CORS_ORIGINS = os.getenv("PASO_CORS_ORIGINS", "http://localhost:5173").split(",")
