# Tareas

## Fase 1 — Datos
- [x] **1. Registrador**: estado oficial del paso (Ministerio de Seguridad) + pronóstico Open-Meteo (Las Cuevas y Portillo) → disco. API `/api/status`, `/api/forecast/{location}`. Front muestra el estado actual. *(SQLite reemplazado por JSONL en la tarea 2.)*
- [x] **2. Registrador cada hora en la nube**: GitHub Actions → rama `data` (JSONL). Estado cada hora, pronóstico cada 6 h. Si una fuente falla, el job falla y GitHub avisa por mail.
- [x] **3. Histórico de cierres 2022–2026**: 100 períodos reconstruidos desde ~4.000 titulares de Google News → [`datasets/closures.csv`](datasets/closures.csv). 2021 descartado (poca cobertura + pandemia). Ver [datasets/README.md](datasets/README.md).
- [x] **4. Clima histórico**: diario 2022→hoy en `datasets/weather_*.csv`. Observado (Historical Forecast) + pronosticado a 1–7 días (Previous Runs: JMA desde 2022, best_match desde 2024). Al predecir en vivo hay que pedir el mismo modelo (`jma_seamless`) que se usó para entrenar.

## Fase 2 — Modelo
- [ ] **5. Baselines + métricas**: "mañana igual que hoy" y tasa histórica por fecha. Brier score, curva de confiabilidad.
- [ ] **6. Modelo A, cierre**: P(cierre | hoy abierto), regresión logística → gradient boosting. Calibrar.
- [ ] **7. Modelo B, reapertura**: supervivencia sobre días cerrado + nieve acumulada + ventana estable pronosticada.
- [ ] **8. Endpoint `/api/predict?date=`**: combina A y B según el estado actual; devuelve probabilidad y confianza según la anticipación (0–24 h, 1–7 d, >10 d → climatología).

## Fase 3 — Producto
- [ ] **9. Frontend**: selector de fecha, probabilidad, historial y pronóstico.
- [ ] **10. Deploy** (back + front + registrador).
