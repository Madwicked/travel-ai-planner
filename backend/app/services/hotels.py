from sqlalchemy.orm import Session
import json
from app.models.hotel import TripHotel
from app.models.trip import Trip
from app.models.hotel_content import HotelContent
from app.models.hotel_room import HotelRoom
from app.schemas.trip import HotelCreate
from app.services.hotel_provider import hotel_provider
from app.services.cache_service import cache_service
from app.services.currency_service import currency_service





def generate_hotel_options(
    trip,
    db: Session,
    refresh: bool = False,
    page: int = 1,
    limit: int = 50,
):
    cache = cache_service.get(
        db=db,
        trip_id=trip.id,
        cache_type="hotel",
    )
    if page < 1:
        page = 1

    if limit < 1:
        limit = 50

    start = (page - 1) * limit
    end = start + limit

    if cache and not refresh:
        outdated = cache_service.is_expired(
            cache,
            ttl_minutes=5,
        )

        options = cache_service.load_data(cache)
        total_options = len(options)
        page_options = options[start:end]

        display_options = [
            {
                **option,

                "destination_price": currency_service.convert(
                    amount=option["total_price"],
                    from_currency=option["currency"],
                    to_currency=trip.destination_currency,
                ),
                "destination_currency": trip.destination_currency,

                "user_price": currency_service.convert(
                    amount=option["total_price"],
                    from_currency=option["currency"],
                    to_currency=trip.user_currency,
                ),
                "user_currency": trip.user_currency,
            }
            for option in page_options
        ]

        return {
            "options": display_options,
            "page": page,
            "limit": limit,
            "total": total_options,
            "total_pages": (
                                   total_options + limit - 1
                           ) // limit,
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
    total_options = len(options)
    page_options = options[start:end]

    display_options = [
        {
            **option,

            "destination_price": currency_service.convert(
                amount=option["total_price"],
                from_currency=option["currency"],
                to_currency=trip.destination_currency,
            ),
            "destination_currency": trip.destination_currency,

            "user_price": currency_service.convert(
                amount=option["total_price"],
                from_currency=option["currency"],
                to_currency=trip.user_currency,
            ),
            "user_currency": trip.user_currency,
        }
        for option in page_options
    ]

    return {
        "options": display_options,
        "page": page,
        "limit": limit,
        "total": total_options,
        "total_pages": (
                               total_options + limit - 1
                       ) // limit,
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
        latitude=hotel.latitude,
        longitude=hotel.longitude,
        price_per_night=hotel.price_per_night,
        nights=hotel.nights,
        total_price=hotel.total_price,
        currency=hotel.currency,
        check_in=hotel.check_in,
        check_out=hotel.check_out,
        hotel_data=hotel.hotel_data,
    )

    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)


    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )

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
            "currency": new_hotel.currency,

            "destination_price": currency_service.convert(
                amount=new_hotel.total_price,
                from_currency=new_hotel.currency,
                to_currency=trip.destination_currency,
            ),
            "destination_currency": trip.destination_currency,

            "user_price": currency_service.convert(
                amount=new_hotel.total_price,
                from_currency=new_hotel.currency,
                to_currency=trip.user_currency,
            ),
            "user_currency": trip.user_currency,

            "check_in": new_hotel.check_in,
            "check_out": new_hotel.check_out,
            **(new_hotel.hotel_data or {}),
        },
    }


def get_hotels(
    trip_id: int,
    db: Session,
):
    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )

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
                "latitude": hotel.latitude,
                "longitude": hotel.longitude,
                "price_per_night": hotel.price_per_night,
                "nights": hotel.nights,
                "total_price": hotel.total_price,
                "currency": hotel.currency,

                "destination_price": currency_service.convert(
                    amount=hotel.total_price,
                    from_currency=hotel.currency,
                    to_currency=trip.destination_currency,
                ),
                "destination_currency": trip.destination_currency,

                "user_price": currency_service.convert(
                    amount=hotel.total_price,
                    from_currency=hotel.currency,
                    to_currency=trip.user_currency,
                ),
                "user_currency": trip.user_currency,

                "check_in": hotel.check_in,
                "check_out": hotel.check_out,
                **(hotel.hotel_data or {}),
            }
            for hotel in hotels
        ],
    }


def delete_hotel(
    trip_id: int,
    hotel_id: int,
    db: Session,
):
    hotel = (
        db.query(TripHotel)
        .filter(
            TripHotel.id == hotel_id,
            TripHotel.trip_id == trip_id,
        )
        .first()
    )

    if hotel is None:
        return None

    db.delete(hotel)
    db.commit()

    return {
        "message": "Hotel deleted",
        "hotel_id": hotel_id,
    }

def get_hotel_room_details(
    db: Session,
    trip_id: int,
    hotel_id: int,
    room_code: str,
):
    hotel = (
        db.query(TripHotel)
        .filter(
            TripHotel.id == hotel_id,
            TripHotel.trip_id == trip_id,
        )
        .first()
    )

    if hotel is None:
        return None

    hotel_data = hotel.hotel_data or {}

    hotel_code = hotel_data.get("hotel_code")

    if not hotel_code:
        return {
            "error": "Hotel code not found"
        }

    hotel_content = (
        db.query(HotelContent)
        .filter(
            HotelContent.hotel_code
            == str(hotel_code)
        )
        .first()
    )

    if hotel_content is None:
        return {
            "error": "Hotel content not found"
        }

    hotel_room = (
        db.query(HotelRoom)
        .filter(
            HotelRoom.hotel_content_id
            == hotel_content.id,
            HotelRoom.room_code
            == str(room_code),
        )
        .first()
    )

    if hotel_room is None:
        return {
            "error": "Room not found"
        }

    room_facilities = []

    if hotel_room.room_facilities:
        room_facilities = json.loads(
            hotel_room.room_facilities
        )

    room_stays = []

    if hotel_room.room_stays:
        room_stays = json.loads(
            hotel_room.room_stays
        )

    return {
        "hotel_id": hotel_id,
        "hotel_code": str(hotel_code),
        "room_code": hotel_room.room_code,
        "room_type": hotel_room.room_type,
        "characteristic_code": (
            hotel_room.characteristic_code
        ),
        "pms_room_code": (
            hotel_room.pms_room_code
        ),
        "min_pax": hotel_room.min_pax,
        "max_pax": hotel_room.max_pax,
        "max_adults": hotel_room.max_adults,
        "max_children": hotel_room.max_children,
        "room_facilities": room_facilities,
        "room_stays": room_stays,
    }