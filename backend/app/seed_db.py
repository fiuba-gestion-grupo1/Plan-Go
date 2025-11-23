import os
import shutil
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

try:
    from backend.app.db import SessionLocal
    from backend.app import models
    from backend.app.models import User, Publication, PublicationPhoto, Category, Review
except ImportError:
    print("Error: Ejecuta este script como un módulo desde la raíz del proyecto.")
    print("Ejemplo: python -m backend.app.seed_db")
    exit(1)


UPLOAD_DIR = os.path.join("backend", "app", "static", "uploads", "publications")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_author_user(db: Session) -> User | None:
    """Busca un usuario admin o el primer usuario para usarlo como autor."""
    admin_user = db.query(User).filter(User.role == "admin").first()
    if admin_user:
        print(f"Usando al usuario admin '{admin_user.username}' como autor.")
        return admin_user

    first_user = db.query(User).first()
    if first_user:
        print(
            f"No se encontró admin. Usando al primer usuario '{first_user.username}' como autor."
        )
        return first_user

    print("Error: No se encontraron usuarios en la base de datos.")
    print(
        "Por favor, crea un usuario (preferiblemente admin) antes de ejecutar el seed."
    )
    return None


def get_review_authors(db: Session, default_author: User) -> list[User]:
    """Busca todos los usuarios para usarlos como autores de reseñas."""
    all_users = db.query(User).all()
    if not all_users:
        print(
            "  > Advertencia: No se encontraron usuarios para reseñas. Usando al autor principal."
        )
        return [default_author]

    print(
        f"  > Encontrados {len(all_users)} usuarios para usar como autores de reseñas."
    )
    return all_users


def update_publication_ratings(db: Session, pub_id: int):
    """
    Recalcula y actualiza el rating_avg y rating_count de una publicación.
    (Lógica copiada de publications.py/_update_publication_rating)
    """
    try:
        avg_, count_ = (
            db.query(func.avg(models.Review.rating), func.count(models.Review.id))
            .filter(models.Review.publication_id == pub_id)
            .one()
        )

        pub = (
            db.query(models.Publication).filter(models.Publication.id == pub_id).first()
        )
        if pub:
            pub.rating_avg = round(float(avg_ or 0.0), 1)
            pub.rating_count = int(count_ or 0)
            db.add(pub)
            print(
                f"  > Ratings actualizados para pub_id={pub_id}: {pub.rating_avg} avg, {pub.rating_count} count"
            )
    except Exception as e:
        print(f"  > ERROR actualizando ratings para pub_id={pub_id}: {e}")


def get_or_create_category(db: Session, slug: str, name: str) -> Category:
    """Busca o crea una categoría."""
    category = db.query(Category).filter_by(slug=slug).first()
    if category:
        return category

    print(f"Creando categoría: {name}")
    new_category = Category(slug=slug, name=name)
    db.add(new_category)
    db.flush()
    return new_category


