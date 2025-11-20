from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user
from ..models import Itinerary, SavedItinerary
from datetime import datetime
import google.generativeai as genai
import re
from ..utils.mailer import send_email_html
from pydantic import BaseModel, EmailStr
import html
from datetime import datetime, date

router = APIRouter(prefix="/api/itineraries", tags=["itineraries"])

# Configurar Gemini (la API key debe estar en variable de entorno)
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
    comments: str | None
) -> str:
    """Construye el prompt para la IA basado en los parámetros del usuario y las publicaciones disponibles"""
    
    # Construir lista de lugares/actividades disponibles
    places_info = []
    for pub in publications:
        place_details = f"- {pub.place_name}"
        if pub.address:
            place_details += f" ({pub.address})"
        if pub.rating_avg and pub.rating_avg > 0:
            place_details += f" - Rating: {pub.rating_avg:.1f}⭐"
        if pub.categories:
            cats = ", ".join([cat.slug for cat in pub.categories])
            place_details += f" - Categorías: {cats}"
        if hasattr(pub, 'duration_min') and pub.duration_min:
            if pub.duration_min < 60:
                place_details += f" - Duración: {pub.duration_min} min"
            else:
                hours = pub.duration_min / 60
                place_details += f" - Duración: {hours:.1f}h"
        places_info.append(place_details)
    
    places_list = "\n".join(places_info) if places_info else "No hay lugares disponibles."
    
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
    
    # Calcular cantidad de lugares disponibles y días del viaje
    num_places = len(publications)
    from datetime import datetime as dt
    start_dt = dt.strptime(start_date, "%Y-%m-%d")
    end_dt = dt.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days + 1
    
    # Determinar cuántos días se pueden generar (máximo 1 día por lugar disponible)
    max_days_possible = num_places
    days_to_generate = min(total_days, max_days_possible)
    
    warning_message = ""
    if num_places < total_days:
        warning_message = f"\n⚠️ IMPORTANTE: Solo hay {num_places} lugar(es) disponible(s) para este destino, pero el viaje es de {total_days} días. GENERA SOLO {days_to_generate} DÍA(S) DE ITINERARIO (1 día por cada lugar disponible).\n"
    
    prompt += f"""
LUGARES Y ACTIVIDADES DISPONIBLES (DEBES USAR SOLO ESTOS):
{places_list}
{warning_message}
RESTRICCIONES CRÍTICAS:
- SOLO podés usar los lugares listados arriba. No inventes lugares ni uses información externa.
- Si hay {num_places} lugar(es) disponible(s) y el viaje dura {total_days} días, GENERA SOLO {days_to_generate} DÍA(S) DE ITINERARIO.
- REGLA: Genera 1 día de itinerario por cada lugar disponible (máximo).
- Si hay menos lugares que días solicitados, MUESTRA ESTE AVISO AL INICIO: "⚠️ AVISO: Se encontraron solo {num_places} publicación(es) para generar el itinerario de {destination}. Se muestra itinerario de {days_to_generate} día(s) con los lugares disponibles."
- IMPORTANTE: Considera la duración estimada de cada actividad/lugar para planificar horarios realistas.
- Para lugares con duración específica, respeta ese tiempo en tu planificación.
- Organiza las actividades de forma lógica según su ubicación, categoría y duración.
- No incluyas transporte ni vuelos. Solo actividades.
- Podés repetir el mismo lugar varias veces en el mismo día para diferentes actividades.

- Formato de salida:
Organiza el itinerario por días de la siguiente manera:

═══════════════════════════════════════════════════
DÍA 1 - [FECHA]
═══════════════════════════════════════════════════

🌅 MAÑANA (6:00 - 12:00)
• 08:00 - Desayuno en [lugar de la lista]
• 09:30 - [Actividad usando lugares de la lista]
• 11:00 - [Actividad usando lugares de la lista]

🌞 TARDE (12:00 - 18:00)
• 12:30 - Almuerzo en [lugar de la lista]
• 14:00 - [Actividad usando lugares de la lista]
• 16:00 - [Actividad usando lugares de la lista]

🌙 NOCHE (18:00 - 23:00)
• 19:00 - [Actividad usando lugares de la lista]
• 20:30 - Cena en [lugar de la lista]
• 22:00 - [Actividad opcional usando lugares de la lista]

(Repetir este formato para cada día del viaje)

IMPORTANTE:
- Usa ÚNICAMENTE los lugares de la lista proporcionada.
- Incluye actividades realistas y variadas según el estilo del viaje.
- Respeta el presupuesto indicado.
- Usa emojis para hacer más visual el itinerario.
- Solo muestra el itinerario, sin introducción ni conclusión."""
    
    return prompt


