# Paso Cristo Redentor

Muestra el año entero del paso a Chile (Cristo Redentor / Los Libertadores), un cuadrado por día:
los días pasados en tono claro (lo que pasó), hoy y los 7 siguientes en tono pleno (la predicción) y el resto en gris.
Verde abierto, rojo cerrado. Los días predichos muestran su % adentro del cuadrado.
Al pasar el mouse por un día de hoy en adelante aparece un tooltip con la fecha, el resultado y un mapita de lo que
cae ese día en la zona (nieve nueva de verde a rojo, lluvia en azul), estilo snow-forecast. En los días pasados el
tooltip muestra la fecha y el estado.

## En pocas palabras

> Juntamos cinco inviernos de historia del paso: qué días estuvo cerrado y qué clima se pronosticaba en ese momento.
> Con eso, la app aprendió qué combinaciones suelen terminar en cierre.
>
> Para cada uno de los próximos 7 días se fija en:
>
> - **Cómo está hoy:** si está abierto o cerrado, hace cuántos días que está así, y si solo pasan camiones.
> - **La nieve que ya cayó:** en los últimos 3, 7 y 14 días, y cuánta hay acumulada en el suelo.
> - **Hace cuánto no nieva fuerte.**
> - **El frío de ayer.**
> - **El pronóstico para ese día:** nieve, lluvia, viento y temperaturas mínima y máxima.
> - **La nieve que viene en camino:** cuánta se espera en total de hoy hasta ese día, y la nevada más fuerte.
> - **La época del año.**
> - **Cuántos días faltan:** cuanto más lejos, menos seguro.
>
> Con todo eso calcula qué chance hay de que esté cerrado. Si pasa del 50% lo pinta de rojo; si no, verde.
>
> Probándola con inviernos que no conocía, acertó más de 8 de cada 10 días. Más allá de una semana no hay pronóstico
> del tiempo confiable, por eso esos días quedan en gris. Es una ayuda para planificar: antes de salir, siempre
> conviene confirmar con las fuentes oficiales.

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

### 3. Cómo se pinta cada día

- **Pasado:** estado real (histórico curado + registrador). "Solo camiones" cuenta como cerrado.
- **Hoy:** estado oficial en vivo.
- **1 a 7 días:** modelo con el pronóstico del tiempo.
- **Más de 7 días:** gris. No hay pronóstico a esa distancia (el promedio de otros años se vería igual de firme
  que una predicción y no lo es).
- **Criterio:** rojo si la probabilidad de cierre es **> 50%**; el 50% justo es verde (`UMBRAL_CERRADO` en
  [routes.py](backend/app/api/routes.py)). Con 35% detectaba 73% de los cierres en vez de 63%, pero con más rojos falsos.
- Los datos externos se cachean: estado y parte 10 min, clima e historial 1 h.
- Rate limit: 30 pedidos por minuto por IP (en [main.py](backend/app/main.py)); pasado eso responde 429.

## Estructura

```
backend/app/
  api/routes.py   endpoints
  live.py         datos en vivo (estado, parte, clima, historial)
  predict.py      modelo en Python puro
  collectors/     lectura de cada fuente
  collect.py      registrador
  ml/             entrenamiento y evaluación (pandas, scikit-learn)
backend/scripts/  descarga de titulares, clima histórico y relieve del mapita
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

- `GET /api/snowmap` → nieve nueva (cm) y lluvia (mm) por día en una grilla de 16×12 puntos (costa del Pacífico a Mendoza),
  próximos 8 días.
- `GET /api/year` → todos los días del año en curso: `{hoy, dias: [{fecha, cerrado, prob_cerrado}]}`
  (`prob_cerrado` solo en los 7 días predichos; `cerrado: null` más allá).

## Limitaciones

- El histórico sale de la prensa: puede faltar algún cierre corto.
- Hay 5 inviernos de datos; 2026 fue récord.
- GitHub ejecuta el registrador con demoras (a veces pocas veces por día).
- Dos colores esconden cuán segura es cada predicción (un 36% y un 99% se ven igual).
- Es una estimación: antes de viajar, consultar las fuentes oficiales.
