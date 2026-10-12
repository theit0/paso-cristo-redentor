# Paso Cristo Redentor — predictor de apertura

Predice si el Paso Internacional Cristo Redentor (Los Libertadores) estará abierto en una fecha dada, con su probabilidad.

```
backend/    FastAPI + Python (registrador de datos, API, después ML)
  app/
    collectors/   fuentes: estado oficial del paso, pronóstico Open-Meteo
    api/          rutas HTTP
    ml/           etiquetas, baselines, métricas y evaluación
    store.py      lectura/escritura de los JSONL
    collect.py    registrador
frontend/   React + Vite + TypeScript
  scripts/      herramientas sueltas (p. ej. juntar titulares)
datasets/   datos curados a mano: histórico de cierres (ver datasets/README.md)
docs/       resultados de evaluación de modelos
data/       worktree de la rama `data` (no está en main)
TASKS.md    hoja de ruta
```

## Datos

GitHub Actions ([collect.yml](.github/workflows/collect.yml)) corre el registrador cada hora (pronóstico cada 6 h)
y commitea en la rama `data`. Para tenerlos local, una sola vez:

```bash
git fetch origin data && git worktree add data data
```

Después, para actualizar: `git -C data pull`. No correr el registrador local sobre `data/`
(generaría conflictos con Actions); para probarlo usar otra carpeta: `PASO_DATA_DIR=/tmp/x python -m app.collect`.

## Correr

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # Linux/mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload  # API en :8000, lee ../data
python -m pytest
```

```bash
cd frontend
npm install
npm run dev                    # :5173, /api va al backend por proxy
```

## API

- `GET /api/predict?date=AAAA-MM-DD` → probabilidad de cerrado/abierto, veredicto, confianza y fuente
  (`estado_oficial` hoy, `modelo` a 1–7 días, `climatologia` más allá). Sin `date`: próximos 8 días.
- `GET /api/status`, `/api/status/history`, `/api/forecast/{las_cuevas|portillo}`: datos del registrador.

## Modelo

```bash
cd backend && pip install -r requirements-ml.txt
python -m app.ml.evaluate > ../docs/evaluacion.md   # comparar modelos
python -m app.ml.export                             # entrenar y exportar app/model.json
```

El servidor solo necesita `requirements.txt`: el modelo exportado corre en Python puro.
En producción, `GITHUB_TOKEN` (solo lectura del repo) permite leer el historial de la rama `data`.

## Fuentes
- Estado: `argentina.gob.ar/seguridad/pasosinternacionales/listado` (id 29).
- Pronóstico: [Open-Meteo](https://open-meteo.com), gratis y sin API key.
