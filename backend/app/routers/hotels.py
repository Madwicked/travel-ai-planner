from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.trip import Trip
from app.models.trip_stop import TripStop
from app.schemas.trip import HotelCreate
from app.services.hotels import (
    generate_hotel_options,
    create_hotel,
    get_hotels,
    delete_hotel,
    get_hotel_room_details,
)


router = APIRouter(
    prefix="/api/trips",
    tags=["Hotels"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{trip_id}/hotels/options")
def get_hotel_options(
    trip_id: int,
    stop_id: int | None = None,
    refresh: bool = False,
    page: int = 1,
    limit: int = 50,
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

    stop = None

    if stop_id is not None:
        stop = (
            db.query(TripStop)
            .filter(
                TripStop.id == stop_id,
                TripStop.trip_id == trip_id,
            )
            .first()
        )

        if stop is None:
            raise HTTPException(
                status_code=404,
                detail="Trip stop not found",
            )

    result = generate_hotel_options(
        trip,
        db,
        refresh=refresh,
        page=page,
        limit=limit,
        stop=stop,
    )

    return {
        "trip_id": trip.id,
        "destination": stop.city if stop else trip.destination,
        "stop_id": stop.id if stop else None,
        **result,
    }


@router.post("/{trip_id}/hotels")
def create_hotel_endpoint(
    trip_id: int,
    hotel: HotelCreate,
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
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return get_hotels(
        trip_id=trip_id,
        db=db,
    )

@router.get(
    "/{trip_id}/hotels/{hotel_id}/rooms/{room_code}"
)
def get_hotel_room_details_endpoint(
    trip_id: int,
    hotel_id: int,
    room_code: str,
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

    result = get_hotel_room_details(
        trip_id=trip_id,
        hotel_id=hotel_id,
        room_code=room_code,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Hotel not found",
        )

    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"],
        )

    return result

@router.delete("/{trip_id}/hotels/{hotel_id}")
def delete_hotel_endpoint(
    trip_id: int,
    hotel_id: int,
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

    result = delete_hotel(
        trip_id=trip_id,
        hotel_id=hotel_id,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Hotel not found",
        )

    return result