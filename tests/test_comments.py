#!/usr/bin/env python3
"""
Script para probar la nueva funcionalidad de comentarios en itinerarios
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

# def test_itinerary_with_comments(token):
#     """Probar crear un itinerario con comentarios"""
#     if not token:
#         print("No hay token disponible")
#         return
    
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }
    
#     # Datos del itinerario con comentarios
#     start_date = datetime.now().date() + timedelta(days=30)
#     end_date = start_date + timedelta(days=3)
    
#     itinerary_data = {
#         "destination": "París, Francia",
#         "start_date": start_date.isoformat(),
#         "end_date": end_date.isoformat(),
#         "budget": 2000,
#         "cant_persons": 2,
#         "trip_type": "Romántico",
#         "arrival_time": "14:30",
#         "departure_time": "18:00",
#         "comments": "No queremos ir a lugares muy concurridos, preferimos actividades culturales tranquilas y restaurantes íntimos. Evitar las zonas turísticas más populares."
#     }
    
#     print("Creando itinerario con comentarios...")
#     print(f"Comentarios: {itinerary_data['comments']}")
    
#     response = requests.post(f"{BASE_URL}/api/itineraries/request", json=itinerary_data, headers=headers)
    
#     if response.status_code == 200:
#         data = response.json()
#         print(f"✅ Itinerario creado exitosamente!")
#         print(f"ID: {data.get('id')}")
#         print(f"Destino: {data.get('destination')}")
#         print(f"Comentarios guardados: {data.get('comments')}")
#         print(f"Estado: {data.get('status')}")
        
#         if data.get('generated_itinerary'):
#             print("✅ Itinerario generado:")
#             print(data.get('generated_itinerary')[:500] + "...")
        
#         return data.get('id')
#     else:
#         print(f"❌ Error al crear itinerario: {response.status_code}")
#         print(response.text)
#         return None

# def test_get_itinerary(token, itinerary_id):
#     """Probar obtener un itinerario específico"""
#     if not token or not itinerary_id:
#         return
    
#     headers = {
#         "Authorization": f"Bearer {token}"
#     }
    
#     print(f"\nObteniendo itinerario {itinerary_id}...")
#     response = requests.get(f"{BASE_URL}/api/itineraries/{itinerary_id}", headers=headers)
    
#     if response.status_code == 200:
#         data = response.json()
#         print(f"✅ Itinerario obtenido exitosamente!")
#         print(f"Comentarios: {data.get('comments')}")
#     else:
#         print(f"❌ Error al obtener itinerario: {response.status_code}")

# def test_list_itineraries(token):
#     """Probar listar todos los itinerarios del usuario"""
#     if not token:
#         return
    
#     headers = {
#         "Authorization": f"Bearer {token}"
#     }
    
#     print(f"\nListando todos los itinerarios del usuario...")
#     response = requests.get(f"{BASE_URL}/api/itineraries/my-itineraries", headers=headers)
    
#     if response.status_code == 200:
#         data = response.json()
#         print(f"✅ {len(data)} itinerarios encontrados")
#         for itinerary in data:
#             print(f"  - ID {itinerary.get('id')}: {itinerary.get('destination')} - Comentarios: {itinerary.get('comments', 'Sin comentarios')}")
#     else:
#         print(f"❌ Error al listar itinerarios: {response.status_code}")

# def test_date_issue():
#     """Probar el problema de fechas que se mueven un día atrás"""
#     token = login()
#     if not token:
#         print("No hay token disponible")
#         return
    
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }
    
#     # Usar una fecha específica para probar
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
    
#     print(f"Enviando fechas:")
#     print(f"  Start: {test_start}")
#     print(f"  End: {test_end}")
    
#     response = requests.post(f"{BASE_URL}/api/itineraries/request", json=itinerary_data, headers=headers)
    
#     if response.status_code == 200:
#         data = response.json()
#         print(f"Fechas recibidas en respuesta:")
#         print(f"  Start: {data.get('start_date')}")
#         print(f"  End: {data.get('end_date')}")
        
#         # Verificar si hay diferencia
#         if data.get('start_date') != test_start:
#             print(f"❌ PROBLEMA: Fecha de inicio cambió de {test_start} a {data.get('start_date')}")
#         else:
#             print(f"✅ Fecha de inicio correcta: {data.get('start_date')}")
            
#         if data.get('end_date') != test_end:
#             print(f"❌ PROBLEMA: Fecha de fin cambió de {test_end} a {data.get('end_date')}")
#         else:
#             print(f"✅ Fecha de fin correcta: {data.get('end_date')}")
            
#         return data.get('id')
#     else:
#         print(f"❌ Error al crear itinerario: {response.status_code}")
#         print(response.text)
#         return None
#     print("=== Prueba de funcionalidad de comentarios en itinerarios ===\n")
    
#     # 1. Login
#     print("1. Haciendo login...")
#     token = login()
    
#     if token:
#         print("✅ Login exitoso")
        
#         # 2. Crear itinerario con comentarios
#         print("\n2. Creando itinerario con comentarios...")
#         itinerary_id = test_itinerary_with_comments(token)
        
#         # 3. Obtener itinerario específico
#         if itinerary_id:
#             print("\n3. Obteniendo itinerario específico...")
#             test_get_itinerary(token, itinerary_id)
        
#         # 4. Listar todos los itinerarios
#         print("\n4. Listando todos los itinerarios...")
#         test_list_itineraries(token)
        
#     else:
#         print("❌ No se pudo hacer login")
    
#     print("\n=== Fin de pruebas ===")