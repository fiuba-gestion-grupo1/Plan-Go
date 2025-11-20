#!/usr/bin/env python3
"""
Parser de itinerarios - Convierte texto de itinerario IA a estructura de itinerario personalizado
"""

import re
from typing import Dict, List, Any
from datetime import datetime, timedelta


def parse_ai_itinerary_to_custom_structure(itinerary_text: str, start_date: str) -> Dict[str, Any]:
    """
    Convierte el texto de un itinerario de IA en la estructura necesaria para un itinerario personalizado
    
    Args:
        itinerary_text: Texto del itinerario generado por IA
        start_date: Fecha de inicio del viaje (YYYY-MM-DD)
    
    Returns:
        Dict con la estructura del itinerario personalizado
    """
    
    print(f"[PARSER] Parseando itinerario de IA desde fecha {start_date}")
    
    # Estructura base del itinerario personalizado
    custom_itinerary = {}
    
    # Dividir el texto en líneas para análisis
    lines = itinerary_text.split('\n')
    
    # Variables de estado
    current_day = None
    current_period = None
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    
    # Patrones de regex para extraer información
    day_pattern = r'DÍA\s*(\d+)\s*-\s*(\d{4}-\d{2}-\d{2})'
    period_pattern = r'🌅\s*(MAÑANA|MADRUGADA).*\((.*?)\)|🌞\s*(TARDE).*\((.*?)\)|🌙\s*(NOCHE).*\((.*?)\)'
    activity_pattern = r'•\s*(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s*-\s*(.*?)\s*\(ID:\s*(\d+)\)'
    
    print(f"[PARSER] Analizando {len(lines)} líneas...")
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('═'):
            continue
            
        # Detectar día
        day_match = re.search(day_pattern, line)
        if day_match:
            day_number = int(day_match.group(1))
            day_date = day_match.group(2)
            
            # Calcular el índice del día basado en la fecha de inicio
            day_dt = datetime.strptime(day_date, "%Y-%m-%d")
            day_index = (day_dt - start_dt).days + 1
            
            current_day = f"day_{day_index}"
            custom_itinerary[current_day] = {
                "morning": {},
                "afternoon": {},
                "evening": {}
            }
            
            print(f"[PARSER] Procesando {current_day} ({day_date})")
            continue
        
        # Detectar período del día
        period_match = re.search(period_pattern, line)
        if period_match and current_day:
            period_name = None
            for i in range(1, 7, 2):  # Grupos 1,3,5 contienen el nombre del período
                if period_match.group(i):
                    period_name = period_match.group(i).lower()
                    break
            
            if period_name == "mañana" or period_name == "madrugada":
                current_period = "morning"
            elif period_name == "tarde":
                current_period = "afternoon"
            elif period_name == "noche":
                current_period = "evening"
            
            print(f"[PARSER]   Período: {current_period}")
            continue
        
        # Detectar actividad
        activity_match = re.search(activity_pattern, line)
        if activity_match and current_day and current_period:
            start_time = activity_match.group(1)
            end_time = activity_match.group(2)
            activity_name = activity_match.group(3).strip()
            publication_id = int(activity_match.group(4))
            
            # Generar time slot key
            time_slot = f"{start_time}-{end_time}"
            
            # Agregar actividad al itinerario
            custom_itinerary[current_day][current_period][time_slot] = {
                "id": publication_id,
                "name": activity_name,
                "start_time": start_time,
                "end_time": end_time
            }
            
            print(f"[PARSER]     Actividad: {time_slot} - {activity_name} (ID: {publication_id})")
    
    # Agregar metadatos del parsing
    parsing_metadata = {
        "parsed_days": len([k for k in custom_itinerary.keys() if k.startswith("day_")]),
        "total_activities": sum([
            len(day_data.get("morning", {})) + 
            len(day_data.get("afternoon", {})) + 
            len(day_data.get("evening", {}))
            for day_data in custom_itinerary.values() 
            if isinstance(day_data, dict)
        ]),
        "parsed_from": "ai_itinerary",
        "start_date": start_date
    }
    
    custom_itinerary["_metadata"] = parsing_metadata
    
    print(f"[PARSER] Parsing completado:")
    print(f"[PARSER]   Días parseados: {parsing_metadata['parsed_days']}")
    print(f"[PARSER]   Actividades totales: {parsing_metadata['total_activities']}")
    
    return custom_itinerary


