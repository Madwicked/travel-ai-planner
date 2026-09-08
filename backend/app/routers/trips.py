from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session



from app.services.itinerary import generate_itinerary_data
from app.services.transport import (
    create_transport,
    get_transports,
    generate_transport_options,
    generate_return_transport_options,
    update_transport,
)
from app.services.hotels import (
    generate_hotel_options,
    create_hotel,
    get_hotels,
)
from app.services.places import (
    generate_place_options,
    delete_places,
    delete_place,
    create_place,
    get_places,
)
from app.database import SessionLocal
from app.models.trip import Trip
from app.schemas.trip import (
    TripCreate,
    TripResponse,
    TransportCreate,
    TransportUpdate,
    HotelCreate,
    PlaceCreate,
)
from app.services.trips import (
    create_trip,
    get_trips,
    delete_trip,
)

router = APIRouter(
    prefix="/api/trips",
    tags=["Trips"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=TripResponse)
def create_trip_endpoint(
    trip: TripCreate,
    db: Session = Depends(get_db),
):
    return create_trip(
        trip=trip,
        db=db,
    )

@router.post("/{trip_id}/transports")
def create_transport_endpoint(
    trip_id: int,
    transport: TransportCreate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return create_transport(
        trip_id=trip_id,
        transport=transport,
        db=db,
    )


@router.get("/{trip_id}/transports")
def get_transports_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return get_transports(
        trip_id=trip_id,
        db=db,
    )


@router.get("/{trip_id}/transports/options")
def get_transport_options(
    trip_id: int,
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    result = generate_transport_options(
        trip,
        db,
        refresh=refresh,
    )

    return {
        "trip_id": trip.id,
        "origin": trip.origin,
        "destination": trip.destination,
        **result,
    }


@router.get("/{trip_id}/transports/return-options")
def get_return_transport_options(
    trip_id: int,
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    result = generate_return_transport_options(
        trip,
        db,
        refresh=refresh,
    )

    return {
        "trip_id": trip.id,
        "origin": trip.destination,
        "destination": trip.origin,
        **result,
    }


@router.put("/{trip_id}/transport")
def update_transport_endpoint(
    trip_id: int,
    transport: TransportUpdate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return update_transport(
        trip_id=trip_id,
        transport=transport,
        db=db,
    )

@router.get("/{trip_id}/hotels/options")
@router.get("/{trip_id}/hotels/options")
def get_hotel_options(
    trip_id: int,
    refresh: bool = False,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    result = generate_hotel_options(
        trip,
        db,
        refresh=refresh,
    )

    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        **result,
    }


@router.post("/{trip_id}/hotels")
def create_hotel_endpoint(
    trip_id: int,
    hotel: HotelCreate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return create_hotel(
        trip_id=trip_id,
        hotel=hotel,
        db=db,
    )


@router.get("/{trip_id}/hotels")
def get_hotels_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return get_hotels(
        trip_id=trip_id,
        db=db,
    )


@router.get("/{trip_id}/places/options")
def get_place_options(
    trip_id: int,
    radius_km: int = 10,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    options = generate_place_options(
        trip,
        radius_km=radius_km,
    )

    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "options": options,
    }


@router.delete("/{trip_id}/places")
def delete_places_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return delete_places(
        trip_id=trip_id,
        db=db,
    )

@router.delete("/{trip_id}/places/{place_id}")
def delete_place_endpoint(
    trip_id: int,
    place_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

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


@router.post("/{trip_id}/places")
def create_place_endpoint(
    trip_id: int,
    place: PlaceCreate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

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


@router.get("/{trip_id}/places")
def get_places_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return get_places(
        trip_id=trip_id,
        db=db,
    )

@router.get("/{trip_id}/itinerary")
def get_itinerary(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return generate_itinerary_data(
        trip_id=trip_id,
        db=db,
    )

@router.get("")
def get_trips_endpoint(
    db: Session = Depends(get_db),
):
    return get_trips(db=db)

@router.delete("/{trip_id}")
def delete_trip_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    result = delete_trip(
        trip_id=trip_id,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return result

