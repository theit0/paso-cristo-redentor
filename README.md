# Datos del registrador

Rama escrita por GitHub Actions (`.github/workflows/collect.yml` en `main`). No editar a mano.

- `status/AAAA-MM.jsonl`: estado oficial del paso, una línea por corrida (GitHub la corre cada pocas horas).
- `mendoza/AAAA-MM.jsonl`: parte diario del Gobierno de Mendoza (aviso del paso y temperaturas).
- `forecast/AAAA-MM.jsonl`: pronóstico Open-Meteo; se dejó de guardar el 17/10/2026 (Open-Meteo ya lo archiva).

Timestamps `fetched_at` en UTC.
