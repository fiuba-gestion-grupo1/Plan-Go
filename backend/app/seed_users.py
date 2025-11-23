import json
from sqlalchemy.orm import Session

try:
    from backend.app.db import SessionLocal
    from backend.app import models, security
except ImportError:
    print("Error: Ejecutá este script como módulo desde la raíz del proyecto.")
    print("Ejemplo: python -m backend.app.seed_users")
    raise


def create_or_update_user(
    db: Session,
    *,
    email: str,
    username: str,
    password: str,
    role: str,
    first_name: str | None = None,
    last_name: str | None = None,
    travel_profile: dict | None = None,
):
    """
    Crea el usuario si no existe. Si existe, actualiza password/role y perfil de viaje si difieren.
    El perfil de viaje se guarda en el campo `travel_preferences` como JSON.
    """
    travel_preferences_str = None
    if travel_profile is not None:
        travel_preferences_str = json.dumps(travel_profile, ensure_ascii=False)

    user = db.query(models.User).filter(models.User.email == email).first()

    if user:
        changed = False

        if user.role != role:
            user.role = role
            changed = True

        if first_name is not None and user.first_name != first_name:
            user.first_name = first_name
            changed = True

        if last_name is not None and user.last_name != last_name:
            user.last_name = last_name
            changed = True

        new_hashed = security.hash_password(password)
        if user.hashed_password != new_hashed:
            user.hashed_password = new_hashed
            changed = True

        if (
            travel_preferences_str is not None
            and user.travel_preferences != travel_preferences_str
        ):
            user.travel_preferences = travel_preferences_str
            changed = True

        if changed:
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Actualizado: {email} (role={role})")
        else:
            print(f"Sin cambios: {email}")
        return user

    new_user = models.User(
        email=email,
        username=username,
        hashed_password=security.hash_password(password),
        role=role,
        first_name=first_name,
        last_name=last_name,
        birth_date=None,
        travel_preferences=travel_preferences_str,
        security_question_1=None,
        hashed_answer_1=None,
        security_question_2=None,
        hashed_answer_2=None,
        profile_picture_url=None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f"Creado: {email} (role={role})")
    return new_user


