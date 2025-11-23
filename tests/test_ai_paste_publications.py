"""
Test para verificar que la búsqueda de publicaciones funciona después de pegar IA
"""

import requests
import json
import pytest

pytestmark = pytest.mark.skip(
    reason="Test de integración manual: requiere backend levantado en http://localhost:8000"
)

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}

def test_publications_after_ai_paste():
    print("🚀 TEST: Publicaciones Disponibles Después de Pegar IA")
    print("=" * 60)
    
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado")
    
    ai_list_response = requests.get(f"{BASE_URL}/api/itineraries/ai-list", headers=headers)
    itineraries = ai_list_response.json()["itineraries"]
    ai_itinerary = itineraries[0]
    
    print(f"\n📋 Itinerario IA:")
    print(f"   Destination: '{ai_itinerary['destination']}'")
    
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
    converted_destination = result["destination"]
    print(f"\n✅ Itinerario convertido:")
    print(f"   Destination: '{converted_destination}'")
    
    city_name = converted_destination.split(',')[0].strip() if ',' in converted_destination else converted_destination
    search_url = f"{BASE_URL}/api/publications/search?destination={city_name}"
    
    print(f"\n🔍 Simulando búsqueda del frontend:")
    print(f"   Destino original: '{converted_destination}'")
    print(f"   Ciudad extraída: '{city_name}'")
    print(f"   URL de búsqueda: {search_url}")
    
    search_response = requests.get(search_url, headers=headers)
    
    if search_response.status_code == 200:
        publications = search_response.json()
        count = len(publications) if publications else 0
        
        print(f"\n🎯 RESULTADO:")
        print(f"   ✅ Búsqueda exitosa: {count} publicaciones encontradas")
        
        if count > 0:
            print(f"\n📋 Ejemplos de publicaciones disponibles:")
            for i, pub in enumerate(publications[:3], 1):
                print(f"   {i}. {pub.get('place_name', 'Sin nombre')}")
                print(f"      📍 {pub.get('address', 'Sin dirección')}")
                print(f"      🏙️ {pub.get('city', 'Sin ciudad')}, {pub.get('country', 'Sin país')}")
                
            success_score = 100
            print(f"\n🌟 Score de éxito: {success_score}/100")
            
        else:
            print(f"\n❌ No se encontraron publicaciones")
            success_score = 0
            
    else:
        print(f"\n❌ Error en búsqueda: {search_response.status_code}")
        success_score = 0
    
    print(f"\n🎯 TESTING MANUAL:")
    print(f"=" * 30)
    print(f"   1. Ir a http://localhost:8000")
    print(f"   2. Login: test_validation / password123")
    print(f"   3. Itinerario Personalizado → Pegar IA")
    print(f"   4. Seleccionar: {ai_itinerary['destination']}")
    print(f"   5. Hacer clic en '+ Agregar actividad'")
    print(f"   6. ✅ Debería mostrar {count} publicaciones disponibles")
    
    return success_score >= 100

if __name__ == "__main__":
    test_publications_after_ai_paste()
