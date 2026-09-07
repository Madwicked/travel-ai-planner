from sqlalchemy.orm import Session

from app.models.place import TripPlace
from app.models.trip import Trip
from app.schemas.trip import PlaceCreate
from app.services.place_provider import place_provider


def generate_place_options(trip):
    return place_provider.get_place_options(trip)


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