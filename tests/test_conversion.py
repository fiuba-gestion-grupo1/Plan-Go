import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}

def test_convert_ai_to_custom():
    print("🚀 TEST: Conversión Itinerario IA → Personalizado")
    print("=" * 55)
    
    print("\n1. Autenticando usuario...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado")
    
    print("\n2. Creando itinerario de IA...")
    tomorrow = datetime.now() + timedelta(days=1)
    end_date = tomorrow + timedelta(days=3)
    
    itinerary_request = {
        "destination": "Buenos Aires, Argentina",
        "start_date": tomorrow.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "budget": 400,
        "cant_persons": 2,
        "trip_type": "cultural",
        "arrival_time": "10:00",
        "departure_time": "18:00",
        "comments": "Itinerario para convertir a personalizado"
    }
    
    ai_response = requests.post(f"{BASE_URL}/api/itineraries/request", 
                               json=itinerary_request, headers=headers)
    
    if ai_response.status_code != 200:
        print(f"❌ Error creando IA: {ai_response.status_code}")
        return
    
    ai_itinerary = ai_response.json()
    itinerary_id = ai_itinerary["id"]
    print(f"✅ Itinerario IA creado (ID: {itinerary_id})")
    
    print(f"\n3. Convirtiendo a itinerario personalizado...")
    convert_response = requests.post(
        f"{BASE_URL}/api/itineraries/{itinerary_id}/convert-to-custom",
        headers=headers
    )
    
    if convert_response.status_code != 200:
        print(f"❌ Error de conversión: {convert_response.status_code}")
        print(f"   Response: {convert_response.text}")
        return
    
    conversion_result = convert_response.json()
    print("✅ Conversión exitosa")
    
    print(f"\n4. Analizando estructura convertida...")
    
    success = conversion_result.get("success", False)
    custom_structure = conversion_result.get("custom_structure", {})
    validation = conversion_result.get("validation", {})
    metadata = conversion_result.get("conversion_metadata", {})
    
    print(f"   ✅ Éxito: {success}")
    print(f"   ✅ Días parseados: {validation.get('total_days', 0)}")
    print(f"   ✅ Actividades: {validation.get('total_activities', 0)}")
    print(f"   ✅ Publicaciones: {len(conversion_result.get('publications_used', []))}")
    
    print(f"\n5. Estructura de días convertidos:")
    day_keys = [k for k in custom_structure.keys() if k.startswith("day_")]
    day_keys.sort(key=lambda x: int(x.split("_")[1]))
    
    for day_key in day_keys[:3]:
        day_data = custom_structure[day_key]
        day_num = day_key.split("_")[1]
        print(f"\n   📅 DÍA {day_num}:")
        
        periods = [
            ("morning", "🌅 Mañana", day_data.get("morning", {})),
            ("afternoon", "🌞 Tarde", day_data.get("afternoon", {})),
            ("evening", "🌙 Noche", day_data.get("evening", {}))
        ]
        
        for period_key, period_name, activities in periods:
            if activities:
                print(f"     {period_name}: {len(activities)} actividad(es)")
                for time_slot, activity in list(activities.items())[:2]:
                    activity_name = activity.get("name", "Sin nombre")
                    pub_id = activity.get("id", "N/A")
                    print(f"       • {time_slot} - {activity_name} (ID: {pub_id})")
    
    original = conversion_result.get("original_itinerary", {})
    print(f"\n6. Información del itinerario original:")
    print(f"   • Destino: {original.get('destination', 'N/A')}")
    print(f"   • Fechas: {original.get('start_date', 'N/A')} → {original.get('end_date', 'N/A')}")
    print(f"   • Presupuesto: US${original.get('budget', 0)}")
    print(f"   • Personas: {original.get('cant_persons', 0)}")
    
    validation_errors = validation.get("errors", [])
    validation_warnings = validation.get("warnings", [])
    
    if validation_errors:
        print(f"\n❌ Errores de validación:")
        for error in validation_errors:
            print(f"   • {error}")
    
    if validation_warnings:
        print(f"\n⚠️ Advertencias:")
        for warning in validation_warnings:
            print(f"   • {warning}")
    
    print(f"\n🎯 RESULTADO FINAL:")
    
    if success and validation.get("valid", False):
        print(f"   ✅ CONVERSIÓN EXITOSA")
        print(f"   🎉 {validation['total_days']} día(s) con {validation['total_activities']} actividad(es)")
        score = "EXCELENTE" if validation['total_activities'] >= 5 else "BUENA"
        print(f"   🌟 Calidad: {score}")
    else:
        print(f"   ❌ CONVERSIÓN FALLIDA")
        print(f"   🔧 Revisar errores de parsing o validación")
    
    print("\n" + "=" * 55)
    print("🎯 PASO 3 (Backend): Conversión IA→Custom IMPLEMENTADO")
    print("🚀 Siguiente: Frontend para botón 'Modificar itinerario'")
    
    return conversion_result

if __name__ == "__main__":
    test_convert_ai_to_custom()
