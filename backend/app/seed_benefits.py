#!/usr/bin/env python3
"""
Script para poblar la base de datos con beneficios premium para publicaciones.
"""

import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

# Ajusta las importaciones para que funcione como un script
try:
    from backend.app.db import SessionLocal
    from backend.app import models
    from backend.app.models import User, Publication, PremiumBenefit, Review, PublicationPhoto
except ImportError:
    print("Error: Ejecuta este script como un módulo desde la raíz del proyecto.")
    print("Ejemplo: python -m backend.app.seed_benefits")
    exit(1)


def get_review_authors(db: Session, default_author: User) -> list[User]:
    """Busca todos los usuarios para usarlos como autores de reseñas."""
    all_users = db.query(User).all()
    if not all_users:
        print("  > Advertencia: No se encontraron usuarios para reseñas. Usando al autor principal.")
        return [default_author]
    
    print(f"  > Encontrados {len(all_users)} usuarios para usar como autores de reseñas.")
    return all_users


def update_publication_ratings(db: Session, pub_id: int):
    """
    Recalcula y actualiza el rating_avg y rating_count de una publicación.
    """
    try:
        # Calcula el promedio (avg) y el conteo (count) de las reseñas
        avg_, count_ = db.query(func.avg(models.Review.rating), func.count(models.Review.id)) \
            .filter(models.Review.publication_id == pub_id).one()
        
        # Busca la publicación
        pub = db.query(models.Publication).filter(models.Publication.id == pub_id).first()
        if pub:
            # Actualiza los campos en el modelo Publication
            pub.rating_avg = round(float(avg_ or 0.0), 1)
            pub.rating_count = int(count_ or 0)
            db.add(pub)
            print(f"  > Ratings actualizados para pub_id={pub_id}: {pub.rating_avg} avg, {pub.rating_count} count")
    except Exception as e:
        print(f"  > ERROR actualizando ratings para pub_id={pub_id}: {e}")


