import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .db import Base, engine
from .api import auth, health, users, publications

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

# Crear tablas
Base.metadata.create_all(bind=engine)

# API routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(publications.router)

# Servir frontend compilado
frontend_build = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_build.exists():
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="frontend")

@app.on_event("startup")
def init_db():
    # Crea TODAS las tablas según tus modelos (incluye 'role')
    Base.metadata.create_all(bind=engine)
