from sqlalchemy.orm import Session

from app.models.place import TripPlace
from app.models.trip import Trip
from app.schemas.trip import PlaceCreate


def generate_place_options(trip):
    return [
        {
            "external_id": "mock-colosseum",
            "source": "mock",
            "name": "Colosseum",
            "city": trip.destination,
            "category": "Culture",
            "address": "Piazza del Colosseo",
            "latitude": 41.8902,
            "longitude": 12.4922,
            "rating": 4.7,
            "opening_hours": {
                "monday": ["08:30", "19:00"],
                "tuesday": ["08:30", "19:00"],
                "wednesday": ["08:30", "19:00"],
                "thursday": ["08:30", "19:00"],
                "friday": ["08:30", "19:00"],
                "saturday": ["08:30", "19:00"],
                "sunday": ["08:30", "19:00"],
            },
            "opening_time": "08:30",
            "closing_time": "19:00",
            "visit_duration": "2h",
        },
        {
            "external_id": "mock-roman-forum",
            "source": "mock",
            "name": "Roman Forum",
            "city": trip.destination,
            "category": "Culture",
            "address": "Via della Salara Vecchia 5/6",
            "latitude": 41.8925,
            "longitude": 12.4853,
            "rating": 4.8,
            "opening_hours": {
                "monday": ["09:00", "19:15"],
                "tuesday": ["09:00", "19:15"],
                "wednesday": ["09:00", "19:15"],
                "thursday": ["09:00", "19:15"],
                "friday": ["09:00", "19:15"],
                "saturday": ["09:00", "19:15"],
                "sunday": ["09:00", "19:15"],
            },
            "opening_time": "09:00",
            "closing_time": "19:15",
            "visit_duration": "1h 30m",
        },
        {
            "external_id": "mock-trevi-fountain",
            "source": "mock",
            "name": "Trevi Fountain",
            "city": trip.destination,
            "category": "Sightseeing",
            "address": "Piazza di Trevi",
            "latitude": 41.9009,
            "longitude": 12.4833,
            "rating": 4.8,
            "opening_hours": {
                "monday": ["00:00", "23:59"],
                "tuesday": ["00:00", "23:59"],
                "wednesday": ["00:00", "23:59"],
                "thursday": ["00:00", "23:59"],
                "friday": ["00:00", "23:59"],
                "saturday": ["00:00", "23:59"],
                "sunday": ["00:00", "23:59"],
            },
            "opening_time": "00:00",
            "closing_time": "23:59",
            "visit_duration": "30m",
        },
        {
            "external_id": "mock-villa-borghese",
            "source": "mock",
            "name": "Villa Borghese",
            "city": trip.destination,
            "category": "Nature",
            "address": "Piazzale Scipione Borghese 5",
            "latitude": 41.9142,
            "longitude": 12.4923,
            "rating": 4.6,
            "opening_hours": {
                "monday": ["09:00", "19:00"],
                "tuesday": ["09:00", "19:00"],
                "wednesday": ["09:00", "19:00"],
                "thursday": ["09:00", "19:00"],
                "friday": ["09:00", "19:00"],
                "saturday": ["09:00", "19:00"],
                "sunday": ["09:00", "19:00"],
            },
            "opening_time": "09:00",
            "closing_time": "19:00",
            "visit_duration": "2h",
        },
        {
            "external_id": "mock-pantheon",
            "source": "mock",
            "name": "Pantheon",
            "city": trip.destination,
            "category": "Culture",
            "address": "Piazza della Rotonda",
            "latitude": 41.8986,
            "longitude": 12.4769,
            "rating": 4.7,
            "opening_hours": {
                "monday": ["09:00", "19:00"],
                "tuesday": ["09:00", "19:00"],
                "wednesday": ["09:00", "19:00"],
                "thursday": ["09:00", "19:00"],
                "friday": ["09:00", "19:00"],
                "saturday": ["09:00", "19:00"],
                "sunday": ["09:00", "19:00"],
            },
            "opening_time": "09:00",
            "closing_time": "19:00",
            "visit_duration": "1h",
        },
    ]


def delete_places(
    trip_id: int,
    db: Session,
):
    db.query(TripPlace).filter(
        TripPlace.trip_id == trip_id
    ).delete(
        synchronize_session=False
    )

    db.commit()

    return {
        "message": "Places deleted",
        "trip_id": trip_id,
    }


def create_place(
    trip_id: int,
    place: PlaceCreate,
    db: Session,
):
    new_place = TripPlace(
        trip_id=trip_id,
        external_id=place.external_id,
        source=place.source,
        name=place.name,
        city=place.city,
        category=place.category,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        rating=place.rating,
        opening_hours=place.opening_hours,
        opening_time=place.opening_time,
        closing_time=place.closing_time,
        visit_duration=place.visit_duration,
    )

    db.add(new_place)
    db.commit()
    db.refresh(new_place)

    return {
        "message": "Place saved",
        "place": {
            "id": new_place.id,
            "trip_id": new_place.trip_id,
            "external_id": new_place.external_id,
            "source": new_place.source,
            "name": new_place.name,
            "city": new_place.city,
            "category": new_place.category,
            "address": new_place.address,
            "latitude": new_place.latitude,
            "longitude": new_place.longitude,
            "rating": new_place.rating,
            "opening_hours": new_place.opening_hours,
            "opening_time": new_place.opening_time,
            "closing_time": new_place.closing_time,
            "visit_duration": new_place.visit_duration,
        },
    }


def get_places(
    trip_id: int,
    db: Session,
):
    places = (
        db.query(TripPlace)
        .filter(TripPlace.trip_id == trip_id)
        .order_by(TripPlace.id)
        .all()
    )

    return {
        "trip_id": trip_id,
        "places": [
            {
                "id": place.id,
                "trip_id": place.trip_id,
                "external_id": place.external_id,
                "source": place.source,
                "name": place.name,
                "city": place.city,
                "category": place.category,
                "address": place.address,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "rating": place.rating,
                "opening_hours": place.opening_hours,
                "opening_time": place.opening_time,
                "closing_time": place.closing_time,
                "visit_duration": place.visit_duration,
            }
            for place in places
        ],
    }