import hashlib
import json

from sqlalchemy.orm import Session

from app.models.place import TripPlace
from app.schemas.trip import PlaceCreate
from app.services.cache_service import cache_service
from app.services.geoapify_places import (
    DEFAULT_LIMIT_PER_CATEGORY,
    GeoapifyPlacesService,
)
from app.services.location_provider import location_provider
from app.services.wikipedia_discovery import (
    WikipediaDiscoveryService,
)


PLACES_CACHE_TTL_MINUTES = 30

DEFAULT_DISCOVERY_RADIUS_KM = 25


CATEGORY_LABELS = {
    "attractions": "Attractions",
    "nature": "Nature",
    "entertainment": "Entertainment",
    "food": "Food",
    "shopping": "Shopping",
}


def _build_places_cache_type(
    trip_id: int,
    latitude: float | None,
    longitude: float | None,
    radius_km: int | None,
    country_place_id: str | None,
    search: str | None,
    search_type: str,
) -> str:
    cache_params = {
        "trip_id": trip_id,
        "latitude": latitude,
        "longitude": longitude,
        "radius_km": radius_km,
        "country_place_id": country_place_id,
        "search": search,
        "search_type": search_type,
    }

    params_json = json.dumps(
        cache_params,
        sort_keys=True,
        default=str,
    )

    digest = hashlib.sha1(
        params_json.encode("utf-8")
    ).hexdigest()[:20]

    return f"places_v5_{digest}"


def _empty_places_response(
    offset: int,
    limit: int,
) -> dict:
    return {
        "options": [],
        "total": 0,
        "offset": offset,
        "limit": limit,
        "has_more": False,
    }


