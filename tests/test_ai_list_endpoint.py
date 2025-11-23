"""
Test script para PASO 4: Verificar endpoint /api/itineraries/ai-list
"""
import requests
import json

BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
AI_LIST_URL = f"{BASE_URL}/api/itineraries/ai-list"

TEST_EMAIL = "normal@fi.uba.ar"
TEST_PASSWORD = "password"

def test_ai_list_endpoint():
    """Probar el endpoint /api/itineraries/ai-list para el paso 4"""
    
    print("🔍 PASO 4 - Test del endpoint /api/itineraries/ai-list")
    print("=" * 60)
    print("📋 1. Intentando login...")
    login_payload = {
        "identifier": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = requests.post(
            LOGIN_URL, 
            json=login_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Error en login: {login_response.status_code}")
            print(f"   Respuesta: {login_response.text}")
            return
            
        token_data = login_response.json()
        token = token_data.get("access_token")
        
        if not token:
            print("❌ No se recibió token de acceso")
            return
            
        print(f"✅ Login exitoso. Token obtenido.")
        
    except Exception as e:
        print(f"❌ Error en login: {str(e)}")
        return
    
    print("📋 2. Llamando al endpoint /api/itineraries/ai-list...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(AI_LIST_URL, headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Endpoint funcionando correctamente!")
            
            data = response.json()
            print(f"📋 Respuesta:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            total = data.get('total', 0)
            itineraries = data.get('itineraries', [])
            
            print(f"\n📈 RESUMEN:")
            print(f"   - Total de itinerarios de IA: {total}")
            print(f"   - Itinerarios en respuesta: {len(itineraries)}")
            
            if itineraries:
                print(f"   - Primer itinerario: {itineraries[0].get('destination', 'N/A')}")
                print(f"   - Estado: {itineraries[0].get('status', 'N/A')}")
                print(f"   - Preview: {itineraries[0].get('preview', 'N/A')[:50]}...")
            
        elif response.status_code == 422:
            print("❌ Error 422 - Problema de validación de parámetros")
            print(f"   Respuesta: {response.text}")
            
        elif response.status_code == 401:
            print("❌ Error 401 - No autorizado")
            print(f"   Respuesta: {response.text}")
            
        else:
            print(f"❌ Error {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error en llamada al endpoint: {str(e)}")

if __name__ == "__main__":
    test_ai_list_endpoint()
