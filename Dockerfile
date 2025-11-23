FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/ ./
RUN npm ci || npm i && npm run build

FROM python:3.11-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

COPY --from=web /web/dist /app/frontend/dist

ENV PORT=8000
EXPOSE 8000


CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
