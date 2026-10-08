from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.trip import Trip
from app.models.trip_stop import TripStop
from app.schemas.trip import PlaceCreate
from app.services.places import (
    generate_place_options,
    delete_places,
    delete_place,
    create_place,
    create_places_bulk,
    get_places,
)


router = APIRouter(
    prefix="/api/trips",
    tags=["Places"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/{trip_id}/places/options")
def get_place_options(
    trip_id: int,
    stop_id: int,
    radius_km: int | None = None,
    category: str | None = None,
    offset: int = 0,
    limit: int = 50,
    search: str | None = None,
    search_type: str = Query(
        "city",
        pattern="^(city|country)$",
    ),
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    stop = (
        db.query(TripStop)
        .filter(
            TripStop.id == stop_id,
            TripStop.trip_id == trip_id,
        )
        .first()
    )

    if not stop:
        raise HTTPException(
            status_code=404,
            detail="Trip stop not found",
        )

    result = generate_place_options(
        trip,
        db=db,
        stop=stop,
        radius_km=radius_km,
        category=category,
        offset=offset,
        limit=limit,
        search=search,
        search_type=search_type,
    )

    return {
        "trip_id": trip.id,
        "stop_id": stop.id,
        "destination": stop.city,
        **result,
    }

@router.post("/{trip_id}/places")
def create_place_endpoint(
    trip_id: int,
    place: PlaceCreate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return create_place(
        trip_id=trip_id,
        place=place,
        db=db,
    )

@router.post("/{trip_id}/places/bulk")
def create_places_bulk_endpoint(
    trip_id: int,
    places: list[PlaceCreate],
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return create_places_bulk(
        trip_id=trip_id,
        places=places,
        db=db,
    )


@router.get("/{trip_id}/places")
def get_places_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return get_places(
        trip_id=trip_id,
        db=db,
    )

@router.delete("/{trip_id}/places")
def delete_places_endpoint(
    trip_id: int,
    stop_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )
    stop = (
        db.query(TripStop)
        .filter(
            TripStop.id == stop_id,
            TripStop.trip_id == trip_id,
        )
        .first()
    )

    if not stop:
        raise HTTPException(
            status_code=404,
            detail="Trip stop not found",
        )

    return delete_places(
        trip_id=trip_id,
        stop_id=stop_id,
        db=db,
    )


@router.delete("/{trip_id}/places/{place_id}")
def delete_place_endpoint(
    trip_id: int,
    place_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    result = delete_place(
        trip_id=trip_id,
        place_id=place_id,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Place not found",
        )

    return result

@router.get("/debug-wikidata/{wikidata_id}")
def debug_wikidata(
    wikidata_id: str,
):
    from app.services.wikipedia_discovery import WikipediaDiscoveryService

    service = WikipediaDiscoveryService()

    return service.debug_candidate(wikidata_id)