def extract_used_publications(itinerary_text: str, available_publications: list) -> list:
    """
    Analiza el texto del itinerario generado y extrae solo las publicaciones que fueron realmente mencionadas.
    Excluye menciones negativas o de exclusión. Usa criterios más estrictos para evitar falsos positivos.
    """
    used_publication_ids = []
    
    if not itinerary_text or not available_publications:
        return used_publication_ids
    
    # Normalizar el texto del itinerario para búsqueda (lowercase, sin acentos)
    itinerary_lower = itinerary_text.lower()
    
    # Palabras que indican recomendación positiva
    positive_indicators = [
        'visitar', 'ir a', 'conocer', 'recorrer', 'pasear por', 'disfrutar',
        'parada en', 'almorzar en', 'cenar en', 'hospedarse en', 'quedarse en',
        'recomiendo', 'sugiero', 'incluir', 'ver', 'explorar', 'caminar por',
        'día en', 'mañana en', 'tarde en', 'noche en'
    ]
    
    for pub in available_publications:
        publication_mentioned = False
        
        # Lista de términos a buscar para esta publicación
        search_terms = []
        
        # Agregar el nombre completo del lugar
        if pub.place_name and len(pub.place_name) >= 4:
            search_terms.append(pub.place_name.lower())
        
        # Solo agregar palabras individuales si el nombre es largo (>15 caracteres)
        # y las palabras son significativas (>4 caracteres)
        if pub.place_name and len(pub.place_name) > 15:
            words = re.findall(r'\b\w{5,}\b', pub.place_name.lower())
            search_terms.extend(words)
        
        # Verificar si algún término de la publicación aparece en el itinerario
        for term in search_terms:
            if term and len(term) >= 4:  # Solo buscar términos de al menos 4 caracteres
                # Buscar como palabra completa para evitar falsos positivos
                pattern = r'\b' + re.escape(term) + r'\b'
                
                # Buscar todas las ocurrencias del término
                matches = list(re.finditer(pattern, itinerary_lower))
                
                for match in matches:
                    # Obtener contexto más amplio alrededor de la coincidencia (±80 caracteres)
                    start_idx = max(0, match.start() - 80)
                    end_idx = min(len(itinerary_lower), match.end() + 80)
                    context = itinerary_lower[start_idx:end_idx]
                    
                    # Palabras que indican exclusión o mención negativa
                    negative_indicators = [
                        'no ', 'sin ', 'excluir', 'evitar', 'omitir', 'no incluí', 'no incluyo',
                        'no recomiendo', 'no visitaremos', 'no iremos', 'no quería', 'no quiero',
                        'excepto', 'menos', 'salvo', 'no consideré', 'descartamos', 'porque no',
                        'no está', 'no hay', 'no encontré', 'no tengo', 'falta', 'ausencia de'
                    ]
                    
                    # Verificar si hay indicadores negativos en el contexto
                    is_negative_mention = any(neg in context for neg in negative_indicators)
                    
                    # Verificar si hay indicadores positivos en el contexto
                    has_positive_indicator = any(pos in context for pos in positive_indicators)
                    
                    # Solo considerar como uso positivo si:
                    # 1. No hay indicadores negativos
                    # 2. Hay indicadores positivos o el contexto sugiere uso
                    if not is_negative_mention and (has_positive_indicator or 'itinerario' in context or 'programa' in context):
                        publication_mentioned = True
                        print(f"[ITINERARY DEBUG] Contexto positivo para {pub.place_name}: '{context.strip()}'")
                        break
                    else:
                        print(f"[ITINERARY DEBUG] Contexto ignorado para {pub.place_name}: '{context.strip()}'")
                
                if publication_mentioned:
                    break
        
        if publication_mentioned:
            used_publication_ids.append(pub.id)
            print(f"[ITINERARY DEBUG] Publicación USADA en itinerario: {pub.place_name}")
        else:
            print(f"[ITINERARY DEBUG] Publicación NO usada en itinerario: {pub.place_name}")
    
    return used_publication_ids


