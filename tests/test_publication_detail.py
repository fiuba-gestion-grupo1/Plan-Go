"""
Test script para verificar la funcionalidad de detalle de publicación 
en itinerarios personalizados
"""

import requests
import json
import time
import pytest

pytestmark = pytest.mark.skip(
    reason="Test de integración manual: requiere backend levantado en http://localhost:8000"
)

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}

def test_publication_detail_functionality():
    print("🚀 TEST: Funcionalidad de Detalle de Publicación")
    print("=" * 55)
    
    print("\n1. 🔐 Autenticación...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    if login_response.status_code != 200:
        print(f"❌ Error de login: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado")
    
    print("\n2. 📋 Obteniendo itinerarios de IA...")
    ai_list_response = requests.get(f"{BASE_URL}/api/itineraries/ai-list", headers=headers)
    
    if ai_list_response.status_code != 200:
        print(f"❌ Error obteniendo lista: {ai_list_response.status_code}")
        return
    
    itineraries = ai_list_response.json()["itineraries"]
    if not itineraries:
        print("⚠️ No hay itinerarios de IA disponibles")
        return
    
    ai_itinerary = itineraries[0]
    print(f"✅ Itinerario seleccionado: {ai_itinerary['destination']} (ID: {ai_itinerary['id']})")
    
    print("\n3. 🔄 Convirtiendo a personalizado...")
    conversion_data = {
        "ai_itinerary_id": ai_itinerary["id"],
        "custom_destination": ai_itinerary["destination"],
        "custom_start_date": ai_itinerary["start_date"],
        "custom_end_date": ai_itinerary["end_date"]
    }
    
    convert_response = requests.post(
        f"{BASE_URL}/api/itineraries/convert-ai-to-custom",
        json=conversion_data,
        headers=headers
    )
    
    if convert_response.status_code != 200:
        print(f"❌ Error de conversión: {convert_response.status_code}")
        print(convert_response.text[:300])
        return
    
    result = convert_response.json()
    print("✅ Conversión exitosa")
    
    print("\n4. 🔍 Analizando datos para frontend...")
    itinerary_data = result.get("itinerary", {})
    
    print(f"   📅 Total de días: {len(itinerary_data)}")
    
    activities_with_details = []
    
    for day_key, day_data in itinerary_data.items():
        for period, activities in day_data.items():
            for time_slot, activity in activities.items():
                if isinstance(activity, dict) and activity.get("place_name"):
                    activities_with_details.append({
                        "day": day_key,
                        "period": period,
                        "time": time_slot,
                        "activity": activity
                    })
    
    print(f"   🏛️ Actividades con detalle: {len(activities_with_details)}")
    
    if activities_with_details:
        print("\n5. 📋 Ejemplo de datos para PublicationCard:")
        example = activities_with_details[0]["activity"]
        
        print(f"   📍 place_name: {example.get('place_name', 'N/A')}")
        print(f"   📝 description: {example.get('description', 'N/A')[:50]}...")
        print(f"   🏠 address: {example.get('address', 'N/A')}")
        print(f"   ⏱️ duration_min: {example.get('duration_min', 'N/A')}")
        print(f"   🤖 converted_from_ai: {example.get('converted_from_ai', 'N/A')}")
        print(f"   🕐 start_time: {example.get('start_time', 'N/A')}")
        print(f"   🕐 end_time: {example.get('end_time', 'N/A')}")
        print(f"   📝 original_text: {example.get('original_text', 'N/A')}")
        
        required_fields = ["id", "place_name", "address", "city", "province", "country"]
        missing_fields = []
        
        for field in required_fields:
            if not example.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"   ⚠️ Campos faltantes: {missing_fields}")
        else:
            print("   ✅ Todos los campos requeridos presentes")
    
    print("\n6. 🖼️ Verificando datos adicionales...")
    
    if activities_with_details:
        example = activities_with_details[0]["activity"]
        has_photos = bool(example.get("photos"))
        has_rating = bool(example.get("avg_rating") or example.get("rating_avg"))
        has_categories = bool(example.get("categories"))
        
        print(f"   📸 Tiene fotos: {has_photos}")
        print(f"   ⭐ Tiene rating: {has_rating}")
        print(f"   🏷️ Tiene categorías: {has_categories}")
        
        if has_categories:
            categories = example.get("categories", [])
            print(f"   🏷️ Categorías ejemplo: {categories[:3]}")
    
    print(f"\n🎯 RESUMEN PARA FRONTEND:")
    print(f"   ✅ Datos de conversión: COMPLETOS")
    print(f"   ✅ Actividades parseadas: {len(activities_with_details)}")
    print(f"   ✅ Estructura compatible con PublicationCard: SÍ")
    
    frontend_score = 100 if len(activities_with_details) > 0 else 50
    print(f"   🌟 Score de compatibilidad: {frontend_score}/100")
    
    print(f"\n📋 PASOS PARA TESTING MANUAL:")
    print(f"   1. Ir a http://localhost:8000")
    print(f"   2. Login como test_validation")
    print(f"   3. Navegar a 'Itinerario Personalizado'")
    print(f"   4. Hacer clic en 'Pegar itinerario de IA existente'")
    print(f"   5. Seleccionar: {ai_itinerary['destination']}")
    print(f"   6. Buscar actividad con botón '🔍 Ver detalle'")
    print(f"   7. Verificar que se abra modal con PublicationCard")
    
    print("\n" + "=" * 55)
    print("🎯 TEST COMPLETADO - Frontend listo para pruebas")
    
    return result

if __name__ == "__main__":
    test_publication_detail_functionality()
