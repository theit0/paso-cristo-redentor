import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import CORS_ORIGINS, STATIC_DIR

app = FastAPI(title="Paso Cristo Redentor")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET"], allow_headers=["*"])

# Rate limit por IP, ventana fija. Una carga de página son ~6 pedidos: 30/min deja ~5 recargas por minuto.
# La IP real llega por X-Forwarded-For (uvicorn corre con --proxy-headers).
# ponytail: en memoria y por proceso; si algún día hay varias réplicas, pasarlo a Redis.
RATE_WINDOW, RATE_MAX = 60, 30
_hits: dict[str, int] = {}
_window_start = 0.0


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    global _window_start
    now = time.monotonic()
    if now - _window_start > RATE_WINDOW:
        _hits.clear()  # vaciar por ventana también evita que el dict crezca sin límite
        _window_start = now
    ip = request.client.host if request.client else "?"
    _hits[ip] = _hits.get(ip, 0) + 1
    if _hits[ip] > RATE_MAX:
        return JSONResponse({"detail": "Demasiados pedidos, probá en un minuto."}, status_code=429,
                            headers={"Retry-After": str(RATE_WINDOW)})
    return await call_next(request)


app.include_router(router)

# En producción el mismo servicio sirve el frontend compilado (un dominio, sin CORS).
# Va después del router para que /api/* tenga prioridad.
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