def seed_users(db: Session):
    print("--- Iniciando Seeding de Usuarios ---")
    create_or_update_user(
        db,
        email="admin@fi.uba.ar",
        username="admin",
        password="password",
        role="admin",
        first_name="Admin",
        travel_profile={
            "city": "Buenos Aires, Argentina",
            "destinations": ["Europa", "Estados Unidos", "Patagonia"],
            "style": "Work & travel",
            "budget": "$$$",
            "about": "Me gusta combinar viajes de trabajo con tiempo libre para conocer ciudades nuevas.",
            "tags": ["Tecnología", "Ciudades grandes", "Restaurantes"],
        },
    )

    create_or_update_user(
        db,
        email="normal@fi.uba.ar",
        username="normal",
        password="password",
        role="user",
        first_name="Usuario",
        last_name="Normal",
        travel_profile={
            "city": "La Plata, Argentina",
            "destinations": ["Brasil", "Costa Atlántica", "Sierras de Córdoba"],
            "style": "Relajado",
            "budget": "$$",
            "about": "Prefiero viajes simples, playa y algo de naturaleza sin tanta planificación.",
            "tags": ["Playas", "Cabañas", "Escapadas de finde"],
        },
    )

    create_or_update_user(
        db,
        email="premium@fi.uba.ar",
        username="premium",
        password="password",
        role="premium",
        first_name="Usuario",
        last_name="Premium",
        travel_profile={
            "city": "Buenos Aires, Argentina",
            "destinations": ["Caribe", "Europa"],
            "style": "Confort & experiencias",
            "budget": "$$$",
            "about": "Busco hoteles cómodos y buenas experiencias gastronómicas.",
            "tags": ["Hoteles boutique", "Vino", "City tours"],
        },
    )

    create_or_update_user(
        db,
        email="premium2@fi.uba.ar",
        username="premium2",
        password="password",
        role="premium",
        first_name="Viajero",
        last_name="Premium 2",
        travel_profile={
            "city": "Córdoba, Argentina",
            "destinations": ["Noroeste argentino", "Bolivia", "Perú"],
            "style": "Aventura",
            "budget": "$$",
            "about": "Me gustan los roadtrips, la montaña y los destinos poco turísticos.",
            "tags": ["Montaña", "Roadtrip", "Trekking"],
        },
    )

    create_or_update_user(
        db,
        email="premium3@fi.uba.ar",
        username="premium3",
        password="password",
        role="premium",
        first_name="Viajera",
        last_name="Premium 3",
        travel_profile={
            "city": "Rosario, Argentina",
            "destinations": ["Madrid", "Barcelona", "Montevideo"],
            "style": "City break",
            "budget": "$$",
            "about": "Me encantan las escapadas cortas para conocer barrios, cafés y museos.",
            "tags": ["Museos", "Cafés", "Mercados"],
        },
    )

    create_or_update_user(
        db,
        email="agus.viajes@fi.uba.ar",
        username="agus.viajes",
        password="password",
        role="user",
        first_name="Agustina",
        travel_profile={
            "city": "Buenos Aires, Argentina",
            "destinations": ["Europa", "París", "Roma"],
            "style": "Low cost & cultural",
            "budget": "$$",
            "about": "Me encantan las ciudades con historia, los museos y los cafés lindos.",
            "tags": ["Museos", "Café", "Caminatas", "Hostels"],
        },
    )

    create_or_update_user(
        db,
        email="viajero.nomade@fi.uba.ar",
        username="viajero.nomade",
        password="password",
        role="user",
        first_name="Nicolás",
        travel_profile={
            "city": "Córdoba, Argentina",
            "destinations": ["Sudeste Asiático", "Tailandia"],
            "style": "Mochilero",
            "budget": "$",
            "about": "Busco gente para viajes largos, poca planificación y mucha aventura.",
            "tags": ["Backpacking", "Playas", "Street food"],
        },
    )

    create_or_update_user(
        db,
        email="city.breaks@fi.uba.ar",
        username="city.breaks",
        password="password",
        role="user",
        first_name="Valen",
        travel_profile={
            "city": "Montevideo, Uruguay",
            "destinations": ["Europa", "Madrid", "Londres"],
            "style": "City break",
            "budget": "$$$",
            "about": "Amo las escapadas cortas, los buenos restaurantes y los barrios con encanto.",
            "tags": ["Restaurantes", "Airbnb", "Mercados"],
        },
    )

    create_or_update_user(
        db,
        email="familia.onboard@fi.uba.ar",
        username="familia.onboard",
        password="password",
        role="user",
        first_name="Mariana",
        travel_profile={
            "city": "Rosario, Argentina",
            "destinations": ["Brasil", "Caribe"],
            "style": "En familia",
            "budget": "$$",
            "about": "Viajo con niños, busco planes tranquilos y alojamientos cómodos.",
            "tags": ["Niños", "All inclusive", "Playa"],
        },
    )

    create_or_update_user(
        db,
        email="solo.traveler@fi.uba.ar",
        username="solo.traveler",
        password="password",
        role="user",
        first_name="Sofi",
        travel_profile={
            "city": "Santiago, Chile",
            "destinations": ["Europa", "Lisboa", "Barcelona"],
            "style": "Solo traveler",
            "budget": "$$",
            "about": "Me gusta viajar sola pero compartir algunos planes con otras personas.",
            "tags": ["Co-working", "Cafés", "Tours a pie"],
        },
    )

    print("--- Seeding de Usuarios completado ---")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_users(db)
    except Exception as e:
        print(f"Ocurrió un error durante el seeding de usuarios: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        print("Conexión cerrada.")
