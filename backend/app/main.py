import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.api import suggestions
from .db import Base, engine, log_db_info
from .api import auth, health, users, publications, debug, categories, preferences, itineraries
from .db_migrations import ensure_min_schema

# 👇 NUEVO
from .api import invitations

app = FastAPI(title="Plan&Go API")

os.makedirs("backend/app/static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")

# CORS abierto para dev; ajustar en prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ❌ Quitar esta línea para evitar duplicado
# Base.metadata.create_all(bind=engine)

# API routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(publications.router)
app.include_router(categories.router)
app.include_router(preferences.router)
app.include_router(suggestions.router)
app.include_router(itineraries.router)
# 👇 NUEVO
app.include_router(invitations.router)

if os.getenv("ENV", "dev") == "dev":
  try:
      from .api import debug as debug_router  # backend/app/api/debug.py
      app.include_router(debug_router.router)
  except Exception as e:
      print(f"[DEBUG] router no cargado: {e}")

# Servir frontend compilado
frontend_build = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_build.exists():
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="frontend")

@app.on_event("startup")
def on_startup():
    log_db_info()
    # ✅ crear tablas y luego asegurar columnas mínimas
    Base.metadata.create_all(bind=engine)
    try:
        ensure_min_schema(engine)
        print("[DB] ensure_min_schema OK")
    except Exception as e:
        print(f"[DB] ensure_min_schema skipped/error: {e}")
