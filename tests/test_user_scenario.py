"""
Test específico para simular el escenario del usuario:
"apreto 17/11/25 y luego el itinerario se comienza a armar el 16/11/25"
"""

import requests

BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "premium@fi.uba.ar"
TEST_USER_PASSWORD = "password"

def login():
    login_data = {"identifier": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    return response.json().get("access_token") if response.status_code == 200 else None

def simulate_user_scenario():
    """Simula exactamente lo que reportó el usuario"""
    token = login()
    if not token:
        print("❌ Error de login")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("🎯 SIMULANDO ESCENARIO DEL USUARIO:")
    print("   Usuario selecciona: 17/11/2025")
    print("   ¿Aparecerá 16/11/2025 en el itinerario? (ANTES SÍ, AHORA NO)")
    print()
    
    user_selected_date = "2025-11-17"
    
    itinerary_data = {
        "destination": "París, Francia",
        "start_date": user_selected_date,
        "end_date": "2025-11-19",
        "budget": 1800,
        "cant_persons": 2,
        "trip_type": "Romántico",
        "comments": "Test del problema reportado por el usuario"
    }
    
    print(f"📅 FECHA SELECCIONADA POR EL USUARIO: {user_selected_date}")
    
    response = requests.post(f"{BASE_URL}/api/itineraries/request", json=itinerary_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        received_date = data.get('start_date')
        
        print(f"📅 FECHA EN LA RESPUESTA: {received_date}")
        
        if received_date != user_selected_date:
            print(f"❌ PROBLEMA PERSISTE:")
            print(f"   Seleccionó: {user_selected_date}")
            print(f"   Recibió: {received_date}")
            print(f"   → ¡Sigue cambiando la fecha!")
        else:
            print(f"✅ PROBLEMA SOLUCIONADO:")
            print(f"   Seleccionó: {user_selected_date}")
            print(f"   Recibió: {received_date}")
            print(f"   → ¡Las fechas coinciden perfectamente!")
        
        itinerary_text = data.get('generated_itinerary', '')
        print(f"\n📝 VERIFICANDO EL ITINERARIO GENERADO:")
        
        if "2025-11-17" in itinerary_text:
            print(f"✅ El itinerario menciona la fecha correcta (17 nov)")
        elif "2025-11-16" in itinerary_text:
            print(f"❌ El itinerario aún menciona la fecha incorrecta (16 nov)")
        else:
            print(f"ℹ️  El itinerario no menciona fechas específicas en formato ISO")
            
        if "17" in itinerary_text and ("DÍA 1" in itinerary_text or "día 1" in itinerary_text):
            print(f"✅ El día 17 aparece en el primer día del itinerario")
        elif "16" in itinerary_text and ("DÍA 1" in itinerary_text or "día 1" in itinerary_text):
            print(f"❌ El día 16 aparece en el primer día (¡problema!)")
            
        lines = itinerary_text.split('\n')[:10]
        print(f"\n📋 PRIMERA PARTE DEL ITINERARIO:")
        for line in lines:
            if line.strip():
                print(f"   {line}")
                
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("=== 🐛➡️✅ Test de corrección del problema reportado ===\n")
    simulate_user_scenario()
    print(f"\n=== Fin del test ===")
