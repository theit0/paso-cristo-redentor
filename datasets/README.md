# Datasets

## closures.csv — histórico de cierres 2022–2026

Reconstruido a mano desde titulares de prensa (`news_headlines.csv`). Una fila por período.

| columna | significado |
|---|---|
| `start` | primer día con el paso cerrado (aunque haya cerrado a la tarde) |
| `end` | día en que reabrió (**exclusivo**: ese día ya hubo tránsito) |
| `scope` | `total` (nadie pasa) o `solo_cargas` (reapertura escalonada: camiones sí, autos no) |
| `cause` | `nieve`, `lluvia_aludes`, `viento`, `otro` (accidentes, sanitario) |
| `confidence` | `alta`: apertura y cierre informados · `media`: un extremo inferido · `baja`: reapertura no informada, estimada en 1–3 días |
| `source`, `evidence` | titular que respalda la fila (link de Google News) |

**Cualquier día que no está en el archivo se asume abierto.** Limitaciones:
- No incluye cortes de pocas horas (accidentes, obras programadas, cierres por demanda).
- Un cierre corto que la prensa no cubrió falta, así que sesga hacia "abierto". Por eso no hay 2021: poca cobertura y frontera cerrada al turismo por la pandemia.
- Días con reapertura y nuevo cierre el mismo día se cuentan como cerrados (ver `notes`).

Control: 2023 da 58 días cerrados al 11/9 (la prensa informó 58–63); el cierre más largo por año coincide con lo publicado (12 días en 2022, 34 en 2026).

## weather_observed.csv / weather_forecast.csv — clima diario 2022→hoy

Open-Meteo para `las_cuevas` y `portillo`, resumido por día en hora de Mendoza
(`_sum` precipitación y nieve en mm/cm, `_min`/`_max`/`_mean` del resto; NaN si faltan horas).

- **weather_observed.csv**: [Historical Forecast API](https://open-meteo.com/en/docs/historical-forecast-api),
  primeras horas de cada corrida ≈ lo que pasó. Incluye isoterma cero, profundidad de nieve y visibilidad.
  Sirve para features del **pasado** (nieve acumulada, días desde la última nevada).
- **weather_forecast.csv**: [Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api),
  lo que se pronosticaba `lead` días antes (1–7). Sirve para features del **futuro** sin hacer trampa.
  - `jma_seamless`: desde 2022, sin ráfagas.
  - `best_match`: desde 2024, con ráfagas (más preciso, menos historia).
  - Ningún modelo archiva isoterma cero a 1–7 días.

Regenerar (tarda ~15 min): `cd backend && pip install -r requirements-ml.txt && python -m scripts.download_weather`

## news_headlines.csv

Titulares con fecha de Google News, 2021–2026. Regenerar con:

```bash
cd backend && python scripts/harvest_news.py 2021-01-01 2026-10-13 > ../datasets/news_headlines.csv
```
