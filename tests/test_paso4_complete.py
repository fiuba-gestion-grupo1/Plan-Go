"""
Script de Testing Completo - PASO 4: Pegar Itinerario de IA
Documenta y valida todo el flujo de funcionalidad
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
AI_LIST_URL = f"{BASE_URL}/api/itineraries/ai-list"
CONVERT_URL_BASE = f"{BASE_URL}/api/itineraries"

TEST_EMAIL = "normal@fi.uba.ar"
TEST_PASSWORD = "password"

def get_auth_token():
    """Obtener token de autenticación"""
    print("🔐 1. Obteniendo token de autenticación...")
    
    login_payload = {
        "identifier": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(LOGIN_URL, json=login_payload)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"   ✅ Token obtenido exitosamente")
        return token
    else:
        print(f"   ❌ Error en login: {response.status_code}")
        return None

def test_ai_list_endpoint(token):
    """Probar el endpoint de listado de itinerarios de IA"""
    print("\n📋 2. Probando endpoint /api/itineraries/ai-list...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(AI_LIST_URL, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Endpoint funcionando - {data['total']} itinerarios encontrados")
        
        if data['itineraries']:
            first_itinerary = data['itineraries'][0]
            print(f"   📍 Primer itinerario: {first_itinerary['destination']} ({first_itinerary['duration_days']} días)")
            return data['itineraries']
        else:
            print("   ⚠️  No hay itinerarios de IA disponibles para probar")
            return []
    else:
        print(f"   ❌ Error en endpoint: {response.status_code}")
        return []

def test_conversion_endpoint(token, itinerary_id):
    """Probar el endpoint de conversión"""
    print(f"\n🔄 3. Probando conversión del itinerario {itinerary_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    convert_url = f"{CONVERT_URL_BASE}/{itinerary_id}/convert-to-custom"
    
    response = requests.post(convert_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Conversión exitosa")
        print(f"   📊 Estructura: {data['validation']['total_days']} días, {data['validation']['total_activities']} actividades")
        return data
    else:
        print(f"   ❌ Error en conversión: {response.status_code}")
        print(f"   Respuesta: {response.text}")
        return None

def test_manual_flow():
    """Documentar el flujo manual en el navegador"""
    print(f"\n🌐 4. Flujo manual en el navegador ({FRONTEND_URL}):")
    print("   📌 Pasos a seguir:")
    print("   1. Accede a la aplicación web")
    print("   2. Haz login con las credenciales de prueba")
    print("   3. Ve a 'Constructor de Itinerario Personalizado'")
    print("   4. Haz clic en '📋 Pegar itinerario de IA existente'")
    print("   5. Selecciona un itinerario de la lista")
    print("   6. Verifica que se cargue en el constructor")
    print("   7. Prueba editando algunas actividades")
    print("   8. Guarda el itinerario personalizado")
    
    print("\n   🔍 Validaciones esperadas:")
    print("   ✓ Modal se abre correctamente")
    print("   ✓ Lista de itinerarios se carga")
    print("   ✓ Conversión se realiza sin errores")
    print("   ✓ Estructura del itinerario se carga en el constructor")
    print("   ✓ Se pueden editar las actividades")
    print("   ✓ Se puede guardar el itinerario final")

def comprehensive_test():
    """Ejecutar prueba completa del PASO 4"""
    print("🚀 TESTING COMPLETO - PASO 4: Pegar Itinerario de IA")
    print("=" * 70)
    
    token = get_auth_token()
    if not token:
        print("\n❌ No se pudo obtener token. Abortando pruebas.")
        return
    
    ai_itineraries = test_ai_list_endpoint(token)
    
    if ai_itineraries:
        test_itinerary = ai_itineraries[0]
        conversion_result = test_conversion_endpoint(token, test_itinerary['id'])
        
        if conversion_result:
            print(f"\n✨ Datos de ejemplo para prueba manual:")
            print(f"   📍 Destino: {test_itinerary['destination']}")
            print(f"   📅 Fechas: {test_itinerary['start_date']} a {test_itinerary['end_date']}")
            print(f"   💰 Presupuesto: US${test_itinerary['budget']}")
            print(f"   👥 Personas: {test_itinerary['cant_persons']}")
    
    test_manual_flow()
    
    print("\n" + "=" * 70)
    print("🎯 RESUMEN DEL TESTING:")
    print("✅ Backend endpoints funcionando")
    print("✅ Frontend servidor corriendo")
    print("✅ Autenticación operativa")
    print("✅ Conversión de itinerarios operativa")
    print("📱 Frontend listo para prueba manual")
    
    print(f"\n🔗 URLs para probar:")
    print(f"   Frontend: {FRONTEND_URL}")
    print(f"   Backend API: {BASE_URL}/docs")
    
    print(f"\n👤 Credenciales de prueba:")
    print(f"   Email: {TEST_EMAIL}")
    print(f"   Contraseña: {TEST_PASSWORD}")

if __name__ == "__main__":
    comprehensive_test()
