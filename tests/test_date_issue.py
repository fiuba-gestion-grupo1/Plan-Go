#!/usr/bin/env python3
"""
Script para probar el problema de fechas en itinerarios
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
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

# def test_date_problem():
#     """Probar el problema específico de fechas"""
#     token = login()
#     if not token:
#         print("❌ No hay token disponible")
#         return
    
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }
    
#     # Usar fechas específicas para probar
#     test_start = "2025-11-17"  # 17 de noviembre
#     test_end = "2025-11-20"    # 20 de noviembre
    
#     itinerary_data = {
#         "destination": "Buenos Aires, Argentina",
#         "start_date": test_start,
#         "end_date": test_end,
#         "budget": 1000,
#         "cant_persons": 1,
#         "trip_type": "Cultural",
#         "comments": "Test de fechas - debería comenzar el 17/11/2025"
#     }
    
#     print(f"📅 ENVIANDO FECHAS:")
#     print(f"   Start: {test_start} (17 nov)")
#     print(f"   End: {test_end} (20 nov)")
#     print()
    
#     response = requests.post(f"{BASE_URL}/api/itineraries/request", json=itinerary_data, headers=headers)
    
#     if response.status_code == 200:
#         data = response.json()
#         received_start = data.get('start_date')
#         received_end = data.get('end_date')
        
#         print(f"📅 FECHAS RECIBIDAS:")
#         print(f"   Start: {received_start}")
#         print(f"   End: {received_end}")
#         print()
        
#         # Verificar si hay diferencia
#         if received_start != test_start:
#             print(f"❌ PROBLEMA CONFIRMADO:")
#             print(f"   Enviado: {test_start}")
#             print(f"   Recibido: {received_start}")
#             print(f"   → Se movió un día hacia atrás!")
#         else:
#             print(f"✅ Fecha de inicio correcta")
            
#         if received_end != test_end:
#             print(f"❌ PROBLEMA en fecha fin:")
#             print(f"   Enviado: {test_end}")
#             print(f"   Recibido: {received_end}")
#         else:
#             print(f"✅ Fecha de fin correcta")
            
#         return data.get('id')
#     else:
#         print(f"❌ Error al crear itinerario: {response.status_code}")
#         print(response.text)
#         return None

if __name__ == "__main__":
    print("=== 🐛 Prueba del problema de fechas ===\n")
    # test_date_problem()
    print("\n=== Fin de la prueba ===")