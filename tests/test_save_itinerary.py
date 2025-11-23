"""
Test para verificar el endpoint de guardar itinerario personalizado
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

test_payload = {
    "destination": "Buenos Aires, Argentina",
    "start_date": "2025-01-15",
    "end_date": "2025-01-17",
    "cant_persons": 2,
    "budget": 500,
    "itinerary_data": {
        "day_1": {
            "morning": {
                "09:00": {
                    "place_name": "Test Place",
                    "publication_id": 1,
                    "duration_min": 120,
                }
            },
            "afternoon": {},
            "evening": {},
        },
        "day_2": {"morning": {}, "afternoon": {}, "evening": {}},
    },
    "type": "custom",
}


def test_backend_health():
    """Verificar que el backend esté funcionando"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Backend health: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Backend no disponible: {e}")
        return False


def test_save_itinerary_without_auth():
    """Test para ver qué error da sin autenticación"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/itineraries/custom",
            json=test_payload,
            headers={"Content-Type": "application/json"},
        )
        print(f"📝 Sin auth - Status: {response.status_code}")
        print(f"📝 Sin auth - Response: {response.text}")
    except Exception as e:
        print(f"❌ Error en test sin auth: {e}")


def test_save_itinerary_structure():
    """Test de la estructura del payload"""
    print("📋 Estructura del payload:")
    print(json.dumps(test_payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("🚀 Iniciando tests...")

    if test_backend_health():
        test_save_itinerary_without_auth()
        test_save_itinerary_structure()
    else:
        print("❌ Backend no está disponible")
