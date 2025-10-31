import os
import shutil
# import requests <--- ELIMINADO
from sqlalchemy.orm import Session
from datetime import datetime

# Ajusta las importaciones para que funcione como un script
# Asume que se ejecuta desde la raíz del proyecto (ej: python -m backend.app.seed_db)
try:
    from backend.app.db import SessionLocal
    from backend.app import models
    from backend.app.models import User, Publication, PublicationPhoto, Category
except ImportError:
    print("Error: Ejecuta este script como un módulo desde la raíz del proyecto.")
    print("Ejemplo: python -m backend.app.seed_db")
    exit(1)


# Define la carpeta de destino de las imágenes (la misma que en publications.py)
UPLOAD_DIR = os.path.join("backend", "app", "static", "uploads", "publications")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_author_user(db: Session) -> User | None:
    """Busca un usuario admin o el primer usuario para usarlo como autor."""
    # 1. Intenta buscar un usuario con role 'admin'
    admin_user = db.query(User).filter(User.role == "admin").first()
    if admin_user:
        print(f"Usando al usuario admin '{admin_user.username}' como autor.")
        return admin_user
    
    # 2. Si no hay admin, busca el primer usuario
    first_user = db.query(User).first()
    if first_user:
        print(f"No se encontró admin. Usando al primer usuario '{first_user.username}' como autor.")
        return first_user

    # 3. Si no hay usuarios
    print("Error: No se encontraron usuarios en la base de datos.")
    print("Por favor, crea un usuario (preferiblemente admin) antes de ejecutar el seed.")
    return None


def get_or_create_category(db: Session, slug: str, name: str) -> Category:
    """Busca o crea una categoría."""
    category = db.query(Category).filter_by(slug=slug).first()
    if category:
        return category
    
    print(f"Creando categoría: {name}")
    new_category = Category(slug=slug, name=name)
    db.add(new_category)
    db.flush()  # Para que el objeto tenga ID
    return new_category


# --- SE ELIMINÓ LA FUNCIÓN download_image ---


