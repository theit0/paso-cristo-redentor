# Paso Cristo Redentor — predictor de apertura

Predice si el Paso Internacional Cristo Redentor (Los Libertadores) estará abierto en una fecha dada, con su probabilidad.

```
backend/    FastAPI + Python (registrador de datos, API, después ML)
  app/
    collectors/   fuentes: estado oficial del paso, pronóstico Open-Meteo
    api/          rutas HTTP
    collect.py    registrador (correr cada hora)
frontend/   React + Vite + TypeScript
TASKS.md    hoja de ruta
```

## Correr

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # Linux/mac: source .venv/bin/activate
pip install -r requirements.txt
python -m app.collect          # guarda una foto del estado + pronóstico
uvicorn app.main:app --reload  # API en :8000
python -m pytest
```

```bash
cd frontend
npm install
npm run dev                    # :5173, /api va al backend por proxy
```

## Fuentes
- Estado: `argentina.gob.ar/seguridad/pasosinternacionales/listado` (id 29).
- Pronóstico: [Open-Meteo](https://open-meteo.com), gratis y sin API key.