def create_premium_benefits(db: Session):
    """Crea beneficios premium para publicaciones existentes."""
    print("🎁 Creando beneficios premium...")

    # Obtener publicaciones por categoría
    restaurants = db.query(Publication).join(Publication.categories).filter(
        models.Category.slug == "gastronomia"
    ).all()
    
    hotels = db.query(Publication).join(Publication.categories).filter(
        models.Category.slug == "hotel"
    ).all()
    
    attractions = db.query(Publication).join(Publication.categories).filter(
        models.Category.slug.in_(["actividad", "aventura", "cultura"])
    ).all()

    benefit_count = 0

    # Beneficios para restaurantes y bares
    restaurant_benefits = [
        {
            "title": "10% descuento en toda la carta",
            "description": "Descuento aplicable en comidas y bebidas del menú principal",
            "discount_percentage": 10,
            "benefit_type": "discount",
            "terms_conditions": "Válido de lunes a viernes. No acumulable con otras promociones."
        },
        {
            "title": "15% descuento en cenas",
            "description": "Descuento especial para cenas después de las 19:00",
            "discount_percentage": 15,
            "benefit_type": "discount",
            "terms_conditions": "Válido únicamente para cenas. Horario: 19:00 a 23:00."
        },
        {
            "title": "Entrada gratuita",
            "description": "Entrada libre para usuarios premium",
            "discount_percentage": None,
            "benefit_type": "free_item",
            "terms_conditions": "Mostrar código QR premium en la entrada."
        },
        {
            "title": "Copa de bienvenida gratuita",
            "description": "Bebida de cortesía al llegar al establecimiento",
            "discount_percentage": None,
            "benefit_type": "free_item",
            "terms_conditions": "Una copa por mesa. Válido solo en primera visita del mes."
        },
        {
            "title": "20% descuento en vinos",
            "description": "Descuento especial en nuestra carta de vinos",
            "discount_percentage": 20,
            "benefit_type": "discount",
            "terms_conditions": "Aplica solo en vinos por copa o botella."
        }
    ]

    # Aplicar beneficios a restaurantes
    for i, restaurant in enumerate(restaurants):
        benefit_data = restaurant_benefits[i % len(restaurant_benefits)]
        
        # Verificar si ya existe el beneficio
        existing = db.query(PremiumBenefit).filter(
            PremiumBenefit.publication_id == restaurant.id
        ).first()
        
        if not existing:
            benefit = PremiumBenefit(
                publication_id=restaurant.id,
                **benefit_data
            )
            db.add(benefit)
            benefit_count += 1
            print(f"  ✅ {restaurant.place_name}: {benefit_data['title']}")

    # Beneficios para hoteles
    hotel_benefits = [
        {
            "title": "15% descuento en desayuno",
            "description": "Descuento en el desayuno buffet del hotel",
            "discount_percentage": 15,
            "benefit_type": "discount",
            "terms_conditions": "Válido para huéspedes y visitantes. Horario: 7:00 a 11:00."
        },
        {
            "title": "Upgrade gratuito de habitación",
            "description": "Mejora automática a habitación superior (sujeto a disponibilidad)",
            "discount_percentage": None,
            "benefit_type": "upgrade",
            "terms_conditions": "Sujeto a disponibilidad. Confirmar al momento del check-in."
        },
        {
            "title": "10% descuento en spa",
            "description": "Descuento en todos los servicios de spa y wellness",
            "discount_percentage": 10,
            "benefit_type": "discount",
            "terms_conditions": "Reserva previa requerida. No válido en días festivos."
        },
        {
            "title": "Wi-Fi premium gratuito",
            "description": "Acceso a internet de alta velocidad sin costo adicional",
            "discount_percentage": None,
            "benefit_type": "free_item",
            "terms_conditions": "Activación automática al mostrar membresía premium."
        },
        {
            "title": "Late check-out gratuito",
            "description": "Extensión de estadía hasta las 15:00 sin costo",
            "discount_percentage": None,
            "benefit_type": "free_item",
            "terms_conditions": "Solicitar en recepción. Sujeto a disponibilidad."
        },
        {
            "title": "20% descuento en restaurante del hotel",
            "description": "Descuento especial en el restaurante interno",
            "discount_percentage": 20,
            "benefit_type": "discount",
            "terms_conditions": "Válido para huéspedes y visitantes externos."
        }
    ]

    # Aplicar beneficios a hoteles
    for i, hotel in enumerate(hotels):
        benefit_data = hotel_benefits[i % len(hotel_benefits)]
        
        existing = db.query(PremiumBenefit).filter(
            PremiumBenefit.publication_id == hotel.id
        ).first()
        
        if not existing:
            benefit = PremiumBenefit(
                publication_id=hotel.id,
                **benefit_data
            )
            db.add(benefit)
            benefit_count += 1
            print(f"  ✅ {hotel.place_name}: {benefit_data['title']}")

    # Beneficios para atracciones y actividades
    attraction_benefits = [
        {
            "title": "20% descuento en gift shop",
            "description": "Descuento en todas las compras de la tienda de recuerdos",
            "discount_percentage": 20,
            "benefit_type": "discount",
            "terms_conditions": "No válido en artículos ya rebajados o promocionales."
        },
        {
            "title": "Entrada prioritaria",
            "description": "Evita las filas con acceso premium",
            "discount_percentage": None,
            "benefit_type": "upgrade",
            "terms_conditions": "Mostrar código QR premium en la entrada."
        },
        {
            "title": "15% descuento en entrada",
            "description": "Descuento en el precio de la entrada general",
            "discount_percentage": 15,
            "benefit_type": "discount",
            "terms_conditions": "No válido en días festivos o eventos especiales."
        },
        {
            "title": "Guía audio gratuita",
            "description": "Acceso gratuito al tour con audio guía",
            "discount_percentage": None,
            "benefit_type": "free_item",
            "terms_conditions": "Disponible en español e inglés."
        },
        {
            "title": "Fotografía gratuita",
            "description": "Una foto profesional gratuita durante tu visita",
            "discount_percentage": None,
            "benefit_type": "free_item",
            "terms_conditions": "Una foto por grupo. Entrega digital."
        },
        {
            "title": "10% descuento en tours",
            "description": "Descuento en tours guiados adicionales",
            "discount_percentage": 10,
            "benefit_type": "discount",
            "terms_conditions": "Reserva con 24 horas de anticipación."
        },
        {
            "title": "Estacionamiento gratuito",
            "description": "Parking sin costo durante tu visita",
            "discount_percentage": None,
            "benefit_type": "free_item",
            "terms_conditions": "Válido por un día. Mostrar ticket de entrada."
        }
    ]

    # Aplicar beneficios a atracciones
    for i, attraction in enumerate(attractions):
        benefit_data = attraction_benefits[i % len(attraction_benefits)]
        
        existing = db.query(PremiumBenefit).filter(
            PremiumBenefit.publication_id == attraction.id
        ).first()
        
        if not existing:
            benefit = PremiumBenefit(
                publication_id=attraction.id,
                **benefit_data
            )
            db.add(benefit)
            benefit_count += 1
            print(f"  ✅ {attraction.place_name}: {benefit_data['title']}")

    db.commit()
    print(f"\n🎉 ¡{benefit_count} beneficios premium creados exitosamente!")


