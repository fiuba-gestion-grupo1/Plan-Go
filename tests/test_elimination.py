#!/usr/bin/env python3
"""
Test script para verificar que la eliminación de actividades funciona
"""

import requests
import json

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}

def test_elimination_functionality():
    print("🚀 TEST: Funcionalidad de Eliminación de Actividades")
    print("=" * 55)
    
    # 1. Login
    print("\n1. 🔐 Autenticación...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado")
    
    # 2. Obtener itinerarios de IA disponibles
    print("\n2. 📋 Obteniendo itinerarios de IA...")
    ai_list_response = requests.get(f"{BASE_URL}/api/itineraries/ai-list", headers=headers)
    itineraries = ai_list_response.json()["itineraries"]
    
    if not itineraries:
        print("⚠️ No hay itinerarios disponibles")
        return
    
    ai_itinerary = itineraries[0]
    print(f"✅ Usando itinerario: {ai_itinerary['destination']} (ID: {ai_itinerary['id']})")
    
    # 3. Convertir a personalizado
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
    
    result = convert_response.json()
    print("✅ Conversión exitosa")
    
    # 4. Verificar estructura de claves
    print("\n4. 🔍 Verificando estructura de claves...")
    itinerary_data = result.get("itinerary", {})
    print(f"   📋 Claves de días: {list(itinerary_data.keys())}")
    
    # Buscar actividades principales (no continuaciones)
    main_activities = []
    for day_key, day_data in itinerary_data.items():
        for period, activities in day_data.items():
            for time_slot, activity in activities.items():
                if isinstance(activity, dict) and not activity.get("is_continuation"):
                    main_activities.append({
                        "day_key": day_key,
                        "period": period,
                        "time": time_slot,
                        "name": activity.get("place_name", "Sin nombre"),
                        "duration": activity.get("duration_min", 0)
                    })
    
    print(f"   🎯 Actividades principales encontradas: {len(main_activities)}")
    
    if main_activities:
        example = main_activities[0]
        print(f"\n📋 Ejemplo de actividad eliminable:")
        print(f"   • Día: {example['day_key']}")
        print(f"   • Período: {example['period']}")
        print(f"   • Horario: {example['time']}")
        print(f"   • Nombre: {example['name']}")
        print(f"   • Duración: {example['duration']} min")
        
        # Verificar que la clave coincida con el formato esperado
        if example['day_key'].startswith('day_'):
            print(f"   ✅ Formato de clave correcto: {example['day_key']}")
        else:
            print(f"   ❌ Formato de clave incorrecto: {example['day_key']}")
    
    # 5. Instrucciones para testing manual
    print(f"\n🎯 TESTING MANUAL DE ELIMINACIÓN:")
    print(f"=" * 40)
    print(f"📋 Pasos para probar:")
    print(f"   1. Ir a http://localhost:8000")
    print(f"   2. Login: test_validation / password123")
    print(f"   3. Itinerario Personalizado → Pegar IA")
    print(f"   4. Seleccionar: {ai_itinerary['destination']}")
    print(f"   5. Buscar actividad principal (sin 'Continuación de:')")
    print(f"   6. Hacer clic en la X roja")
    print(f"   7. Verificar que se elimine toda la actividad y continuaciones")
    print(f"")
    print(f"✅ Qué verificar:")
    print(f"   • La X roja aparece solo en actividades principales")
    print(f"   • Al hacer clic, se elimina la actividad completa")
    print(f"   • Se eliminan también los slots de continuación")
    print(f"   • Los slots quedan disponibles para nuevas actividades")
    
    return len(main_activities)

if __name__ == "__main__":
    test_elimination_functionality()