from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.trip import Trip
from app.services.itinerary import generate_itinerary_data


router = APIRouter(
    prefix="/api/trips",
    tags=["Itinerary"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{trip_id}/itinerary")
def get_itinerary(
    trip_id: int,
    include_arrival_day: bool = False,
    include_departure_day: bool = False,
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

    print(
        "ITINERARY REQUEST:",
        trip_id,
        include_arrival_day,
        include_departure_day,
    )

    return generate_itinerary_data(
        trip_id=trip_id,
        db=db,
        include_arrival_day=include_arrival_day,
        include_departure_day=include_departure_day,
    )