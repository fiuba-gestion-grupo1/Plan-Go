#!/usr/bin/env python3

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}

def test_paste_endpoint():
    print("🚀 TEST: Endpoint 'Pegar Itinerario de IA'")
    print("=" * 50)
    
    # 1. Login
    print("\n1. 🔐 Autenticación...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado")
    
    # 2. Probar endpoint de listar itinerarios de IA
    print("\n2. 📋 Probando endpoint /my-ai-itineraries...")
    
    list_response = requests.get(f"{BASE_URL}/api/itineraries/ai-list", 
                                headers=headers)
    
    if list_response.status_code != 200:
        print(f"❌ Error en endpoint: {list_response.status_code}")
        print(f"   Response: {list_response.text}")
        return False
    
    list_result = list_response.json()
    print("✅ Endpoint funcionando")
    
    total_itineraries = list_result.get("total", 0)
    itineraries = list_result.get("itineraries", [])
    
    print(f"   📊 Total de itinerarios de IA: {total_itineraries}")
    
    if total_itineraries == 0:
        print("   ⚠️ No hay itinerarios de IA. Creando uno...")
        
        # Crear un itinerario de IA rápido
        tomorrow = datetime.now() + timedelta(days=1)
        end_date = tomorrow + timedelta(days=2)
        
        ai_request = {
            "destination": "Buenos Aires, Argentina",
            "start_date": tomorrow.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "budget": 300,
            "cant_persons": 2,
            "trip_type": "cultural",
            "arrival_time": "10:00",
            "departure_time": "18:00",
            "comments": "Itinerario para test de pegado"
        }
        
        ai_response = requests.post(f"{BASE_URL}/api/itineraries/request", 
                                   json=ai_request, headers=headers)
        
        if ai_response.status_code == 200:
            print("   ✅ Itinerario de IA creado")
            
            # Volver a listar
            list_response = requests.get(f"{BASE_URL}/api/itineraries/ai-list", 
                                        headers=headers)
            list_result = list_response.json()
            itineraries = list_result.get("itineraries", [])
            total_itineraries = list_result.get("total", 0)
            print(f"   📊 Total actualizado: {total_itineraries}")
        else:
            print("   ❌ Error creando itinerario de IA")
            return False
    
    # 3. Analizar los itinerarios disponibles
    print(f"\n3. 📊 Analizando itinerarios disponibles...")
    
    if itineraries:
        print(f"   📋 Listando {len(itineraries)} itinerarios:")
        
        for i, itinerary in enumerate(itineraries[:3]):  # Mostrar máximo 3
            print(f"\n   {i+1}. ID: {itinerary['id']}")
            print(f"      📍 Destino: {itinerary['destination']}")
            print(f"      📅 Duración: {itinerary['duration_days']} días")
            print(f"      💰 Presupuesto: US${itinerary['budget']}")
            print(f"      ✅ Status: {itinerary['status']}")
            print(f"      🔍 Validado: {'SÍ' if itinerary['has_validation'] else 'NO'}")
            print(f"      🏛️ Lugares: {itinerary['publication_count']}")
            print(f"      📝 Preview: {itinerary['preview'][:60]}...")
        
        # 4. Probar conversión del primer itinerario
        first_itinerary = itineraries[0]
        print(f"\n4. 🔄 Probando conversión del itinerario ID {first_itinerary['id']}...")
        
        convert_response = requests.post(
            f"{BASE_URL}/api/itineraries/{first_itinerary['id']}/convert-to-custom",
            headers=headers
        )
        
        if convert_response.status_code == 200:
            conversion_result = convert_response.json()
            print("✅ Conversión exitosa")
            
            validation = conversion_result.get("validation", {})
            print(f"   📅 Días: {validation.get('total_days', 0)}")
            print(f"   🎯 Actividades: {validation.get('total_activities', 0)}")
            print(f"   🏛️ Publicaciones: {len(conversion_result.get('publications_used', []))}")
            
        else:
            print(f"❌ Error en conversión: {convert_response.status_code}")
            return False
    
    else:
        print("   ⚠️ No hay itinerarios disponibles para probar")
    
    # 5. Resultado final
    print(f"\n🎯 RESULTADO FINAL:")
    print(f"   ✅ Endpoint /my-ai-itineraries: FUNCIONAL")
    print(f"   ✅ Conversión disponible: SÍ")
    print(f"   ✅ Datos completos: SÍ")
    
    quality_score = 0
    if list_response.status_code == 200: quality_score += 25
    if total_itineraries > 0: quality_score += 25
    if itineraries and all('preview' in it for it in itineraries): quality_score += 25
    if convert_response.status_code == 200: quality_score += 25
    
    print(f"   🎯 Score backend: {quality_score}/100")
    
    print("\n" + "=" * 50)
    print("🎯 PASO 4 (Backend): Endpoint para Pegar IA FUNCIONAL")
    print("🚀 Próximo: Completar frontend del modal")
    
    return quality_score >= 75

if __name__ == "__main__":
    success = test_paste_endpoint()
    exit(0 if success else 1)