def seed_publications(db: Session):
    """Función principal que crea las publicaciones."""
    print("--- Iniciando Seeding de Publicaciones ---")
    
    # 1. Obtener autor
    author = get_author_user(db)
    if not author:
        return

    # 2. Obtener/Crear Categorías
    cat_hotel = get_or_create_category(db, "hotel", "Hotel")
    cat_actividad = get_or_create_category(db, "actividad", "Actividad")
    # --- NUEVAS CATEGORÍAS ---
    cat_aventura = get_or_create_category(db, "aventura", "Aventura")
    cat_cultura = get_or_create_category(db, "cultura", "Cultura")
    cat_gastro = get_or_create_category(db, "gastronomia", "Gastronomía")
    
    
    # 3. Definir datos de prueba (AHORA CON NOMBRES DE ARCHIVO LOCALES)
    data_to_seed = [
        # --- Hoteles (4) ---
        {
            "place_name": "Hotel Continental",
            "country": "Argentina", "province": "Buenos Aires", "city": "CABA",
            "address": "Av. Corrientes 865",
            # --- CAMPOS ACTUALIZADOS ---
            "categories": [cat_hotel, cat_cultura, cat_gastro],
            "continent": "américa",
            "climate": "templado",
            "activities": ["cultura", "gastronomia", "ciudad", "noche"],
            "cost_per_day": 200,
            "duration_days": 1,
            # ---
            "images": [
                "hotel_continental_1.jpg",
                "hotel_continental_2.jpg"
            ]
        },
        {
            "place_name": "Ritz Paris",
            "country": "Francia", "province": "Isla de Francia", "city": "París",
            "address": "15 Pl. Vendôme, 75001 Paris",
            # --- CAMPOS ACTUALIZADOS ---
            "categories": [cat_hotel, cat_cultura, cat_gastro],
            "continent": "europa",
            "climate": "templado",
            "activities": ["cultura", "gastronomia", "lujo", "romance", "ciudad"],
            "cost_per_day": 1200,
            "duration_days": 1,
            # ---
            "images": [
                "ritz_paris_1.jpg",
                "ritz_paris_2.jpg"
            ]
        },
        {
            "place_name": "Four Seasons Kyoto",
            "country": "Japón", "province": "Prefectura de Kioto", "city": "Kioto",
            "address": "445-3 Myohoin Maekawacho, Higashiyama Ward",
            # --- CAMPOS ACTUALIZADOS ---
            "categories": [cat_hotel, cat_cultura],
            "continent": "asia",
            "climate": "templado",
            "activities": ["cultura", "relax", "naturaleza", "historia"],
            "cost_per_day": 900,
            "duration_days": 1,
            # ---
            "images": [
                "four_seasons_kyoto_1.jpg",
                "four_seasons_kyoto_2.jpg"
            ]
        },
        {
            "place_name": "Palms Casino Resort",
            "country": "EE.UU.", "province": "Nevada", "city": "Las Vegas",
            "address": "4321 W Flamingo Rd",
            # --- CAMPOS ACTUALIZADOS ---
            "categories": [cat_hotel],
            "continent": "américa",
            "climate": "seco",
            "activities": ["show", "casino", "gastronomia", "noche"],
            "cost_per_day": 450,
            "duration_days": 1,
            # ---
            "images": [
                "palms_casino_1.jpg",
                "palms_casino_2.jpg"
            ]
        },
        
        # --- Actividades (4) ---
        {
            "place_name": "Tour de Vinos en Mendoza",
            "country": "Argentina", "province": "Mendoza", "city": "Luján de Cuyo",
            "address": "Ruta Provincial 15, km 29",
            # --- CAMPOS ACTUALIZADOS ---
            "categories": [cat_actividad, cat_gastro],
            "continent": "américa",
            "climate": "seco",
            "activities": ["gastronomia", "tour", "naturaleza"],
            "cost_per_day": 150,
            "duration_days": 1,
            # ---
            "images": [
                "tour_vinos_mendoza_1.jpg",
                "tour_vinos_mendoza_2.jpg"
            ]
        },
        {
            "place_name": "Clase de Surf en Bondi Beach",
            "country": "Australia", "province": "Nueva Gales del Sur", "city": "Sydney",
            "address": "Bondi Beach",
            # --- CAMPOS ACTUALIZADOS ---
            "categories": [cat_actividad, cat_aventura],
            "continent": "oceanía",
            "climate": "templado",
            "activities": ["playa", "deporte", "aventura"],
            "cost_per_day": 100,
            "duration_days": 1,
            # ---
            "images": [
                "surf_bondi_1.jpg",
                "surf_bondi_2.jpg"
            ]
        },
        {
            "place_name": "Caminata al Machu Picchu (Camino Inca)",
            "country": "Perú", "province": "Cusco", "city": "Aguas Calientes",
            "address": "Camino Inca",
            # --- CAMPOS ACTUALIZADOS ---
            "categories": [cat_actividad, cat_aventura, cat_cultura],
            "continent": "américa",
            "climate": "frío",
            "activities": ["trekking", "cultura", "aventura", "montaña", "historia"],
            "cost_per_day": 125,
            "duration_days": 4,
            # ---
            "images": [
                "machu_picchu_1.jpg",
                "machu_picchu_2.jpg"
            ]
        },
        {
            "place_name": "Visita al Museo del Louvre",
            "country": "Francia", "province": "Isla de Francia", "city": "París",
            "address": "Rue de Rivoli, 75001 Paris",
            # --- CAMPOS ACTUALIZADOS ---
            "categories": [cat_actividad, cat_cultura],
            "continent": "europa",
            "climate": "templado",
            "activities": ["cultura", "arte", "historia", "ciudad"],
            "cost_per_day": 25,
            "duration_days": 1,
            # ---
            "images": [
                "museo_louvre_1.jpg",
                "museo_louvre_2.jpg"
            ]
        },

        # --- NUEVAS PUBLICACIONES (12) ---
        {
            "place_name": "The Palms Resort Zanzíbar",
            "country": "Tanzania", "province": "Zanzíbar", "city": "Bwejuu",
            "address": "Bwejuu Beach",
            "categories": [cat_hotel],
            "continent": "áfrica",
            "climate": "tropical",
            "activities": ["playa", "relax", "naturaleza"],
            "cost_per_day": 750,
            "duration_days": 1,
            "images": [
                "palms_zanzibar_1.jpg",
                "palms_zanzibar_2.jpg"
            ]
        },
        {
            "place_name": "Safari en el Serengeti",
            "country": "Tanzania", "province": "Región de Arusha", "city": "Serengeti",
            "address": "Parque Nacional Serengeti",
            "categories": [cat_actividad, cat_aventura],
            "continent": "áfrica",
            "climate": "seco",
            "activities": ["aventura", "naturaleza", "safari"],
            "cost_per_day": 600,
            "duration_days": 5,
            "images": [
                "serengeti_1.jpg",
                "serengeti_2.jpg"
            ]
        },
        {
            "place_name": "Villa privada en Bali",
            "country": "Indonesia", "province": "Bali", "city": "Ubud",
            "address": "Jl. Raya Sayan",
            "categories": [cat_hotel, cat_cultura],
            "continent": "asia",
            "climate": "tropical",
            "activities": ["playa", "relax", "cultura", "gastronomia", "naturaleza"],
            "cost_per_day": 300,
            "duration_days": 1,
            "images": [
                "bali_villa_1.jpg",
                "bali_villa_2.jpg"
            ]
        },
        {
            "place_name": "Glaciar Perito Moreno",
            "country": "Argentina", "province": "Santa Cruz", "city": "El Calafate",
            "address": "Parque Nacional Los Glaciares",
            "categories": [cat_actividad, cat_aventura],
            "continent": "américa",
            "climate": "frío",
            "activities": ["naturaleza", "montaña", "trekking"],
            "cost_per_day": 100,
            "duration_days": 1,
            "images": [
                "perito_moreno_1.jpg",
                "perito_moreno_2.jpg"
            ]
        },
        {
            "place_name": "Hotel The Standard, High Line",
            "country": "EE.UU.", "province": "Nueva York", "city": "Nueva York",
            "address": "848 Washington St",
            "categories": [cat_hotel, cat_cultura],
            "continent": "américa",
            "climate": "templado",
            "activities": ["ciudad", "cultura", "gastronomia", "noche", "show"],
            "cost_per_day": 550,
            "duration_days": 1,
            "images": [
                "standard_nyc_1.jpg",
                "standard_nyc_2.jpg"
            ]
        },
        {
            "place_name": "Tour Gastronómico en Roma",
            "country": "Italia", "province": "Lacio", "city": "Roma",
            "address": "Campo de' Fiori",
            "categories": [cat_actividad, cat_gastro, cat_cultura],
            "continent": "europa",
            "climate": "templado",
            "activities": ["historia", "cultura", "ciudad", "gastronomia"],
            "cost_per_day": 90,
            "duration_days": 1,
            "images": [
                "roma_gastro_1.jpg",
                "roma_gastro_2.jpg"
            ]
        },
        {
            "place_name": "Hotel Fasano Rio de Janeiro",
            "country": "Brasil", "province": "Río de Janeiro", "city": "Río de Janeiro",
            "address": "Av. Vieira Souto, 80 - Ipanema",
            "categories": [cat_hotel],
            "continent": "américa",
            "climate": "tropical",
            "activities": ["playa", "ciudad", "noche", "gastronomia"],
            "cost_per_day": 650,
            "duration_days": 1,
            "images": [
                "fasano_rio_1.jpg",
                "fasano_rio_2.jpg"
            ]
        },
        {
            "place_name": "Tour de Comida Callejera en Bangkok",
            "country": "Tailandia", "province": "Bangkok", "city": "Bangkok",
            "address": "Yaowarat Road (Chinatown)",
            "categories": [cat_actividad, cat_gastro, cat_cultura],
            "continent": "asia",
            "climate": "tropical",
            "activities": ["gastronomia", "ciudad", "cultura", "noche"],
            "cost_per_day": 40,
            "duration_days": 1,
            "images": [
                "bangkok_food_1.jpg",
                "bangkok_food_2.jpg"
            ]
        },
        {
            "place_name": "Bungee Jumping en Queenstown",
            "country": "Nueva Zelanda", "province": "Otago", "city": "Queenstown",
            "address": "Kawarau Gorge Suspension Bridge",
            "categories": [cat_actividad, cat_aventura],
            "continent": "oceanía",
            "climate": "templado",
            "activities": ["aventura", "deporte", "montaña", "naturaleza"],
            "cost_per_day": 180,
            "duration_days": 1,
            "images": [
                "queenstown_bungee_1.jpg",
                "queenstown_bungee_2.jpg"
            ]
        },
        {
            "place_name": "Tour de Auroras Boreales",
            "country": "Islandia", "province": "Región Capital", "city": "Reikiavik",
            "address": "Salida desde Reikiavik",
            "categories": [cat_actividad, cat_aventura],
            "continent": "europa",
            "climate": "frío",
            "activities": ["naturaleza", "aventura", "noche"],
            "cost_per_day": 110,
            "duration_days": 1,
            "images": [
                "aurora_iceland_1.jpg",
                "aurora_iceland_2.jpg"
            ]
        },
        {
            "place_name": "Visita a las Pirámides de Giza",
            "country": "Egipto", "province": "Giza", "city": "Giza",
            "address": "Al Haram, Nazlet El-Semman",
            "categories": [cat_actividad, cat_cultura, cat_aventura],
            "continent": "áfrica",
            "climate": "seco",
            "activities": ["historia", "cultura", "desierto"],
            "cost_per_day": 80,
            "duration_days": 1,
            "images": [
                "giza_pyramids_1.jpg",
                "giza_pyramids_2.jpg"
            ]
        },
        {
            "place_name": "Resort All-Inclusive en Cancún",
            "country": "México", "province": "Quintana Roo", "city": "Cancún",
            "address": "Blvd. Kukulcan, Zona Hotelera",
            "categories": [cat_hotel],
            "continent": "américa",
            "climate": "tropical",
            "activities": ["playa", "relax", "noche", "gastronomia"],
            "cost_per_day": 400,
            "duration_days": 1,
            "images": [
                "cancun_resort_1.jpg",
                "cancun_resort_2.jpg"
            ]
        },
    ]

    # 4. Procesar y crear
    created_count = 0
    for item in data_to_seed:
        # Verificar si ya existe
        exists = db.query(Publication).filter_by(place_name=item["place_name"]).first()
        if exists:
            print(f"Skipping: '{item['place_name']}' ya existe.")
            continue
            
        print(f"Creando: '{item['place_name']}'...")
        
        # Crear la publicación
        pub = Publication(
            place_name=item["place_name"],
            country=item["country"],
            province=item["province"],
            city=item["city"],
            address=item["address"],
            categories=item["categories"],
            
            # Asignar autor y status
            created_by_user_id=author.id,
            status="approved",
            created_at=datetime.utcnow(),
            
            # Campos de enriquecimiento
            continent=item.get("continent"),
            climate=item.get("climate"),
            activities=item.get("activities"), # AHORA PASA LA LISTA
            cost_per_day=item.get("cost_per_day"),
            duration_days=item.get("duration_days"),
            
            # Campos legacy (basado en models.py)
            name=item["place_name"],
            street=item["address"].split(",")[0],
        )
        
        db.add(pub)
        db.flush()  # IMPORTANTE: para obtener pub.id
        
        # --- LÓGICA DE IMÁGENES ACTUALIZADA ---
        # Busca los archivos definidos en la lista 'images'
        image_filenames = item.get("images", [])
        for idx, filename in enumerate(image_filenames):
            
            # 1. Comprueba si el archivo existe en la carpeta UPLOAD_DIR
            absolute_path = os.path.join(UPLOAD_DIR, filename)
            relative_url = f"/static/uploads/publications/{filename}"

            if os.path.exists(absolute_path):
                # 2. Si existe, lo asocia a la publicación
                print(f"  > Imagen encontrada: {filename}")
                photo = PublicationPhoto(
                    publication_id=pub.id,
                    url=relative_url,
                    index_order=idx
                )
                db.add(photo)
            else:
                # 3. Si no existe, te avisa
                print(f"  > ADVERTENCIA: No se encontró la imagen '{filename}' en {UPLOAD_DIR}")
        
        db.commit() # Commit por cada publicación
        created_count += 1

    print(f"--- Seeding completado. {created_count} nuevas publicaciones creadas. ---")


if __name__ == "__main__":
    print("Conectando a la base de datos...")
    db = SessionLocal()
    try:
        seed_publications(db)
    except Exception as e:
        print(f"Ocurrió un error during el seeding: {e}")
        db.rollback()
    finally:
        db.close()
        print("Conexión cerrada.")