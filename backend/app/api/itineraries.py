from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user
from datetime import datetime
import google.generativeai as genai
import re

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
    departure_time: str | None
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
- Organiza las actividades de forma lógica según su ubicación y categoría.
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
    """
    used_publication_ids = []
    
    if not itinerary_text or not available_publications:
        return used_publication_ids
    
    # Normalizar el texto del itinerario para búsqueda (lowercase, sin acentos)
    itinerary_lower = itinerary_text.lower()
    
    for pub in available_publications:
        publication_mentioned = False
        
        # Lista de términos a buscar para esta publicación
        search_terms = []
        
        # Agregar el nombre del lugar
        if pub.place_name:
            search_terms.append(pub.place_name.lower())
        
        # Agregar palabras clave del nombre (dividir por espacios, comas, etc.)
        if pub.place_name:
            # Extraer palabras significativas (más de 2 caracteres)
            words = re.findall(r'\b\w{3,}\b', pub.place_name.lower())
            search_terms.extend(words)
        
        # Verificar si algún término de la publicación aparece en el itinerario
        for term in search_terms:
            if term and len(term) >= 3:  # Solo buscar términos de al menos 3 caracteres
                # Buscar como palabra completa para evitar falsos positivos
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, itinerary_lower):
                    publication_mentioned = True
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
            departure_time=payload.departure_time
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
                    duration_days=getattr(pub, "duration_days", None),
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
    Obtiene todos los itinerarios del usuario actual.
    """
    itineraries = db.query(models.Itinerary).filter(
        models.Itinerary.user_id == current_user.id
    ).order_by(models.Itinerary.created_at.desc()).all()
    
    # Obtener IDs de favoritos del usuario actual
    favorite_ids = {
        fav.publication_id
        for fav in db.query(models.Favorite).filter(models.Favorite.user_id == current_user.id).all()
    }
    
    result = []
    for it in itineraries:
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
                    duration_days=getattr(pub, "duration_days", None),
                    is_favorite=pub.id in favorite_ids
                ))
        
        result.append(schemas.ItineraryOut(
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
            generated_itinerary=it.generated_itinerary,
            status=it.status,
            created_at=it.created_at.isoformat(),
            publications=publication_list
        ))
    
    return result


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
                duration_days=getattr(pub, "duration_days", None),
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