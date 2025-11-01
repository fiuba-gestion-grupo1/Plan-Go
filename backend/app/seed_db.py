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
            "description": "Un hotel icónico en el corazón de Buenos Aires, sobre la vibrante Avenida Corrientes. Perfecto para disfrutar de teatros, gastronomía y la vida nocturna porteña.",
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
            "description": "Lujo y elegancia incomparables en la Place Vendôme. El Ritz Paris es más que un hotel, es una leyenda que ofrece una experiencia parisina de máximo nivel.",
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
            "description": "Un refugio de serenidad en el distrito de templos de Kioto. Disfruta de un jardín japonés tradicional, un servicio impecable y una calma absoluta.",
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
            "description": "Vive la experiencia de Las Vegas al máximo. Lujo moderno, gastronomía de chefs reconocidos mundialmente y entretenimiento sin fin en un solo lugar.",
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
            "description": "Recorre las bodegas más prestigiosas de Luján de Cuyo y descubre por qué el Malbec argentino es famoso mundialmente, con los Andes como telón de fondo.",
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
            "description": "Atrévete a dominar las olas en la playa más famosa de Sydney. Clases para todos los niveles, perfectas para sentir el estilo de vida 'aussie'.",
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
            "description": "Una aventura inolvidable de 4 días a través de paisajes montañosos impresionantes, culminando en la majestuosa ciudadela inca de Machu Picchu al amanecer.",
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
            "description": "Explora la historia del arte mundial en el museo más visitado del planeta. Hogar de la Mona Lisa, la Venus de Milo y miles de tesoros invaluables.",
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
            "description": "Un exclusivo resort boutique en una playa de arena blanca y aguas turquesas. Lujo tropical y privacidad absoluta en la exótica isla de Zanzíbar.",
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
            "description": "Vive la 'Gran Migración' y observa a los Cinco Grandes en su hábitat natural. Una experiencia de vida salvaje que te cambiará la perspectiva en el corazón de Tanzania.",
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
            "description": "Sumérgete en la cultura y la naturaleza de Ubud desde tu propia villa privada con piscina. El balance perfecto entre lujo, espiritualidad y selva tropical.",
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
            "description": "Contempla la imponente majestuosidad de este gigante de hielo vivo. Escucha el estruendo de sus desprendimientos en un espectáculo natural único en la Patagonia.",
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
            "description": "Diseño de vanguardia y vistas espectaculares en el vibrante Meatpacking District de NYC. Flota sobre el High Line Park y disfruta de su famoso rooftop bar.",
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
            "description": "Descubre los sabores auténticos de la Ciudad Eterna. Un recorrido a pie por Trastevere o Campo de' Fiori probando pizza, pasta, quesos y vinos locales.",
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
            "description": "El epítome del diseño y la sofisticación en la playa de Ipanema. Disfruta de su icónica piscina infinita con vistas al Morro Dos Hermanos.",
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
            "description": "Un festín para los sentidos en el caótico y delicioso Chinatown de Bangkok. Prueba desde Pad Thai hasta postres exóticos en este tour nocturno.",
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
            "description": "Salta al vacío desde el histórico puente Kawarau, la cuna mundial del bungee. Pura adrenalina en la capital de la aventura de Nueva Zelanda.",
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
            "description": "Caza la mágica danza de las luces del norte en esta excursión nocturna desde Reikiavik. Una experiencia etérea bajo el cielo ártico de Islandia.",
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
            "description": "Viaja 4.500 años al pasado y maravíllate ante la última de las Siete Maravillas del Mundo Antiguo que sigue en pie. Una visita obligada en Egipto.",
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
            "description": "Relajo total en el Caribe Mexicano. Disfruta de playas turquesas, múltiples restaurantes y entretenimiento sin fin en la Zona Hotelera de Cancún.",
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
            description=item.get("description"), # <-- CAMBIO AÑADIDO
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