def extract_publication_ids_from_structure(custom_structure: Dict[str, Any]) -> List[int]:
    """
    Extrae todos los IDs de publicaciones de la estructura de itinerario personalizado
    
    Args:
        custom_structure: Estructura del itinerario personalizado
    
    Returns:
        Lista de IDs de publicaciones
    """
    
    publication_ids = set()
    
    for day_key, day_data in custom_structure.items():
        if not day_key.startswith("day_") or not isinstance(day_data, dict):
            continue
            
        for period_key, period_data in day_data.items():
            if not isinstance(period_data, dict):
                continue
                
            for time_slot, activity in period_data.items():
                if isinstance(activity, dict) and "id" in activity:
                    publication_ids.add(activity["id"])
    
    return list(publication_ids)


def generate_custom_itinerary_preview(custom_structure: Dict[str, Any]) -> str:
    """
    Genera un preview en texto del itinerario personalizado para mostrar al usuario
    
    Args:
        custom_structure: Estructura del itinerario personalizado
    
    Returns:
        String con preview del itinerario
    """
    
    preview_lines = ["📋 PREVIEW DEL ITINERARIO PERSONALIZADO:", "=" * 50]
    
    # Ordenar días
    day_keys = [k for k in custom_structure.keys() if k.startswith("day_")]
    day_keys.sort(key=lambda x: int(x.split("_")[1]))
    
    for day_key in day_keys:
        day_data = custom_structure[day_key]
        day_num = day_key.split("_")[1]
        
        preview_lines.append(f"\n🗓️  DÍA {day_num}")
        preview_lines.append("-" * 30)
        
        periods = [
            ("morning", "🌅 MAÑANA", day_data.get("morning", {})),
            ("afternoon", "🌞 TARDE", day_data.get("afternoon", {})),
            ("evening", "🌙 NOCHE", day_data.get("evening", {}))
        ]
        
        for period_key, period_name, period_activities in periods:
            if period_activities:
                preview_lines.append(f"\n{period_name}:")
                for time_slot, activity in period_activities.items():
                    activity_name = activity.get("name", "Actividad sin nombre")
                    preview_lines.append(f"  • {time_slot} - {activity_name}")
    
    # Agregar metadatos si existen
    if "_metadata" in custom_structure:
        metadata = custom_structure["_metadata"]
        preview_lines.extend([
            f"\n📊 INFORMACIÓN:",
            f"   • Días: {metadata.get('parsed_days', 0)}",
            f"   • Actividades: {metadata.get('total_activities', 0)}",
            f"   • Origen: {metadata.get('parsed_from', 'unknown')}"
        ])
    
    return "\n".join(preview_lines)


def validate_custom_structure(custom_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida que la estructura de itinerario personalizado sea correcta
    
    Args:
        custom_structure: Estructura a validar
    
    Returns:
        Dict con resultado de validación
    """
    
    errors = []
    warnings = []
    
    # Verificar estructura básica
    day_keys = [k for k in custom_structure.keys() if k.startswith("day_")]
    if not day_keys:
        errors.append("No se encontraron días en el itinerario")
    
    total_activities = 0
    for day_key in day_keys:
        day_data = custom_structure.get(day_key)
        if not isinstance(day_data, dict):
            errors.append(f"Estructura inválida para {day_key}")
            continue
            
        # Verificar períodos
        for period in ["morning", "afternoon", "evening"]:
            period_data = day_data.get(period, {})
            if isinstance(period_data, dict):
                total_activities += len(period_data)
                
                # Verificar actividades
                for time_slot, activity in period_data.items():
                    if not isinstance(activity, dict) or "id" not in activity:
                        warnings.append(f"Actividad inválida en {day_key}.{period}.{time_slot}")
    
    if total_activities == 0:
        warnings.append("No se encontraron actividades en el itinerario")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "total_days": len(day_keys),
        "total_activities": total_activities
    }