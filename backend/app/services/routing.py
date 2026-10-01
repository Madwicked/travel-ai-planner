from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.place import TripPlace
from app.services.routing_provider import mapbox_routing_provider


def get_walking_route(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
):
    return mapbox_routing_provider.get_walking_route(
        origin_latitude=origin_latitude,
        origin_longitude=origin_longitude,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
    )


def get_optimized_walking_route(
    points: list[tuple[float, float]],
):
    return mapbox_routing_provider.get_optimized_walking_route(
        points=points,
    )


def get_optimized_walking_route_for_trip(
    trip_id: int,
    db: Session,
):
    places = (
        db.query(TripPlace)
        .filter(
            TripPlace.trip_id == trip_id,
            TripPlace.latitude.isnot(None),
            TripPlace.longitude.isnot(None),
        )
        .order_by(TripPlace.id)
        .all()
    )

    if len(places) < 2:
        raise ValueError(
            "At least 2 places with coordinates are required"
        )

    points = [
        (
            place.latitude,
            place.longitude,
        )
        for place in places
    ]

    route = get_optimized_walking_route(
        points=points,
    )

    return {
        "places": [
            {
                "id": place.id,
                "name": place.name,
                "latitude": place.latitude,
                "longitude": place.longitude,
            }
            for place in places
        ],
        "order": route["order"],
        "distance": route["distance"],
        "duration": route["duration"],
        "geometry": route["geometry"],
    }