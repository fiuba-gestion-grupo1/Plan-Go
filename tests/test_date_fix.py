#!/usr/bin/env python3
"""
Test específico para verificar que las fechas se manejan correctamente
después de aplicar la corrección en el frontend
"""

import requests
import json

BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "premium@fi.uba.ar"
TEST_USER_PASSWORD = "password"

def login():
    """Login y obtener token"""
    login_data = {
        "identifier": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Error en login: {response.status_code} - {response.text}")
        return None

def test_date_formats():
    """Probar diferentes formatos de fecha"""
    token = login()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Casos de prueba con diferentes fechas
    test_cases = [
        {
            "name": "Fecha normal (mañana)",
            "start": "2025-11-17",
            "end": "2025-11-19",
            "expected_start": "2025-11-17",
            "expected_end": "2025-11-19"
        },
        {
            "name": "Fecha en otro mes",
            "start": "2025-12-01",
            "end": "2025-12-05",
            "expected_start": "2025-12-01", 
            "expected_end": "2025-12-05"
        },
        {
            "name": "Fecha de año nuevo",
            "start": "2025-12-31",
            "end": "2026-01-03",
            "expected_start": "2025-12-31",
            "expected_end": "2026-01-03"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {case['name']}")
        print(f"   Enviando: {case['start']} → {case['end']}")
        
        itinerary_data = {
            "destination": "Madrid, España",
            "start_date": case["start"],
            "end_date": case["end"],
            "budget": 1500,
            "cant_persons": 2,
            "trip_type": "Cultural",
            "comments": f"Test de fechas caso {i}"
        }
        
        response = requests.post(f"{BASE_URL}/api/itineraries/request", json=itinerary_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            received_start = data.get('start_date')
            received_end = data.get('end_date')
            
            print(f"   Recibido: {received_start} → {received_end}")
            
            # Verificar exactitud
            start_correct = received_start == case["expected_start"]
            end_correct = received_end == case["expected_end"]
            
            if start_correct and end_correct:
                print(f"   ✅ CORRECTO")
            else:
                print(f"   ❌ ERROR:")
                if not start_correct:
                    print(f"      Start: esperado {case['expected_start']}, recibido {received_start}")
                if not end_correct:
                    print(f"      End: esperado {case['expected_end']}, recibido {received_end}")
                    
            # Verificar también el itinerario generado para ver la fecha
            if data.get('generated_itinerary'):
                itinerary_text = data.get('generated_itinerary')
                if case['start'][-2:] in itinerary_text:  # Buscar el día en el texto
                    print(f"   ✅ Fecha aparece correctamente en el itinerario")
                else:
                    print(f"   ⚠️  Revisar si la fecha aparece correctamente en el itinerario")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")

if __name__ == "__main__":
    print("=== 🔧 Test de corrección de fechas ===")
    test_date_formats()
    print("\n=== Fin del test ===")