import os
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[2]
# Worktree de la rama `data` (ver README). En Actions se pasa por variable de entorno.
DATA_DIR = Path(os.getenv("PASO_DATA_DIR", REPO_DIR / "data"))

# Ministerio de Seguridad: estado de los 156 pasos internacionales (JSON).
PASSES_URL = "https://www.argentina.gob.ar/seguridad/pasosinternacionales/listado"
PASS_ID = 29  # Sistema Cristo Redentor

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_DAYS = 7
HOURLY_VARS = [
    "temperature_2m",
    "precipitation",
    "snowfall",
    "snow_depth",
    "wind_speed_10m",
    "wind_gusts_10m",
    "freezing_level_height",
    "visibility",
    "cloud_cover",
]
# Un punto de cada lado: el paso cierra si cualquiera de los dos no está transitable.
LOCATIONS = {
    "las_cuevas": (-32.811, -70.050),  # lado argentino, ~3150 m
    "portillo": (-32.835, -70.130),    # lado chileno (Caracoles), ~2880 m
}

# En producción el historial del registrador se lee de la rama `data` vía API (token de solo lectura).
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "theit0/paso-cristo-redentor")

# Frontend compilado: si existe, lo sirve el mismo servicio (ver main.py).
STATIC_DIR = Path(os.getenv("PASO_STATIC_DIR", REPO_DIR / "frontend" / "dist"))
CORS_ORIGINS = os.getenv("PASO_CORS_ORIGINS", "http://localhost:5173").split(",")
