# backend/app/api/debug.py
from fastapi import APIRouter
from sqlalchemy import inspect
from ..db import engine

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.get("/db")
def debug_db():
    insp = inspect(engine)
    tables = {}
    for t in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns(t)]
        tables[t] = cols
    return {"url": str(engine.url), "tables": tables}
