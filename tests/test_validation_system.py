import requests
import json
from datetime import datetime, timedelta
import pytest

pytestmark = pytest.mark.skip(
    reason="Test de integración manual: requiere backend levantado en http://localhost:8000"
)

BASE_URL = "http://localhost:8000"
TEST_USER = {
    "identifier": "test_validation",
    "password": "password123"
}

def test_ai_validation():
    print("🚀 TEST: Sistema de Validación de Itinerarios IA")
    print("=" * 50)
    
    print("\n1. Autenticando usuario...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    if login_response.status_code != 200:
        print(f"❌ Error de login: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado")
    
    tomorrow = datetime.now() + timedelta(days=1)
    end_date = tomorrow + timedelta(days=3)
    
    itinerary_request = {
        "destination": "Buenos Aires, Argentina",
        "start_date": tomorrow.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "budget": 150,
        "cant_persons": 2,
        "trip_type": "cultural",
        "arrival_time": "14:00",
        "departure_time": "18:00",
        "comments": "Queremos ver museos"
    }
    
    print(f"\n2. Solicitando itinerario...")
    print(f"   Destino: {itinerary_request['destination']}")
    print(f"   Presupuesto: US${itinerary_request['budget']}")
    
    response = requests.post(
        f"{BASE_URL}/api/itineraries/request",
        json=itinerary_request,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    result = response.json()
    print("✅ Itinerario generado")
    
    print(f"\n3. Analizando validación...")
    print(f"   Status: {result['status']}")
    
    generated_text = result['generated_itinerary']
    
    validation_indicators = [
        "ERRORES DE VALIDACIÓN",
        "ADVERTENCIAS", 
        "COSTO REAL:",
        "COSTO TOTAL:",
        "IA estimó:"
    ]
    
    found_validation = []
    for indicator in validation_indicators:
        if indicator in generated_text:
            found_validation.append(indicator)
    
    print(f"   Validación encontrada: {len(found_validation)}/5")
    for indicator in found_validation:
        print(f"   ✅ {indicator}")
    
    print(f"\n4. Fragmento del itinerario:")
    lines = generated_text.split('\n')[:10]
    for line in lines:
        if line.strip():
            print(f"   {line}")
    
    cost_lines = []
    for line in generated_text.split('\n'):
        if any(keyword in line for keyword in ["COSTO", "US$", "presupuesto"]):
            cost_lines.append(line.strip())
    
    if cost_lines:
        print(f"\n5. Información de costos:")
        for line in cost_lines:
            print(f"   {line}")
    
    validation_score = len(found_validation)
    print(f"\n🎉 RESUMEN:")
    print(f"   ✅ Generación: EXITOSA")
    print(f"   ✅ Validación: {'ACTIVA' if validation_score >= 2 else 'LIMITADA'}")
    print(f"   ✅ Score: {validation_score}/5")
    
    if validation_score >= 3:
        print(f"\n🌟 Sistema de validación funcionando correctamente!")
    elif validation_score >= 1:
        print(f"\n⚠️ Validación parcialmente activa")
    else:
        print(f"\n❌ Validación no detectada")
    
    print("\n" + "=" * 50)
    print("🎯 PASO 2 COMPLETADO: Validación Backend")
    return result

if __name__ == "__main__":
    test_ai_validation()
