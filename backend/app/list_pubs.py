#!/usr/bin/env python3
"""
Script para listar todas las publicaciones
"""
from sqlalchemy import create_engine, text

# Conectar a la base de datos
engine = create_engine('sqlite:///data/plan_go.db')

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, place_name, status, rejection_reason FROM publications ORDER BY id"))
    pubs = result.fetchall()
    
    if pubs:
        print(f"\n📋 Total de publicaciones: {len(pubs)}\n")
        for pub in pubs:
            reason_text = f" | Razón: {pub[3][:50]}..." if pub[3] else ""
            print(f"ID: {pub[0]} | Nombre: {pub[1]} | Estado: {pub[2]}{reason_text}")
    else:
        print("No hay publicaciones en la base de datos")
