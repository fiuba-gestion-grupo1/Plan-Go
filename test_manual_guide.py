#!/usr/bin/env python3
"""
Guía Interactiva - Testing Manual PASO 4: Pegar Itinerario de IA
Prueba paso a paso del flujo completo en el navegador
"""
import time

class TestingGuide:
    def __init__(self):
        self.step = 0
        self.total_steps = 8
        self.results = {}
        
    def next_step(self, title, description, expected_result, instructions=None):
        self.step += 1
        print(f"\n{'='*60}")
        print(f"📋 PASO {self.step}/{self.total_steps}: {title}")
        print(f"{'='*60}")
        print(f"📝 Descripción: {description}")
        print(f"✅ Resultado esperado: {expected_result}")
        
        if instructions:
            print(f"\n📌 Instrucciones:")
            for i, instruction in enumerate(instructions, 1):
                print(f"   {i}. {instruction}")
        
        print(f"\n⏳ Realiza este paso en el navegador...")
        result = input("¿El paso fue exitoso? (s/n/detalle): ").strip().lower()
        
        if result == 's':
            self.results[self.step] = "✅ EXITOSO"
            print("   ✅ Paso completado exitosamente")
        elif result == 'n':
            error_detail = input("   Describe el error: ")
            self.results[self.step] = f"❌ ERROR: {error_detail}"
            print("   ❌ Error registrado")
        else:
            self.results[self.step] = f"📝 DETALLE: {result}"
            print("   📝 Detalle registrado")
    
    def show_summary(self):
        print(f"\n{'='*60}")
        print("📊 RESUMEN FINAL DE LA PRUEBA")
        print(f"{'='*60}")
        
        success_count = 0
        for step, result in self.results.items():
            print(f"Paso {step}: {result}")
            if result.startswith("✅"):
                success_count += 1
        
        print(f"\n📈 Estadísticas:")
        print(f"   Pasos exitosos: {success_count}/{self.total_steps}")
        print(f"   Porcentaje de éxito: {(success_count/self.total_steps)*100:.1f}%")
        
        if success_count == self.total_steps:
            print("\n🎉 ¡PASO 4 COMPLETADO EXITOSAMENTE!")
            print("   Todas las funcionalidades están operativas")
        elif success_count >= self.total_steps * 0.8:
            print("\n🟡 PASO 4 MAYORMENTE FUNCIONAL")
            print("   Algunas mejoras menores pueden ser necesarias")
        else:
            print("\n🔴 PASO 4 NECESITA REVISIÓN")
            print("   Se encontraron problemas significativos")

def run_manual_testing():
    print("🚀 GUÍA DE TESTING MANUAL - PASO 4")
    print("🎯 Objetivo: Validar funcionalidad 'Pegar itinerario de IA'")
    print("\n📱 URLs de prueba:")
    print("   Frontend: http://localhost:5173/")
    print("   Credenciales: normal@fi.uba.ar / password")
    
    guide = TestingGuide()
    
    # Paso 1: Acceso a la aplicación
    guide.next_step(
        "Acceso a la aplicación",
        "Verificar que la aplicación web esté accesible y cargue correctamente",
        "La página principal se carga sin errores",
        [
            "Abre http://localhost:5173/ en tu navegador",
            "Verifica que la página principal cargue",
            "Comprueba que no hay errores en la consola del navegador"
        ]
    )
    
    # Paso 2: Login
    guide.next_step(
        "Autenticación de usuario",
        "Realizar login con las credenciales de prueba",
        "Login exitoso y redirección al dashboard",
        [
            "Haz clic en 'Iniciar Sesión' o botón de login",
            "Ingresa: normal@fi.uba.ar",
            "Ingresa contraseña: password",
            "Haz clic en 'Iniciar Sesión'"
        ]
    )
    
    # Paso 3: Navegación al constructor
    guide.next_step(
        "Navegación al Constructor Personalizado",
        "Encontrar y acceder al constructor de itinerarios personalizados",
        "Se abre la página del constructor personalizado",
        [
            "Busca la opción 'Constructor Personalizado' o similar",
            "Haz clic para acceder",
            "Verifica que se muestre la pantalla de configuración inicial"
        ]
    )
    
    # Paso 4: Hacer clic en botón pegar IA
    guide.next_step(
        "Activar funcionalidad 'Pegar IA'",
        "Usar el botón 'Pegar itinerario de IA existente'",
        "Se abre el modal con lista de itinerarios de IA",
        [
            "Busca el botón '📋 Pegar itinerario de IA existente'",
            "Haz clic en el botón",
            "Verifica que se abra un modal/ventana emergente",
            "Confirma que aparezca 'Cargando tus itinerarios de IA...'"
        ]
    )
    
    # Paso 5: Verificar lista de itinerarios
    guide.next_step(
        "Lista de itinerarios de IA",
        "Verificar que se muestre la lista de itinerarios disponibles",
        "Se muestra al menos 1 itinerario (francia, 3 días, $1500)",
        [
            "Verifica que se cargue la lista de itinerarios",
            "Confirma que aparezca el itinerario de 'francia'",
            "Revisa que muestre información: 3 días, $1500, 3 personas",
            "Verifica que tenga badges de estado (Completo, Validado, etc.)"
        ]
    )
    
    # Paso 6: Seleccionar itinerario
    guide.next_step(
        "Selección y conversión de itinerario",
        "Seleccionar un itinerario de IA para pegar",
        "El itinerario se convierte y carga en el constructor",
        [
            "Haz clic en el itinerario de 'francia'",
            "Verifica que aparezca mensaje de conversión exitosa",
            "Confirma que el modal se cierre automáticamente",
            "Verifica que se carguen los datos en el constructor"
        ]
    )
    
    # Paso 7: Verificar carga en constructor
    guide.next_step(
        "Constructor con datos cargados",
        "Verificar que el itinerario se haya cargado correctamente en el constructor",
        "Se muestra la vista de construcción con 3 días y badge 'Convertido desde IA'",
        [
            "Verifica que aparezca '✏️ Itinerario Personalizado'",
            "Confirma que muestre badge '🔄 Convertido desde IA'",
            "Revisa que aparezcan 3 días (DÍA 1, DÍA 2, DÍA 3)",
            "Confirma que se muestren franjas horarias (MAÑANA, TARDE, NOCHE)"
        ]
    )
    
    # Paso 8: Funcionalidad de edición
    guide.next_step(
        "Funcionalidad de edición",
        "Probar que se pueden agregar/editar actividades manualmente",
        "Se pueden agregar nuevas actividades y guardar el itinerario",
        [
            "Haz clic en '+ Agregar actividad' en cualquier horario",
            "Verifica que se abra el modal de selección de publicaciones",
            "Prueba agregar una actividad",
            "Haz clic en '💾 Guardar Itinerario'",
            "Confirma que aparezca mensaje de guardado exitoso"
        ]
    )
    
    # Mostrar resumen final
    guide.show_summary()
    
    # Generar reporte
    print(f"\n📄 REPORTE GENERADO:")
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"test_paso4_manual_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("REPORTE DE TESTING MANUAL - PASO 4\n")
        f.write("="*50 + "\n")
        f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Funcionalidad: Pegar itinerario de IA\n\n")
        
        for step, result in guide.results.items():
            f.write(f"Paso {step}: {result}\n")
        
        success_count = sum(1 for r in guide.results.values() if r.startswith("✅"))
        f.write(f"\nÉxito: {success_count}/{guide.total_steps} pasos\n")
    
    print(f"   📁 Archivo: {report_file}")
    
if __name__ == "__main__":
    run_manual_testing()