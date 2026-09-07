from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.transport import TripTransport
from app.models.hotel import TripHotel
from app.models.place import TripPlace
from app.schemas.trip import TripCreate


def create_trip(
    trip: TripCreate,
    db: Session,
):
    new_trip = Trip(
        origin=trip.origin,
        origin_country=trip.origin_country,
        origin_latitude=trip.origin_latitude,
        origin_longitude=trip.origin_longitude,

        destination=trip.destination,
        destination_country=trip.destination_country,
        destination_latitude=trip.destination_latitude,
        destination_longitude=trip.destination_longitude,

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
        .order_by(Trip.start_date, Trip.id)
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


def delete_trip(
    trip_id: int,
    db: Session,
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        return None

    db.query(TripTransport).filter(
        TripTransport.trip_id == trip_id
    ).delete()

    db.query(TripHotel).filter(
        TripHotel.trip_id == trip_id
    ).delete()

    db.query(TripPlace).filter(
        TripPlace.trip_id == trip_id
    ).delete()

    db.delete(trip)
    db.commit()

    return {
        "message": "Trip deleted",
        "trip_id": trip_id,
    }