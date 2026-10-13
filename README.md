# Paso Cristo Redentor

Predice si el paso a Chile (Cristo Redentor / Los Libertadores) va a estar abierto en los próximos días, con su probabilidad.

## Cómo funciona

### 1. Datos

- **Estado en vivo:** API del Ministerio de Seguridad (abierto/cerrado) + parte diario del Gobierno de Mendoza
  (si pasan todos los vehículos o solo camiones, y temperaturas en la ruta). El aviso del Ministerio a veces queda
  viejo; por eso el detalle sale del parte de Mendoza.
- **Clima:** Open-Meteo, gratis. Pronóstico a 7 días del modelo JMA y clima de los últimos 61 días, en Las Cuevas
  (lado argentino) y Portillo (lado chileno); se toma el peor de los dos.
- **Histórico de cierres 2022–2026** ([datasets/closures.csv](datasets/closures.csv)): no existe uno oficial, así que
  se reconstruyó a mano desde ~4.000 titulares de prensa. 100 cierres, cada uno con su fuente.
- **Registrador:** GitHub Actions guarda estado, parte y pronóstico en la rama `data` para ir sumando historial propio.

### 2. Modelo

- **Regresión logística** que da la probabilidad de que el paso esté cerrado dentro de 1 a 7 días.
- **Mira:** si hoy está abierto o cerrado y hace cuántos días; la nieve caída (3, 7 y 14 días, y en el suelo);
  el pronóstico de nieve, lluvia, temperatura y viento hasta ese día; y la época del año.
- **Sin trampa:** se entrenó con lo que se *pronosticaba* en cada momento, no con el clima que finalmente hubo.
- **Resultados** (invierno, probado sobre años que no vio): acierta 87% a 1 día, 86% a 3 y 80% a 7.
  Cuando el estado cambia, a 3 días acierta 68% contra 23% de la mejor alternativa simple.
  Detalle en [docs/evaluacion.md](docs/evaluacion.md).
- Se entrena en la PC (pandas + scikit-learn) y se exporta a [app/model.json](backend/app/model.json) (5 KB).
  El servidor lo calcula en Python puro, así consume poco (~60 MB).

### 3. En cada consulta

- **Hoy** → estado oficial. **1 a 7 días** → modelo. **Más de 7** → tasa de cierre de otros años para esa fecha.
- Abierto si la probabilidad de abierto es ≥ 50%; entre 35% y 65% se marca como ajustado.
- Cada día muestra los 3 factores que más lo empujan a abrir o cerrar (exactos, porque el modelo es lineal).
- Los datos externos se cachean: estado y parte 10 min, clima e historial 1 h.

## Estructura

```
backend/app/
  api/routes.py   endpoints
  live.py         datos en vivo (estado, parte, clima, historial)
  predict.py      features + modelo en Python puro
  collectors/     lectura de cada fuente
  collect.py      registrador
  ml/             entrenamiento y evaluación (pandas, scikit-learn)
backend/scripts/  descarga de titulares y clima histórico
frontend/         React + Vite + Tailwind
datasets/         histórico de cierres y clima para entrenar
```

## Correr local

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate    # Linux/mac: source .venv/bin/activate
pip install -r requirements-ml.txt
uvicorn app.main:app --reload --port 8010
python -m pytest
```

```bash
cd frontend && npm install && npm run dev          # http://localhost:5173
```

Historial del registrador en local (opcional): `git fetch origin data && git worktree add data data`.

## Reentrenar

```bash
cd backend
python -m scripts.download_weather                  # clima histórico actualizado
python -m app.ml.evaluate > ../docs/evaluacion.md   # comparar contra las alternativas simples
python -m app.ml.export                             # entrenar y generar app/model.json
```

Conviene hacerlo antes de cada invierno, sumando a `closures.csv` los cierres nuevos.

## API

- `GET /api/predict` → próximos 8 días; `?date=AAAA-MM-DD` → una fecha (hasta 1 año).
  Incluye probabilidad, confianza, clima, factores y contexto (nieve reciente, días en el estado actual).
- `GET /api/status` → estado oficial en vivo.

## Limitaciones

- El histórico sale de la prensa: puede faltar algún cierre corto.
- Hay 5 inviernos de datos; 2026 fue récord.
- GitHub ejecuta el registrador con demoras (a veces pocas veces por día).
- Es una estimación: antes de viajar, consultar las fuentes oficiales.
