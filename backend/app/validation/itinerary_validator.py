#!/usr/bin/env python3
"""
Módulo de validación de itinerarios - valida tanto itinerarios de IA como personalizados
"""

from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app import models


class ItineraryValidationError:
    """Representa un error de validación en un itinerario"""
    def __init__(self, error_type: str, message: str, publication_id: int = None, 
                 day: str = None, time_slot: str = None, severity: str = "error"):
        self.error_type = error_type
        self.message = message
        self.publication_id = publication_id
        self.day = day
        self.time_slot = time_slot
        self.severity = severity  # "error", "warning", "info"
    
    def to_dict(self):
        return {
            "error_type": self.error_type,
            "message": self.message,
            "publication_id": self.publication_id,
            "day": self.day,
            "time_slot": self.time_slot,
            "severity": self.severity
        }


class ItineraryValidator:
    """Validador de itinerarios que verifica disponibilidad, costos y coherencia"""
    
    def __init__(self, db: Session):
        self.db = db
        self.errors = []
        self.warnings = []
        self.total_cost = 0.0
        
    def validate_itinerary(self, itinerary_data: dict, budget: float, 
                          cant_persons: int, start_date: str, end_date: str) -> dict:
        """
        Valida un itinerario completo y retorna resultados de validación
        
        Args:
            itinerary_data: Puede ser AI response dict o custom itinerary data
            budget: Presupuesto total en USD
            cant_persons: Número de personas
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
        
        Returns:
            dict con resultado de validación
        """
        self.errors = []
        self.warnings = []
        self.total_cost = 0.0
        
        # Determinar el tipo de datos de entrada
        if "used_publications" in itinerary_data:
            # Es respuesta de IA
            return self._validate_ai_itinerary(itinerary_data, budget, cant_persons, start_date, end_date)
        else:
            # Es itinerario personalizado
            return self._validate_custom_itinerary(itinerary_data, budget, cant_persons, start_date, end_date)
    
    def _validate_ai_itinerary(self, ai_data: dict, budget: float, 
                              cant_persons: int, start_date: str, end_date: str) -> dict:
        """Valida un itinerario generado por IA"""
        
        print(f"[VALIDATION] Validando itinerario de IA...")
        print(f"[VALIDATION] Presupuesto: US${budget} | Personas: {cant_persons}")
        
        # Validar publicaciones utilizadas
        used_publications = ai_data.get("used_publications", [])
        ai_total_cost = ai_data.get("total_cost", 0)
        
        real_total_cost = 0.0
        validated_publications = []
        
        for pub_usage in used_publications:
            pub_id = pub_usage.get("id")
            times_used = pub_usage.get("times_used", 1)
            days_used = pub_usage.get("days_used", [])
            hours_used = pub_usage.get("hours_used", [])
            ai_cost = pub_usage.get("total_cost", 0)
            
            # Buscar publicación en BD
            publication = self.db.query(models.Publication).filter(
                models.Publication.id == pub_id
            ).first()
            
            if not publication:
                self._add_error("PUBLICATION_NOT_FOUND", 
                              f"Publicación con ID {pub_id} no encontrada en la base de datos",
                              publication_id=pub_id)
                continue
            
            # Validar disponibilidad de días
            validation_result = self._validate_publication_availability(
                publication, days_used, hours_used, pub_id
            )
            
            # Calcular costo real
            real_cost = self._calculate_real_cost(publication, times_used, cant_persons, len(days_used))
            real_total_cost += real_cost
            
            # Comparar con costo estimado por IA
            if abs(real_cost - ai_cost) > 0.01:  # Tolerancia de 1 centavo
                self._add_warning("COST_MISMATCH",
                                f"Costo real de {publication.place_name}: US${real_cost:.2f} vs IA estimó: US${ai_cost:.2f}",
                                publication_id=pub_id)
            
            validated_publications.append({
                "id": pub_id,
                "name": publication.place_name,
                "times_used": times_used,
                "days_used": days_used,
                "hours_used": hours_used,
                "ai_estimated_cost": ai_cost,
                "real_cost": real_cost,
                "availability_valid": validation_result["valid"]
            })
        
        # Validar presupuesto total
        if real_total_cost > budget:
            self._add_error("BUDGET_EXCEEDED",
                          f"Costo real total US${real_total_cost:.2f} excede presupuesto US${budget:.2f} por US${real_total_cost - budget:.2f}")
        elif real_total_cost < budget * 0.3:  # Si usa menos del 30% del presupuesto
            self._add_warning("UNDERUTILIZED_BUDGET",
                            f"Solo se usa US${real_total_cost:.2f} ({(real_total_cost/budget)*100:.1f}%) del presupuesto de US${budget:.2f}")
        
        # Validar fechas
        self._validate_dates(start_date, end_date, used_publications)
        
        self.total_cost = real_total_cost
        
        return {
            "valid": len(self.errors) == 0,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "ai_estimated_cost": ai_total_cost,
            "real_total_cost": real_total_cost,
            "budget": budget,
            "budget_utilization_percent": (real_total_cost / budget) * 100 if budget > 0 else 0,
            "validated_publications": validated_publications,
            "validation_summary": self._generate_validation_summary()
        }
    
    def _validate_custom_itinerary(self, custom_data: dict, budget: float,
                                  cant_persons: int, start_date: str, end_date: str) -> dict:
        """Valida un itinerario personalizado"""
        
        print(f"[VALIDATION] Validando itinerario personalizado...")
        
        real_total_cost = 0.0
        validated_publications = []
        publication_usage = {}  # {id: {times_used, days_used, hours_used}}
        
        # Extraer información de uso de publicaciones del itinerario personalizado
        for day_key, day_data in custom_data.items():
            for period_key, period_data in day_data.items():
                for time_slot, activity in period_data.items():
                    if activity and isinstance(activity, dict) and 'id' in activity:
                        pub_id = activity['id']
                        
                        if pub_id not in publication_usage:
                            publication_usage[pub_id] = {
                                'times_used': 0,
                                'days_used': set(),
                                'hours_used': []
                            }
                        
                        publication_usage[pub_id]['times_used'] += 1
                        publication_usage[pub_id]['days_used'].add(day_key)
                        publication_usage[pub_id]['hours_used'].append(time_slot)
        
        # Validar cada publicación usada
        for pub_id, usage_data in publication_usage.items():
            publication = self.db.query(models.Publication).filter(
                models.Publication.id == pub_id
            ).first()
            
            if not publication:
                self._add_error("PUBLICATION_NOT_FOUND",
                              f"Publicación con ID {pub_id} no encontrada",
                              publication_id=pub_id)
                continue
            
            days_used = list(usage_data['days_used'])
            hours_used = usage_data['hours_used']
            times_used = usage_data['times_used']
            
            # Validar disponibilidad
            self._validate_publication_availability(publication, days_used, hours_used, pub_id)
            
            # Calcular costo
            real_cost = self._calculate_real_cost(publication, times_used, cant_persons, len(days_used))
            real_total_cost += real_cost
            
            validated_publications.append({
                "id": pub_id,
                "name": publication.place_name,
                "times_used": times_used,
                "days_used": days_used,
                "hours_used": hours_used,
                "real_cost": real_cost
            })
        
        # Validar presupuesto
        if real_total_cost > budget:
            self._add_error("BUDGET_EXCEEDED",
                          f"Costo total US${real_total_cost:.2f} excede presupuesto US${budget:.2f}")
        
        self.total_cost = real_total_cost
        
        return {
            "valid": len(self.errors) == 0,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "real_total_cost": real_total_cost,
            "budget": budget,
            "budget_utilization_percent": (real_total_cost / budget) * 100 if budget > 0 else 0,
            "validated_publications": validated_publications,
            "validation_summary": self._generate_validation_summary()
        }
    
    def _validate_publication_availability(self, publication: models.Publication, 
                                          days_used: List[str], hours_used: List[str], 
                                          pub_id: int) -> dict:
        """Valida que una publicación esté disponible en los días y horarios especificados"""
        
        availability_errors = []
        
        # Validar días disponibles
        if hasattr(publication, 'available_days') and publication.available_days:
            available_days = publication.available_days
            for day in days_used:
                # Convertir fecha a día de la semana
                try:
                    day_obj = datetime.fromisoformat(day).date()
                    day_name = self._get_day_name_spanish(day_obj)
                    
                    if day_name not in available_days:
                        availability_errors.append(f"No disponible {day_name} ({day})")
                        self._add_error("DAY_NOT_AVAILABLE",
                                      f"{publication.place_name} no está disponible los {day_name} (usado en {day})",
                                      publication_id=pub_id, day=day)
                except ValueError:
                    self._add_error("INVALID_DATE_FORMAT",
                                  f"Formato de fecha inválido: {day}",
                                  publication_id=pub_id, day=day)
        
        # Validar horarios disponibles  
        if hasattr(publication, 'available_hours') and publication.available_hours:
            available_hours = publication.available_hours
            for hour in hours_used:
                if not self._time_in_available_ranges(hour, available_hours):
                    availability_errors.append(f"Horario {hour} no disponible")
                    self._add_error("TIME_NOT_AVAILABLE",
                                  f"{publication.place_name} no está disponible a las {hour}",
                                  publication_id=pub_id, time_slot=hour)
        
        return {
            "valid": len(availability_errors) == 0,
            "errors": availability_errors
        }
    
    def _calculate_real_cost(self, publication: models.Publication, times_used: int, 
                            cant_persons: int, days_used: int) -> float:
        """Calcula el costo real de usar una publicación"""
        
        base_cost = 0.0
        
        if hasattr(publication, 'cost_per_day') and publication.cost_per_day:
            # Costo por día por persona
            base_cost = publication.cost_per_day * cant_persons * days_used
        
        # Si no hay costo específico, se asume gratuito (museos públicos, parques, etc.)
        return base_cost
    
    def _time_in_available_ranges(self, time_slot: str, available_ranges: List[str]) -> bool:
        """Verifica si un horario está dentro de los rangos disponibles"""
        
        try:
            slot_time = datetime.strptime(time_slot, "%H:%M").time()
            
            for time_range in available_ranges:
                if "-" in time_range:
                    start_str, end_str = time_range.split("-")
                    start_time = datetime.strptime(start_str.strip(), "%H:%M").time()
                    end_time = datetime.strptime(end_str.strip(), "%H:%M").time()
                    
                    if start_time <= slot_time <= end_time:
                        return True
            
            return False
        except ValueError:
            return True  # Si hay error en el formato, asumir disponible
    
    def _get_day_name_spanish(self, date_obj: date) -> str:
        """Convierte un objeto date al nombre del día en español"""
        days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        return days[date_obj.weekday()]
    
    def _validate_dates(self, start_date: str, end_date: str, used_publications: List[dict]):
        """Valida coherencia de fechas"""
        try:
            start = datetime.fromisoformat(start_date).date()
            end = datetime.fromisoformat(end_date).date()
            
            if end < start:
                self._add_error("INVALID_DATE_RANGE",
                              f"Fecha fin ({end}) anterior a fecha inicio ({start})")
            
            # Validar que las fechas de uso estén dentro del rango
            for pub in used_publications:
                for day_str in pub.get("days_used", []):
                    try:
                        day = datetime.fromisoformat(day_str).date()
                        if not (start <= day <= end):
                            self._add_error("DATE_OUT_OF_RANGE",
                                          f"Fecha {day} fuera del rango del viaje ({start} - {end})",
                                          publication_id=pub.get("id"))
                    except ValueError:
                        pass  # Ya se maneja en otra validación
                        
        except ValueError:
            self._add_error("INVALID_DATE_FORMAT",
                          "Formato de fechas de inicio o fin inválido")
    
    def _add_error(self, error_type: str, message: str, **kwargs):
        """Agrega un error de validación"""
        error = ItineraryValidationError(error_type, message, **kwargs)
        self.errors.append(error)
        print(f"[VALIDATION ERROR] {error_type}: {message}")
    
    def _add_warning(self, warning_type: str, message: str, **kwargs):
        """Agrega una advertencia de validación"""
        warning = ItineraryValidationError(warning_type, message, severity="warning", **kwargs)
        self.warnings.append(warning)
        print(f"[VALIDATION WARNING] {warning_type}: {message}")
    
    def _generate_validation_summary(self) -> str:
        """Genera un resumen de la validación"""
        if len(self.errors) == 0:
            return f"✅ Itinerario válido. Costo total: US${self.total_cost:.2f}. {len(self.warnings)} advertencias."
        else:
            return f"❌ Itinerario inválido. {len(self.errors)} errores, {len(self.warnings)} advertencias."