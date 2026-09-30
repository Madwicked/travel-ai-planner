from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from babel.numbers import get_territory_currencies

from app.models.trip import Trip
from app.models.transport import TripTransport
from app.models.hotel import TripHotel
from app.models.place import TripPlace
from app.models.trip_stop import TripStop
from app.schemas.trip import TripCreate
from app.models.api_cache import ApiCache

def get_currency_for_country(country_code: str | None) -> str | None:
    if not country_code:
        return None

    currencies = get_territory_currencies(
        country_code.upper(),
        tender=True,
    )

    if not currencies:
        return None

    return currencies[0]




def create_trip(
    trip: TripCreate,
    db: Session,
):
    destination_country = trip.destination_country

    destination_country_code = trip.destination_country_code

    destination_currency = get_currency_for_country(
        destination_country_code
    )

    new_trip = Trip(
        origin=trip.origin,
        origin_country=trip.origin_country,
        origin_latitude=trip.origin_latitude,
        origin_longitude=trip.origin_longitude,

        destination=trip.destination,
        destination_country=destination_country,
        destination_country_code=destination_country_code,
        destination_currency=destination_currency,

        destination_latitude=trip.destination_latitude,
        destination_longitude=trip.destination_longitude,

        start_date=trip.start_date,
        end_date=trip.end_date,
        travelers=trip.travelers,
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
                "food_preference": trip.food_preference,
                "destination_currency": trip.destination_currency,
                "user_currency": trip.user_currency,
            }
            for trip in trips
        ],
    }

def update_user_currency(
    trip_id: int,
    user_currency: str,
    db: Session,
):
    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )

    if not trip:
        return None

    trip.user_currency = user_currency.upper()

    db.commit()
    db.refresh(trip)

    return {
        "message": "User currency updated",
        "trip_id": trip.id,
        "user_currency": trip.user_currency,
    }

def update_food_preference(
    trip_id: int,
    food_preference: str,
    db: Session,
):
    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )

    if not trip:
        return None

    trip.food_preference = food_preference

    db.commit()
    db.refresh(trip)

    return {
        "message": "Food preference updated",
        "trip_id": trip.id,
        "food_preference": trip.food_preference,
    }

def update_trip_dates(
    trip_id: int,
    start_date,
    end_date,
    db: Session,
):
    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )

    if not trip:
        return None

    trip.start_date = start_date
    trip.end_date = end_date

    db.commit()
    db.refresh(trip)

    return {
        "message": "Trip dates updated",
        "trip_id": trip.id,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
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

    db.query(ApiCache).filter(
        ApiCache.trip_id == trip_id
    ).delete()

    db.delete(trip)
    db.commit()

    return {
        "message": "Trip deleted",
        "trip_id": trip_id,
    }

def create_trip_stop(
    trip_id: int,
    city: str,
    country: str | None,
    latitude: float | None,
    longitude: float | None,
    start_date,
    end_date,
    db: Session,
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
    ).first()

    if trip is None:
        return None

    overlapping_stop = (
        db.query(TripStop)
        .filter(
            TripStop.trip_id == trip_id,
            TripStop.start_date < end_date,
            TripStop.end_date > start_date,
        )
        .first()
    )

    if overlapping_stop is not None:
        raise ValueError(
            f"Dates overlap with existing stop "
            f"'{overlapping_stop.city}' "
            f"({overlapping_stop.start_date} — "
            f"{overlapping_stop.end_date})"
        )

    last_stop = (
        db.query(TripStop)
        .filter(TripStop.trip_id == trip_id)
        .order_by(TripStop.sort_order.desc())
        .first()
    )

    next_sort_order = (
        last_stop.sort_order + 1
        if last_stop
        else 0
    )

    stop = TripStop(
        trip_id=trip_id,
        city=city,
        country=country,
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        sort_order=next_sort_order,
    )

    db.add(stop)
    db.commit()
    db.refresh(stop)

    return stop


def get_trip_stops(
    trip_id: int,
    db: Session,
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
    ).first()

    if trip is None:
        return None

    stops = (
        db.query(TripStop)
        .filter(TripStop.trip_id == trip_id)
        .order_by(TripStop.start_date, TripStop.id)
        .all()
    )

    return [
        {
            "id": stop.id,
            "trip_id": stop.trip_id,
            "city": stop.city,
            "country": stop.country,
            "latitude": stop.latitude,
            "longitude": stop.longitude,
            "start_date": stop.start_date,
            "end_date": stop.end_date,
            "sort_order": stop.sort_order,
        }
        for stop in stops
    ]


def update_trip_stop(
    trip_id: int,
    stop_id: int,
    city: str,
    country: str | None,
    latitude: float | None,
    longitude: float | None,
    start_date,
    end_date,
    db: Session,
):
    stop = (
        db.query(TripStop)
        .filter(
            TripStop.id == stop_id,
            TripStop.trip_id == trip_id,
        )
        .first()
    )

    if stop is None:
        return None

    overlapping_stop = (
        db.query(TripStop)
        .filter(
            TripStop.trip_id == trip_id,
            TripStop.id != stop_id,
            TripStop.start_date < end_date,
            TripStop.end_date > start_date,
        )
        .first()
    )

    if overlapping_stop is not None:
        raise ValueError(
            f"Dates overlap with existing stop "
            f"'{overlapping_stop.city}' "
            f"({overlapping_stop.start_date} — "
            f"{overlapping_stop.end_date})"
        )

    stop.city = city
    stop.country = country
    stop.latitude = latitude
    stop.longitude = longitude
    stop.start_date = start_date
    stop.end_date = end_date

    db.commit()
    db.refresh(stop)

    return stop


def delete_trip_stop(
    trip_id: int,
    stop_id: int,
    db: Session,
):
    stop = (
        db.query(TripStop)
        .filter(
            TripStop.id == stop_id,
            TripStop.trip_id == trip_id,
        )
        .first()
    )

    if stop is None:
        return None

    parent_transports = (
        db.query(TripTransport)
        .filter(
            TripTransport.trip_id == trip_id,
            ~TripTransport.transport_type.startswith("Transfer"),
        )
        .filter(
            (
                (TripTransport.direction == "outbound")
                & (TripTransport.arrival_date >= stop.start_date)
                & (TripTransport.arrival_date <= stop.end_date)
            )
            |
            (
                (TripTransport.direction == "return")
                & (TripTransport.departure_date >= stop.start_date)
                & (TripTransport.departure_date <= stop.end_date)
            )
        )
        .all()
    )

    parent_ids = [
        transport.id
        for transport in parent_transports
        if transport.id is not None
    ]

    if parent_ids:
        db.query(TripTransport).filter(
            TripTransport.trip_id == trip_id,
            TripTransport.parent_transport_id.in_(parent_ids),
            TripTransport.transport_type.startswith("Transfer"),
        ).delete(
            synchronize_session=False
        )

    db.query(TripHotel).filter(
        TripHotel.trip_id == trip_id,
        TripHotel.stop_id == stop_id,
    ).delete(synchronize_session=False)

    db.delete(stop)
    db.commit()

    return {
        "message": "Trip stop deleted",
        "stop_id": stop_id,
    }