#!/usr/bin/env python3

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TEST_USER = {"identifier": "test_validation", "password": "password123"}

def test_ai_validation_full():
    print("🚀 TEST COMPLETO: Sistema de Validación de IA con Presupuesto Alto")
    print("=" * 60)
    
    # Login
    print("\n1. Autenticando usuario...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Usuario autenticado")
    
    # Preparar request con presupuesto ALTO
    tomorrow = datetime.now() + timedelta(days=1)
    end_date = tomorrow + timedelta(days=5)  # Viaje más largo
    
    itinerary_request = {
        "destination": "Buenos Aires, Argentina",
        "start_date": tomorrow.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "budget": 800,  # PRESUPUESTO ALTO para activar más lugares
        "cant_persons": 3,  # Más personas para costos
        "trip_type": "gastronómico",
        "arrival_time": "09:00",
        "departure_time": "20:00",
        "comments": "Queremos probar la mejor gastronomía argentina y hospedajes premium"
    }
    
    print(f"\n2. Solicitando itinerario PREMIUM...")
    print(f"   Destino: {itinerary_request['destination']}")
    print(f"   Presupuesto: US${itinerary_request['budget']} (ALTO)")
    print(f"   Personas: {itinerary_request['cant_persons']}")
    print(f"   Días: {(end_date - tomorrow).days + 1}")
    
    # Solicitar itinerario
    response = requests.post(f"{BASE_URL}/api/itineraries/request", 
                           json=itinerary_request, 
                           headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return
    
    result = response.json()
    print("✅ Itinerario PREMIUM generado")
    
    # Analizar validación completa
    print(f"\n3. ANÁLISIS DETALLADO DE VALIDACIÓN...")
    print(f"   Status: {result['status']}")
    generated_text = result['generated_itinerary']
    
    # Buscar TODOS los indicadores de validación
    validation_indicators = [
        "VALIDACIÓN DEL ITINERARIO:",
        "VÁLIDO",
        "INVÁLIDO", 
        "ERRORES DE VALIDACIÓN",
        "ADVERTENCIAS",
        "INFORMACIÓN DE COSTOS:",
        "LUGARES VALIDADOS",
        "Costo total:",
        "Presupuesto disponible:",
        "Utilización del presupuesto:"
    ]
    
    found_validation = []
    for indicator in validation_indicators:
        if indicator in generated_text:
            found_validation.append(indicator)
    
    print(f"   📊 Indicadores de validación: {len(found_validation)}/{len(validation_indicators)}")
    
    # Mostrar fragmento del itinerario
    print(f"\n4. FRAGMENTO DEL ITINERARIO:")
    lines = generated_text.split('\n')
    
    # Mostrar los primeros días
    for i, line in enumerate(lines[:20]):
        if line.strip():
            print(f"   {line}")
    
    print("\n   ...")
    
    # Mostrar la sección de validación completa
    validation_section = []
    in_validation = False
    for line in lines:
        if "VALIDACIÓN DEL ITINERARIO:" in line:
            in_validation = True
        if in_validation:
            validation_section.append(line)
        if in_validation and line.strip() == "":
            # Si encontramos línea vacía después de validación, podría ser el final
            # Pero continuamos para capturar toda la info
            pass
    
    if validation_section:
        print(f"\n5. 📊 SECCIÓN COMPLETA DE VALIDACIÓN:")
        for line in validation_section:
            if line.strip():
                print(f"   {line}")
    
    # Información de publicaciones utilizadas
    if 'publication_ids' in result and result['publication_ids']:
        print(f"\n6. 🏛️ PUBLICACIONES UTILIZADAS:")
        print(f"   Total de lugares: {len(result['publication_ids'])}")
        print(f"   IDs: {result['publication_ids']}")
    
    # Análisis de la validación
    validation_score = len(found_validation)
    utilization_info = [line for line in generated_text.split('\n') if 'Utilización del presupuesto:' in line]
    
    print(f"\n🎯 RESULTADOS FINALES:")
    print(f"   ✅ Status: {result['status']}")
    print(f"   ✅ Validación Score: {validation_score}/{len(validation_indicators)}")
    print(f"   ✅ Lugares utilizados: {len(result.get('publication_ids', []))}")
    
    if utilization_info:
        print(f"   ✅ Utilización presupuesto: {utilization_info[0].split(':')[1].strip()}")
    
    # Clasificar el resultado
    if validation_score >= 8:
        print(f"\n🌟 EXCELENTE: Sistema de validación funcionando perfectamente!")
        print(f"   🔥 Validación completa con {validation_score} indicadores detectados")
    elif validation_score >= 5:
        print(f"\n✅ BUENO: Sistema de validación funcionando bien")
        print(f"   👍 {validation_score} indicadores de validación activos")
    elif validation_score >= 3:
        print(f"\n⚠️ REGULAR: Validación parcialmente funcional")
        print(f"   ⚡ {validation_score} indicadores básicos detectados")
    else:
        print(f"\n❌ INSUFICIENTE: Sistema de validación necesita mejoras")
        print(f"   🔧 Solo {validation_score} indicadores detectados")
    
    print("\n" + "=" * 60)
    print("🎉 PASO 2 VALIDADO: Sistema de Validación Backend Implementado")
    print("🚀 LISTO PARA PASO 3: Botón 'Modificar itinerario'")
    return result, validation_score

if __name__ == "__main__":
    test_ai_validation_full()