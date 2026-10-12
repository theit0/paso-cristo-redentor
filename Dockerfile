# 1) Compila el frontend
FROM node:22-alpine AS frontend
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 2) Servidor: FastAPI sin pandas/sklearn (el modelo exportado corre en Python puro)
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app backend/app
COPY datasets/closures.csv datasets/closures.csv
COPY --from=frontend /src/dist frontend/dist
WORKDIR /app/backend
# Railway define PORT; un solo proceso alcanza y mantiene la memoria baja.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