def _build_trip_place(
    trip_id: int,
    place: PlaceCreate,
) -> TripPlace:
    return TripPlace(
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


def _place_to_dict(
    place: TripPlace,
) -> dict:
    return {
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


def _normalize_category(
    category: str | None,
) -> str | None:
    if not category:
        return None

    category_key = category.strip().casefold()

    return CATEGORY_LABELS.get(
        category_key,
        category,
    )


def _normalize_place_category(
    place: dict,
) -> dict:
    normalized = dict(place)

    category = normalized.get(
        "category"
    )

    normalized["category"] = (
        _normalize_category(category)
    )

    normalized.pop(
        "_geo_categories",
        None,
    )

    normalized.pop(
        "_wikipedia_match",
        None,
    )

    normalized.pop(
        "_wikidata_id",
        None,
    )

    return normalized


def _build_wikipedia_place(
    candidate: dict,
    category: str,
    city: str | None,
    country: str | None,
) -> dict:
    return {
        "external_id": candidate.get(
            "wikidata_id"
        ),
        "source": "wikipedia",
        "name": candidate.get(
            "title"
        ),
        "city": city,
        "country": country,
        "category": category,
        "address": None,
        "latitude": candidate.get(
            "latitude"
        ),
        "longitude": candidate.get(
            "longitude"
        ),
        "distance_km": candidate.get(
            "distance_km"
        ),
        "rating": None,
        "opening_hours": None,
        "opening_time": None,
        "closing_time": None,
        "visit_duration": None,
    }


def _load_wikipedia_city_places(
    latitude: float,
    longitude: float,
    radius_km: float,
    city: str,
    country: str,
    category: str,
) -> list[dict]:
    wikipedia_service = WikipediaDiscoveryService()

    candidates = wikipedia_service.discover(
        city=city,
        country=country,
        target_latitude=latitude,
        target_longitude=longitude,
        radius_km=radius_km,
        category=category,
    )

    options = [
        _build_wikipedia_place(
            candidate=candidate,
            category=category,
            city=city,
            country=country,
        )
        for candidate in candidates
    ]

    return [
        _normalize_place_category(option)
        for option in options
        if option.get("name")
        and option.get("latitude") is not None
        and option.get("longitude") is not None
    ]


def _load_wikipedia_country_places(
    country: str,
    category: str,
) -> list[dict]:
    wikipedia_service = WikipediaDiscoveryService()

    candidates = (
        wikipedia_service.discover_by_country(
            country=country,
            category=category,
        )
    )

    options = [
        _build_wikipedia_place(
            candidate=candidate,
            category=category,
            city=None,
            country=country,
        )
        for candidate in candidates
    ]

    return [
        _normalize_place_category(option)
        for option in options
        if option.get("name")
        and option.get("latitude") is not None
        and option.get("longitude") is not None
    ]


def _load_places_from_geoapify(
    latitude: float | None,
    longitude: float | None,
    radius_km: float | None,
    country_place_id: str | None,
    city: str | None,
    country: str | None,
) -> list[dict]:
    service = GeoapifyPlacesService()

    discovery_radius = (
        radius_km
        if radius_km is not None
        else DEFAULT_DISCOVERY_RADIUS_KM
    )

    options = []

    # ---------------------------------------------------------
    # City search:
    # Attractions / Nature / Entertainment -> Wikipedia
    # Food / Shopping -> Geoapify
    # ---------------------------------------------------------
    if (
        country_place_id is None
        and latitude is not None
        and longitude is not None
        and city
        and country
    ):
        wikipedia_service = WikipediaDiscoveryService()

        candidates = wikipedia_service.discover_all_categories(
            city=city,
            country=country,
            target_latitude=latitude,
            target_longitude=longitude,
            radius_km=discovery_radius,
        )

        options.extend(
            _normalize_place_category(
                _build_wikipedia_place(
                    candidate=candidate,
                    category=candidate["source_category"],
                    city=city,
                    country=country,
                )
            )
            for candidate in candidates
            if candidate.get("title")
            and candidate.get("latitude") is not None
            and candidate.get("longitude") is not None
        )

        geo_options = service.get_places_by_categories(
            latitude=latitude,
            longitude=longitude,
            radius_km=discovery_radius,
            categories=[
                "food",
                "shopping",
            ],
            limit=DEFAULT_LIMIT_PER_CATEGORY,
        )

        options.extend(
            _normalize_place_category(option)
            for option in geo_options
        )

        return [
            option
            for option in options
            if option.get("name")
            and option.get("latitude") is not None
            and option.get("longitude") is not None
        ]


    # ---------------------------------------------------------
    # Country search:
    # Attractions / Nature / Entertainment -> Wikipedia
    # Food / Shopping -> Geoapify
    # ---------------------------------------------------------
    if (
        country_place_id
        and country
    ):
        for wikipedia_category in (
            "Attractions",
            "Nature",
            "Entertainment",
        ):
            options.extend(
                _load_wikipedia_country_places(
                    country=country,
                    category=wikipedia_category,
                )
            )

        geo_options = service.get_places_by_country_categories(
            country_place_id=country_place_id,
            categories=[
                "food",
                "shopping",
            ],
            limit=DEFAULT_LIMIT_PER_CATEGORY,
        )

        options.extend(
            _normalize_place_category(option)
            for option in geo_options
        )

        return [
            option
            for option in options
            if option.get("name")
            and option.get("latitude") is not None
            and option.get("longitude") is not None
        ]

    return []


def _filter_by_category(
    options: list[dict],
    category: str | None,
) -> list[dict]:
    if not category:
        return options

    normalized_category = _normalize_category(
        category
    )

    return [
        option
        for option in options
        if option.get("category")
        == normalized_category
    ]


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

    city = trip.destination
    country = trip.destination_country

    # ---------------------------------------------------------
    # Country search
    # ---------------------------------------------------------
    if search_type == "country" and not search:
        if not country:
            return _empty_places_response(
                offset,
                limit,
            )

        country_place_id = (
            location_provider.get_country_place_id(
                country
            )
        )

        if not country_place_id:
            return _empty_places_response(
                offset,
                limit,
            )

        latitude = None
        longitude = None
        radius_km = None

    # ---------------------------------------------------------
    # Explicit location search
    # ---------------------------------------------------------
    elif search:
        location = location_provider.search_locations(
            search,
            search_type,
        )

        if location is None:
            return _empty_places_response(
                offset,
                limit,
            )

        latitude = location["latitude"]
        longitude = location["longitude"]

        city = location.get(
            "name",
            search,
        )

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

    # ---------------------------------------------------------
    # Cache contains ALL categories.
    # Category is intentionally NOT part of cache key.
    # ---------------------------------------------------------
    cache_type = _build_places_cache_type(
        trip_id=trip.id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        country_place_id=country_place_id,
        search=search,
        search_type=search_type,
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
        cached_data = cache_service.load_data(
            cache
        )

        options = cached_data.get(
            "options",
            [],
        )

    else:
        if not city or not country:
            return _empty_places_response(
                offset,
                limit,
            )

        options = _load_places_from_geoapify(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            country_place_id=country_place_id,
            city=city,
            country=country,
        )

        cache_service.save(
            db=db,
            trip_id=trip.id,
            cache_type=cache_type,
            data={
                "options": options,
            },
        )

    # ---------------------------------------------------------
    # Category filtering happens AFTER cache loading.
    # ---------------------------------------------------------

    options = _filter_by_category(
        options,
        category,
    )

    total = len(options)

    paginated_options = options[
        offset:offset + limit
    ]

    return {
        "options": paginated_options,
        "total": total,
        "offset": offset,
        "limit": len(paginated_options),
        "has_more": (
            offset + limit < total
        ),
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
    new_place = _build_trip_place(
        trip_id,
        place,
    )

    db.add(new_place)
    db.commit()
    db.refresh(new_place)

    return {
        "message": "Place saved",
        "place": _place_to_dict(
            new_place
        ),
    }


def create_places_bulk(
    trip_id: int,
    places: list[PlaceCreate],
    db: Session,
):
    existing_places = (
        db.query(TripPlace)
        .filter(
            TripPlace.trip_id == trip_id
        )
        .all()
    )

    existing_keys = {
        (
            place.external_id,
            place.category,
        )
        for place in existing_places
    }

    new_places = []
    added_keys = set()

    for place in places:
        key = (
            place.external_id,
            place.category,
        )

        if key in existing_keys:
            continue

        if key in added_keys:
            continue

        new_place = _build_trip_place(
            trip_id,
            place,
        )

        new_places.append(new_place)
        added_keys.add(key)

    if new_places:
        db.add_all(new_places)
        db.commit()

        for place in new_places:
            db.refresh(place)

    return {
        "message": "Places saved",
        "trip_id": trip_id,
        "count": len(new_places),
        "places": [
            _place_to_dict(place)
            for place in new_places
        ],
    }

def get_places(
    trip_id: int,
    db: Session,
):
    places = (
        db.query(TripPlace)
        .filter(
            TripPlace.trip_id == trip_id
        )
        .order_by(TripPlace.name)
        .all()
    )

    return {
        "trip_id": trip_id,
        "places": [
            _place_to_dict(place)
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