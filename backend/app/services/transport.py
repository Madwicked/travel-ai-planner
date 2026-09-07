from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.transport import TripTransport
from app.schemas.trip import TransportCreate, TransportUpdate
from app.services.transport_provider import transport_provider


def generate_transport_options(trip):
    return transport_provider.get_outbound_options(trip)


def generate_return_transport_options(trip):
    return transport_provider.get_return_options(trip)


def create_transport(
    trip_id: int,
    transport: TransportCreate,
    db: Session,
):
    existing_transport = (
        db.query(TripTransport)
        .filter(
            TripTransport.trip_id == trip_id,
            TripTransport.direction == transport.direction,
        )
        .first()
    )

    if existing_transport:
        db.delete(existing_transport)
        db.flush()

    new_transport = TripTransport(
        trip_id=trip_id,
        direction=transport.direction,
        transport_type=transport.transport_type,
        transport_price=transport.transport_price,
        transport_duration=transport.transport_duration,
        departure_date=transport.departure_date,
        departure_time=transport.departure_time,
        departure_location=transport.departure_location,
        arrival_date=transport.arrival_date,
        arrival_time=transport.arrival_time,
        arrival_location=transport.arrival_location,
    )

    db.add(new_transport)
    db.commit()
    db.refresh(new_transport)

    return {
        "message": "Transport created",
        "transport": {
            "id": new_transport.id,
            "trip_id": new_transport.trip_id,
            "direction": new_transport.direction,
            "type": new_transport.transport_type,
            "price": new_transport.transport_price,
            "duration": new_transport.transport_duration,
            "departure_date": new_transport.departure_date,
            "departure_time": new_transport.departure_time,
            "departure_location": new_transport.departure_location,
            "arrival_date": new_transport.arrival_date,
            "arrival_time": new_transport.arrival_time,
            "arrival_location": new_transport.arrival_location,
        },
    }


def get_transports(
    trip_id: int,
    db: Session,
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    transports = (
        db.query(TripTransport)
        .filter(TripTransport.trip_id == trip_id)
        .order_by(
            TripTransport.departure_date,
            TripTransport.departure_time,
        )
        .all()
    )

    return {
        "trip_id": trip.id,
        "origin": trip.origin,
        "destination": trip.destination,
        "transports": [
            {
                "id": transport.id,
                "direction": transport.direction,
                "type": transport.transport_type,
                "price": transport.transport_price,
                "duration": transport.transport_duration,
                "departure_date": transport.departure_date,
                "departure_time": transport.departure_time,
                "departure_location": transport.departure_location,
                "arrival_date": transport.arrival_date,
                "arrival_time": transport.arrival_time,
                "arrival_location": transport.arrival_location,
            }
            for transport in transports
        ],
    }


def update_transport(
    trip_id: int,
    transport: TransportUpdate,
    db: Session,
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    trip.transport_type = transport.transport_type
    trip.transport_price = transport.transport_price
    trip.transport_duration = transport.transport_duration
    trip.transport_departure = transport.transport_departure
    trip.transport_arrival = transport.transport_arrival
    trip.transport_departure_date = transport.transport_departure_date
    trip.transport_arrival_date = transport.transport_arrival_date
    trip.transport_departure_location = (
        transport.transport_departure_location
    )
    trip.transport_arrival_location = (
        transport.transport_arrival_location
    )

    db.commit()
    db.refresh(trip)

    return {
        "message": "Transport updated",
        "trip_id": trip.id,
        "transport": transport,
    }