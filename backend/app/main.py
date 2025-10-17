from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .db import Base, engine
from .api import auth, health


app = FastAPI(title="Plan&Go API")


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


# Servir frontend compilado
frontend_build = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_build.exists():
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="frontend")
