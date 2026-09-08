from sqlalchemy.orm import Session

from app.models.hotel import TripHotel
from app.models.trip import Trip
from app.schemas.trip import HotelCreate
from app.services.hotel_provider import hotel_provider
from app.services.cache_service import cache_service


def generate_hotel_options(
    trip,
    db: Session,
    refresh: bool = False,
):
    cache = cache_service.get(
        db=db,
        trip_id=trip.id,
        cache_type="hotel",
    )

    if cache and not refresh:
        outdated = cache_service.is_expired(
            cache,
            ttl_minutes=5,
        )

        return {
            "options": cache_service.load_data(cache),
            "cached": True,
            "outdated": outdated,
            "fetched_at": cache.fetched_at,
            "expires_at": cache_service.get_expires_at(
                cache,
                ttl_minutes=5,
            ),
        }

    options = hotel_provider.get_hotel_options(
        trip
    )

    cache = cache_service.save(
        db=db,
        trip_id=trip.id,
        cache_type="hotel",
        data=options,
    )

    return {
        "options": options,
        "cached": False,
        "outdated": False,
        "fetched_at": cache.fetched_at,
        "expires_at": cache_service.get_expires_at(
            cache,
            ttl_minutes=5,
        ),
    }


def create_hotel(
    trip_id: int,
    hotel: HotelCreate,
    db: Session,
):
    existing_hotel = (
        db.query(TripHotel)
        .filter(
            TripHotel.trip_id == trip_id,
        )
        .first()
    )

    if existing_hotel:
        db.delete(existing_hotel)
        db.flush()

    new_hotel = TripHotel(
        trip_id=trip_id,
        name=hotel.name,
        city=hotel.city,
        address=hotel.address,
        price_per_night=hotel.price_per_night,
        nights=hotel.nights,
        total_price=hotel.total_price,
        check_in=hotel.check_in,
        check_out=hotel.check_out,
    )

    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)

    return {
        "message": "Hotel created",
        "hotel": {
            "id": new_hotel.id,
            "trip_id": new_hotel.trip_id,
            "name": new_hotel.name,
            "city": new_hotel.city,
            "address": new_hotel.address,
            "price_per_night": new_hotel.price_per_night,
            "nights": new_hotel.nights,
            "total_price": new_hotel.total_price,
            "check_in": new_hotel.check_in,
            "check_out": new_hotel.check_out,
        },
    }


def get_hotels(
    trip_id: int,
    db: Session,
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    hotels = (
        db.query(TripHotel)
        .filter(TripHotel.trip_id == trip_id)
        .order_by(TripHotel.id)
        .all()
    )

    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "hotels": [
            {
                "id": hotel.id,
                "name": hotel.name,
                "city": hotel.city,
                "address": hotel.address,
                "price_per_night": hotel.price_per_night,
                "nights": hotel.nights,
                "total_price": hotel.total_price,
                "check_in": hotel.check_in,
                "check_out": hotel.check_out,
            }
            for hotel in hotels
        ],
    }