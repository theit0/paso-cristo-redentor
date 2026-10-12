from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import CORS_ORIGINS, STATIC_DIR

app = FastAPI(title="Paso Cristo Redentor")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET"], allow_headers=["*"])
app.include_router(router)

# En producción el mismo servicio sirve el frontend compilado (un dominio, sin CORS).
# Va después del router para que /api/* tenga prioridad.
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
