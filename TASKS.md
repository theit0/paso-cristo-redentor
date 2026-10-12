# Tareas

## Fase 1 — Datos
- [x] **1. Registrador**: estado oficial del paso (Ministerio de Seguridad) + pronóstico Open-Meteo (Las Cuevas y Portillo) → SQLite. API `/api/status`, `/api/forecast/{location}`. Front muestra el estado actual.
- [ ] **2. Correr el registrador cada hora en la nube** (GitHub Actions cron o un VPS chico), para que no dependa de que la PC esté prendida. Es el dato más valioso: empezar cuanto antes.
- [ ] **3. Histórico de cierres 2021–2026**: reconstruir desde comunicados y notas diarias (Sitio Andino, Los Andes, UPF) → `data/closures.csv` (inicio, fin, tipo: total/solo cargas, causa).
- [ ] **4. Pronósticos históricos**: Open-Meteo Historical Forecast (2021+) y Previous Runs (anticipación 1–7 días, 2024+) para esas fechas. Entrenar con lo pronosticado, no con lo observado.

## Fase 2 — Modelo
- [ ] **5. Baselines + métricas**: "mañana igual que hoy" y tasa histórica por fecha. Brier score, curva de confiabilidad.
- [ ] **6. Modelo A, cierre**: P(cierre | hoy abierto), regresión logística → gradient boosting. Calibrar.
- [ ] **7. Modelo B, reapertura**: supervivencia sobre días cerrado + nieve acumulada + ventana estable pronosticada.
- [ ] **8. Endpoint `/api/predict?date=`**: combina A y B según el estado actual; devuelve probabilidad y confianza según la anticipación (0–24 h, 1–7 d, >10 d → climatología).

## Fase 3 — Producto
- [ ] **9. Frontend**: selector de fecha, probabilidad, historial y pronóstico.
- [ ] **10. Deploy** (back + front + registrador).
