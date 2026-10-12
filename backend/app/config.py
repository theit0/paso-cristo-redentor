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

# Puntos de la ruta para el mapa (solo visualización; el modelo usa LOCATIONS).
# ponytail: coordenadas a mano, verificadas contra la API de elevación de Open-Meteo; alcanzan para el mapa.
ROUTE_POINTS = [
    {"id": "uspallata", "nombre": "Uspallata", "lat": -32.593, "lon": -69.346, "altura": 1890},
    {"id": "puente_del_inca", "nombre": "Puente del Inca", "lat": -32.825, "lon": -69.912, "altura": 2720},
    {"id": "las_cuevas", "nombre": "Las Cuevas", "lat": -32.811, "lon": -70.050, "altura": 3150},
    {"id": "portillo", "nombre": "Portillo", "lat": -32.835, "lon": -70.130, "altura": 2880},
    {"id": "guardia_vieja", "nombre": "Guardia Vieja", "lat": -32.905, "lon": -70.280, "altura": 1600},
]

# En producción el historial del registrador se lee de la rama `data` vía API (token de solo lectura).
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "theit0/paso-cristo-redentor")

# Frontend compilado: si existe, lo sirve el mismo servicio (ver main.py).
STATIC_DIR = Path(os.getenv("PASO_STATIC_DIR", REPO_DIR / "frontend" / "dist"))
CORS_ORIGINS = os.getenv("PASO_CORS_ORIGINS", "http://localhost:5173").split(",")
