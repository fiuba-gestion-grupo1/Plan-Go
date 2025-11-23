"""
Script para diagnosticar el problema de búsqueda de publicaciones
"""

import requests
import json

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}


def diagnose_publication_search():
    print("🔍 DIAGNÓSTICO: Búsqueda de Publicaciones en Itinerario Pegado")
    print("=" * 65)

    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ai_list_response = requests.get(
        f"{BASE_URL}/api/itineraries/ai-list", headers=headers
    )
    itineraries = ai_list_response.json()["itineraries"]

    if not itineraries:
        print("❌ No hay itinerarios de IA disponibles")
        return

    ai_itinerary = itineraries[0]
    print(f"📋 Itinerario de IA seleccionado:")
    print(f"   ID: {ai_itinerary['id']}")
    print(f"   Destination: \"{ai_itinerary['destination']}\"")

    print(f"\n🔄 Convirtiendo a personalizado...")
    conversion_data = {
        "ai_itinerary_id": ai_itinerary["id"],
        "custom_destination": ai_itinerary["destination"],
        "custom_start_date": ai_itinerary["start_date"],
        "custom_end_date": ai_itinerary["end_date"],
    }

    convert_response = requests.post(
        f"{BASE_URL}/api/itineraries/convert-ai-to-custom",
        json=conversion_data,
        headers=headers,
    )

    if convert_response.status_code != 200:
        print(f"❌ Error en conversión: {convert_response.status_code}")
        return

    result = convert_response.json()
    converted_destination = result["destination"]
    print(f"✅ Conversión exitosa")
    print(f'   Destination convertido: "{converted_destination}"')

    print(f"\n🔍 Probando búsquedas de publicaciones:")

    test_destinations = [
        converted_destination,
        "Buenos Aires",
        "Buenos Aires, Argentina",
        "buenos aires",
        "Argentina",
        "buenos aires, argentina",
        ai_itinerary["destination"],
    ]

    for i, dest in enumerate(test_destinations, 1):
        try:
            search_url = f"{BASE_URL}/api/publications/search?destination={dest}"
            search_response = requests.get(search_url, headers=headers)

            if search_response.status_code == 200:
                publications = search_response.json()
                count = len(publications) if publications else 0
                status = "✅" if count > 0 else "❌"
                print(f'   {i}. "{dest}": {status} {count} publicaciones')

                if count > 0 and i == 1:
                    print(f"      Ejemplos:")
                    for j, pub in enumerate(publications[:3], 1):
                        print(
                            f"        {j}. {pub.get('place_name', 'Sin nombre')} - {pub.get('city', 'Sin ciudad')}"
                        )
            else:
                print(f'   {i}. "{dest}": ❌ ERROR {search_response.status_code}')

        except Exception as e:
            print(f'   {i}. "{dest}": ❌ EXCEPCIÓN {str(e)}')

    print(f"\n📊 Verificando publicaciones en la base de datos:")
    try:
        all_pubs_response = requests.get(
            f"{BASE_URL}/api/publications", headers=headers
        )
        if all_pubs_response.status_code == 200:
            all_publications = all_pubs_response.json()
            cities = set()
            countries = set()

            for pub in all_publications:
                if pub.get("city"):
                    cities.add(pub["city"])
                if pub.get("country"):
                    countries.add(pub["country"])

            print(f"   Total publicaciones en BD: {len(all_publications)}")
            print(f"   Ciudades disponibles: {sorted(list(cities))[:5]}...")
            print(f"   Países disponibles: {sorted(list(countries))}")

            ba_publications = [
                p
                for p in all_publications
                if "buenos aires" in p.get("city", "").lower()
            ]
            print(f"   Publicaciones con 'Buenos Aires': {len(ba_publications)}")

        else:
            print(
                f"   ❌ Error obteniendo todas las publicaciones: {all_pubs_response.status_code}"
            )

    except Exception as e:
        print(f"   ❌ Error verificando BD: {str(e)}")

    print(f"\n🎯 CONCLUSIONES:")
    print(f"   • Destination original: \"{ai_itinerary['destination']}\"")
    print(f'   • Destination convertido: "{converted_destination}"')
    print(f'   • El frontend debería buscar con: "{converted_destination}"')
    print(f"   • Verificar si el endpoint de búsqueda es case-sensitive")
    print(f"   • Verificar formato exacto de destinos en la BD")


if __name__ == "__main__":
    diagnose_publication_search()
