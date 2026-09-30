from sqlalchemy.orm import Session
import json
import os

from app.models.hotel import TripHotel
from app.models.trip import Trip
from app.models.transport import TripTransport
from app.models.trip_stop import TripStop
from app.models.hotel_content import HotelContent
from app.models.hotel_room import HotelRoom
from app.schemas.trip import HotelCreate
from app.services.hotel_provider import hotel_provider
from app.services.cache_service import cache_service
from app.services.currency_service import currency_service
from app.services.hotel_content import HotelContentProvider
from app.services.hotel_content_service import HotelContentService
from types import SimpleNamespace
from app.services.trip_consistency import get_trip_consistency_warnings





def generate_hotel_options(
    trip,
    db: Session,
    refresh: bool = False,
    page: int = 1,
    limit: int = 50,
    stop=None,
):
    search_context = trip

    if stop is not None:
        search_context = SimpleNamespace(
            id=trip.id,
            destination=stop.city,
            destination_latitude=stop.latitude,
            destination_longitude=stop.longitude,
            start_date=stop.start_date,
            end_date=stop.end_date,
            destination_currency=trip.destination_currency,
            user_currency=trip.user_currency,
        )

    cache_type = (
        f"hotel_stop_{stop.id}"
        if stop is not None
        else "hotel"
    )

    cache = cache_service.get(
        db=db,
        trip_id=trip.id,
        cache_type=cache_type,
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

    options = hotel_provider.get_hotel_options(search_context)

    cache = cache_service.save(
        db=db,
        trip_id=trip.id,
        cache_type=cache_type,
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
    existing_hotel_query = (
        db.query(TripHotel)
        .filter(
            TripHotel.trip_id == trip_id,
        )
    )

    if hotel.stop_id is None:
        existing_hotel_query = existing_hotel_query.filter(
            TripHotel.stop_id.is_(None),
        )
    else:
        existing_hotel_query = existing_hotel_query.filter(
            TripHotel.stop_id == hotel.stop_id,
        )

    existing_hotel = existing_hotel_query.first()

    if existing_hotel:
        db.delete(existing_hotel)
        db.flush()

    print(
        "CREATE HOTEL COORDINATES: "
        f"name={hotel.name}, "
        f"stop_id={hotel.stop_id}, "
        f"latitude={hotel.latitude}, "
        f"longitude={hotel.longitude}"
    )

    new_hotel = TripHotel(
        trip_id=trip_id,
        stop_id=hotel.stop_id,
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

    hotel_data = new_hotel.hotel_data or {}
    hotel_code = hotel_data.get("hotel_code")

    if hotel_code:
        api_key = os.getenv("HOTELBEDS_API_KEY")
        secret = os.getenv("HOTELBEDS_SECRET")

        if api_key and secret:
            hotel_content = (
                db.query(HotelContent)
                .filter(
                    HotelContent.hotel_code == str(hotel_code)
                )
                .first()
            )

            if hotel_content is None:
                provider = HotelContentProvider(
                    api_key=api_key,
                    secret=secret,
                )

                service = HotelContentService(
                    db=db,
                    provider=provider,
                )

                service.sync_hotels(
                    language="ENG",
                    hotel_code=str(hotel_code),
                )

    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )

    warnings = get_trip_consistency_warnings(
        trip_id=trip_id,
        db=db,
    )

    print("HOTEL CONSISTENCY WARNINGS:", warnings)

    return {
        "message": "Hotel created",
        "hotel": {
            "id": new_hotel.id,
            "trip_id": new_hotel.trip_id,
            "stop_id": new_hotel.stop_id,
            "name": new_hotel.name,
            "city": new_hotel.city,
            "address": new_hotel.address,
            "latitude": new_hotel.latitude,
            "longitude": new_hotel.longitude,
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
        "warnings": warnings,
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
                "stop_id": hotel.stop_id,
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

    print(
        "DELETE HOTEL: "
        f"hotel_id={hotel.id}, "
        f"trip_id={hotel.trip_id}, "
        f"stop_id={hotel.stop_id}"
    )

    all_transports = (
        db.query(TripTransport)
        .filter(
            TripTransport.trip_id == trip_id,
        )
        .all()
    )

    print(
        "ALL TRANSPORTS BEFORE HOTEL DELETE: "
        f"{[(t.id, t.transport_type, t.direction, t.parent_transport_id) for t in all_transports]}"
    )

    transfers = [
        transport
        for transport in all_transports
        if transport.transport_type.startswith("Transfer")
    ]

    print(
        "TRANSFERS BEFORE HOTEL DELETE: "
        f"{[(t.id, t.transport_type, t.direction, t.parent_transport_id) for t in transfers]}"
    )

    parent_ids = {
        transport.parent_transport_id
        for transport in transfers
        if transport.parent_transport_id is not None
    }

    print(
        "TRANSFER PARENT IDS: "
        f"{sorted(parent_ids)}"
    )

    for transfer in transfers:
        print(
            "DELETE TRANSFER WITH HOTEL: "
            f"id={transfer.id}, "
            f"parent={transfer.parent_transport_id}"
        )

        db.delete(transfer)

    db.delete(hotel)

    stop_after_hotel_delete = None

    if hotel.stop_id is not None:
        stop_after_hotel_delete = (
            db.query(TripStop)
            .filter(
                TripStop.id == hotel.stop_id,
                TripStop.trip_id == trip_id,
            )
            .first()
        )

    print(
        "STOP BEFORE HOTEL COMMIT:",
        (
            stop_after_hotel_delete.id,
            stop_after_hotel_delete.city,
        )
        if stop_after_hotel_delete is not None
        else None,
    )

    db.commit()

    stop_after_commit = None

    if hotel.stop_id is not None:
        stop_after_commit = (
            db.query(TripStop)
            .filter(
                TripStop.id == hotel.stop_id,
                TripStop.trip_id == trip_id,
            )
            .first()
        )

    print(
        "STOP AFTER HOTEL COMMIT:",
        (
            stop_after_commit.id,
            stop_after_commit.city,
        )
        if stop_after_commit is not None
        else None,
    )

    print(
        "HOTEL AND TRANSFERS DELETED: "
        f"hotel_id={hotel_id}"
    )

    warnings = get_trip_consistency_warnings(
        trip_id=trip_id,
        db=db,
    )

    print(
        "HOTEL CONSISTENCY WARNINGS AFTER DELETE:",
        warnings,
    )

    return {
        "message": "Hotel deleted",
        "hotel_id": hotel_id,
        "warnings": warnings,
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