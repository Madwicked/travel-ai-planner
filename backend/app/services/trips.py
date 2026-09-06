from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.schemas.trip import TripCreate


def create_trip(
    trip: TripCreate,
    db: Session,
):
    new_trip = Trip(
        origin=trip.origin,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        travelers=trip.travelers,
        budget=trip.budget,
        interests=", ".join(trip.interests),
    )

    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    return {
        "message": "Trip created",
        "trip_id": new_trip.id,
        "trip": trip,
    }


def get_trips(
    db: Session,
):
    trips = (
        db.query(Trip)
        .order_by(Trip.id)
        .all()
    )

    return {
        "trips": [
            {
                "id": trip.id,
                "origin": trip.origin,
                "destination": trip.destination,
                "start_date": trip.start_date,
                "end_date": trip.end_date,
                "travelers": trip.travelers,
                "budget": trip.budget,
                "interests": trip.interests,
            }
            for trip in trips
        ],
    }