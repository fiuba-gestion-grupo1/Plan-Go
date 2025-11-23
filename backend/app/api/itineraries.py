from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user
from ..models import Itinerary, SavedItinerary
from datetime import datetime, timedelta
import google.generativeai as genai
import re
from ..utils.mailer import send_email_html
from pydantic import BaseModel, EmailStr
import html
from datetime import datetime, date
from ..validation.itinerary_validator import ItineraryValidator
from ..utils.itinerary_parser import (
    parse_ai_itinerary_to_custom_structure,
    generate_custom_itinerary_preview,
    validate_custom_structure,
)
from typing import Dict, List

router = APIRouter(prefix="/api/itineraries", tags=["itineraries"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def build_itinerary_prompt(
    destination: str,
    start_date: str,
    end_date: str,
    budget: int,
    cant_persons: int,
    trip_type: str,
    publications: list,
    user_preferences: str | None,
    arrival_time: str | None,
    departure_time: str | None,
    comments: str | None,
) -> str:
    """Construye el prompt para la IA basado en los parámetros del usuario y las publicaciones disponibles"""

    publications_json = []
    for pub in publications:
        pub_data = {
            "id": pub.id,
            "place_name": pub.place_name,
            "address": pub.address or "",
            "city": pub.city or "",
            "province": pub.province or "",
            "country": pub.country or "",
            "description": pub.description or "",
            "rating_avg": float(pub.rating_avg or 0),
            "rating_count": int(pub.rating_count or 0),
            "categories": [cat.slug for cat in (pub.categories or [])],
            "duration_min": pub.duration_min or 120,
            "available_days": (
                pub.available_days
                if hasattr(pub, "available_days") and pub.available_days
                else [
                    "lunes",
                    "martes",
                    "miércoles",
                    "jueves",
                    "viernes",
                    "sábado",
                    "domingo",
                ]
            ),
            "available_hours": (
                pub.available_hours
                if hasattr(pub, "available_hours") and pub.available_hours
                else ["09:00-18:00"]
            ),
            "cost_per_day": pub.cost_per_day or 0,
        }
        publications_json.append(pub_data)

    import json

    publications_json_str = json.dumps(publications_json, ensure_ascii=False, indent=2)

    places_info = []
    for pub in publications:
        place_details = f"- ID:{pub.id} | {pub.place_name}"
        if pub.address:
            place_details += f" ({pub.address})"
        if pub.rating_avg and pub.rating_avg > 0:
            place_details += f" - Rating: {pub.rating_avg:.1f}⭐"
        if pub.categories:
            cats = ", ".join([cat.slug for cat in pub.categories])
            place_details += f" - Categorías: {cats}"

        if hasattr(pub, "duration_min") and pub.duration_min:
            if pub.duration_min < 60:
                place_details += f" - Duración: {pub.duration_min} min"
            else:
                hours = pub.duration_min / 60
                place_details += f" - Duración: {hours:.1f}h"

        if hasattr(pub, "available_days") and pub.available_days:
            days_str = ", ".join(pub.available_days)
            place_details += f" - Días: {days_str}"

        if hasattr(pub, "available_hours") and pub.available_hours:
            hours_str = ", ".join(pub.available_hours)
            place_details += f" - Horarios: {hours_str}"

        if hasattr(pub, "cost_per_day") and pub.cost_per_day:
            place_details += f" - Costo: US${pub.cost_per_day}/día"

        places_info.append(place_details)

    places_list = (
        "\n".join(places_info) if places_info else "No hay lugares disponibles."
    )

    prompt = f"""Generá un itinerario de viaje (realista y variado) para '{destination}' desde '{start_date}' hasta '{end_date}'.

- Condiciones:
Presupuesto: US${budget}.
Cantidad de personas: {cant_persons}.
Estilo: {trip_type}.
"""

    if user_preferences:
        prompt += f"Preferencias del viajero: {user_preferences}.\n"

    if comments:
        prompt += f"Comentarios adicionales del usuario: {comments}.\n"

    if arrival_time:
        prompt += f"Hora estimada de llegada al destino: {arrival_time}.\n"

    if departure_time:
        prompt += f"Hora estimada de salida del destino: {departure_time}.\n"

    num_places = len(publications)
    from datetime import datetime as dt

    start_dt = dt.strptime(start_date, "%Y-%m-%d")
    end_dt = dt.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days + 1
    max_days_possible = num_places
    days_to_generate = min(total_days, max_days_possible)
    warning_message = ""
    if num_places < total_days:
        warning_message = f"\n⚠️ IMPORTANTE: Solo hay {num_places} lugar(es) disponible(s) para este destino, pero el viaje es de {total_days} días. GENERA SOLO {days_to_generate} DÍA(S) DE ITINERARIO (1 día por cada lugar disponible).\n"

    prompt += f"""
LUGARES Y ACTIVIDADES DISPONIBLES (JSON COMPLETO):
{publications_json_str}

RESUMEN DE LUGARES (para referencia rápida):
{places_list}
{warning_message}

RESTRICCIONES CRÍTICAS - VALIDACIÓN DE DISPONIBILIDAD:
- SOLO podés usar los lugares listados arriba con sus IDs. No inventes lugares ni uses información externa.
- OBLIGATORIO: Respeta los días disponibles de cada publicación (ejemplo: si dice "available_days": ["lunes", "martes", "viernes"] NO lo uses miércoles/jueves).
- OBLIGATORIO: Respeta los horarios disponibles de cada publicación (ejemplo: si dice "available_hours": ["09:00-12:00", "14:00-17:00"] NO lo uses a las 13:00).
- OBLIGATORIO: Respeta la duración de cada actividad (si dice "duration_min": 120 planifica 2 horas, no más ni menos).
- Calcula el costo total: si una publicación tiene cost_per_day > 0, multiplica por cantidad de personas y días de uso.
- El costo total de TODAS las actividades NO puede exceder el presupuesto de US${budget}.
- Si hay {num_places} lugar(es) disponible(s) y el viaje dura {total_days} días, GENERA SOLO {days_to_generate} DÍA(S) DE ITINERARIO.

FORMATO DE SALIDA OBLIGATORIO - DEBES DEVOLVER EXACTAMENTE ESTO:

```json
{{
  "itinerary_text": "═══════════════════════════════════════════════════\\nDÍA 1 - [FECHA]\\n═══════════════════════════════════════════════════\\n\\n🌅 MAÑANA (6:00 - 12:00)\\n• 08:00-10:00 - Desayuno con vista al Sena en Ritz Paris (ID: X)\\n• 10:30-12:00 - Visita guiada por los jardines del Louvre (ID: Y)\\n\\n🌞 TARDE (12:00 - 18:00)\\n• 12:30-14:00 - Almuerzo gourmet en Le Procope (ID: Z)\\n\\n🌙 NOCHE (18:00 - 23:00)\\n• 19:00-21:00 - Cena romántica con vista nocturna en Torre Eiffel (ID: W)\\n\\n[Repetir para más días si es necesario]",
  "used_publications": [
    {{
      "id": X,
      "name": "Nombre completo del lugar",
      "times_used": 1,
      "total_cost": 50,
      "days_used": ["2024-12-01"],
      "hours_used": ["08:00-10:00"]
    }},
    {{
      "id": Y,
      "name": "Otro lugar completo",
      "times_used": 2,
      "total_cost": 100,
      "days_used": ["2024-12-01", "2024-12-02"],
      "hours_used": ["10:30-12:00", "14:00-16:00"]
    }}
  ],
  "total_cost": 150,
  "validation_notes": "Todos los horarios y días respetan las disponibilidades. Costo total dentro del presupuesto."
}}
```

INSTRUCCIONES PARA EL TEXTO DEL ITINERARIO:
- En el "itinerary_text", puedes escribir descripciones creativas y atractivas de las actividades
- Ejemplo: "Desayuno con vista al Sena en Ritz Paris" en lugar de solo "Ritz Paris"  
- Ejemplo: "Cena romántica con vista nocturna en Torre Eiffel" en lugar de solo "Torre Eiffel"
- SIEMPRE incluye el ID entre paréntesis al final: (ID: X)
- Las descripciones deben ser inspiradoras y específicas del lugar

VALIDACIONES OBLIGATORIAS:
1. Verifica que cada publicación usada esté disponible en los días programados
2. Verifica que cada publicación usada esté disponible en los horarios programados  
3. Calcula el costo real basado en cost_per_day × cant_persons × días_usados
4. Asegúrate que total_cost ≤ presupuesto
5. En "used_publications", incluye TODAS las publicaciones mencionadas en el itinerario con sus IDs exactos

IMPORTANTE: 
- Devuelve SOLO el JSON, sin texto adicional antes o después
- El campo "itinerary_text" debe contener el itinerario formateado con \\n para saltos de línea
- El array "used_publications" debe incluir TODAS las publicaciones mencionadas en el itinerario
- Respeta ESTRICTAMENTE las disponibilidades de días y horarios de cada publicación"""

    return prompt


def parse_ai_response(ai_response: str) -> dict:
    """
    Procesa la respuesta de la IA que debe estar en formato JSON.
    Retorna un dict con itinerary_text, used_publications, total_cost y validation_notes.
    """
    import json

    try:
        response_text = ai_response.strip()
        if response_text.startswith("```json"):
            start = response_text.find("```json") + 7
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()
        elif response_text.startswith("```"):
            start = response_text.find("```") + 3
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()

        parsed_data = json.loads(response_text)
        required_fields = ["itinerary_text", "used_publications", "total_cost"]
        for field in required_fields:
            if field not in parsed_data:
                raise ValueError(
                    f"Campo requerido '{field}' no encontrado en la respuesta de IA"
                )

        return parsed_data

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[AI ERROR] No se pudo parsear respuesta de IA como JSON: {e}")
        print(f"[AI ERROR] Respuesta recibida: {ai_response[:500]}...")
        return {
            "itinerary_text": ai_response,
            "used_publications": [],
            "total_cost": 0,
            "validation_notes": "Error: La IA no devolvió un formato JSON válido. Usar método de extracción manual.",
        }


def extract_used_publications_fallback(
    itinerary_text: str, available_publications: list
) -> list:
    """
    Método de fallback para extraer publicaciones cuando la IA no devuelve JSON válido.
    Busca IDs en el formato (ID: X) en el texto del itinerario.
    """
    import re

    used_publication_ids = []

    if not itinerary_text or not available_publications:
        return used_publication_ids

    id_patterns = re.findall(r"\(ID:\s*(\d+)\)", itinerary_text, re.IGNORECASE)
    for id_str in id_patterns:
        try:
            pub_id = int(id_str)
            if pub_id not in used_publication_ids:
                for pub in available_publications:
                    if pub.id == pub_id:
                        used_publication_ids.append(pub_id)
                        print(
                            f"[ITINERARY DEBUG] Publicación encontrada por ID: {pub.place_name} (ID: {pub_id})"
                        )
                        break
        except ValueError:
            continue

    if not used_publication_ids:
        print(
            "[ITINERARY DEBUG] No se encontraron IDs en formato (ID: X), usando búsqueda por texto..."
        )
        used_publication_ids = extract_used_publications_legacy(
            itinerary_text, available_publications
        )

    return used_publication_ids


def extract_used_publications_legacy(
    itinerary_text: str, available_publications: list
) -> list:
    """
    Método legacy para extraer publicaciones del texto cuando no hay IDs específicos.
    Mantiene la funcionalidad anterior como respaldo.
    """
    used_publication_ids = []

    if not itinerary_text or not available_publications:
        return used_publication_ids

    itinerary_lower = itinerary_text.lower()
    positive_indicators = [
        "visitar",
        "ir a",
        "conocer",
        "recorrer",
        "pasear por",
        "disfrutar",
        "parada en",
        "almorzar en",
        "cenar en",
        "hospedarse en",
        "quedarse en",
        "recomiendo",
        "sugiero",
        "incluir",
        "ver",
        "explorar",
        "caminar por",
        "día en",
        "mañana en",
        "tarde en",
        "noche en",
    ]

    for pub in available_publications:
        publication_mentioned = False
        search_terms = []
        if pub.place_name and len(pub.place_name) >= 4:
            search_terms.append(pub.place_name.lower())

        if pub.place_name and len(pub.place_name) > 15:
            words = re.findall(r"\b\w{5,}\b", pub.place_name.lower())
            search_terms.extend(words)

        for term in search_terms:
            if term and len(term) >= 4:
                pattern = r"\b" + re.escape(term) + r"\b"
                matches = list(re.finditer(pattern, itinerary_lower))

                for match in matches:
                    start_idx = max(0, match.start() - 80)
                    end_idx = min(len(itinerary_lower), match.end() + 80)
                    context = itinerary_lower[start_idx:end_idx]

                    negative_indicators = [
                        "no ",
                        "sin ",
                        "excluir",
                        "evitar",
                        "omitir",
                        "no incluí",
                        "no incluyo",
                        "no recomiendo",
                        "no visitaremos",
                        "no iremos",
                        "no quería",
                        "no quiero",
                        "excepto",
                        "menos",
                        "salvo",
                        "no consideré",
                        "descartamos",
                        "porque no",
                        "no está",
                        "no hay",
                        "no encontré",
                        "no tengo",
                        "falta",
                        "ausencia de",
                    ]

                    is_negative_mention = any(
                        neg in context for neg in negative_indicators
                    )
                    has_positive_indicator = any(
                        pos in context for pos in positive_indicators
                    )
                    if not is_negative_mention and (
                        has_positive_indicator
                        or "itinerario" in context
                        or "programa" in context
                    ):
                        publication_mentioned = True
                        print(
                            f"[ITINERARY DEBUG] Contexto positivo para {pub.place_name}: '{context.strip()}'"
                        )
                        break
                    negative_indicators = [
                        "no ",
                        "sin ",
                        "excluir",
                        "evitar",
                        "omitir",
                        "no incluí",
                        "no incluyo",
                        "no recomiendo",
                        "no visitaremos",
                        "no iremos",
                        "no quería",
                        "no quiero",
                        "excepto",
                        "menos",
                        "salvo",
                        "no consideré",
                        "descartamos",
                        "porque no",
                        "no está",
                        "no hay",
                        "no encontré",
                        "no tengo",
                        "falta",
                        "ausencia de",
                    ]

                    is_negative_mention = any(
                        neg in context for neg in negative_indicators
                    )
                    has_positive_indicator = any(
                        pos in context for pos in positive_indicators
                    )
                    if not is_negative_mention and (
                        has_positive_indicator
                        or "itinerario" in context
                        or "programa" in context
                    ):
                        publication_mentioned = True
                        print(
                            f"[ITINERARY DEBUG] Contexto positivo para {pub.place_name}: '{context.strip()}'"
                        )
                        break
                    else:
                        print(
                            f"[ITINERARY DEBUG] Contexto ignorado para {pub.place_name}: '{context.strip()}'"
                        )

                if publication_mentioned:
                    break

        if publication_mentioned:
            used_publication_ids.append(pub.id)
            print(
                f"[ITINERARY DEBUG] Publicación USADA en itinerario: {pub.place_name}"
            )
        else:
            print(
                f"[ITINERARY DEBUG] Publicación NO usada en itinerario: {pub.place_name}"
            )

    return used_publication_ids


@router.post("/request", response_model=schemas.ItineraryOut)
def request_itinerary(
    payload: schemas.ItineraryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Endpoint para que un usuario básico solicite la generación de un itinerario con IA.
    Solo usuarios con rol 'user' pueden solicitar itinerarios.
    """

    if current_user.role not in ["user", "premium"]:
        raise HTTPException(
            status_code=403,
            detail="Solo usuarios básicos y premium pueden solicitar itinerarios",
        )

    start = (
        payload.start_date
        if isinstance(payload.start_date, datetime)
        else payload.start_date
    )
    end = (
        payload.end_date if isinstance(payload.end_date, datetime) else payload.end_date
    )
    if end < start:
        raise HTTPException(
            status_code=400,
            detail="La fecha de fin debe ser posterior a la fecha de inicio",
        )

    itinerary = models.Itinerary(
        user_id=current_user.id,
        destination=payload.destination,
        start_date=start,
        end_date=end,
        budget=payload.budget,
        cant_persons=payload.cant_persons,
        trip_type=payload.trip_type,
        arrival_time=payload.arrival_time,
        departure_time=payload.departure_time,
        comments=payload.comments,
        status="pending",
    )

    db.add(itinerary)
    db.commit()
    db.refresh(itinerary)
    destination_lower = payload.destination.lower()
    print(
        f"[ITINERARY DEBUG] Buscando publicaciones para destino: '{payload.destination}' (normalizado: '{destination_lower}')"
    )
    all_approved = (
        db.query(models.Publication)
        .filter(models.Publication.status == "approved")
        .all()
    )
    print(f"[ITINERARY DEBUG] Total publicaciones aprobadas: {len(all_approved)}")
    for pub in all_approved:
        print(
            f"[ITINERARY DEBUG] - {pub.place_name} | País: {pub.country} | Provincia: {pub.province} | Ciudad: {pub.city}"
        )

    from sqlalchemy import or_, and_

    exact_match_pubs = (
        db.query(models.Publication)
        .filter(
            models.Publication.status == "approved",
            or_(
                models.Publication.city.ilike(f"%{destination_lower}%"),
                models.Publication.province.ilike(f"%{destination_lower}%"),
                models.Publication.country.ilike(f"%{destination_lower}%"),
                models.Publication.address.ilike(f"%{destination_lower}%"),
            ),
        )
        .all()
    )

    print(
        f"[ITINERARY DEBUG] Búsqueda exacta encontró: {len(exact_match_pubs)} publicaciones"
    )
    if len(exact_match_pubs) == 0:
        print(
            f"[ITINERARY DEBUG] No se encontró con búsqueda exacta, probando con palabras clave..."
        )
        import re

        keywords = [
            word.strip()
            for word in re.split(r"[,;\s]+", destination_lower)
            if word.strip() and len(word.strip()) >= 4
        ]
        print(f"[ITINERARY DEBUG] Palabras clave extraídas (>=4 chars): {keywords}")

        if keywords:
            conditions = []
            for keyword in keywords:
                keyword_conditions = or_(
                    models.Publication.city.ilike(f"%{keyword}%"),
                    models.Publication.province.ilike(f"%{keyword}%"),
                    models.Publication.country.ilike(f"%{keyword}%"),
                    models.Publication.address.ilike(f"%{keyword}%"),
                )
                conditions.append(keyword_conditions)

            if len(conditions) == 1:
                final_condition = conditions[0]
            else:
                final_condition = and_(*conditions)

            publications = (
                db.query(models.Publication)
                .filter(models.Publication.status == "approved", final_condition)
                .all()
            )
        else:
            publications = []
    else:
        publications = exact_match_pubs

    print(f"[ITINERARY DEBUG] Publicaciones encontradas: {len(publications)}")
    for pub in publications:
        print(f"[ITINERARY DEBUG] Match: {pub.place_name} ({pub.city}, {pub.country})")

    if len(publications) == 0:
        itinerary.status = "failed"
        itinerary.generated_itinerary = f"❌ No se encontraron publicaciones relacionadas con '{payload.destination}' en nuestra base de datos.\n\nPor favor, intenta con otro destino o espera a que se agreguen más lugares de este destino a la plataforma."
        db.commit()
        db.refresh(itinerary)
        return schemas.ItineraryOut(
            id=itinerary.id,
            user_id=itinerary.user_id,
            destination=itinerary.destination,
            start_date=itinerary.start_date,
            end_date=itinerary.end_date,
            budget=itinerary.budget,
            cant_persons=itinerary.cant_persons,
            trip_type=itinerary.trip_type,
            arrival_time=itinerary.arrival_time,
            departure_time=itinerary.departure_time,
            comments=itinerary.comments,
            generated_itinerary=itinerary.generated_itinerary,
            status=itinerary.status,
            created_at=itinerary.created_at.isoformat(),
        )

    try:
        if not GEMINI_API_KEY:
            raise Exception("GEMINI_API_KEY no configurada")

        prompt = build_itinerary_prompt(
            destination=payload.destination,
            start_date=str(start),
            end_date=str(end),
            budget=payload.budget,
            cant_persons=payload.cant_persons,
            trip_type=payload.trip_type,
            publications=publications,
            user_preferences=current_user.travel_preferences,
            arrival_time=payload.arrival_time,
            departure_time=payload.departure_time,
            comments=payload.comments,
        )

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        ai_data = parse_ai_response(response.text)
        print(f"[VALIDATION] Iniciando validación backend del itinerario de IA...")
        validator = ItineraryValidator(db)

        validation_result = validator.validate_itinerary(
            itinerary_data=ai_data,
            budget=payload.budget,
            cant_persons=payload.cant_persons,
            start_date=str(start),
            end_date=str(end),
        )

        print(
            f"[VALIDATION] Resultado: {'✅ VÁLIDO' if validation_result['valid'] else '❌ INVÁLIDO'}"
        )
        print(f"[VALIDATION] {validation_result['validation_summary']}")
        validation_report = ""
        validation_report += f"\n\n📊 VALIDACIÓN DEL ITINERARIO:\n"
        validation_report += f"{'✅ VÁLIDO' if validation_result['valid'] else '❌ INVÁLIDO'} - {validation_result['validation_summary']}\n"
        if not validation_result["valid"]:
            validation_report += "\n🚨 ERRORES DE VALIDACIÓN DETECTADOS:\n"
            for error in validation_result["errors"]:
                validation_report += f"❌ {error['message']}\n"

        if validation_result["warnings"]:
            validation_report += "\n⚠️ ADVERTENCIAS:\n"
            for warning in validation_result["warnings"]:
                validation_report += f"⚠️ {warning['message']}\n"

        ai_cost = validation_result.get("ai_estimated_cost", 0)
        real_cost = validation_result.get("real_total_cost", 0)
        budget_utilization = validation_result.get("budget_utilization_percent", 0)
        validation_report += f"\n💰 INFORMACIÓN DE COSTOS:\n"
        if abs(ai_cost - real_cost) > 0.01:
            validation_report += f"• Costo estimado por IA: US${ai_cost:.2f}\n"
            validation_report += f"• Costo real validado: US${real_cost:.2f}\n"
        else:
            validation_report += f"• Costo total: US${real_cost:.2f}\n"

        validation_report += f"• Presupuesto disponible: US${payload.budget:.2f}\n"
        validation_report += (
            f"• Utilización del presupuesto: {budget_utilization:.1f}%\n"
        )
        if "validated_publications" in validation_result:
            validation_report += f"\n🏛️ LUGARES VALIDADOS ({len(validation_result['validated_publications'])}):\n"
            for pub in validation_result["validated_publications"][:5]:
                availability = "✅" if pub.get("availability_valid", True) else "❌"
                validation_report += (
                    f"• {availability} {pub['name']} - US${pub['real_cost']:.2f}\n"
                )

        itinerary.generated_itinerary = ai_data["itinerary_text"] + validation_report
        if validation_result["valid"]:
            itinerary.status = "completed"
        else:
            itinerary.status = "completed_with_warnings"
            print(f"[VALIDATION] Itinerario generado pero con errores de validación")

        itinerary.validation_metadata = validation_result
        if ai_data["used_publications"]:
            used_publication_ids = [pub["id"] for pub in ai_data["used_publications"]]
            valid_ids = []
            available_ids = [pub.id for pub in publications]
            for pub_id in used_publication_ids:
                if pub_id in available_ids:
                    valid_ids.append(pub_id)
                else:
                    print(
                        f"[ITINERARY WARNING] ID {pub_id} no encontrado en publicaciones disponibles"
                    )

            itinerary.publication_ids = valid_ids
        else:
            used_publication_ids = extract_used_publications_fallback(
                response.text, publications
            )
            itinerary.publication_ids = used_publication_ids

        if "total_cost" in ai_data:
            print(
                f"[ITINERARY DEBUG] Costo calculado por IA: US${ai_data['total_cost']}"
            )
        if "validation_notes" in ai_data:
            print(
                f"[ITINERARY DEBUG] Notas de validación: {ai_data['validation_notes']}"
            )

        print(f"[ITINERARY DEBUG] Publicaciones disponibles: {len(publications)}")
        print(
            f"[ITINERARY DEBUG] Publicaciones realmente usadas: {len(itinerary.publication_ids)}"
        )

    except Exception as e:
        itinerary.status = "failed"
        itinerary.generated_itinerary = f"Error al generar itinerario: {str(e)}"

    db.commit()
    db.refresh(itinerary)
    favorite_ids = {
        fav.publication_id
        for fav in db.query(models.Favorite)
        .filter(models.Favorite.user_id == current_user.id)
        .all()
    }

    publication_list = []
    if itinerary.publication_ids:
        for pub in publications:
            if pub.id in itinerary.publication_ids:
                categories = (
                    [cat.slug for cat in pub.categories] if pub.categories else []
                )
                photos = [photo.url for photo in pub.photos] if pub.photos else []
                publication_list.append(
                    schemas.PublicationOut(
                        id=pub.id,
                        place_name=pub.place_name,
                        country=pub.country,
                        province=pub.province,
                        city=pub.city,
                        address=pub.address,
                        description=getattr(pub, "description", None),
                        status=pub.status,
                        created_by_user_id=pub.created_by_user_id,
                        created_at=pub.created_at.isoformat(),
                        photos=photos,
                        rating_avg=pub.rating_avg or 0.0,
                        rating_count=pub.rating_count or 0,
                        categories=categories,
                        continent=getattr(pub, "continent", None),
                        climate=getattr(pub, "climate", None),
                        activities=getattr(pub, "activities", None) or [],
                        cost_per_day=getattr(pub, "cost_per_day", None),
                        duration_min=getattr(pub, "duration_min", None),
                        is_favorite=pub.id in favorite_ids,
                    )
                )

    return schemas.ItineraryOut(
        id=itinerary.id,
        user_id=itinerary.user_id,
        destination=itinerary.destination,
        start_date=itinerary.start_date,
        end_date=itinerary.end_date,
        budget=itinerary.budget,
        cant_persons=itinerary.cant_persons,
        trip_type=itinerary.trip_type,
        arrival_time=itinerary.arrival_time,
        departure_time=itinerary.departure_time,
        comments=itinerary.comments,
        generated_itinerary=itinerary.generated_itinerary,
        status=itinerary.status,
        created_at=itinerary.created_at.isoformat(),
        publications=publication_list,
    )


@router.get("/my-itineraries", response_model=list[schemas.ItineraryOut])
def get_my_itineraries(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene todos los itinerarios del usuario actual, incluyendo los itinerarios guardados.
    """
    own_itineraries = (
        db.query(models.Itinerary)
        .filter(models.Itinerary.user_id == current_user.id)
        .order_by(models.Itinerary.created_at.desc())
        .all()
    )

    saved_itineraries = (
        db.query(SavedItinerary)
        .filter(SavedItinerary.user_id == current_user.id)
        .order_by(SavedItinerary.saved_at.desc())
        .all()
    )

    favorite_ids = {
        fav.publication_id
        for fav in db.query(models.Favorite)
        .filter(models.Favorite.user_id == current_user.id)
        .all()
    }

    all_itineraries = []
    for it in own_itineraries:
        publication_list = []
        if it.publication_ids:
            pubs = (
                db.query(models.Publication)
                .filter(models.Publication.id.in_(it.publication_ids))
                .all()
            )

            for pub in pubs:
                categories = (
                    [cat.slug for cat in pub.categories] if pub.categories else []
                )
                photos = [photo.url for photo in pub.photos] if pub.photos else []
                publication_list.append(
                    schemas.PublicationOut(
                        id=pub.id,
                        place_name=pub.place_name,
                        country=pub.country,
                        province=pub.province,
                        city=pub.city,
                        address=pub.address,
                        description=getattr(pub, "description", None),
                        status=pub.status,
                        created_by_user_id=pub.created_by_user_id,
                        created_at=pub.created_at.isoformat(),
                        photos=photos,
                        rating_avg=pub.rating_avg or 0.0,
                        rating_count=pub.rating_count or 0,
                        categories=categories,
                        continent=getattr(pub, "continent", None),
                        climate=getattr(pub, "climate", None),
                        activities=getattr(pub, "activities", None) or [],
                        cost_per_day=getattr(pub, "cost_per_day", None),
                        duration_min=getattr(pub, "duration_min", None),
                        is_favorite=pub.id in favorite_ids,
                    )
                )

        all_itineraries.append(
            schemas.ItineraryOut(
                id=it.id,
                user_id=it.user_id,
                destination=it.destination,
                start_date=it.start_date,
                end_date=it.end_date,
                budget=it.budget,
                cant_persons=it.cant_persons,
                trip_type=it.trip_type,
                arrival_time=it.arrival_time,
                departure_time=it.departure_time,
                comments=it.comments,
                generated_itinerary=it.generated_itinerary,
                status=it.status,
                created_at=it.created_at.isoformat(),
                publications=publication_list,
            )
        )

        print(
            f"📊 [DEBUG] Itinerario {it.id} desde BD: budget={it.budget}, cant_persons={it.cant_persons}"
        )

    for saved in saved_itineraries:
        original_it = saved.original_itinerary
        publication_list = []
        if original_it.publication_ids:
            pubs = (
                db.query(models.Publication)
                .filter(models.Publication.id.in_(original_it.publication_ids))
                .all()
            )

            for pub in pubs:
                categories = (
                    [cat.slug for cat in pub.categories] if pub.categories else []
                )
                photos = [photo.url for photo in pub.photos] if pub.photos else []
                publication_list.append(
                    schemas.PublicationOut(
                        id=pub.id,
                        place_name=pub.place_name,
                        country=pub.country,
                        province=pub.province,
                        city=pub.city,
                        address=pub.address,
                        description=getattr(pub, "description", None),
                        status=pub.status,
                        created_by_user_id=pub.created_by_user_id,
                        created_at=pub.created_at.isoformat(),
                        photos=photos,
                        rating_avg=pub.rating_avg or 0.0,
                        rating_count=pub.rating_count or 0,
                        categories=categories,
                        continent=getattr(pub, "continent", None),
                        climate=getattr(pub, "climate", None),
                        activities=getattr(pub, "activities", None) or [],
                        cost_per_day=getattr(pub, "cost_per_day", None),
                        duration_min=getattr(pub, "duration_min", None),
                        is_favorite=pub.id in favorite_ids,
                    )
                )

        all_itineraries.append(
            schemas.ItineraryOut(
                id=saved.id,
                user_id=original_it.user_id,
                destination=original_it.destination,
                start_date=original_it.start_date,
                end_date=original_it.end_date,
                budget=original_it.budget,
                cant_persons=original_it.cant_persons,
                trip_type=original_it.trip_type,
                arrival_time=original_it.arrival_time,
                departure_time=original_it.departure_time,
                comments=original_it.comments,
                generated_itinerary=original_it.generated_itinerary,
                status="saved",
                created_at=saved.saved_at.isoformat(),
                publications=publication_list,
            )
        )

    return all_itineraries


@router.get("/ai-list")
def get_my_ai_itineraries(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    """
    Endpoint del PASO 4: Obtiene los itinerarios de IA del usuario para el botón "Pegar itinerario de IA"
    """

    print(f"[PASTE] Usuario {current_user.id} solicitando sus itinerarios de IA...")
    ai_itineraries = (
        db.query(models.Itinerary)
        .filter(
            models.Itinerary.user_id == current_user.id,
            models.Itinerary.status.in_(["completed", "completed_with_warnings"]),
            models.Itinerary.generated_itinerary.isnot(None),
        )
        .order_by(models.Itinerary.created_at.desc())
        .all()
    )

    print(f"[PASTE] Encontrados {len(ai_itineraries)} itinerarios de IA")

    itineraries_list = []
    for itinerary in ai_itineraries:
        lines = itinerary.generated_itinerary.split("\n")
        preview = "Sin preview disponible"
        for line in lines:
            if line.strip() and not line.startswith("═") and "DÍA" in line:
                preview = line.strip()
                break

        duration_days = (itinerary.end_date - itinerary.start_date).days + 1
        has_validation = any(
            keyword in itinerary.generated_itinerary
            for keyword in [
                "VALIDACIÓN DEL ITINERARIO",
                "COSTO TOTAL",
                "LUGARES VALIDADOS",
            ]
        )

        itinerary_data = {
            "id": itinerary.id,
            "destination": itinerary.destination,
            "start_date": str(itinerary.start_date),
            "end_date": str(itinerary.end_date),
            "budget": itinerary.budget,
            "cant_persons": itinerary.cant_persons,
            "trip_type": itinerary.trip_type,
            "status": itinerary.status,
            "created_at": itinerary.created_at.isoformat(),
            "duration_days": duration_days,
            "preview": preview,
            "has_validation": has_validation,
            "publication_count": (
                len(itinerary.publication_ids) if itinerary.publication_ids else 0
            ),
        }

        itineraries_list.append(itinerary_data)

    return {
        "itineraries": itineraries_list,
        "total": len(itineraries_list),
        "user_id": current_user.id,
    }


@router.post("/convert-ai-to-custom")
def convert_ai_to_custom_itinerary(
    conversion_data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Endpoint del PASO 4: Convierte un itinerario de IA a formato personalizado (custom)
    """

    print(f"[CONVERT] Usuario {current_user.id} convirtiendo itinerario de IA...")
    print(f"[CONVERT] Datos recibidos: {conversion_data}")

    try:
        ai_itinerary_id = conversion_data.get("ai_itinerary_id")
        custom_destination = conversion_data.get("custom_destination", "")
        custom_start_date = conversion_data.get("custom_start_date")
        custom_end_date = conversion_data.get("custom_end_date")

        if not ai_itinerary_id:
            raise HTTPException(
                status_code=400, detail="ID del itinerario de IA es requerido"
            )

        ai_itinerary = (
            db.query(models.Itinerary)
            .filter(
                models.Itinerary.id == ai_itinerary_id,
                models.Itinerary.user_id == current_user.id,
            )
            .first()
        )

        if not ai_itinerary:
            raise HTTPException(
                status_code=404, detail="Itinerario de IA no encontrado"
            )

        if not ai_itinerary.generated_itinerary:
            raise HTTPException(
                status_code=400, detail="El itinerario no tiene contenido generado"
            )

        start_date = custom_start_date or str(ai_itinerary.start_date)
        end_date = custom_end_date or str(ai_itinerary.end_date)
        destination = custom_destination or ai_itinerary.destination

        from datetime import datetime, date

        if isinstance(start_date, str):
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_dt = start_date

        if isinstance(end_date, str):
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_dt = end_date

        total_days = (end_dt - start_dt).days + 1

        days = []
        current_date = start_dt
        for i in range(total_days):
            days.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "day_name": current_date.strftime("%A"),
                    "day_number": i + 1,
                }
            )
            from datetime import timedelta

            current_date += timedelta(days=1)

        print(f"[CONVERT] Generando estructura para {total_days} días")

        custom_structure = {
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "itinerary": {},
        }

        print(f"[CONVERT] Parseando texto generado por IA...")

        publication_ids = ai_itinerary.publication_ids or []
        print(f"[CONVERT] Publication IDs guardados: {publication_ids}")

        publications_map = {}
        if publication_ids:
            used_publications = (
                db.query(models.Publication)
                .filter(models.Publication.id.in_(publication_ids))
                .all()
            )
            publications_map = {pub.id: pub for pub in used_publications}
            print(f"[CONVERT] Publicaciones cargadas: {len(publications_map)}")

        for day in days:
            day_key = f"day_{day['day_number']}"
            custom_structure["itinerary"][day_key] = {
                "morning": {},
                "afternoon": {},
                "evening": {},
            }

        ai_text = ai_itinerary.generated_itinerary or ""
        print(f"[CONVERT] Parseando {len(ai_text)} caracteres de texto de IA...")

        import re

        activity_pattern = (
            r"• (\d{2}:\d{2})-(\d{2}:\d{2}) - ([^(]+)(?:\(ID:\s*(\d+)\))?"
        )

        day_pattern = r"DÍA (\d+) - ([^═\n]+)"

        lines = ai_text.split("\n")
        current_day = None
        current_period = None

        def get_period_for_time(time_str):
            hour = int(time_str.split(":")[0])
            if 6 <= hour < 12:
                return "morning"
            elif 12 <= hour < 18:
                return "afternoon"
            else:
                return "evening"

        def _time_to_minutes_local(time_str):
            """Convierte un tiempo HH:MM a minutos desde medianoche"""
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes

        activities_found = 0
        for line in lines:
            line = line.strip()

            day_match = re.search(day_pattern, line)
            if day_match:
                day_num = int(day_match.group(1))
                current_day = f"day_{day_num}"
                print(f"[CONVERT] Procesando {current_day}")
                continue

            if "🌅 MAÑANA" in line or "MAÑANA" in line:
                current_period = "morning"
                continue
            elif "🌞 TARDE" in line or "TARDE" in line:
                current_period = "afternoon"
                continue
            elif "🌙 NOCHE" in line or "NOCHE" in line:
                current_period = "evening"
                continue

            activity_match = re.search(activity_pattern, line)
            if activity_match and current_day:
                start_time = activity_match.group(1)
                end_time = activity_match.group(2)
                description = activity_match.group(3).strip()
                pub_id_str = activity_match.group(4)

                period = get_period_for_time(start_time)

                pub_id = None
                publication_data = None

                if pub_id_str:
                    pub_id = int(pub_id_str)
                    publication_data = publications_map.get(pub_id)

                if not publication_data:
                    for pid, pub in publications_map.items():
                        if pub.place_name.lower() in description.lower():
                            pub_id = pid
                            publication_data = pub
                            break

                start_minutes = _time_to_minutes_local(start_time)
                end_minutes = _time_to_minutes_local(end_time)
                actual_duration = end_minutes - start_minutes

                activity_entry = {
                    "id": pub_id,
                    "place_name": (
                        publication_data.place_name if publication_data else description
                    ),
                    "address": publication_data.address if publication_data else "",
                    "city": (
                        publication_data.city
                        if publication_data
                        else destination.split(",")[0].strip()
                    ),
                    "province": publication_data.province if publication_data else "",
                    "country": publication_data.country if publication_data else "",
                    "description": (
                        publication_data.description
                        if publication_data
                        else description
                    ),
                    "duration_min": actual_duration,
                    "categories": (
                        [cat.slug for cat in (publication_data.categories or [])]
                        if publication_data
                        else []
                    ),
                    "cost_per_day": (
                        publication_data.cost_per_day if publication_data else None
                    ),
                    "photos": (
                        [photo.url for photo in (publication_data.photos or [])]
                        if publication_data
                        else []
                    ),
                    "rating_avg": (
                        publication_data.rating_avg if publication_data else None
                    ),
                    "rating_count": (
                        publication_data.rating_count if publication_data else 0
                    ),
                    "converted_from_ai": True,
                    "original_text": description,
                    "start_time": start_time,
                    "end_time": end_time,
                }

                if current_day in custom_structure["itinerary"]:
                    custom_structure["itinerary"][current_day][period][
                        start_time
                    ] = activity_entry
                    activities_found += 1
                    print(
                        f"[CONVERT] ✓ {current_day}/{period}/{start_time}: {description[:50]}... (duración: {actual_duration}min)"
                    )

                    if actual_duration > 30:
                        slots_needed = (actual_duration + 29) // 30

                        time_slots_for_period = {
                            "morning": [
                                "06:00",
                                "06:30",
                                "07:00",
                                "07:30",
                                "08:00",
                                "08:30",
                                "09:00",
                                "09:30",
                                "10:00",
                                "10:30",
                                "11:00",
                                "11:30",
                            ],
                            "afternoon": [
                                "12:00",
                                "12:30",
                                "13:00",
                                "13:30",
                                "14:00",
                                "14:30",
                                "15:00",
                                "15:30",
                                "16:00",
                                "16:30",
                                "17:00",
                                "17:30",
                            ],
                            "evening": [
                                "18:00",
                                "18:30",
                                "19:00",
                                "19:30",
                                "20:00",
                                "20:30",
                                "21:00",
                                "21:30",
                                "22:00",
                                "22:30",
                                "23:00",
                                "23:30",
                            ],
                        }

                        available_slots = time_slots_for_period.get(period, [])
                        start_slot_index = (
                            available_slots.index(start_time)
                            if start_time in available_slots
                            else -1
                        )

                        if start_slot_index >= 0:
                            for slot_offset in range(1, slots_needed):
                                continuation_slot_index = start_slot_index + slot_offset

                                if continuation_slot_index < len(available_slots):
                                    continuation_time = available_slots[
                                        continuation_slot_index
                                    ]

                                    continuation_entry = {
                                        "id": pub_id,
                                        "place_name": (
                                            publication_data.place_name
                                            if publication_data
                                            else description
                                        ),
                                        "city": (
                                            publication_data.city
                                            if publication_data
                                            else destination.split(",")[0].strip()
                                        ),
                                        "province": (
                                            publication_data.province
                                            if publication_data
                                            else ""
                                        ),
                                        "country": (
                                            publication_data.country
                                            if publication_data
                                            else ""
                                        ),
                                        "address": (
                                            publication_data.address
                                            if publication_data
                                            else ""
                                        ),
                                        "is_continuation": True,
                                        "main_slot_time": start_time,
                                        "start_time": start_time,
                                        "end_time": end_time,
                                        "converted_from_ai": True,
                                        "continuation_of": start_time,
                                    }

                                    custom_structure["itinerary"][current_day][period][
                                        continuation_time
                                    ] = continuation_entry
                                    print(
                                        f"[CONVERT]   + Continuación en {continuation_time}"
                                    )
                                else:
                                    next_period = None
                                    if period == "morning":
                                        next_period = "afternoon"
                                    elif period == "afternoon":
                                        next_period = "evening"

                                    if (
                                        next_period
                                        and next_period in time_slots_for_period
                                    ):
                                        next_slots = time_slots_for_period[next_period]
                                        overflow_slots = continuation_slot_index - len(
                                            available_slots
                                        )

                                        if overflow_slots < len(next_slots):
                                            continuation_time = next_slots[
                                                overflow_slots
                                            ]

                                            continuation_entry = {
                                                "id": pub_id,
                                                "place_name": (
                                                    publication_data.place_name
                                                    if publication_data
                                                    else description
                                                ),
                                                "city": (
                                                    publication_data.city
                                                    if publication_data
                                                    else destination.split(",")[
                                                        0
                                                    ].strip()
                                                ),
                                                "province": (
                                                    publication_data.province
                                                    if publication_data
                                                    else ""
                                                ),
                                                "country": (
                                                    publication_data.country
                                                    if publication_data
                                                    else ""
                                                ),
                                                "address": (
                                                    publication_data.address
                                                    if publication_data
                                                    else ""
                                                ),
                                                "is_continuation": True,
                                                "main_slot_time": start_time,
                                                "start_time": start_time,
                                                "end_time": end_time,
                                                "converted_from_ai": True,
                                                "continuation_of": start_time,
                                                "period_overflow": True,
                                            }

                                            custom_structure["itinerary"][current_day][
                                                next_period
                                            ][continuation_time] = continuation_entry
                                            print(
                                                f"[CONVERT]   + Continuación en {next_period}/{continuation_time}"
                                            )

        print(f"[CONVERT] Actividades extraídas: {activities_found}")

        if activities_found == 0 and publications_map:
            print(
                f"[CONVERT] No se pudieron parsear actividades, usando distribución simple..."
            )

            publications_list = list(publications_map.values())
            publications_per_day = len(publications_list) // total_days
            extra_publications = len(publications_list) % total_days

            time_slots = {
                "morning": ["08:00", "09:30", "11:00"],
                "afternoon": ["12:30", "14:00", "15:30"],
                "evening": ["19:00", "20:30", "22:00"],
            }

            pub_index = 0
            for day_index, day in enumerate(days):
                day_key = f"day_{day['day_number']}"

                pubs_for_this_day = publications_per_day
                if day_index < extra_publications:
                    pubs_for_this_day += 1

                period_keys = ["morning", "afternoon", "evening"]
                for i in range(pubs_for_this_day):
                    if pub_index >= len(publications_list):
                        break

                    pub = publications_list[pub_index]

                    period_index = i % len(period_keys)
                    period = period_keys[period_index]
                    time_index = i // len(period_keys)

                    if time_index < len(time_slots[period]):
                        time_slot = time_slots[period][time_index]

                        custom_structure["itinerary"][day_key][period][time_slot] = {
                            "id": pub.id,
                            "place_name": pub.place_name,
                            "address": pub.address or "",
                            "city": pub.city or destination.split(",")[0].strip(),
                            "province": pub.province or "",
                            "country": pub.country or "",
                            "description": pub.description or "",
                            "duration_min": pub.duration_min or 120,
                            "categories": [cat.slug for cat in (pub.categories or [])],
                            "cost_per_day": pub.cost_per_day,
                            "photos": (
                                [photo.url for photo in (pub.photos or [])]
                                if pub.photos
                                else []
                            ),
                            "rating_avg": pub.rating_avg,
                            "rating_count": pub.rating_count or 0,
                            "converted_from_ai": True,
                        }

                        pub_index += 1

        print(f"[CONVERT] Conversión exitosa para {destination}")
        print(f"[CONVERT] Estructura creada con {total_days} días")

        print(f"[CONVERT] ==== ESTRUCTURA FINAL ====")
        print(f"[CONVERT] Días en estructura: {len(custom_structure['itinerary'])}")
        for day_key, day_data in custom_structure["itinerary"].items():
            total_activities = sum(len(period) for period in day_data.values())
            print(f"[CONVERT] {day_key}: {total_activities} actividades")
            for period, activities in day_data.items():
                if activities:
                    print(f"[CONVERT]   {period}: {len(activities)} slots ocupados")
                    for time, activity in activities.items():
                        title = (
                            activity.get("place_name", "Sin título")
                            if isinstance(activity, dict)
                            else str(activity)
                        )
                        print(f"[CONVERT]     {time}: {title}")
        print(f"[CONVERT] ========================")

        return {
            "success": True,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "itinerary": custom_structure["itinerary"],
            "converted_from": {
                "id": ai_itinerary.id,
                "destination": ai_itinerary.destination,
                "original_text": ai_itinerary.generated_itinerary[:500] + "...",
            },
            "message": f"Itinerario convertido exitosamente para {total_days} día(s) en {destination}",
        }

    except Exception as e:
        print(f"[CONVERT] Error en conversión: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error al convertir itinerario: {str(e)}"
        )


@router.get("/{itinerary_id}", response_model=schemas.ItineraryOut)
def get_itinerary(
    itinerary_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Obtiene un itinerario específico por ID.
    Solo puede ver sus propios itinerarios.
    """
    itinerary = (
        db.query(models.Itinerary).filter(models.Itinerary.id == itinerary_id).first()
    )

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")

    if itinerary.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="No tienes permiso para ver este itinerario"
        )

    favorite_ids = {
        fav.publication_id
        for fav in db.query(models.Favorite)
        .filter(models.Favorite.user_id == current_user.id)
        .all()
    }

    publication_list = []
    if itinerary.publication_ids:
        pubs = (
            db.query(models.Publication)
            .filter(models.Publication.id.in_(itinerary.publication_ids))
            .all()
        )

        for pub in pubs:
            categories = [cat.slug for cat in pub.categories] if pub.categories else []
            photos = [photo.url for photo in pub.photos] if pub.photos else []

            publication_list.append(
                schemas.PublicationOut(
                    id=pub.id,
                    place_name=pub.place_name,
                    country=pub.country,
                    province=pub.province,
                    city=pub.city,
                    address=pub.address,
                    description=getattr(pub, "description", None),
                    status=pub.status,
                    created_by_user_id=pub.created_by_user_id,
                    created_at=pub.created_at.isoformat(),
                    photos=photos,
                    rating_avg=pub.rating_avg or 0.0,
                    rating_count=pub.rating_count or 0,
                    categories=categories,
                    continent=getattr(pub, "continent", None),
                    climate=getattr(pub, "climate", None),
                    activities=getattr(pub, "activities", None) or [],
                    cost_per_day=getattr(pub, "cost_per_day", None),
                    duration_min=getattr(pub, "duration_min", None),
                    is_favorite=pub.id in favorite_ids,
                )
            )

    return schemas.ItineraryOut(
        id=itinerary.id,
        user_id=itinerary.user_id,
        destination=itinerary.destination,
        start_date=itinerary.start_date,
        end_date=itinerary.end_date,
        budget=itinerary.budget,
        cant_persons=itinerary.cant_persons,
        trip_type=itinerary.trip_type,
        arrival_time=itinerary.arrival_time,
        departure_time=itinerary.departure_time,
        comments=itinerary.comments,
        generated_itinerary=itinerary.generated_itinerary,
        status=itinerary.status,
        created_at=itinerary.created_at.isoformat(),
        publications=publication_list,
    )


@router.delete("/{itinerary_id}")
def delete_itinerary(
    itinerary_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Elimina un itinerario específico por ID.
    Solo puede eliminar sus propios itinerarios.
    """
    itinerary = (
        db.query(models.Itinerary).filter(models.Itinerary.id == itinerary_id).first()
    )

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")

    if itinerary.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="No tienes permiso para eliminar este itinerario"
        )

    db.delete(itinerary)
    db.commit()

    return {"message": "Itinerario eliminado exitosamente", "id": itinerary_id}


class SharePayload(BaseModel):
    to: EmailStr
    note: str | None = None


def _abs_url(path: str, base: str) -> str:
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = (base or "").rstrip("/")
    path = path if path.startswith("/") else f"/{path}"
    return f"{base}{path}"


def _build_itinerary_email_html(
    itinerary: models.Itinerary, pubs: list[models.Publication]
) -> str:
    app_url = os.getenv("APP_PUBLIC_URL", "http://localhost:8000")
    brand = os.getenv("APP_BRAND_NAME", "Plan&Go")

    title = f"Itinerario: {itinerary.destination}"
    start = _to_date(itinerary.start_date)
    end = _to_date(itinerary.end_date)
    date_range = (
        f"{_fmt_date_ymd(itinerary.start_date)} → {_fmt_date_ymd(itinerary.end_date)}"
    )
    status_pill = itinerary.status.capitalize()
    budget = f"US$ {itinerary.budget}"
    persons = f"{itinerary.cant_persons}"

    gen_html = html.escape(itinerary.generated_itinerary or "").replace("\n", "<br />")

    cards_html = ""
    for p in pubs:
        photo_url = ""
        if getattr(p, "photos", None):
            photo_url = _abs_url(p.photos[0].url, app_url)
        address = f"{p.address}, {p.city}, {p.province}, {p.country}"
        rating = (
            f"{getattr(p, 'rating_avg', 0.0):.1f} ⭐ ({getattr(p, 'rating_count', 0)})"
        )
        cats = ", ".join([c.slug for c in (p.categories or [])])

        cards_html += f"""
        <tr>
          <td style="padding:12px 0;">
            <table width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
              {"<tr><td><img src='"+photo_url+"' alt='' style='width:100%;max-height:220px;object-fit:cover;display:block;'/></td></tr>" if photo_url else ""}
              <tr>
                <td style="padding:12px 16px;">
                  <div style="font-weight:600;font-size:16px;margin:0 0 4px 0;">{html.escape(p.place_name)}</div>
                  <div style="color:#6b7280;font-size:13px;margin:0 0 6px 0;">{html.escape(address)}</div>
                  <div style="font-size:13px;">
                    <span>⭐ {rating}</span>
                    {" — <span style='color:#6b7280;'>" + html.escape(cats) + "</span>" if cats else ""}
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """

    return f"""
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>{html.escape(title)}</title></head>
  <body style="font-family: Arial, sans-serif; background:#f6fbff; padding:24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width:760px;margin:0 auto;background:#ffffff;border-radius:16px;box-shadow:0 6px 20px rgba(0,0,0,0.06);overflow:hidden;">
      <tr>
        <td style="background:linear-gradient(135deg,#0ea5e9,#22d3ee);color:#fff;padding:24px 24px;">
          <h1 style="margin:0;font-size:22px;">✈️ {html.escape(title)}</h1>
          <p style="margin:8px 0 0 0;opacity:0.95;">{html.escape(date_range)} • Estado: {html.escape(status_pill)}</p>
          <p style="margin:6px 0 0 0;opacity:0.95;">Presupuesto: {html.escape(budget)} • Personas: {html.escape(persons)}</p>
        </td>
      </tr>

      <tr>
        <td style="padding:20px 24px;">
          <div style="font-weight:600;margin-bottom:8px;">Itinerario generado</div>
          <div style="border:1px solid #e5e7eb;background:#f9fafb;border-radius:12px;padding:16px;line-height:1.6;font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;">
            {gen_html}
          </div>
        </td>
      </tr>

      <tr>
        <td style="padding:0 24px 8px 24px;">
          <div style="font-weight:600;margin:8px 0 10px 0;">Lugares incluidos en este itinerario</div>
          <table width="100%" cellpadding="0" cellspacing="0">
            {cards_html or "<tr><td style='color:#6b7280;'>No hay lugares asociados.</td></tr>"}
          </table>
        </td>
      </tr>

      <tr>
        <td style="padding:16px 24px; background:#f9fafb; color:#6b7280; font-size:12px;">
          © {html.escape(brand)} — Compartido desde la app. Link: <a href="{_abs_url(f'/itinerary/{itinerary.id}', app_url)}" style="color:#0ea5e9;">ver en la web</a>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()


@router.post("/{itinerary_id}/share-email")
def share_itinerary_by_email(
    itinerary_id: int,
    payload: SharePayload,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Envía por email el itinerario (HTML) al destinatario indicado.
    Solo el dueño del itinerario puede compartirlo.
    Solo disponible para usuarios PREMIUM.
    """
    if current_user.role != "premium":
        raise HTTPException(
            status_code=403, detail="Función disponible solo para usuarios premium."
        )

    it = db.query(models.Itinerary).filter(models.Itinerary.id == itinerary_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")

    if it.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="No tienes permiso para compartir este itinerario"
        )

    pubs: list[models.Publication] = []
    if getattr(it, "publication_ids", None):
        pubs = (
            db.query(models.Publication)
            .filter(models.Publication.id.in_(it.publication_ids))
            .all()
        )

    html_body = _build_itinerary_email_html(it, pubs)
    subject = f"Tu itinerario: {it.destination} ({_fmt_date_ymd(it.start_date)} → {_fmt_date_ymd(it.end_date)})"

    if payload.note:
        note_html = f"<p style='margin:0 0 12px 0'><em>Mensaje de {html.escape(current_user.username)}:</em> {html.escape(payload.note)}</p>"
        html_body = html_body.replace("<table", note_html + "<table", 1)

    send_email_html(payload.to, subject, html_body)
    return {"ok": True, "message": "Itinerario enviado por email"}


@router.get("/by-user/{user_id}", response_model=list[schemas.ItineraryOut])
def get_itineraries_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Itinerarios generados por un usuario concreto (para ver su perfil viajero).
    """
    itineraries = (
        db.query(models.Itinerary)
        .filter(models.Itinerary.user_id == user_id)
        .order_by(models.Itinerary.created_at.desc())
        .all()
    )
    return itineraries


@router.get("/by-user/{user_id}")
def get_itineraries_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Itinerarios visibles del usuario indicado.
    Por ahora dejamos que cualquier usuario autenticado pueda ver los itinerarios
    publicados de otros.
    """
    its = (
        db.query(models.Itinerary)
        .filter(models.Itinerary.user_id == user_id)
        .order_by(models.Itinerary.created_at.desc())
        .all()
    )

    result = []
    for it in its:
        result.append(
            {
                "id": it.id,
                "destination": it.destination,
                "start_date": it.start_date,
                "end_date": it.end_date,
                "trip_type": getattr(it, "trip_type", None),
                "budget": getattr(it, "budget", None),
                "cant_persons": getattr(it, "cant_persons", None),
                "status": it.status,
                "arrival_time": getattr(it, "arrival_time", None),
                "departure_time": getattr(it, "departure_time", None),
                "generated_itinerary": getattr(it, "generated_itinerary", None),
                "created_at": (
                    it.created_at.isoformat()
                    if getattr(it, "created_at", None)
                    else None
                ),
            }
        )
    return result


def _to_date(value):
    """Acepta datetime/date/str y devuelve date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%d").date()
    return value


def _fmt_date_ymd(value) -> str:
    """Devuelve la fecha como 'YYYY-MM-DD' aceptando date/datetime/str ISO."""
    if isinstance(value, datetime):
        d = value.date()
    elif isinstance(value, date):
        d = value
    elif isinstance(value, str):
        try:
            d = datetime.fromisoformat(value).date()
        except ValueError:
            try:
                d = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return str(value)
    else:
        return str(value)
    return d.strftime("%Y-%m-%d")


@router.post("/save", response_model=schemas.SavedItineraryOut)
def save_itinerary(
    payload: schemas.SavedItineraryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Guardar una copia del itinerario de otro usuario en mis itinerarios guardados
    """

    original_itinerary = (
        db.query(Itinerary)
        .filter(Itinerary.id == payload.original_itinerary_id)
        .first()
    )

    if not original_itinerary:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")

    if original_itinerary.user_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="No puedes guardar tu propio itinerario"
        )

    existing_saved = (
        db.query(SavedItinerary)
        .filter(
            SavedItinerary.user_id == current_user.id,
            SavedItinerary.original_itinerary_id == payload.original_itinerary_id,
        )
        .first()
    )

    if existing_saved:
        raise HTTPException(
            status_code=400, detail="Ya tienes este itinerario guardado"
        )

    saved_itinerary = SavedItinerary(
        user_id=current_user.id,
        original_itinerary_id=original_itinerary.id,
        destination=original_itinerary.destination,
        start_date=original_itinerary.start_date,
        end_date=original_itinerary.end_date,
        budget=original_itinerary.budget,
        cant_persons=original_itinerary.cant_persons,
        trip_type=original_itinerary.trip_type,
        arrival_time=original_itinerary.arrival_time,
        departure_time=original_itinerary.departure_time,
        comments=original_itinerary.comments,
        generated_itinerary=original_itinerary.generated_itinerary,
        publication_ids=original_itinerary.publication_ids,
        original_author_id=original_itinerary.user_id,
    )

    db.add(saved_itinerary)
    db.commit()
    db.refresh(saved_itinerary)

    publications = []
    if saved_itinerary.publication_ids:
        publications = (
            db.query(models.Publication)
            .filter(models.Publication.id.in_(saved_itinerary.publication_ids))
            .all()
        )

    return schemas.SavedItineraryOut(
        id=saved_itinerary.id,
        user_id=saved_itinerary.user_id,
        original_itinerary_id=saved_itinerary.original_itinerary_id,
        destination=saved_itinerary.destination,
        start_date=saved_itinerary.start_date,
        end_date=saved_itinerary.end_date,
        budget=saved_itinerary.budget,
        cant_persons=saved_itinerary.cant_persons,
        trip_type=saved_itinerary.trip_type,
        arrival_time=saved_itinerary.arrival_time,
        departure_time=saved_itinerary.departure_time,
        comments=saved_itinerary.comments,
        generated_itinerary=saved_itinerary.generated_itinerary,
        original_author_id=saved_itinerary.original_author_id,
        saved_at=saved_itinerary.saved_at,
        publications=[
            schemas.PublicationOut(
                id=pub.id,
                place_name=pub.place_name,
                country=pub.country,
                province=pub.province,
                city=pub.city,
                address=pub.address,
                description=pub.description,
                status=pub.status,
                created_by_user_id=pub.created_by_user_id,
                created_at=pub.created_at,
                photos=pub.photos or [],
                categories=pub.categories or [],
            )
            for pub in publications
        ],
    )


@router.get("/saved")
def get_saved_itineraries(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    """
    Obtener todos los itinerarios guardados por el usuario actual
    """
    saved_itineraries = (
        db.query(SavedItinerary)
        .filter(SavedItinerary.user_id == current_user.id)
        .order_by(SavedItinerary.saved_at.desc())
        .all()
    )

    result = []
    for saved in saved_itineraries:
        publications = []
        if saved.publication_ids:
            publications = (
                db.query(models.Publication)
                .filter(models.Publication.id.in_(saved.publication_ids))
                .all()
            )

        result.append(
            {
                "id": saved.id,
                "user_id": saved.user_id,
                "original_itinerary_id": saved.original_itinerary_id,
                "destination": saved.destination,
                "start_date": (
                    saved.start_date.isoformat() if saved.start_date else None
                ),
                "end_date": saved.end_date.isoformat() if saved.end_date else None,
                "budget": saved.budget,
                "cant_persons": saved.cant_persons,
                "trip_type": saved.trip_type,
                "arrival_time": saved.arrival_time,
                "departure_time": saved.departure_time,
                "comments": saved.comments,
                "generated_itinerary": saved.generated_itinerary,
                "original_author_id": saved.original_author_id,
                "saved_at": saved.saved_at.isoformat() if saved.saved_at else None,
                "status": "saved",
                "created_at": saved.saved_at.isoformat() if saved.saved_at else None,
                "publications": [
                    {
                        "id": pub.id,
                        "place_name": pub.place_name,
                        "country": pub.country,
                        "province": pub.province,
                        "city": pub.city,
                        "address": pub.address,
                        "description": pub.description,
                        "status": pub.status,
                        "created_by_user_id": pub.created_by_user_id,
                        "created_at": (
                            pub.created_at.isoformat() if pub.created_at else None
                        ),
                        "photos": pub.photos or [],
                        "categories": pub.categories or [],
                    }
                    for pub in publications
                ],
            }
        )

    return result


class CustomItineraryRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    cant_persons: int = 1
    budget: int = 0
    itinerary_data: dict
    type: str = "custom"


def _extract_publication_ids(itinerary_data: Dict) -> List[int]:
    """Extrae todos los IDs de publicaciones del itinerary_data"""
    publication_ids = []

    for day_key, day_data in itinerary_data.items():
        if not day_key.startswith("day_"):
            continue

        for period in ["morning", "afternoon", "evening"]:
            if period in day_data:
                for time_slot, activity in day_data[period].items():
                    if activity and activity.get("id"):
                        publication_ids.append(activity.get("id"))

    return list(set(publication_ids))


def _time_to_minutes(time_str: str) -> int:
    """Convierte una hora en formato HH:MM a minutos desde medianoche"""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except:
        return 0


@router.post("/custom", response_model=schemas.ItineraryOut)
async def create_custom_itinerary(
    request: CustomItineraryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Crea un itinerario personalizado donde el usuario ha seleccionado
    manualmente las actividades para cada horario
    """
    try:
        print(f"🔍 [DEBUG] Datos recibidos:")
        print(f"  - Destino: {request.destination}")
        print(
            f"  - Personas: {request.cant_persons} (tipo: {type(request.cant_persons)})"
        )
        print(f"  - Presupuesto: {request.budget} (tipo: {type(request.budget)})")
        print(f"  - Fechas: {request.start_date} a {request.end_date}")

        validation_errors = []
        publication_ids = _extract_publication_ids(request.itinerary_data)

        total_cost = 0
        budget_validation = []

        if publication_ids:
            publications = (
                db.query(models.Publication)
                .filter(models.Publication.id.in_(publication_ids))
                .all()
            )

            start_date_obj = datetime.fromisoformat(request.start_date).date()

            for pub in publications:
                if pub.cost_per_day and pub.cost_per_day > 0:
                    activity_cost = pub.cost_per_day * request.cant_persons
                    total_cost += activity_cost
                    budget_validation.append(
                        {
                            "name": pub.place_name,
                            "cost_per_person": pub.cost_per_day,
                            "total_cost": activity_cost,
                        }
                    )

                for day_key, day_data in request.itinerary_data.items():
                    if not day_key.startswith("day_"):
                        continue

                    day_number = int(day_key.split("_")[1])
                    from datetime import timedelta

                    current_date = start_date_obj + timedelta(days=day_number - 1)
                    day_name = current_date.strftime("%A").lower()

                    day_names_es = {
                        "monday": "lunes",
                        "tuesday": "martes",
                        "wednesday": "miércoles",
                        "thursday": "jueves",
                        "friday": "viernes",
                        "saturday": "sábado",
                        "sunday": "domingo",
                    }
                    day_name_es = day_names_es.get(day_name, day_name)

                    pub_in_day = False
                    for period in ["morning", "afternoon", "evening"]:
                        if period in day_data:
                            for time_slot, activity in day_data[period].items():
                                if activity and activity.get("id") == pub.id:
                                    pub_in_day = True

                                    available_days = pub.available_days or []
                                    if (
                                        available_days
                                        and day_name_es not in available_days
                                    ):
                                        validation_errors.append(
                                            f"❌ {pub.place_name} no está disponible los {day_name_es} "
                                            f"(día {day_number} - {current_date.strftime('%d/%m/%y')}). "
                                            f"Días disponibles: {', '.join(available_days)}"
                                        )

                                    available_hours = pub.available_hours or []
                                    if available_hours:
                                        time_available = False
                                        for time_range in available_hours:
                                            start_time, end_time = time_range.split("-")
                                            start_minutes = _time_to_minutes(start_time)
                                            end_minutes = _time_to_minutes(end_time)
                                            slot_minutes = _time_to_minutes(time_slot)

                                            if (
                                                start_minutes
                                                <= slot_minutes
                                                <= end_minutes
                                            ):
                                                time_available = True
                                                break

                                        if not time_available:
                                            validation_errors.append(
                                                f"❌ {pub.place_name} no está disponible a las {time_slot}. "
                                                f"Horarios disponibles: {', '.join(available_hours)}"
                                            )

        if request.budget > 0 and total_cost > request.budget:
            validation_errors.append(
                f"💰 Presupuesto excedido: Costo total ${total_cost:.2f} USD > Presupuesto ${request.budget:.2f} USD. "
                f"Exceso: ${total_cost - request.budget:.2f} USD"
            )
        elif request.budget <= 0 and total_cost > 0:
            validation_errors.append(
                f"💰 Presupuesto requerido: El itinerario tiene un costo de ${total_cost:.2f} USD pero no se especificó presupuesto"
            )

        if validation_errors:
            error_message = (
                "❌ NO ES POSIBLE GUARDAR EL ITINERARIO\n\nProblemas encontrados:\n\n"
                + "\n\n".join(validation_errors)
            )
            error_message += f"\n\n💡 Por favor corrige estos problemas y vuelve a intentar guardar el itinerario."

            raise HTTPException(status_code=400, detail=error_message)

            if total_cost > request.budget:
                budget_warning = f"\n⚠️ ADVERTENCIA DE PRESUPUESTO:\nCosto estimado: ${total_cost:.2f} USD\nPresupuesto: ${request.budget:.2f} USD\nExceso: ${total_cost - request.budget:.2f} USD\n"
            else:
                budget_warning = f"\n✅ PRESUPUESTO VALIDADO:\nCosto estimado: ${total_cost:.2f} USD\nPresupuesto: ${request.budget:.2f} USD\nDisponible: ${request.budget - total_cost:.2f} USD\n"
        else:
            budget_warning = ""

        itinerary = models.Itinerary(
            destination=request.destination,
            start_date=datetime.fromisoformat(request.start_date).date(),
            end_date=datetime.fromisoformat(request.end_date).date(),
            budget=request.budget,
            cant_persons=request.cant_persons,
            trip_type="personalizado",
            user_id=current_user.id,
            status="completed",
            generated_itinerary=_format_custom_itinerary(
                request.itinerary_data, request.start_date
            )
            + budget_warning,
        )

        db.add(itinerary)
        db.commit()
        db.refresh(itinerary)

        print(f"✅ [DEBUG] Itinerario guardado en BD:")
        print(f"  - ID: {itinerary.id}")
        print(f"  - Personas en BD: {itinerary.cant_persons}")
        print(f"  - Presupuesto en BD: {itinerary.budget}")
        print(f"  - Destino en BD: {itinerary.destination}")

        publications = []

        if publication_ids:
            publications = (
                db.query(models.Publication)
                .filter(models.Publication.id.in_(publication_ids))
                .all()
            )
            itinerary.publication_ids = list(publication_ids)

        db.commit()

        response_obj = schemas.ItineraryOut(
            id=itinerary.id,
            destination=itinerary.destination,
            start_date=itinerary.start_date.isoformat(),
            end_date=itinerary.end_date.isoformat(),
            budget=itinerary.budget,
            cant_persons=itinerary.cant_persons,
            trip_type=itinerary.trip_type,
            user_id=itinerary.user_id,
            status=itinerary.status,
            created_at=itinerary.created_at.isoformat(),
            generated_itinerary=itinerary.generated_itinerary,
            publications=[
                schemas.PublicationOut(
                    id=pub.id,
                    place_name=pub.place_name,
                    country=pub.country,
                    province=pub.province,
                    city=pub.city,
                    address=pub.address,
                    description=getattr(pub, "description", None),
                    status=pub.status,
                    created_by_user_id=pub.created_by_user_id,
                    created_at=pub.created_at.isoformat() if pub.created_at else None,
                    photos=[ph.url for ph in pub.photos] if pub.photos else [],
                    categories=(
                        [cat.slug for cat in pub.categories] if pub.categories else []
                    ),
                    rating_avg=getattr(pub, "rating_avg", 0.0) or 0.0,
                    rating_count=getattr(pub, "rating_count", 0) or 0,
                    continent=getattr(pub, "continent", None),
                    climate=getattr(pub, "climate", None),
                    activities=getattr(pub, "activities", None) or [],
                    cost_per_day=getattr(pub, "cost_per_day", None),
                    duration_min=getattr(pub, "duration_min", None),
                    available_days=getattr(pub, "available_days", None) or [],
                    available_hours=getattr(pub, "available_hours", None) or [],
                )
                for pub in publications
            ],
        )

        print(f"📤 [DEBUG] Respuesta enviada:")
        print(f"  - ID: {response_obj.id}")
        print(f"  - Personas en respuesta: {response_obj.cant_persons}")
        print(f"  - Presupuesto en respuesta: {response_obj.budget}")

        return response_obj

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear itinerario personalizado: {str(e)}",
        )


def _format_custom_itinerary(itinerary_data: dict, start_date: str) -> str:
    """
    Formatea los datos del itinerario personalizado en un texto legible
    con horarios reales de inicio y fin de actividades
    """
    result = []

    start_date_obj = datetime.fromisoformat(start_date).date()

    day_keys = sorted(
        [k for k in itinerary_data.keys() if k.startswith("day_")],
        key=lambda x: int(x.split("_")[1]),
    )

    for day_counter, day_key in enumerate(day_keys, 1):
        day_data = itinerary_data[day_key]

        from datetime import timedelta

        current_date = start_date_obj + timedelta(days=day_counter - 1)
        date_formatted = current_date.strftime("%d/%m/%y")
        day_name = current_date.strftime("%A")

        day_names_es = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo",
        }
        day_name_es = day_names_es.get(day_name, day_name)

        result.append(f"═══════════════════════════════════════════════════")
        result.append(f"DÍA {day_counter} - {day_name_es}, {date_formatted}")
        result.append(f"═══════════════════════════════════════════════════")
        result.append("")

        daily_activities = []

        periods = ["morning", "afternoon", "evening"]
        time_slots = {
            "morning": [
                "06:00",
                "06:30",
                "07:00",
                "07:30",
                "08:00",
                "08:30",
                "09:00",
                "09:30",
                "10:00",
                "10:30",
                "11:00",
                "11:30",
            ],
            "afternoon": [
                "12:00",
                "12:30",
                "13:00",
                "13:30",
                "14:00",
                "14:30",
                "15:00",
                "15:30",
                "16:00",
                "16:30",
                "17:00",
                "17:30",
            ],
            "evening": [
                "18:00",
                "18:30",
                "19:00",
                "19:30",
                "20:00",
                "20:30",
                "21:00",
                "21:30",
                "22:00",
                "22:30",
                "23:00",
                "23:30",
            ],
        }

        all_time_slots = []
        for period in periods:
            if period in day_data:
                for time_slot in time_slots[period]:
                    if time_slot in day_data[period]:
                        activity = day_data[period][time_slot]
                        all_time_slots.append(
                            {"time": time_slot, "activity": activity, "period": period}
                        )

        processed_times = set()

        for slot_info in all_time_slots:
            time_slot = slot_info["time"]
            activity = slot_info["activity"]

            if activity and time_slot not in processed_times:
                if not activity.get("is_continuation", False):
                    start_time = time_slot
                    duration_min = activity.get("duration_min", 120)

                    start_minutes = _time_to_minutes(start_time)
                    end_minutes = start_minutes + duration_min
                    end_time = _minutes_to_time(end_minutes)

                    place_name = activity.get("place_name", "Actividad")

                    daily_activities.append(
                        {
                            "start_time": start_time,
                            "end_time": end_time,
                            "place_name": place_name,
                            "start_minutes": start_minutes,
                        }
                    )

                    slots_needed = (duration_min + 29) // 30
                    for i in range(slots_needed):
                        slot_minutes = start_minutes + (i * 30)
                        slot_time = _minutes_to_time(slot_minutes)
                        processed_times.add(slot_time)

        daily_activities.sort(key=lambda x: x["start_minutes"])

        current_period = None
        period_labels = {
            "morning": "🌅 MAÑANA (6:00 - 12:00)",
            "afternoon": "🌞 TARDE (12:00 - 18:00)",
            "evening": "🌙 NOCHE (18:00 - 23:00)",
        }

        for activity in daily_activities:
            activity_period = _get_period_for_time(activity["start_time"])

            if activity_period != current_period:
                if current_period is not None:
                    result.append("")
                result.append(period_labels[activity_period])
                current_period = activity_period

            result.append(
                f"• {activity['start_time']} - {activity['end_time']} | {activity['place_name']}"
            )

        if daily_activities:
            result.append("")
        else:
            result.append("Sin actividades programadas")
            result.append("")

    return "\n".join(result)


def _time_to_minutes(time_str: str) -> int:
    """Convierte un tiempo HH:MM a minutos desde medianoche"""
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes


def _minutes_to_time(minutes: int) -> str:
    """Convierte minutos desde medianoche a formato HH:MM"""
    minutes = min(minutes, 23 * 60 + 59)
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def _get_period_for_time(time_str: str) -> str:
    """Determina el período del día para un tiempo dado"""
    minutes = _time_to_minutes(time_str)

    if 6 * 60 <= minutes < 12 * 60:
        return "morning"
    elif 12 * 60 <= minutes < 18 * 60:
        return "afternoon"
    else:
        return "evening"


def _extract_publication_ids(itinerary_data: dict) -> set:
    """
    Extrae los IDs únicos de las publicaciones del itinerary_data
    """
    publication_ids = set()

    for day_data in itinerary_data.values():
        for period_data in day_data.values():
            for activity in period_data.values():
                if activity and isinstance(activity, dict) and "id" in activity:
                    publication_ids.add(activity["id"])

    return publication_ids


@router.post("/{itinerary_id}/convert-to-custom")
def convert_ai_itinerary_to_custom(
    itinerary_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Endpoint del PASO 3: Convierte un itinerario de IA a estructura de itinerario personalizado
    Permite al usuario modificar manualmente un itinerario generado por IA
    """

    print(f"[CONVERT] Convirtiendo itinerario {itinerary_id} de IA a personalizado...")

    itinerary = (
        db.query(models.Itinerary)
        .filter(
            models.Itinerary.id == itinerary_id,
            models.Itinerary.user_id == current_user.id,
        )
        .first()
    )

    if not itinerary:
        raise HTTPException(
            status_code=404,
            detail="Itinerario no encontrado o no tienes permisos para acceder a él",
        )

    if not itinerary.generated_itinerary:
        raise HTTPException(
            status_code=400,
            detail="El itinerario no tiene contenido generado para convertir",
        )

    try:
        custom_structure = parse_ai_itinerary_to_custom_structure(
            itinerary_text=itinerary.generated_itinerary,
            start_date=str(itinerary.start_date),
        )

        validation = validate_custom_structure(custom_structure)

        if not validation["valid"]:
            print(f"[CONVERT] Errores de parsing: {validation['errors']}")
            raise HTTPException(
                status_code=422,
                detail=f"Error al parsear itinerario: {'; '.join(validation['errors'])}",
            )

        preview = generate_custom_itinerary_preview(custom_structure)

        publication_ids = []
        for day_key, day_data in custom_structure.items():
            if not day_key.startswith("day_"):
                continue
            for period_key, period_data in day_data.items():
                for time_slot, activity in period_data.items():
                    if isinstance(activity, dict) and "id" in activity:
                        publication_ids.append(activity["id"])

        publications_info = []
        if publication_ids:
            publications = (
                db.query(models.Publication)
                .filter(models.Publication.id.in_(publication_ids))
                .all()
            )

            for pub in publications:
                publications_info.append(
                    {
                        "id": pub.id,
                        "place_name": pub.place_name,
                        "city": pub.city,
                        "country": pub.country,
                    }
                )

        print(f"[CONVERT] Conversión exitosa:")
        print(f"[CONVERT]   Días: {validation['total_days']}")
        print(f"[CONVERT]   Actividades: {validation['total_activities']}")
        print(f"[CONVERT]   Publicaciones: {len(publication_ids)}")

        return {
            "success": True,
            "custom_structure": custom_structure,
            "preview": preview,
            "validation": validation,
            "original_itinerary": {
                "id": itinerary.id,
                "destination": itinerary.destination,
                "start_date": str(itinerary.start_date),
                "end_date": str(itinerary.end_date),
                "budget": itinerary.budget,
                "cant_persons": itinerary.cant_persons,
                "trip_type": itinerary.trip_type,
            },
            "publications_used": publications_info,
            "conversion_metadata": {
                "converted_from_ai": True,
                "original_itinerary_id": itinerary.id,
                "conversion_timestamp": datetime.now().isoformat(),
                "total_days": validation["total_days"],
                "total_activities": validation["total_activities"],
            },
        }

    except Exception as e:
        print(f"[CONVERT] Error durante conversión: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error interno al convertir itinerario: {str(e)}"
        )
