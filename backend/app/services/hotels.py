from sqlalchemy.orm import Session

from app.models.hotel import TripHotel
from app.models.trip import Trip
from app.schemas.trip import HotelCreate
from app.services.hotel_provider import hotel_provider

def generate_hotel_options(trip):
    return hotel_provider.get_hotel_options(trip)


def create_hotel(
    trip_id: int,
    hotel: HotelCreate,
    db: Session,
):
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