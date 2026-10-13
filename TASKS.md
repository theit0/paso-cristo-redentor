# Tareas

## Fase 1 — Datos
- [x] **1. Registrador**: estado oficial del paso (Ministerio de Seguridad) + pronóstico Open-Meteo (Las Cuevas y Portillo) → disco. API `/api/status`, `/api/forecast/{location}`. Front muestra el estado actual. *(SQLite reemplazado por JSONL en la tarea 2.)*
- [x] **2. Registrador cada hora en la nube**: GitHub Actions → rama `data` (JSONL). Estado cada hora, pronóstico cada 6 h. Si una fuente falla, el job falla y GitHub avisa por mail.
- [x] **3. Histórico de cierres 2022–2026**: 100 períodos reconstruidos desde ~4.000 titulares de Google News → [`datasets/closures.csv`](datasets/closures.csv). 2021 descartado (poca cobertura + pandemia). Ver [datasets/README.md](datasets/README.md).
- [x] **4. Clima histórico**: diario 2022→hoy en `datasets/weather_*.csv`. Observado (Historical Forecast) + pronosticado a 1–7 días (Previous Runs: JMA desde 2022, best_match desde 2024). Al predecir en vivo hay que pedir el mismo modelo (`jma_seamless`) que se usó para entrenar.

## Fase 2 — Modelo
- [x] **5. Baselines + métricas** ([docs/baselines.md](docs/baselines.md), `python -m app.ml.evaluate`). Target: cerrado para autos (total o solo cargas). Validación dejando un año afuera.
  El mejor es **Markov** (estado de hoy + mes). Vara a superar en invierno (Brier): **0,130 a 1 día · 0,191 a 3 · 0,206 a 7 · 0,229 a 14** (= climatología: a 2 semanas el estado de hoy ya no informa). "Mañana igual que hoy" pierde contra la climatología desde los 3 días.
- [x] **6. Modelo de cierre y reapertura** ([docs/evaluacion.md](docs/evaluacion.md)): un solo modelo P(cerrado en t+h), h=1–7, con estado actual + nieve pasada + pronóstico JMA + interacciones.
  **Gana la regresión logística** (al boosting también). Brier invierno: **0,093 / 0,102 / 0,147** a 1/3/7 días vs Markov 0,130 / 0,191 / 0,206.
  Aciertos a 3 días: 86% (Markov 74%); en los días en que el estado cambia: **68%** (Markov 23%). Calibración buena en los extremos; algo subestimada en 30–60% a 1–3 días.
- [x] ~~**7. Modelo B, reapertura (supervivencia)**~~: no hizo falta. El modelo único predice "¿sigue cerrado?" un 52% mejor que Markov. Retomar solo si la reapertura falla en producción.
- [x] **8. Endpoint** (hoy `/api/year`): hoy → estado oficial; 1–7 días → modelo; más → climatología.
  El modelo se exporta a `app/model.json` (`python -m app.ml.export`) y corre en Python puro: el servidor no carga pandas/sklearn (test lo garantiza).
  Test de equivalencia entrenamiento ↔ producción. Datos en vivo con caché: estado (10 min), historial y clima (1 h).
  **Reentrenar** cada tanto: actualizar `closures.csv` con el registrador, `download_weather`, `export`.

## Fase 3 — Producto
- [x] **9. Frontend**: un cuadrado por día del año, verde/rojo; pasado en tono claro (real), hoy y 7 días en tono pleno (predicción), más adelante gris. Rojo si P(cerrado) ≥ 35%. Solo cuadrados (sin título, leyenda, meses ni marca de hoy), centrado, tooltip con la fecha. (Antes se probaron un tablero con mapa, uno con 8 días y factores, y uno de una sola fecha.)
- [ ] **10. Deploy** (back + front + registrador).
