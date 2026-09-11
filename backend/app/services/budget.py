from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.transport import TripTransport
from app.models.hotel import TripHotel
from app.services.currency_service import CurrencyService
from app.services.food_budget import get_food_daily_estimate
from app.services.local_transport_budget import (
    get_local_transport_ride_estimate,
    RIDES_PER_DAY,
)



def calculate_budget(
    trip_id: int,
    db: Session,
):
    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )

    if not trip:
        return None

    destination_currency = (
        trip.destination_currency or "EUR"
    )

    # -------------------------
    # Transport
    # -------------------------

    transports = (
        db.query(TripTransport)
        .filter(TripTransport.trip_id == trip_id)
        .all()
    )

    transport_total = 0.0

    for transport in transports:
        transport_total += CurrencyService.convert(
            amount=transport.transport_price,
            from_currency=transport.currency,
            to_currency=destination_currency,
        )

    # -------------------------
    # Hotel
    # -------------------------

    hotel = (
        db.query(TripHotel)
        .filter(TripHotel.trip_id == trip_id)
        .first()
    )

    hotel_total = 0.0

    if hotel:
        hotel_total = CurrencyService.convert(
            amount=hotel.total_price,
            from_currency=hotel.currency,
            to_currency=destination_currency,
        )

    # -------------------------
    # Food
    # -------------------------

    food_preference = (
            trip.food_preference
            or "Mixed"
    )

    food_daily_estimate = get_food_daily_estimate(
        country=trip.destination_country,
        food_preference=food_preference,
    )

    days = (
        trip.end_date - trip.start_date
    ).days

    food_total = (
        food_daily_estimate
        * trip.travelers
        * days
    )

    # -------------------------
    # Future expenses
    # -------------------------

    local_transport_ride_estimate = (
        get_local_transport_ride_estimate(
            trip.destination,
        )
    )

    local_transportation_total = (
            local_transport_ride_estimate
            * RIDES_PER_DAY
            * days
            * trip.travelers
    )


    activities_and_trips_total = 0.0

    # -------------------------
    # Total
    # -------------------------

    total = (
            transport_total
            + hotel_total
            + food_total
            + local_transportation_total
            + activities_and_trips_total
    )

    user_currency = trip.user_currency

    user_total = None

    if user_currency:
        user_total = CurrencyService.convert(
            amount=total,
            from_currency=destination_currency,
            to_currency=user_currency,
        )

    return {
        "trip_id": trip.id,
        "currency": destination_currency,

        "transport": {
            "amount": round(transport_total, 2),
            "currency": destination_currency,
        },

        "hotel": {
            "amount": round(hotel_total, 2),
            "currency": destination_currency,
        },

        "food": {
            "amount": round(food_total, 2),
            "currency": destination_currency,
            "preference": food_preference,
            "daily_estimate": food_daily_estimate,
        },

        "local_transportation": {
            "amount": round(
                local_transportation_total,
                2,
            ),
            "currency": destination_currency,
        },

        "activities_and_trips": {
            "amount": round(
                activities_and_trips_total,
                2,
            ),
            "currency": destination_currency,
        },

        "total": {
            "amount": round(total, 2),
            "currency": destination_currency,
        },

        "is_estimate": True,

        "user_total": {
            "amount": user_total,
            "currency": user_currency,
        } if user_currency else None,
    }