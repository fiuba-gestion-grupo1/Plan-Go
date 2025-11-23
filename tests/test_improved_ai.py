"""
Script de prueba para el nuevo prompt mejorado de IA con validaciones
"""

import requests
import json
from datetime import datetime, timedelta

def test_improved_ai_itinerary():
    """Prueba el endpoint con el nuevo prompt mejorado"""
    
    base_url = "http://localhost:8000"
    
    login_data = {
        "identifier": "premium@fi.uba.ar",
        "password": "password"
    }
    
    login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Error en login: {login_response.status_code}")
        return False
    
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    today = datetime.now().date()
    end_date = today + timedelta(days=2)
    
    ai_request = {
        "destination": "Buenos Aires",
        "start_date": today.isoformat(),
        "end_date": end_date.isoformat(),
        "budget": 500,
        "cant_persons": 2,
        "trip_type": "cultural",
        "comments": "Nos gusta la gastronomía y la cultura local"
    }
    
    print("🤖 Probando generación con IA mejorada...")
    print(f"📅 Fechas: {today} → {end_date}")
    print(f"💰 Presupuesto: US${ai_request['budget']}")
    print(f"👥 Personas: {ai_request['cant_persons']}")
    
    response = requests.post(
        f"{base_url}/api/itineraries/request",
        json=ai_request,
        headers=headers
    )
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ ¡Éxito! Itinerario generado con IA mejorada")
        result = response.json()
        print(f"🆔 ID del itinerario: {result['id']}")
        print(f"📍 Destino: {result['destination']}")
        print(f"📋 Estado: {result['status']}")
        print(f"📄 Publicaciones encontradas: {len(result['publications'])}")
        
        itinerary_text = result.get('generated_itinerary', '')
        preview = itinerary_text[:300] + "..." if len(itinerary_text) > 300 else itinerary_text
        print(f"📝 Preview del itinerario:\n{preview}")
        
        if result['publications']:
            print("\n🏛️ Publicaciones utilizadas:")
            for pub in result['publications']:
                print(f"  • ID:{pub['id']} - {pub['place_name']}")
                if pub.get('available_days'):
                    print(f"    📅 Días: {', '.join(pub['available_days'])}")
                if pub.get('available_hours'):
                    print(f"    🕒 Horarios: {', '.join(pub['available_hours'])}")
                if pub.get('duration_min'):
                    hours = pub['duration_min'] / 60
                    print(f"    ⏱️ Duración: {hours:.1f}h")
        
        return True
    else:
        print(f"❌ Error al generar itinerario: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"💬 Detalle del error: {error_detail}")
        except:
            print(f"💬 Respuesta: {response.text}")
        return False

if __name__ == "__main__":
    print("🚀 Probando IA mejorada con validaciones...")
    success = test_improved_ai_itinerary()
    if success:
        print("\n🎉 Prueba de IA mejorada completada!")
    else:
        print("\n💥 Prueba falló!")
