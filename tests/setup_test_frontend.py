#!/usr/bin/env python3
"""
Script para crear un itinerario de prueba específico para testing de frontend
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}

def setup_test_itinerary():
    print("🚀 SETUP: Creando itinerario de prueba para frontend")
    print("=" * 55)
    
    # 1. Login
    print("\n1. 🔐 Autenticación...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado")
    
    # 2. Crear itinerario de IA específico para testing
    print("\n2. 🤖 Creando itinerario de IA de prueba...")
    tomorrow = datetime.now() + timedelta(days=1)
    end_date = tomorrow + timedelta(days=2)  # 3 días para testing
    
    itinerary_request = {
        "destination": "Buenos Aires, Argentina",
        "start_date": tomorrow.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "budget": 500,
        "cant_persons": 2,
        "trip_type": "cultural",
        "arrival_time": "09:00",
        "departure_time": "19:00",
        "comments": "Itinerario específico para testing de PublicationCard modal"
    }
    
    ai_response = requests.post(f"{BASE_URL}/api/itineraries/request", 
                               json=itinerary_request, headers=headers)
    
    if ai_response.status_code != 200:
        print(f"❌ Error creando IA: {ai_response.status_code}")
        return None
    
    ai_itinerary = ai_response.json()
    print(f"✅ Itinerario IA creado (ID: {ai_itinerary['id']})")
    
    # 3. Verificar que se puede convertir
    print("\n3. 🔄 Verificando conversión...")
    conversion_data = {
        "ai_itinerary_id": ai_itinerary["id"],
        "custom_destination": "Buenos Aires, Argentina",
        "custom_start_date": tomorrow.strftime("%Y-%m-%d"),
        "custom_end_date": end_date.strftime("%Y-%m-%d")
    }
    
    convert_response = requests.post(
        f"{BASE_URL}/api/itineraries/convert-ai-to-custom",
        json=conversion_data,
        headers=headers
    )
    
    if convert_response.status_code != 200:
        print(f"❌ Error de conversión: {convert_response.status_code}")
        return None
    
    result = convert_response.json()
    activities_count = sum(
        len(day_data.get("morning", {})) + 
        len(day_data.get("afternoon", {})) + 
        len(day_data.get("evening", {}))
        for day_data in result["itinerary"].values()
    )
    
    print(f"✅ Conversión exitosa: {activities_count} actividades")
    
    # 4. Instrucciones de testing manual
    print(f"\n🎯 TESTING MANUAL READY:")
    print(f"=" * 40)
    print(f"📋 Pasos específicos:")
    print(f"   1. Abrir http://localhost:8000")
    print(f"   2. Login: test_validation / password123")
    print(f"   3. Ir a 'Itinerario Personalizado'")
    print(f"   4. Clic en 'Pegar itinerario de IA existente'")
    print(f"   5. Seleccionar: Buenos Aires, Argentina (ID: {ai_itinerary['id']})")
    print(f"   6. Buscar actividades con horarios específicos")
    print(f"   7. Hacer clic en botón '🔍 Ver detalle'")
    print(f"")
    print(f"✅ Qué verificar en el modal:")
    print(f"   • Se abre modal con PublicationCard")
    print(f"   • Muestra fotos en carrusel (si las hay)")
    print(f"   • Muestra rating y reseñas")
    print(f"   • Muestra descripción completa")
    print(f"   • Muestra horarios específicos (ej: 10:30-11:30)")
    print(f"   • Muestra texto original de IA")
    print(f"   • Muestra costo estimado")
    print(f"   • Muestra información de disponibilidad")
    
    return ai_itinerary["id"]

if __name__ == "__main__":
    setup_test_itinerary()