def seed_publications(db: Session):
    """Función principal que crea las publicaciones."""
    print("--- Iniciando Seeding de Publicaciones ---")

    author = get_author_user(db)
    if not author:
        return

    review_authors = get_review_authors(db, author)

    cat_hotel = get_or_create_category(db, "hotel", "Hotel")
    cat_actividad = get_or_create_category(db, "actividad", "Actividad")
    cat_aventura = get_or_create_category(db, "aventura", "Aventura")
    cat_cultura = get_or_create_category(db, "cultura", "Cultura")
    cat_gastro = get_or_create_category(db, "gastronomia", "Gastronomía")

    data_to_seed = [
        {
            "place_name": "Hotel Continental",
            "country": "Argentina",
            "province": "Buenos Aires",
            "city": "CABA",
            "address": "Av. Corrientes 865",
            "description": "Un hotel icónico en el corazón de Buenos Aires, sobre la vibrante Avenida Corrientes.",
            "categories": [cat_hotel, cat_cultura, cat_gastro],
            "continent": "américa",
            "climate": "templado",
            "activities": ["cultura", "gastronomia", "ciudad", "noche"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["hotel_continental_1.jpg", "hotel_continental_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["00:00-23:59"],
            "reviews": [
                (
                    5,
                    "Excelente ubicación, pleno centro. La habitación muy cómoda y el personal amable.",
                ),
                (
                    4,
                    "Muy buen hotel, algo ruidoso por estar en Corrientes, pero es de esperar. El desayuno 10/10.",
                ),
                (5, "Impecable. Volvería sin dudarlo. La cama era súper cómoda."),
                (4, "Buena relación precio-calidad para la zona. Recomendable."),
            ],
        },
        {
            "place_name": "Ritz Paris",
            "country": "Francia",
            "province": "Isla de Francia",
            "city": "París",
            "address": "15 Pl. Vendôme, 75001 Paris",
            "description": "Lujo y elegancia incomparables en la Place Vendôme. El Ritz Paris es más que un hotel, es una leyenda.",
            "categories": [cat_hotel, cat_cultura, cat_gastro],
            "continent": "europa",
            "climate": "templado",
            "activities": ["cultura", "gastronomia", "lujo", "romance", "ciudad"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["ritz_paris_1.jpg", "ritz_paris_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["00:00-23:59"],
            "reviews": [
                (
                    5,
                    "Insuperable. Cada detalle es perfecto. El servicio es de otro nivel.",
                ),
                (
                    5,
                    "Un sueño hecho realidad. El Bar Hemingway es una visita obligada.",
                ),
                (
                    5,
                    "No hay palabras para describir la experiencia. Lujo en estado puro.",
                ),
                (
                    5,
                    "Vale cada centavo. La piscina es espectacular y la ubicación inmejorable.",
                ),
            ],
        },
        {
            "place_name": "Four Seasons Kyoto",
            "country": "Japón",
            "province": "Prefectura de Kioto",
            "city": "Kioto",
            "address": "445-3 Myohoin Maekawacho, Higashiyama Ward",
            "description": "Un refugio de serenidad en el distrito de templos de Kioto. Disfruta de un jardín japonés tradicional.",
            "categories": [cat_hotel, cat_cultura],
            "continent": "asia",
            "climate": "templado",
            "activities": ["cultura", "relax", "naturaleza", "historia"],
            "cost_per_day": None,
            "duration_min": None,
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["00:00-23:59"],
            "images": ["four_seasons_kyoto_1.jpg", "four_seasons_kyoto_2.jpg"],
            "reviews": [
                (5, "Paz absoluta. El jardín es mágico, parece salido de una pintura."),
                (
                    5,
                    "El servicio japonés en su máxima expresión. Te hacen sentir especial.",
                ),
                (
                    5,
                    "Las habitaciones son enormes y con vistas preciosas. El té de bienvenida fue un detalle encantador.",
                ),
                (
                    5,
                    "La ubicación es perfecta para explorar los templos de Higashiyama. De los mejores hoteles en los que he estado.",
                ),
            ],
        },
        {
            "place_name": "Palms Casino Resort",
            "country": "EE.UU.",
            "province": "Nevada",
            "city": "Las Vegas",
            "address": "4321 W Flamingo Rd",
            "description": "Vive la experiencia de Las Vegas al máximo. Lujo moderno y entretenimiento sin fin.",
            "categories": [cat_hotel],
            "continent": "américa",
            "climate": "seco",
            "activities": ["show", "casino", "gastronomia", "noche"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["palms_casino_1.jpg", "palms_casino_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["00:00-23:59"],
            "reviews": [
                (4, "Habitaciones modernas y muy limpias. Buenas opciones de comida."),
                (
                    3,
                    "Está un poco lejos del Strip principal, hay que tomar taxi para todo.",
                ),
                (
                    2,
                    "El check-in fue una pesadilla, más de una hora de espera. Inaceptable.",
                ),
                (
                    4,
                    "La piscina es genial y el ambiente más relajado que en otros hoteles del Strip.",
                ),
            ],
        },
        {
            "place_name": "Tour de Vinos en Mendoza",
            "country": "Argentina",
            "province": "Mendoza",
            "city": "Luján de Cuyo",
            "address": "Ruta Provincial 15, km 29",
            "description": "Recorre las bodegas más prestigiosas de Luján de Cuyo y descubre el Malbec argentino.",
            "categories": [cat_actividad, cat_gastro],
            "continent": "américa",
            "climate": "seco",
            "activities": ["gastronomia", "tour", "naturaleza"],
            "cost_per_day": 150,
            "duration_min": 1440,
            "available_days": ["lunes", "martes", "miércoles", "viernes", "sábado"],
            "available_hours": ["11:00-21:00"],
            "images": ["tour_vinos_mendoza_1.jpg", "tour_vinos_mendoza_2.jpg"],
            "reviews": [
                (5, "Increíble. Las bodegas son hermosas y los vinos espectaculares."),
                (
                    4,
                    "Hermosos paisajes, aunque el tour fue un poco apurado. Me hubiese quedado más tiempo en cada bodega.",
                ),
                (
                    5,
                    "El Malbec de Luján de Cuyo es el mejor del mundo. El almuerzo fue inolvidable.",
                ),
                (5, "Súper organizado, el guía sabía muchísimo. 100% recomendable."),
            ],
        },
        {
            "place_name": "Clase de Surf en Bondi Beach",
            "country": "Australia",
            "province": "Nueva Gales del Sur",
            "city": "Sydney",
            "address": "Bondi Beach",
            "description": "Atrévete a dominar las olas en la playa más famosa de Sydney. Clases para todos los niveles.",
            "categories": [cat_actividad, cat_aventura],
            "continent": "oceanía",
            "climate": "templado",
            "activities": ["playa", "deporte", "aventura"],
            "cost_per_day": 100,
            "duration_min": 1440,
            "images": ["surf_bondi_1.jpg", "surf_bondi_2.jpg"],
            "available_days": ["martes", "jueves", "viernes", "sábado"],
            "available_hours": ["09:00-17:00"],
            "reviews": [
                (
                    5,
                    "¡Genial! Era mi primera vez y logré pararme en la tabla. El instructor un genio.",
                ),
                (
                    4,
                    "Muy divertido, pero había demasiada gente en el agua. Es Bondi, qué se le va a hacer.",
                ),
                (
                    5,
                    "El agua estaba helada pero con el traje de neopreno ni se siente. Gran experiencia.",
                ),
                (
                    5,
                    "Súper recomendable para arrancar. Los grupos son chicos y te dan buena atención.",
                ),
            ],
        },
        {
            "place_name": "Caminata al Machu Picchu (Camino Inca)",
            "country": "Perú",
            "province": "Cusco",
            "city": "Aguas Calientes",
            "address": "Camino Inca",
            "description": "Una aventura inolvidable de 4 días a través de paisajes montañosos impresionantes.",
            "categories": [cat_actividad, cat_aventura, cat_cultura],
            "continent": "américa",
            "climate": "frío",
            "activities": ["trekking", "cultura", "aventura", "montaña", "historia"],
            "cost_per_day": 125,
            "duration_min": 5760,
            "images": ["machu_picchu_1.jpg", "machu_picchu_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
            ],
            "available_hours": ["07:00-18:30"],
            "reviews": [
                (
                    5,
                    "La mejor experiencia de mi vida. Llegar a la Puerta del Sol al amanecer es algo que no me olvidaré jamás.",
                ),
                (
                    5,
                    "Durísimo, la altura se siente, pero vale cada segundo de esfuerzo. Los paisajes son de otro planeta.",
                ),
                (
                    5,
                    "Nuestro guía fue increíble, nos contó toda la historia. La comida de los porteadores, un lujo.",
                ),
                (5, "Mágico es la única palabra. Hay que hacerlo una vez en la vida."),
            ],
        },
        {
            "place_name": "Visita al Museo del Louvre",
            "country": "Francia",
            "province": "Isla de Francia",
            "city": "París",
            "address": "Rue de Rivoli, 75001 Paris",
            "description": "Explora la historia del arte mundial en el museo más visitado del planeta.",
            "categories": [cat_actividad, cat_cultura],
            "continent": "europa",
            "climate": "templado",
            "activities": ["cultura", "arte", "historia", "ciudad"],
            "cost_per_day": 25,
            "duration_min": 1440,
            "images": ["museo_louvre_1.jpg", "museo_louvre_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["08:00-20:30"],
            "reviews": [
                (5, "Impresionante. Es enorme, necesitas días para verlo bien."),
                (
                    3,
                    "Ver la Mona Lisa fue una decepción. Un cuadro chiquito rodeado de 500 personas. El resto del museo, genial.",
                ),
                (
                    4,
                    "Imposible verlo todo. Recomiendo ir con un plan de qué salas visitar. La parte de Egipto es espectacular.",
                ),
                (
                    5,
                    "Una maravilla arquitectónica e histórica. Comprar la entrada con anticipación es clave.",
                ),
            ],
        },
        {
            "place_name": "The Palms Resort Zanzíbar",
            "country": "Tanzania",
            "province": "Zanzíbar",
            "city": "Bwejuu",
            "address": "Bwejuu Beach",
            "description": "Un exclusivo resort boutique en una playa de arena blanca y aguas turquesas.",
            "categories": [cat_hotel],
            "continent": "áfrica",
            "climate": "tropical",
            "activities": ["playa", "relax", "naturaleza"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["palms_zanzibar_1.jpg", "palms_zanzibar_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["00:00-23:59"],
            "reviews": [
                (
                    5,
                    "El paraíso en la tierra. Privacidad total, servicio de mayordomo impecable.",
                ),
                (
                    5,
                    "La playa es de las más lindas que vi. El color del agua es irreal.",
                ),
                (
                    4,
                    "Comida excelente, aunque algo cara. Las villas son gigantes y lujosas.",
                ),
                (5, "Ideal para luna de miel. Cero ruido, solo el mar."),
            ],
        },
        {
            "place_name": "Safari en el Serengeti",
            "country": "Tanzania",
            "province": "Región de Arusha",
            "city": "Serengeti",
            "address": "Parque Nacional Serengeti",
            "description": "Vive la 'Gran Migración' y observa a los Cinco Grandes en su hábitat natural.",
            "categories": [cat_actividad, cat_aventura],
            "continent": "áfrica",
            "climate": "seco",
            "activities": ["aventura", "naturaleza", "safari"],
            "cost_per_day": 600,
            "duration_min": 7200,
            "images": ["serengeti_1.jpg", "serengeti_2.jpg"],
            "available_days": ["lunes", "martes", "jueves", "sábado", "domingo"],
            "available_hours": ["08:00-19:30"],
            "reviews": [
                (
                    5,
                    "¡Vi a los 5 grandes en dos días! Nuestro guía, Joseph, fue el mejor.",
                ),
                (
                    5,
                    "Ver la gran migración cruzando el río Mara es algo que te marca. Impresionante.",
                ),
                (
                    5,
                    "Dormir en los lodges en medio del parque, escuchando a los animales, es una locura.",
                ),
                (5, "El precio lo vale. Es una experiencia única."),
            ],
        },
        {
            "place_name": "Villa privada en Bali",
            "country": "Indonesia",
            "province": "Bali",
            "city": "Ubud",
            "address": "Jl. Raya Sayan",
            "description": "Sumérgete en la cultura y la naturaleza de Ubud desde tu propia villa privada con piscina.",
            "categories": [cat_hotel, cat_cultura],
            "continent": "asia",
            "climate": "tropical",
            "activities": ["playa", "relax", "cultura", "gastronomia", "naturaleza"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["bali_villa_1.jpg", "bali_villa_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["00:00-23:59"],
            "reviews": [
                (5, "Paz total en medio de la selva. La piscina privada es un lujo."),
                (
                    4,
                    "El desayuno 'flotante' es genial para la foto. El staff muy amable.",
                ),
                (
                    5,
                    "Ubud es mágico y esta villa fue el complemento perfecto. Cerca de todo pero aislado del ruido.",
                ),
                (5, "Volvería mil veces. Increíble relación precio-calidad."),
            ],
        },
        {
            "place_name": "Tour Glaciar Perito Moreno",
            "country": "Argentina",
            "province": "Santa Cruz",
            "city": "El Calafate",
            "address": "Parque Nacional Los Glaciares",
            "description": "Contempla la imponente majestuosidad de este gigante de hielo vivo.",
            "categories": [cat_actividad, cat_aventura],
            "continent": "américa",
            "climate": "frío",
            "activities": ["naturaleza", "montaña", "trekking"],
            "cost_per_day": 100,
            "duration_min": 1440,
            "images": ["perito_moreno_1.jpg", "perito_moreno_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["10:00-18:30"],
            "reviews": [
                (5, "Imponente. Te sentís muy chiquito al lado de esa masa de hielo."),
                (5, "El ruido del hielo rompiendo y cayendo al agua es inolvidable."),
                (
                    5,
                    "Las pasarelas están perfectas, se puede ver desde todos los ángulos. Imperdible.",
                ),
                (
                    5,
                    "Hicimos el mini-trekking sobre el glaciar. CARO, pero lo vale 100%.",
                ),
            ],
        },
        {
            "place_name": "Hotel The Standard, High Line",
            "country": "EE.UU.",
            "province": "Nueva York",
            "city": "Nueva York",
            "address": "848 Washington St",
            "description": "Diseño de vanguardia y vistas espectaculares en el vibrante Meatpacking District de NYC.",
            "categories": [cat_hotel, cat_cultura],
            "continent": "américa",
            "climate": "templado",
            "activities": ["ciudad", "cultura", "gastronomia", "noche", "show"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["standard_nyc_1.jpg", "standard_nyc_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["00:00-23:59"],
            "reviews": [
                (
                    4,
                    "Las vistas desde la habitación (con ventana de piso a techo) son LO MÁS.",
                ),
                (
                    3,
                    "El rooftop es EL lugar para ir, pero la música estaba tan fuerte que se escuchaba en la habitación.",
                ),
                (2, "La habitación 'standard' es MINÚSCULA. No vale lo que cuesta."),
                (
                    4,
                    "Ubicación 10/10 en Meatpacking, sobre el High Line. El diseño del hotel es genial.",
                ),
            ],
        },
        {
            "place_name": "Tour Gastronómico en Roma",
            "country": "Italia",
            "province": "Lacio",
            "city": "Roma",
            "address": "Campo de' Fiori",
            "description": "Descubre los sabores auténticos de la Ciudad Eterna. Un recorrido a pie por Trastevere.",
            "categories": [cat_actividad, cat_gastro, cat_cultura],
            "continent": "europa",
            "climate": "templado",
            "activities": ["historia", "cultura", "ciudad", "gastronomia"],
            "cost_per_day": 90,
            "duration_min": 1440,
            "images": ["roma_gastro_1.jpg", "roma_gastro_2.jpg"],
            "available_days": ["lunes", "martes", "viernes", "sábado"],
            "available_hours": ["17:30-20:30"],
            "reviews": [
                (
                    5,
                    "La mejor pasta Cacio e Pepe que probé en mi vida. El guía un genio.",
                ),
                (
                    5,
                    "Descubrimos lugares que jamás hubiésemos encontrado solos. Buenísimo.",
                ),
                (4, "Mucha comida, ¡ir con hambre! El guía muy simpático."),
                (
                    5,
                    "Hacerlo en Trastevere de noche fue una gran decisión. Súper pintoresco.",
                ),
            ],
        },
        {
            "place_name": "Hotel Fasano Rio de Janeiro",
            "country": "Brasil",
            "province": "Río de Janeiro",
            "city": "Río de Janeiro",
            "address": "Av. Vieira Souto, 80 - Ipanema",
            "description": "El epítome del diseño y la sofisticación en la playa de Ipanema. Disfruta de su icónica piscina infinita.",
            "categories": [cat_hotel],
            "continent": "américa",
            "climate": "tropical",
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["00:00-23:59"],
            "activities": ["playa", "ciudad", "noche", "gastronomia"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["fasano_rio_1.jpg", "fasano_rio_2.jpg"],
            "reviews": [
                (
                    5,
                    "La piscina en el rooftop es TODO. La vista a Ipanema y al Morro Dos Hermanos no tiene precio.",
                ),
                (
                    5,
                    "Diseño impecable, atención de primer nivel. El desayuno es espectacular.",
                ),
                (
                    4,
                    "Caro, pero es el mejor hotel de Rio sin dudas. La ubicación es perfecta.",
                ),
                (5, "Servicio de playa 10 puntos. Te sentís una celebridad."),
            ],
        },
        {
            "place_name": "Tour de Comida Callejera en Bangkok",
            "country": "Tailandia",
            "province": "Bangkok",
            "city": "Bangkok",
            "address": "Yaowarat Road (Chinatown)",
            "description": "Un festín para los sentidos en el caótico y delicioso Chinatown de Bangkok.",
            "categories": [cat_actividad, cat_gastro, cat_cultura],
            "continent": "asia",
            "climate": "tropical",
            "activities": ["gastronomia", "ciudad", "cultura", "noche"],
            "cost_per_day": 40,
            "duration_min": 1440,
            "images": ["bangkok_food_1.jpg", "bangkok_food_2.jpg"],
            "available_days": ["lunes", "martes", "viernes", "sábado"],
            "available_hours": ["17:30-20:30"],
            "reviews": [
                (
                    5,
                    "Sabores que nunca había probado. Una locura. El guía nos llevó a puestos increíbles.",
                ),
                (5, "El mejor Pad Thai de mi vida, lo comí en la calle por 2 dólares."),
                (
                    4,
                    "Es caótico y hay mucha gente, pero es parte de la experiencia. Increíble.",
                ),
                (5, "El postre de mango sticky rice... uff. Imperdible."),
            ],
        },
        {
            "place_name": "Bungee Jumping en Queenstown",
            "country": "Nueva Zelanda",
            "province": "Otago",
            "city": "Queenstown",
            "address": "Kawarau Gorge Suspension Bridge",
            "description": "Salta al vacío desde el histórico puente Kawarau, la cuna mundial del bungee.",
            "categories": [cat_actividad, cat_aventura],
            "continent": "oceanía",
            "climate": "templado",
            "activities": ["aventura", "deporte", "montaña", "naturaleza"],
            "cost_per_day": 180,
            "duration_min": 1440,
            "images": ["queenstown_bungee_1.jpg", "queenstown_bungee_2.jpg"],
            "available_days": ["lunes", "martes", "viernes", "sábado"],
            "available_hours": ["11:30-20:30"],
            "reviews": [
                (5, "¡Adrenalina pura! La sensación de caer es indescriptible."),
                (5, "Súper seguro y organizado. El staff te da toda la confianza."),
                (5, "¡Salté! No lo puedo creer. El paisaje encima es alucinante."),
                (
                    5,
                    "Si vas a Queenstown, TENÉS que hacerlo. Es la capital de la aventura.",
                ),
            ],
        },
        {
            "place_name": "Tour de Auroras Boreales",
            "country": "Islandia",
            "province": "Región Capital",
            "city": "Reikiavik",
            "address": "Salida desde Reikiavik",
            "description": "Caza la mágica danza de las luces del norte en esta excursión nocturna desde Reikiavik.",
            "categories": [cat_actividad, cat_aventura],
            "continent": "europa",
            "climate": "frío",
            "activities": ["naturaleza", "aventura", "noche"],
            "cost_per_day": 110,
            "duration_min": 1440,
            "available_days": ["lunes", "martes", "miercoles", "viernes", "sábado"],
            "available_hours": ["19:30-23:30"],
            "images": ["aurora_iceland_1.jpg", "aurora_iceland_2.jpg"],
            "reviews": [
                (5, "¡Las vimos! Bailaron en el cielo por más de una hora. Mágico."),
                (
                    2,
                    "Mala suerte. Noche nublada, no vimos absolutamente nada. Te dejan volver otro día gratis, pero igual...",
                ),
                (
                    4,
                    "Mucho frío, hay que ir MUY abrigado. El guía se esforzó mucho por encontrarlas y lo logró.",
                ),
                (
                    5,
                    "Una experiencia que hay que vivir. El chocolate caliente que te dan ayuda mucho.",
                ),
            ],
        },
        {
            "place_name": "Visita a las Pirámides de Giza",
            "country": "Egipto",
            "province": "Giza",
            "city": "Giza",
            "address": "Al Haram, Nazlet El-Semman",
            "description": "Viaja 4.500 años al pasado y maravíllate ante la última de las Siete Maravillas del Mundo Antiguo.",
            "categories": [cat_actividad, cat_cultura, cat_aventura],
            "continent": "áfrica",
            "climate": "seco",
            "activities": ["historia", "cultura", "desierto"],
            "cost_per_day": 80,
            "duration_min": 1440,
            "available_days": [
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sábado",
            ],
            "available_hours": ["10:30-18:30"],
            "images": ["giza_pyramids_1.jpg", "giza_pyramids_2.jpg"],
            "reviews": [
                (
                    5,
                    "No hay foto ni video que le haga justicia. Estar ahí es imponente.",
                ),
                (
                    3,
                    "Lo malo es la cantidad de vendedores acosando. Es agotador. Pero las pirámides, un 10.",
                ),
                (5, "Historia pura. Entrar a la Gran Pirámide fue increíble."),
                (
                    4,
                    "Recomiendo ir a primera hora de la mañana para evitar el calor y las multitudes.",
                ),
            ],
        },
        {
            "place_name": "Resort All-Inclusive en Cancún",
            "country": "México",
            "province": "Quintana Roo",
            "city": "Cancún",
            "address": "Blvd. Kukulcan, Zona Hotelera",
            "description": "Relajo total en el Caribe Mexicano. Disfruta de playas turquesas y entretenimiento sin fin.",
            "categories": [cat_hotel],
            "continent": "américa",
            "climate": "tropical",
            "activities": ["playa", "relax", "noche", "gastronomia"],
            "cost_per_day": None,
            "duration_min": None,
            "images": ["cancun_resort_1.jpg", "cancun_resort_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["00:00-23:59"],
            "reviews": [
                (
                    4,
                    "Playa hermosa y la piscina gigante. Ideal para no moverse en una semana.",
                ),
                (
                    3,
                    "El buffet era muy repetitivo. Los restaurantes 'a la carta' eran mejores.",
                ),
                (
                    2,
                    "Demasiada gente y ruido para mi gusto. La música en la piscina estaba altísima todo el día.",
                ),
                (4, "Buena atención del personal, siempre amables. Los tragos bien."),
            ],
        },
        {
            "place_name": "Visita a la Torre Eiffel",
            "country": "Francia",
            "province": "Isla de Francia",
            "city": "París",
            "address": "Champ de Mars, 5 Av. Anatole France, 75007 Paris",
            "description": "El ícono indiscutible de París. Sube a la cima para disfrutar de vistas panorámicas inigualables de la ciudad.",
            "categories": [cat_actividad, cat_cultura],
            "continent": "europa",
            "climate": "templado",
            "activities": [
                "cultura",
                "historia",
                "ciudad",
                "romance",
                "vista_panoramica",
            ],
            "cost_per_day": 50,
            "duration_min": 120,
            "available_days": [
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": [
                "09:30-11:30",
                "12:00-14:00",
                "14:30-16:30",
                "17:00-19:00",
                "19:30-21:30",
            ],
            "images": ["torre_eiffel_1.jpg", "torre_eiffel_2.jpg"],
            "reviews": [
                (
                    5,
                    "¡Absolutamente mágico! Subir al atardecer es una experiencia que no tiene precio. París a tus pies.",
                ),
                (
                    4,
                    "Mucha, mucha fila, incluso con entrada anticipada. Pero las vistas lo valen. Impresionante.",
                ),
                (
                    5,
                    "Verla de noche, iluminada y destellando, es de las cosas más lindas que vi. Un ícono mundial.",
                ),
                (
                    3,
                    "La experiencia arriba es un poco caótica por la cantidad de gente. Pero hay que hacerlo.",
                ),
            ],
        },
        {
            "place_name": "Palacio de Versalles",
            "country": "Francia",
            "province": "Isla de Francia",
            "city": "Versalles",
            "address": "Place d'Armes, 78000 Versailles",
            "description": "Sumérgete en la opulencia de la monarquía francesa. Explora el Salón de los Espejos y los vastos jardines.",
            "categories": [cat_actividad, cat_cultura],
            "continent": "europa",
            "climate": "templado",
            "activities": ["cultura", "historia", "arte", "naturaleza", "palacio"],
            "cost_per_day": 70,
            "duration_min": 1440,
            "images": ["palacio_versalles_1.jpg", "palacio_versalles_2.jpg"],
            "available_days": [
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ],
            "available_hours": ["09:30-20:30"],
            "reviews": [
                (
                    5,
                    "El Salón de los Espejos te deja sin aliento. Es una locura pensar cómo vivían.",
                ),
                (
                    5,
                    "Los jardines son LO MEJOR. Alquilamos un carrito de golf para recorrerlos porque son inmensos. Un día no alcanza.",
                ),
                (
                    4,
                    "Absolutamente desbordado de gente. Es difícil apreciar los salones. Recomiendo ir a los Trianon, que son más tranquilos.",
                ),
                (
                    5,
                    "Historia pura en cada rincón. Es abrumador de tanta belleza y opulencia. Imperdible.",
                ),
            ],
        },
    ]

    created_count = 0
    updated_count = 0
    for item in data_to_seed:
        exists = db.query(Publication).filter_by(place_name=item["place_name"]).first()
        if exists:
            print(f"Actualizando: '{item['place_name']}'...")

            exists.country = item["country"]
            exists.province = item["province"]
            exists.city = item["city"]
            exists.address = item["address"]
            exists.description = item.get("description")
            exists.categories = item["categories"]
            exists.continent = item.get("continent")
            exists.climate = item.get("climate")
            exists.activities = item.get("activities")
            exists.cost_per_day = item.get("cost_per_day")
            exists.duration_min = item.get("duration_min")
            exists.available_days = item.get("available_days", [])
            exists.available_hours = item.get("available_hours", [])
            exists.name = item["place_name"]
            exists.street = item["address"].split(",")[0]

            db.flush()
            updated_count += 1
            db.commit()
            continue

        print(f"Creando: '{item['place_name']}'...")

        pub = Publication(
            place_name=item["place_name"],
            country=item["country"],
            province=item["province"],
            city=item["city"],
            address=item["address"],
            description=item.get("description"),
            categories=item["categories"],
            created_by_user_id=author.id,
            status="approved",
            created_at=datetime.utcnow(),
            continent=item.get("continent"),
            climate=item.get("climate"),
            activities=item.get("activities"),
            cost_per_day=item.get("cost_per_day"),
            duration_min=item.get("duration_min"),
            available_days=item.get("available_days", []),
            available_hours=item.get("available_hours", []),
            name=item["place_name"],
            street=item["address"].split(",")[0],
        )

        db.add(pub)
        db.flush()

        image_filenames = item.get("images", [])
        for idx, filename in enumerate(image_filenames):
            absolute_path = os.path.join(UPLOAD_DIR, filename)
            relative_url = f"/static/uploads/publications/{filename}"

            if os.path.exists(absolute_path):
                print(f"  > Imagen encontrada: {filename}")
                photo = PublicationPhoto(
                    publication_id=pub.id, url=relative_url, index_order=idx
                )
                db.add(photo)
            else:
                print(
                    f"  > ADVERTENCIA: No se encontró la imagen '{filename}' en {UPLOAD_DIR}"
                )

        reviews_to_add = item.get("reviews", [])
        if reviews_to_add:
            print(f"  > Creando {len(reviews_to_add)} reseñas...")
            for i, (rating, comment) in enumerate(reviews_to_add):
                reviewer = review_authors[i % len(review_authors)]

                review = Review(
                    publication_id=pub.id,
                    author_id=reviewer.id,
                    rating=rating,
                    comment=comment,
                    created_at=datetime.utcnow()
                    - timedelta(days=len(reviews_to_add) - i),
                )
                db.add(review)

            db.flush()
            update_publication_ratings(db, pub.id)

        db.commit()
        created_count += 1

    print(
        f"--- Seeding completado. {created_count} nuevas publicaciones creadas, {updated_count} actualizadas. ---"
    )


if __name__ == "__main__":
    print("Conectando a la base de datos...")
    db = SessionLocal()
    try:
        seed_publications(db)
    except Exception as e:
        print(f"Ocurrió un error durante el seeding: {e}")
        db.rollback()
    finally:
        db.close()
        print("Conexión cerrada.")
