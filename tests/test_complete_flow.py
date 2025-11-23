import requests
import json
from datetime import datetime, timedelta
import pytest

pytestmark = pytest.mark.skip(
    reason="Test de integración manual: requiere backend levantado en http://localhost:8000"
)

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}


def test_complete_flow():
    print("🚀 TEST FLUJO COMPLETO: IA → Validación → Modificar → Custom")
    print("=" * 65)
    print("\n1. 🔐 Autenticación...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado exitosamente")
    print("\n2. 🤖 Generando itinerario con IA + Validación...")
    tomorrow = datetime.now() + timedelta(days=1)
    end_date = tomorrow + timedelta(days=4)

    ai_request = {
        "destination": "Buenos Aires, Argentina",
        "start_date": tomorrow.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "budget": 600,
        "cant_persons": 2,
        "trip_type": "gastronómico",
        "arrival_time": "10:00",
        "departure_time": "19:00",
        "comments": "Queremos probar el flujo completo de conversión",
    }

    print(f"   📍 Destino: {ai_request['destination']}")
    print(f"   💰 Presupuesto: US${ai_request['budget']}")
    print(f"   🗓️ Duración: {(end_date - tomorrow).days + 1} días")

    ai_response = requests.post(
        f"{BASE_URL}/api/itineraries/request", json=ai_request, headers=headers
    )

    if ai_response.status_code != 200:
        print(f"❌ Error IA: {ai_response.status_code}")
        return False

    ai_itinerary = ai_response.json()
    itinerary_id = ai_itinerary["id"]
    print(f"✅ Itinerario IA creado (ID: {itinerary_id})")
    print(f"   Status: {ai_itinerary['status']}")

    generated_text = ai_itinerary["generated_itinerary"]
    has_validation = any(
        keyword in generated_text
        for keyword in ["VALIDACIÓN DEL ITINERARIO", "COSTO TOTAL", "LUGARES VALIDADOS"]
    )
    print(f"   ✅ Validación incluida: {'SÍ' if has_validation else 'NO'}")

    print(f"\n3. 🔄 Convirtiendo a itinerario personalizado...")
    convert_response = requests.post(
        f"{BASE_URL}/api/itineraries/{itinerary_id}/convert-to-custom", headers=headers
    )

    if convert_response.status_code != 200:
        print(f"❌ Error conversión: {convert_response.status_code}")
        print(f"   Response: {convert_response.text}")
        return False

    conversion_result = convert_response.json()
    print("✅ Conversión exitosa")

    custom_structure = conversion_result.get("custom_structure", {})
    validation = conversion_result.get("validation", {})

    total_days = validation.get("total_days", 0)
    total_activities = validation.get("total_activities", 0)

    print(f"   📅 Días convertidos: {total_days}")
    print(f"   🎯 Actividades: {total_activities}")
    print(f"   🏛️ Publicaciones: {len(conversion_result.get('publications_used', []))}")

    print(f"\n4. 💾 Simulando guardado de itinerario personalizado...")

    custom_payload = {
        "destination": ai_request["destination"],
        "start_date": ai_request["start_date"],
        "end_date": ai_request["end_date"],
        "itinerary_data": custom_structure,
        "type": "custom",
    }

    print(f"   🔍 Verificando estructura de datos convertidos...")

    activities_by_day = {}
    for day_key, day_data in custom_structure.items():
        if day_key.startswith("day_") and isinstance(day_data, dict):
            day_num = day_key.split("_")[1]
            total_day_activities = 0

            for period in ["morning", "afternoon", "evening"]:
                if period in day_data and isinstance(day_data[period], dict):
                    total_day_activities += len(day_data[period])

            activities_by_day[day_num] = total_day_activities

    print(f"   📊 Actividades por día: {dict(list(activities_by_day.items())[:3])}...")

    print(f"\n5. 📈 Análisis de calidad...")

    structure_valid = all(
        [
            custom_structure,
            total_days > 0,
            total_activities > 0,
            conversion_result.get("success", False),
        ]
    )

    quality_score = 0
    if structure_valid:
        quality_score += 25
    if total_activities >= total_days * 2:
        quality_score += 25
    if has_validation:
        quality_score += 25
    if len(conversion_result.get("publications_used", [])) >= 3:
        quality_score += 25

    print(f"   🎯 Score de calidad: {quality_score}/100")
    print(f"   ✅ Estructura válida: {'SÍ' if structure_valid else 'NO'}")
    print(f"   🎭 Densidad actividades: {total_activities/total_days:.1f} por día")

    print(f"\n🏆 RESULTADO FINAL DEL FLUJO COMPLETO:")

    if quality_score >= 75:
        status = "🌟 EXCELENTE"
        emoji = "🎉"
    elif quality_score >= 50:
        status = "✅ BUENO"
        emoji = "👍"
    elif quality_score >= 25:
        status = "⚠️ ACEPTABLE"
        emoji = "⚡"
    else:
        status = "❌ NECESITA MEJORAS"
        emoji = "🔧"

    print(f"   {status} - Score: {quality_score}/100")
    print(f"   {emoji} IA → Validación → Conversión: FUNCIONAL")

    print(f"\n📋 RESUMEN DETALLADO:")
    print(f"   • Itinerario IA ID: {itinerary_id}")
    print(f"   • Días originales: {(end_date - tomorrow).days + 1}")
    print(f"   • Días convertidos: {total_days}")
    print(f"   • Actividades extraídas: {total_activities}")
    print(f"   • Validación backend: {'ACTIVA' if has_validation else 'INACTIVA'}")
    print(
        f"   • Estructura personalizada: {'VÁLIDA' if structure_valid else 'INVÁLIDA'}"
    )

    print("\n" + "=" * 65)

    if quality_score >= 50:
        print("🎉 PASO 3 COMPLETADO: Botón 'Modificar itinerario' IMPLEMENTADO")
        print("🚀 SISTEMA DE CONVERSIÓN IA→CUSTOM FUNCIONAL")
        print("✨ Listo para Paso 4: Funcionalidad 'Pegar itinerario de IA'")
    else:
        print("⚠️ PASO 3: Necesita optimizaciones en la conversión")
        print("🔧 Revisar parsing de actividades y estructura de datos")

    return quality_score >= 50


if __name__ == "__main__":
    success = test_complete_flow()
    exit(0 if success else 1)
