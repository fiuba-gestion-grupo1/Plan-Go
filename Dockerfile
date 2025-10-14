# 1) Build del frontend
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/ ./
RUN npm ci || npm i && npm run build


# 2) Imagen final con Python + app
FROM python:3.11-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1
WORKDIR /app


# libs del sistema
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*


# deps python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# código backend
COPY backend/ ./backend/


# estáticos del frontend
COPY --from=web /web/dist /app/frontend/dist


# FastAPI sirve la SPA desde /frontend/dist (ver main.py)
ENV PORT=8000
EXPOSE 8000


CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]