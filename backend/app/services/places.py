import hashlib
import json

from sqlalchemy.orm import Session

from app.models.place import TripPlace
from app.schemas.trip import PlaceCreate
from app.services.place_provider import place_provider
from app.services.location_provider import location_provider
from app.services.cache_service import cache_service

PLACES_CACHE_TTL_MINUTES = 30
PLACES_CACHE_LIMIT = 500


def _build_places_cache_type(
    trip_id: int,
    latitude: float | None,
    longitude: float | None,
    radius_km: int | None,
    category: str | None,
    country_place_id: str | None,
):
    cache_params = {
        "trip_id": trip_id,
        "latitude": latitude,
        "longitude": longitude,
        "radius_km": radius_km,
        "category": category,
        "country_place_id": country_place_id,
    }

    params_json = json.dumps(
        cache_params,
        sort_keys=True,
        default=str,
    )

    digest = hashlib.sha1(
        params_json.encode("utf-8")
    ).hexdigest()[:20]

    return f"places_{digest}"

def generate_place_options(
    trip,
    db: Session,
    radius_km: int | None = None,
    category: str | None = None,
    offset: int = 0,
    limit: int = 50,
    search: str | None = None,
    search_type: str = "city",
):
    latitude = trip.destination_latitude
    longitude = trip.destination_longitude
    country_place_id = None

    if search_type == "country" and not search:
        country = trip.destination_country

        if not country:
            return {
                "options": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "has_more": False,
            }

        country_place_id = (
            location_provider.get_country_place_id(country)
        )

        if not country_place_id:
            return {
                "options": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "has_more": False,
            }

        latitude = None
        longitude = None
        radius_km = None

    elif search:
        location = location_provider.search_locations(
            search,
            search_type,
        )

        if location is None:
            return {
                "options": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "has_more": False,
            }

        latitude = location["latitude"]
        longitude = location["longitude"]

    if (
        country_place_id is None
        and (
            latitude is None
            or longitude is None
        )
    ):
        raise ValueError(
            "Destination coordinates are required"
        )

    cache_type = _build_places_cache_type(
        trip_id=trip.id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        category=category,
        country_place_id=country_place_id,
    )

    cache = cache_service.get(
        db=db,
        trip_id=trip.id,
        cache_type=cache_type,
    )

    if cache and not cache_service.is_expired(
        cache,
        PLACES_CACHE_TTL_MINUTES,
    ):

        cached_data = cache_service.load_data(cache)

        options = cached_data.get("options", [])

    else:

        result = place_provider.get_place_options(
            trip,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            category=category,
            offset=0,
            limit=PLACES_CACHE_LIMIT,
            country_place_id=country_place_id,
        )

        options = result.get("options", [])

        cache_service.save(
            db=db,
            trip_id=trip.id,
            cache_type=cache_type,
            data={
                "options": options,
            },
        )
    return {
        "options": options,
        "total": len(options),
        "offset": 0,
        "limit": len(options),
        "has_more": False,
    }




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
        country=place.country,
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
            "country": new_place.country,
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

def create_places_bulk(
    trip_id: int,
    places: list[PlaceCreate],
    db: Session,
):
    new_places = [
        TripPlace(
            trip_id=trip_id,
            external_id=place.external_id,
            source=place.source,
            name=place.name,
            city=place.city,
            country=place.country,
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
        for place in places
    ]

    db.add_all(new_places)
    db.commit()

    for place in new_places:
        db.refresh(place)

    return {
        "message": "Places saved",
        "trip_id": trip_id,
        "count": len(new_places),
        "places": [
            {
                "id": place.id,
                "trip_id": place.trip_id,
                "external_id": place.external_id,
                "source": place.source,
                "name": place.name,
                "city": place.city,
                "country": place.country,
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
            for place in new_places
        ],
    }


def get_places(
    trip_id: int,
    db: Session,
):
    places = (
        db.query(TripPlace)
        .filter(TripPlace.trip_id == trip_id)
        .order_by(TripPlace.name)
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
                "country": place.country,
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
def delete_place(
    trip_id: int,
    place_id: int,
    db: Session,
):
    place = (
        db.query(TripPlace)
        .filter(
            TripPlace.id == place_id,
            TripPlace.trip_id == trip_id,
        )
        .first()
    )

    if place is None:
        return None

    db.delete(place)
    db.commit()

    return {
        "message": "Place deleted",
        "trip_id": trip_id,
        "place_id": place_id,
    }