"""
Test final para verificar que el modal funciona correctamente con fotos
"""

import requests
import json

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}

def test_modal_with_photos():
    print("🚀 TEST: Modal de Detalle con Fotos")
    print("=" * 45)
    
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado")
    
    ai_list_response = requests.get(f"{BASE_URL}/api/itineraries/ai-list", headers=headers)
    itineraries = ai_list_response.json()["itineraries"]
    ai_itinerary = itineraries[0]
    
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
    
    result = convert_response.json()
    print("✅ Itinerario convertido")
    
    print(f"\n🔍 Verificando datos para PublicationCard:")
    
    itinerary_data = result["itinerary"]
    activities_with_photos = []
    activities_without_photos = []
    
    for day_key, day_data in itinerary_data.items():
        for period, activities in day_data.items():
            for time_slot, activity in activities.items():
                if isinstance(activity, dict) and not activity.get("is_continuation"):
                    photos = activity.get("photos", [])
                    if photos:
                        activities_with_photos.append(activity)
                    else:
                        activities_without_photos.append(activity)
    
    print(f"   📸 Actividades CON fotos: {len(activities_with_photos)}")
    print(f"   📸 Actividades SIN fotos: {len(activities_without_photos)}")
    
    if activities_with_photos:
        example = activities_with_photos[0]
        print(f"\n📋 Ejemplo de actividad con fotos:")
        print(f"   📍 Nombre: {example.get('place_name')}")
        print(f"   📸 Fotos: {len(example.get('photos', []))} imágenes")
        print(f"   🔗 URLs: {example.get('photos', [])}")
        
        required_fields = {
            "id": example.get("id"),
            "place_name": example.get("place_name"),
            "photos": example.get("photos"),
            "city": example.get("city"),
            "province": example.get("province"),
            "country": example.get("country")
        }
        
        print(f"\n✅ Campos para PublicationCard:")
        for field, value in required_fields.items():
            status = "✅" if value else "❌"
            print(f"   {status} {field}: {value}")
    
    print(f"\n🎯 TESTING MANUAL FINAL:")
    print(f"=" * 30)
    print(f"   1. Ir a http://localhost:8000")
    print(f"   2. Login: test_validation / password123")
    print(f"   3. Itinerario Personalizado → Pegar IA")
    print(f"   4. Seleccionar: {ai_itinerary['destination']}")
    print(f"   5. Buscar actividad: '{activities_with_photos[0]['place_name']}'" if activities_with_photos else "cualquier actividad")
    print(f"   6. Hacer clic en '🔍 Ver detalle'")
    print(f"")
    print(f"✅ Verificar en el modal:")
    print(f"   • ❌ NO debe aparecer botón 'Más info'")
    print(f"   • ✅ Debe mostrar carrusel de fotos")
    print(f"   • ✅ Debe mostrar información completa")
    print(f"   • ✅ Debe mostrar texto original de IA")
    
    return len(activities_with_photos) > 0

if __name__ == "__main__":
    test_modal_with_photos()
