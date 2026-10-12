import httpx

from app.config import FORECAST_DAYS, HOURLY_VARS, LOCATIONS, OPEN_METEO_URL


def fetch(client: httpx.Client) -> dict[str, dict]:
    out = {}
    for name, (lat, lon) in LOCATIONS.items():
        r = client.get(OPEN_METEO_URL, params={
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(HOURLY_VARS),
            "forecast_days": FORECAST_DAYS,
            "timezone": "UTC",
        })
        r.raise_for_status()
        out[name] = r.json()
    return out