@router.post("/request", response_model=schemas.ItineraryOut)
def request_itinerary(
    payload: schemas.ItineraryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Endpoint para que un usuario básico solicite la generación de un itinerario con IA.
    Solo usuarios con rol 'user' pueden solicitar itinerarios.
    """
    
    # Verifica usuario (admin no puede hacer itinerarios, pero sí users y premium)
    if current_user.role not in ["user", "premium"]:
        raise HTTPException(
            status_code=403,
            detail="Solo usuarios básicos y premium pueden solicitar itinerarios"
        )
    
    # Validar fechas
    start = payload.start_date if isinstance(payload.start_date, datetime) else payload.start_date
    end = payload.end_date if isinstance(payload.end_date, datetime) else payload.end_date
    
    if end < start:
        raise HTTPException(
            status_code=400,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    # Registro dle itinerario en la bdd con status pendiente
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
        status="pending"
    )
    
    db.add(itinerary)
    db.commit()
    db.refresh(itinerary)
    
    # Buscar publicaciones relacionadas con el destino
    destination_lower = payload.destination.lower()
    
    # Log para debug: ver qué estamos buscando
    print(f"[ITINERARY DEBUG] Buscando publicaciones para destino: '{payload.destination}' (normalizado: '{destination_lower}')")
    
    # Primero, ver todas las publicaciones aprobadas
    all_approved = db.query(models.Publication).filter(
        models.Publication.status == "approved"
    ).all()
    print(f"[ITINERARY DEBUG] Total publicaciones aprobadas: {len(all_approved)}")
    for pub in all_approved:
        print(f"[ITINERARY DEBUG] - {pub.place_name} | País: {pub.country} | Provincia: {pub.province} | Ciudad: {pub.city}")
    
    # Hacer búsqueda más específica y restrictiva
    from sqlalchemy import or_, and_
    
    # Primero intentar con coincidencia exacta en ciudad o país
    exact_match_pubs = db.query(models.Publication).filter(
        models.Publication.status == "approved",
        or_(
            models.Publication.city.ilike(f"%{destination_lower}%"),
            models.Publication.province.ilike(f"%{destination_lower}%"),
            models.Publication.country.ilike(f"%{destination_lower}%"),
            models.Publication.address.ilike(f"%{destination_lower}%")
        )
    ).all()
    
    print(f"[ITINERARY DEBUG] Búsqueda exacta encontró: {len(exact_match_pubs)} publicaciones")
    
    # Si no encontramos con búsqueda exacta, dividir en palabras clave
    if len(exact_match_pubs) == 0:
        print(f"[ITINERARY DEBUG] No se encontró con búsqueda exacta, probando con palabras clave...")
        import re
        keywords = [word.strip() for word in re.split(r'[,;\s]+', destination_lower) if word.strip() and len(word.strip()) >= 4]
        print(f"[ITINERARY DEBUG] Palabras clave extraídas (>=4 chars): {keywords}")
        
        if keywords:
            # Buscar que TODAS las palabras clave importantes estén presentes (AND en lugar de OR)
            conditions = []
            for keyword in keywords:
                keyword_conditions = or_(
                    models.Publication.city.ilike(f"%{keyword}%"),
                    models.Publication.province.ilike(f"%{keyword}%"),
                    models.Publication.country.ilike(f"%{keyword}%"),
                    models.Publication.address.ilike(f"%{keyword}%")
                )
                conditions.append(keyword_conditions)
            
            # Usar AND entre las palabras clave para ser más restrictivo
            if len(conditions) == 1:
                final_condition = conditions[0]
            else:
                final_condition = and_(*conditions)
            
            publications = db.query(models.Publication).filter(
                models.Publication.status == "approved",
                final_condition
            ).all()
        else:
            publications = []
    else:
        publications = exact_match_pubs
    
    print(f"[ITINERARY DEBUG] Publicaciones encontradas: {len(publications)}")
    for pub in publications:
        print(f"[ITINERARY DEBUG] Match: {pub.place_name} ({pub.city}, {pub.country})")
    
    # Verificar si hay publicaciones
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
            created_at=itinerary.created_at.isoformat()
        )
    
    # Generar el itinerario con IA usando las publicaciones encontradas
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
            comments=payload.comments
        )
        
        # Llamar a la API de Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Guardar el resultado
        itinerary.generated_itinerary = response.text
        itinerary.status = "completed"
        
        # Extraer solo las publicaciones que fueron realmente mencionadas en el itinerario
        used_publication_ids = extract_used_publications(response.text, publications)
        itinerary.publication_ids = used_publication_ids
        
        print(f"[ITINERARY DEBUG] Publicaciones disponibles: {len(publications)}")
        print(f"[ITINERARY DEBUG] Publicaciones realmente usadas: {len(used_publication_ids)}")
        
    except Exception as e:
        itinerary.status = "failed"
        itinerary.generated_itinerary = f"Error al generar itinerario: {str(e)}"
    
    db.commit()
    db.refresh(itinerary)
    
    # Obtener IDs de favoritos del usuario actual
    favorite_ids = {
        fav.publication_id
        for fav in db.query(models.Favorite).filter(models.Favorite.user_id == current_user.id).all()
    }

    # Preparar lista de publicaciones para la respuesta
    publication_list = []
    if itinerary.publication_ids:
        for pub in publications:
            if pub.id in itinerary.publication_ids:
                # Obtener categorías
                categories = [cat.slug for cat in pub.categories] if pub.categories else []
                # Obtener fotos
                photos = [photo.url for photo in pub.photos] if pub.photos else []
                
                publication_list.append(schemas.PublicationOut(
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
                    is_favorite=pub.id in favorite_ids
                ))
    
    # Convertir a schema de salida
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
        publications=publication_list
    )


@router.get("/my-itineraries", response_model=list[schemas.ItineraryOut])
def get_my_itineraries(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene todos los itinerarios del usuario actual, incluyendo los itinerarios guardados.
    """
    # Itinerarios propios
    own_itineraries = db.query(models.Itinerary).filter(
        models.Itinerary.user_id == current_user.id
    ).order_by(models.Itinerary.created_at.desc()).all()
    
    # Itinerarios guardados
    saved_itineraries = db.query(SavedItinerary).filter(
        SavedItinerary.user_id == current_user.id
    ).order_by(SavedItinerary.saved_at.desc()).all()
    
    # Obtener IDs de favoritos del usuario actual
    favorite_ids = {
        fav.publication_id
        for fav in db.query(models.Favorite).filter(models.Favorite.user_id == current_user.id).all()
    }
    
    # Combinar todos los itinerarios
    all_itineraries = []
    
    # Procesar itinerarios propios
    for it in own_itineraries:
        # Obtener publicaciones si existen IDs guardados
        publication_list = []
        if it.publication_ids:
            pubs = db.query(models.Publication).filter(
                models.Publication.id.in_(it.publication_ids)
            ).all()
            
            for pub in pubs:
                categories = [cat.slug for cat in pub.categories] if pub.categories else []
                photos = [photo.url for photo in pub.photos] if pub.photos else []
                
                publication_list.append(schemas.PublicationOut(
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
                    is_favorite=pub.id in favorite_ids
                ))
        
        all_itineraries.append(schemas.ItineraryOut(
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
            publications=publication_list
        ))
    
    # Procesar itinerarios guardados
    for saved in saved_itineraries:
        original_it = saved.original_itinerary
        # Obtener publicaciones si existen IDs guardados
        publication_list = []
        if original_it.publication_ids:
            pubs = db.query(models.Publication).filter(
                models.Publication.id.in_(original_it.publication_ids)
            ).all()
            
            for pub in pubs:
                categories = [cat.slug for cat in pub.categories] if pub.categories else []
                photos = [photo.url for photo in pub.photos] if pub.photos else []
                
                publication_list.append(schemas.PublicationOut(
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
                    is_favorite=pub.id in favorite_ids
                ))
        
        all_itineraries.append(schemas.ItineraryOut(
            id=saved.id,  # Usar ID del saved itinerary
            user_id=original_it.user_id,  # Mantener el ID del creador original
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
            status="saved",  # Indicador de que es un itinerario guardado
            created_at=saved.saved_at.isoformat(),  # Usar fecha de guardado
            publications=publication_list
        ))
    
    return all_itineraries


@router.get("/{itinerary_id}", response_model=schemas.ItineraryOut)
def get_itinerary(
    itinerary_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene un itinerario específico por ID.
    Solo puede ver sus propios itinerarios.
    """
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id == itinerary_id
    ).first()
    
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    
    # Verificar que el itinerario pertenece al usuario
    if itinerary.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este itinerario")
    
    # Obtener IDs de favoritos del usuario actual
    favorite_ids = {
        fav.publication_id
        for fav in db.query(models.Favorite).filter(models.Favorite.user_id == current_user.id).all()
    }
    
    # Obtener publicaciones si existen IDs guardados
    publication_list = []
    if itinerary.publication_ids:
        pubs = db.query(models.Publication).filter(
            models.Publication.id.in_(itinerary.publication_ids)
        ).all()
        
        for pub in pubs:
            categories = [cat.slug for cat in pub.categories] if pub.categories else []
            photos = [photo.url for photo in pub.photos] if pub.photos else []
            
            publication_list.append(schemas.PublicationOut(
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
                is_favorite=pub.id in favorite_ids
            ))
    
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
        publications=publication_list
    )


@router.delete("/{itinerary_id}")
def delete_itinerary(
    itinerary_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Elimina un itinerario específico por ID.
    Solo puede eliminar sus propios itinerarios.
    """
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id == itinerary_id
    ).first()
    
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    
    # Verificar que el itinerario pertenece al usuario
    if itinerary.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este itinerario")
    
    # Eliminar el itinerario
    db.delete(itinerary)
    db.commit()
    
    return {"message": "Itinerario eliminado exitosamente", "id": itinerary_id}


class SharePayload(BaseModel):
    to: EmailStr
    note: str | None = None  # opcional, mensaje corto del remitente

def _abs_url(path: str, base: str) -> str:
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = (base or "").rstrip("/")
    path = path if path.startswith("/") else f"/{path}"
    return f"{base}{path}"

def _build_itinerary_email_html(itinerary: models.Itinerary, pubs: list[models.Publication]) -> str:
    app_url = os.getenv("APP_PUBLIC_URL", "http://localhost:8000")
    brand = os.getenv("APP_BRAND_NAME", "Plan&Go")

    # Encabezado
    title = f"Itinerario: {itinerary.destination}"
    start = _to_date(itinerary.start_date)
    end = _to_date(itinerary.end_date)
    date_range = f"{_fmt_date_ymd(itinerary.start_date)} → {_fmt_date_ymd(itinerary.end_date)}"
    status_pill = itinerary.status.capitalize()
    budget = f"US$ {itinerary.budget}"
    persons = f"{itinerary.cant_persons}"

    # Texto IA (lo escapamos y convertimos \n en <br>)
    gen_html = html.escape(itinerary.generated_itinerary or "").replace("\n", "<br />")

    # Tarjetas de lugares
    cards_html = ""
    for p in pubs:
        photo_url = ""
        if getattr(p, "photos", None):
            photo_url = _abs_url(p.photos[0].url, app_url)
        address = f"{p.address}, {p.city}, {p.province}, {p.country}"
        rating = f"{getattr(p, 'rating_avg', 0.0):.1f} ⭐ ({getattr(p, 'rating_count', 0)})"
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
    # 🔒 Solo premium
    if current_user.role != "premium":
        raise HTTPException(
            status_code=403,
            detail="Función disponible solo para usuarios premium."
        )

    it = db.query(models.Itinerary).filter(models.Itinerary.id == itinerary_id).first()
    if not it:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")

    if it.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para compartir este itinerario")

    # Publicaciones vinculadas al itinerario (si quedaron guardadas)
    pubs: list[models.Publication] = []
    if getattr(it, "publication_ids", None):
        pubs = db.query(models.Publication).filter(models.Publication.id.in_(it.publication_ids)).all()

    html_body = _build_itinerary_email_html(it, pubs)
    subject = f"Tu itinerario: {it.destination} ({_fmt_date_ymd(it.start_date)} → {_fmt_date_ymd(it.end_date)})"

    # Nota opcional del remitente
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

    # devolvemos dicts serializables
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
        # intenta ISO primero (YYYY-MM-DD[THH:MM:SS])
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            # fallback a solo fecha
            return datetime.strptime(value, "%Y-%m-%d").date()
    # último recurso: devolvelo tal cual; str() no romperá
    return value



def _fmt_date_ymd(value) -> str:
    """Devuelve la fecha como 'YYYY-MM-DD' aceptando date/datetime/str ISO."""
    if isinstance(value, datetime):
        d = value.date()
    elif isinstance(value, date):
        d = value
    elif isinstance(value, str):
        # intenta ISO 'YYYY-MM-DD' o 'YYYY-MM-DDTHH:MM:SS'
        try:
            d = datetime.fromisoformat(value).date()
        except ValueError:
            try:
                d = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return str(value)  # último recurso
    else:
        return str(value)
    return d.strftime("%Y-%m-%d")


@router.post("/save", response_model=schemas.SavedItineraryOut)
def save_itinerary(
    payload: schemas.SavedItineraryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Guardar una copia del itinerario de otro usuario en mis itinerarios guardados
    """
    
    # Verificar que el itinerario original existe
    original_itinerary = db.query(Itinerary).filter(
        Itinerary.id == payload.original_itinerary_id
    ).first()
    
    if not original_itinerary:
        raise HTTPException(
            status_code=404,
            detail="Itinerario no encontrado"
        )
    
    # Verificar que no es el propio itinerario
    if original_itinerary.user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="No puedes guardar tu propio itinerario"
        )
    
    # Verificar si ya fue guardado por este usuario
    existing_saved = db.query(SavedItinerary).filter(
        SavedItinerary.user_id == current_user.id,
        SavedItinerary.original_itinerary_id == payload.original_itinerary_id
    ).first()
    
    if existing_saved:
        raise HTTPException(
            status_code=400,
            detail="Ya tienes este itinerario guardado"
        )
    
    # Crear la copia guardada
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
        original_author_id=original_itinerary.user_id
    )
    
    db.add(saved_itinerary)
    db.commit()
    db.refresh(saved_itinerary)
    
    # Obtener publicaciones si existen
    publications = []
    if saved_itinerary.publication_ids:
        publications = db.query(models.Publication).filter(
            models.Publication.id.in_(saved_itinerary.publication_ids)
        ).all()
    
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
                categories=pub.categories or []
            ) for pub in publications
        ]
    )


@router.get("/saved")
def get_saved_itineraries(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtener todos los itinerarios guardados por el usuario actual
    """
    saved_itineraries = db.query(SavedItinerary).filter(
        SavedItinerary.user_id == current_user.id
    ).order_by(SavedItinerary.saved_at.desc()).all()
    
    result = []
    for saved in saved_itineraries:
        # Obtener publicaciones si existen
        publications = []
        if saved.publication_ids:
            publications = db.query(models.Publication).filter(
                models.Publication.id.in_(saved.publication_ids)
            ).all()
        
        result.append({
            "id": saved.id,
            "user_id": saved.user_id,
            "original_itinerary_id": saved.original_itinerary_id,
            "destination": saved.destination,
            "start_date": saved.start_date.isoformat() if saved.start_date else None,
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
            "status": "saved",  # Estado especial para itinerarios guardados
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
                    "created_at": pub.created_at.isoformat() if pub.created_at else None,
                    "photos": pub.photos or [],
                    "categories": pub.categories or []
                } for pub in publications
            ]
        })
    
    return result


class CustomItineraryRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    itinerary_data: dict
    type: str = "custom"


@router.post("/custom", response_model=schemas.ItineraryOut)
async def create_custom_itinerary(
    request: CustomItineraryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un itinerario personalizado donde el usuario ha seleccionado
    manualmente las actividades para cada horario
    """
    try:
        # Crear el itinerario en la base de datos
        itinerary = models.Itinerary(
            destination=request.destination,
            start_date=datetime.fromisoformat(request.start_date).date(),
            end_date=datetime.fromisoformat(request.end_date).date(),
            budget=0,  # No aplica para itinerarios personalizados
            cant_persons=1,  # Valor por defecto
            trip_type="personalizado",
            user_id=current_user.id,
            status="completed",  # Ya está listo
            generated_itinerary=_format_custom_itinerary(request.itinerary_data),
            user_preferences="Itinerario personalizado creado manualmente"
        )
        
        db.add(itinerary)
        db.commit()
        db.refresh(itinerary)
        
        # Extraer IDs de publicaciones del itinerary_data y crear relaciones
        publication_ids = _extract_publication_ids(request.itinerary_data)
        publications = []
        
        for pub_id in publication_ids:
            pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
            if pub:
                publications.append(pub)
                # Crear la relación many-to-many
                itinerary.publications.append(pub)
        
        db.commit()
        
        return schemas.ItineraryOut(
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
                    "created_at": pub.created_at.isoformat() if pub.created_at else None,
                    "photos": [ph.url for ph in pub.photos] if pub.photos else [],
                    "categories": [{"name": cat.name, "slug": cat.slug} for cat in pub.categories] if pub.categories else [],
                    "rating_avg": getattr(pub, 'rating_avg', 0.0) or 0.0,
                    "rating_count": getattr(pub, 'rating_count', 0) or 0,
                    "is_favorite": False  # TODO: calcular si es favorito del usuario actual
                } for pub in publications
            ]
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear itinerario personalizado: {str(e)}"
        )


def _format_custom_itinerary(itinerary_data: dict) -> str:
    """
    Formatea los datos del itinerario personalizado en un texto legible
    similar al formato de la IA
    """
    result = []
    
    for day_key in sorted(itinerary_data.keys()):
        day_data = itinerary_data[day_key]
        
        # Convertir fecha a formato legible
        try:
            date_obj = datetime.fromisoformat(day_key).date()
            day_counter = len(result) + 1
            result.append(f"═══════════════════════════════════════════════════")
            result.append(f"DÍA {day_counter} - {date_obj.strftime('%Y-%m-%d')}")
            result.append(f"═══════════════════════════════════════════════════")
            result.append("")
        except:
            continue
        
        # Procesar cada período del día
        periods = {
            'morning': '🌅 MAÑANA (6:00 - 12:00)',
            'afternoon': '🌞 TARDE (12:00 - 18:00)',
            'evening': '🌙 NOCHE (18:00 - 23:00)'
        }
        
        for period_key, period_label in periods.items():
            if period_key not in day_data:
                continue
                
            period_data = day_data[period_key]
            has_activities = any(activity for activity in period_data.values() if activity)
            
            if has_activities:
                result.append(period_label)
                
                for time_slot in sorted(period_data.keys()):
                    activity = period_data[time_slot]
                    if activity and isinstance(activity, dict):
                        place_name = activity.get('place_name', 'Actividad')
                        result.append(f"• {time_slot} - {place_name}")
                
                result.append("")
    
    return "\n".join(result)


def _extract_publication_ids(itinerary_data: dict) -> set:
    """
    Extrae los IDs únicos de las publicaciones del itinerary_data
    """
    publication_ids = set()
    
    for day_data in itinerary_data.values():
        for period_data in day_data.values():
            for activity in period_data.values():
                if activity and isinstance(activity, dict) and 'id' in activity:
                    publication_ids.add(activity['id'])
    
    return publication_ids