def add_premium_publications(db: Session):
    """Agrega nuevas publicaciones especialmente diseñadas para tener beneficios premium."""
    print("\n🏪 Agregando publicaciones con beneficios premium...")
    
    # Buscar un usuario para crear las publicaciones
    admin_user = db.query(User).filter(User.role == "admin").first()
    if not admin_user:
        admin_user = db.query(User).first()
    
    if not admin_user:
        print("Error: No se encontraron usuarios. Crea al menos un usuario primero.")
        return

    # Obtener categorías
    cat_gastro = db.query(models.Category).filter_by(slug="gastronomia").first()
    cat_hotel = db.query(models.Category).filter_by(slug="hotel").first()
    cat_actividad = db.query(models.Category).filter_by(slug="actividad").first()
    cat_cultura = db.query(models.Category).filter_by(slug="cultura").first()

    new_publications = [
        # Restaurantes y bares con beneficios atractivos
        {
            "place_name": "La Terraza Premium",
            "description": "Restaurante de cocina internacional con vista panorámica y ambiente exclusivo para ocasiones especiales.",
            "country": "Argentina", "province": "Buenos Aires", "city": "Buenos Aires",
            "address": "Av. Corrientes 1234, Puerto Madero",
            "categories": [cat_gastro],
            "continent": "américa", "climate": "templado",
            "activities": ["gastronomia", "ciudad", "romance", "vista_panoramica"],
            "cost_per_day": None,  # Varía según consumo
            "duration_min": None,  
            "images": ["terraza_prmeium_1.jpg", "terraza_prmeium_2.jpg"],
            "reviews": [
                (5, "Vista increíble de Puerto Madero. La cena fue perfecta para nuestro aniversario."),
                (4, "Ambiente elegante y comida exquisita. El servicio podría ser un poco más rápido."),
                (5, "El mejor lugar para una cita especial. Los cócktails son arte líquido."),
                (5, "Calidad-precio excelente considerando la ubicación y la vista panorámica.")
            ]
        },
        {
            "place_name": "Wine & Dine Club",
            "description": "Bar de vinos y tapas gourmet con más de 200 etiquetas y maridajes especializados.",
            "country": "Argentina", "province": "Mendoza", "city": "Mendoza",
            "address": "Calle San Martín 567, Ciudad de Mendoza",
            "categories": [cat_gastro],
            "continent": "américa", "climate": "seco",
            "activities": ["gastronomia", "vinos", "cultura", "relax"],
            "cost_per_day": None,  # Varía según consumo
            "duration_min": None,  
            "images": ["wine_club_1.jpg", "wine_club_2.jpg"],
            "reviews": [
                (5, "El sommelier conoce cada etiqueta de memoria. Los maridajes son perfectos."),
                (5, "Gran variedad de vinos locales e internacionales. Tapas deliciosas."),
                (4, "Ambiente acogedor y selección impresionante. Los precios son razonables para la calidad."),
                (5, "Imperdible para los amantes del vino. Aprendí mucho sobre los terroirs mendocinos.")
            ]
        },
        {
            "place_name": "Asado Porteño",
            "description": "Parrilla tradicional argentina con carnes premium y ambiente familiar auténtico.",
            "country": "Argentina", "province": "Buenos Aires", "city": "San Isidro",
            "address": "Av. del Libertador 890, San Isidro",
            "categories": [cat_gastro],
            "continent": "américa", "climate": "templado",
            "activities": ["gastronomia", "familia", "tradicion", "carnes"],
            "cost_per_day": None,  # Varía según consumo
            "duration_min": None,  
            "images": ["asado_porteno_1.jpg", "asado_porteno_2.jpg"],
            "reviews": [
                (5, "El mejor bife de chorizo que probé en años. La parrilla se ve desde la mesa, espectáculo incluido."),
                (4, "Tradicional y auténtico. Las empanadas de entrada son caseras y deliciosas."),
                (5, "Ambiente familiar perfecto para domingo. El asador es un artista con las brasas."),
                (5, "Carnes de primera calidad y cocción perfecta. El chimichurri casero está brutal.")
            ]
        },
        {
            "place_name": "Café de los Artistas",
            "description": "Cafetería temática con exposiciones de arte local, ideal para trabajar o reunirse.",
            "country": "Argentina", "province": "Córdoba", "city": "Córdoba",
            "address": "Calle 27 de Abril 234, Centro",
            "categories": [cat_gastro],
            "continent": "américa", "climate": "templado",
            "activities": ["cafe", "arte", "cultura", "trabajo", "reunion"],
            "cost_per_day": None,  # Varía según consumo
            "duration_min": None,  
            "images": ["cafe_artistas_1.jpg", "cafe_artistas_2.jpg"],
            "reviews": [
                (5, "Perfecto para trabajar con laptop. WiFi excelente y el café está buenísimo."),
                (4, "Las exposiciones cambian cada mes. Me encanta el ambiente bohemio y tranquilo."),
                (5, "Los tostados artesanales son increíbles. Apoyan mucho al arte local."),
                (4, "Ideal para reuniones informales. La decoración con obras locales le da un toque único.")
            ]
        },

        # Hoteles boutique con servicios premium
        {
            "place_name": "Grand Palace Hotel & Spa",
            "description": "Hotel 5 estrellas con spa de lujo, piscina climatizada y servicio personalizado las 24 horas.",
            "country": "Argentina", "province": "Buenos Aires", "city": "Recoleta",
            "address": "Av. Alvear 1123, Recoleta",
            "categories": [cat_hotel],
            "continent": "américa", "climate": "templado",
            "activities": ["spa", "lujo", "relax", "ciudad", "cultura"],
            "cost_per_day": None,
            "duration_min": None, 
            "images": ["grand_palace_1.jpg", "grand_palace_2.jpg"],
            "reviews": [
                (5, "Lujo absoluto en el corazón de Recoleta. El spa es de otro nivel, relajación total."),
                (5, "Servicio impecable, me sentí como VIP desde el check-in. La piscina climatizada en el rooftop es increíble."),
                (4, "Habitaciones amplias y elegantes. El desayuno buffet tiene opciones para todos los gustos."),
                (5, "Ubicación perfecta para explorar museos y shopping. El concierge me organizó todo el itinerario.")
            ]
        },
        {
            "place_name": "Boutique Hotel Pampa",
            "description": "Hotel boutique con decoración regional y servicios exclusivos en el corazón de la ciudad.",
            "country": "Argentina", "province": "Salta", "city": "Salta",
            "address": "Calle Balcarce 456, Centro Histórico",
            "categories": [cat_hotel],
            "continent": "américa", "climate": "seco",
            "activities": ["cultura", "historia", "tradicion", "turismo", "relax"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["boutique_pampa_1.jpg", "boutique_pampa_2.jpg"],
            "reviews": [
                (5, "Decoración auténtica con arte regional salteño. Cada habitación cuenta una historia."),
                (4, "Ubicación excelente para recorrer el centro histórico a pie. Personal muy amable y local."),
                (5, "El desayuno incluye productos regionales deliciosos. Se siente la calidez del norte argentino."),
                (5, "Hotel pequeño pero con gran atención personalizada. Conocen todos los tours y excursiones.")
            ]
        },
        {
            "place_name": "Mountain View Resort",
            "description": "Resort de montaña con vistas espectaculares, ideal para escapadas románticas y familiares.",
            "country": "Argentina", "province": "Mendoza", "city": "Las Leñas",
            "address": "Ruta 222 Km 15, Valle de Las Leñas",
            "categories": [cat_hotel],
            "continent": "américa", "climate": "frío",
            "activities": ["montaña", "naturaleza", "romance", "familia", "aventura", "relax"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["mountain_resort_1.jpg", "mountain_resort_2.jpg"],
            "reviews": [
                (5, "Despertar con vista a las montañas nevadas no tiene precio. Resort familiar pero también romántico."),
                (5, "Las cabañas son amplias y acogedoras. Chimenea a leña y todo el confort moderno."),
                (4, "Perfecto para desconectar de la ciudad. Las actividades para niños están muy bien organizadas."),
                (5, "El restaurante del resort ofrece platos regionales con ingredientes locales. Vista espectacular desde el comedor.")
            ]
        },

        # Atracciones y actividades con experiencias premium
        {
            "place_name": "Museo Interactivo de Ciencias",
            "description": "Museo moderno con exhibiciones interactivas, planetario y talleres para toda la familia.",
            "country": "Argentina", "province": "Buenos Aires", "city": "Tigre",
            "address": "Av. Victorica 789, Puerto de Frutos",
            "categories": [cat_cultura],
            "continent": "américa", "climate": "templado",
            "activities": ["educacion", "familia", "ciencia", "tecnologia", "interactivo"],
            "cost_per_day": 25,
            "duration_min": None,  # Visita promedio 4 horas
            "images": ["museo_ciencias_1.jpeg", "museo_ciencias_2.jpeg"],
            "reviews": [
                (5, "Los niños se divirtieron tanto que no se querían ir. Aprendieron jugando, una maravilla."),
                (5, "El planetario es increíble, te sentís viajando por el espacio. Exhibiciones muy modernas."),
                (4, "Perfecto para pasar una tarde en familia. Los talleres están muy bien diseñados."),
                (5, "Interactivo de verdad, no solo para mirar. Los experimentos de física son geniales.")
            ]
        },
        {
            "place_name": "Parque Aventura Extrema",
            "description": "Parque temático con tirolesa, escalada y actividades al aire libre para todas las edades.",
            "country": "Argentina", "province": "Córdoba", "city": "Villa Carlos Paz",
            "address": "Camino a San Antonio s/n, Villa Carlos Paz",
            "categories": [cat_actividad],
            "continent": "américa", "climate": "templado",
            "activities": ["aventura", "deportes", "naturaleza", "familia", "adrenalina"],
            "cost_per_day": 35,
            "duration_min": None,  # Actividades promedio 5 horas
            "images": ["parque_aventura_1.jpg", "parque_aventura_2.jpg"],
            "reviews": [
                (5, "¡Adrenalina pura! La tirolesa sobre el lago es espectacular. Súper seguro y organizado."),
                (5, "Actividades para toda la familia, desde niños hasta abuelos. Los instructores muy profesionales."),
                (4, "Pasamos todo el día ahí. El circuito de escalada en árboles está genial, se siente la naturaleza."),
                (5, "Precios accesibles para toda la diversión que ofrecen. Volveremos seguro.")
            ]
        },
        {
            "place_name": "Tour Gastronómico Premium",
            "description": "Experiencia culinaria exclusiva visitando los mejores restaurantes locales con chef guía.",
            "country": "Argentina", "province": "Buenos Aires", "city": "Palermo",
            "address": "Plaza Serrano, Palermo Soho",
            "categories": [cat_gastro, cat_cultura],
            "continent": "américa", "climate": "templado",
            "activities": ["gastronomia", "cultura", "ciudad", "tour", "enologia"],
            "cost_per_day": 75,  # Precio fijo del tour incluye todo
            "duration_min": 240,  # Tour promedio 4 horas
            "images": ["tour_gastro_1.jpg", "tour_gastro_2.jpg"],
            "reviews": [
                (5, "Conocimos rincones gastronómicos que jamás hubiésemos encontrado solos. El chef guía es un genio."),
                (5, "La experiencia incluye 5 paradas con degustaciones. Valor increíble por lo que está incluido."),
                (4, "Aprendés mucho sobre la historia culinaria del barrio mientras comés delicioso. Muy recomendable."),
                (5, "Tour pequeño y personalizado. Se siente exclusivo y no masivo como otros tours.")
            ]
        }
    ]

    publications_added = 0
    # Obtener autores para reseñas
    review_authors = get_review_authors(db, admin_user)
    
    for pub_data in new_publications:
        # Verificar si la publicación ya existe
        existing = db.query(Publication).filter(
            Publication.place_name == pub_data["place_name"]
        ).first()
        
        if not existing:
            # Extraer datos especiales que no van directamente al modelo
            categories = pub_data.pop("categories")
            reviews_data = pub_data.pop("reviews", [])
            images_data = pub_data.pop("images", [])
            
            print(f"  📝 Creando: {pub_data['place_name']}...")
            
            # Crear la publicación
            publication = Publication(
                created_by_user_id=admin_user.id,
                status="approved",
                name=pub_data["place_name"],  # Agregar campo name
                street=pub_data["address"].split(",")[0] if pub_data.get("address") else "",  # Agregar campo street
                created_at=datetime.utcnow(),
                **pub_data
            )
            db.add(publication)
            db.flush()  # Para obtener el ID
            
            # Asignar categorías
            for category in categories:
                if category:
                    publication.categories.append(category)
            
            # Crear imágenes
            for idx, filename in enumerate(images_data):
                photo = PublicationPhoto(
                    publication_id=publication.id,
                    url=f"/static/uploads/publications/{filename}",
                    index_order=idx
                )
                db.add(photo)
                print(f"    🖼️ Imagen agregada: {filename}")
            
            # Crear reseñas
            if reviews_data:
                print(f"    💬 Creando {len(reviews_data)} reseñas...")
                for i, (rating, comment) in enumerate(reviews_data):
                    # Asigna un autor de forma rotativa
                    reviewer = review_authors[i % len(review_authors)]
                    
                    review = Review(
                        publication_id=publication.id,
                        author_id=reviewer.id,
                        rating=rating,
                        comment=comment,
                        # Resta días para que no todas tengan la misma fecha
                        created_at=datetime.utcnow() - timedelta(days=len(reviews_data) - i) 
                    )
                    db.add(review)
                
                # Actualizar ratings en la publicación
                db.flush() # Asegura que las reseñas estén en la sesión antes de calcular
                update_publication_ratings(db, publication.id)
            
            publications_added += 1
            print(f"    ✅ {pub_data['place_name']} creada exitosamente!")

    db.commit()
    print(f"\n🏪 {publications_added} nuevas publicaciones agregadas!")


def main():
    """Función principal del script."""
    print("🚀 Iniciando script de beneficios premium...")
    
    db = SessionLocal()
    try:
        # Crear tabla de beneficios si no existe
        from backend.app.db import engine
        PremiumBenefit.__table__.create(engine, checkfirst=True)
        print("✅ Tabla de beneficios verificada/creada")
        
        # Agregar nuevas publicaciones premium
        add_premium_publications(db)
        
        # Crear beneficios para todas las publicaciones
        create_premium_benefits(db)
        
        print("\n🎉 ¡Script completado exitosamente!")
        print("Los usuarios premium ahora pueden disfrutar de descuentos y beneficios exclusivos.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()