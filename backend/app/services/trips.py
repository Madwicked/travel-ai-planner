from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.transport import TripTransport
from app.models.hotel import TripHotel
from app.models.place import TripPlace
from app.schemas.trip import TripCreate
from app.models.api_cache import ApiCache



COUNTRY_CURRENCIES = {
    "Italy": "EUR",
    "France": "EUR",
    "Germany": "EUR",
    "Spain": "EUR",
    "Portugal": "EUR",
    "Greece": "EUR",
    "Austria": "EUR",
    "Serbia": "RSD",
    "Turkey": "TRY",
    "United Kingdom": "GBP",
    "United States": "USD",
    "Canada": "CAD",
    "Japan": "JPY",
    "China": "CNY",
    "Thailand": "THB",
    "United Arab Emirates": "AED",
    "Switzerland": "CHF",
}

CITY_COUNTRIES = {
    "Rome": "Italy",
    "Belgrade": "Serbia",
    "Paris": "France",
    "Berlin": "Germany",
    "Madrid": "Spain",
    "Lisbon": "Portugal",
    "Athens": "Greece",
    "Vienna": "Austria",
    "Istanbul": "Turkey",
    "London": "United Kingdom",
    "New York": "United States",
    "Toronto": "Canada",
    "Tokyo": "Japan",
    "Beijing": "China",
    "Bangkok": "Thailand",
    "Dubai": "United Arab Emirates",
    "Zurich": "Switzerland",
}

def create_trip(
    trip: TripCreate,
    db: Session,
):
    destination_country = trip.destination_country

    if not destination_country:
        destination_country = CITY_COUNTRIES.get(
            trip.destination
        )

    new_trip = Trip(
        origin=trip.origin,
        origin_country=trip.origin_country,
        origin_latitude=trip.origin_latitude,
        origin_longitude=trip.origin_longitude,

        destination=trip.destination,
        destination_country=trip.destination_country,
        destination_currency=COUNTRY_CURRENCIES.get(
            destination_country
        ),

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