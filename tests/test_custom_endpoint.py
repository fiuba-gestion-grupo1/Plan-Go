"""
Script de prueba para el endpoint /api/itineraries/custom
"""

import requests
import json
from datetime import datetime, timedelta
import pytest

pytestmark = pytest.mark.skip(
    reason="Test de integración manual: requiere backend levantado en http://localhost:8000"
)


def test_custom_itinerary():
    """Prueba el endpoint de itinerarios personalizados"""

    base_url = "http://localhost:8000"

    login_data = {"identifier": "premium@fi.uba.ar", "password": "password"}

    login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Error en login: {login_response.status_code}")
        print(login_response.text)
        return False

    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    test_data = {
        "destination": "Buenos Aires",
        "start_date": today.isoformat(),
        "end_date": tomorrow.isoformat(),
        "type": "custom",
        "itinerary_data": {
            today.isoformat(): {
                "morning": {
                    "08:00": {
                        "id": 1,
                        "place_name": "Hotel Continental",
                        "duration_min": 120,
                    },
                    "10:00": {"is_continuation": True},
                },
                "afternoon": {
                    "14:00": {"id": 2, "place_name": "Ritz Paris", "duration_min": 180},
                    "14:30": {"is_continuation": True},
                    "15:00": {"is_continuation": True},
                },
            }
        },
    }

    print("🧪 Probando endpoint /api/itineraries/custom...")
    print(f"📅 Fechas: {today} → {tomorrow}")

    response = requests.post(
        f"{base_url}/api/itineraries/custom", json=test_data, headers=headers
    )

    print(f"📊 Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✅ ¡Éxito! Itinerario personalizado creado correctamente")
        result = response.json()
        print(f"🆔 ID del itinerario: {result['id']}")
        print(f"📍 Destino: {result['destination']}")
        print(f"📋 Estado: {result['status']}")
        print(f"📄 Publicaciones: {len(result['publications'])} encontradas")
        return True
    else:
        print(f"❌ Error al crear itinerario: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"💬 Detalle del error: {error_detail}")
        except:
            print(f"💬 Respuesta: {response.text}")
        return False


if __name__ == "__main__":
    success = test_custom_itinerary()
    if success:
        print("\n🎉 Prueba completada exitosamente!")
    else:
        print("\n💥 Prueba falló!")
