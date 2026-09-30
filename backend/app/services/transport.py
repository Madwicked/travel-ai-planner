from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.services.currency_service import currency_service
from app.models.transport import TripTransport
from app.schemas.trip import TransportCreate, TransportUpdate
from app.services.transport_provider import transport_provider
from app.services.cache_service import cache_service
from app.services.trip_consistency import get_trip_consistency_warnings

TRANSPORT_CACHE_TTL_MINUTES = 30


def _prepare_transport_options(
    options,
    trip,
):
    return [
        {
            **option,

            "destination_price": currency_service.convert(
                amount=option["price"],
                from_currency=option["currency"],
                to_currency=trip.destination_currency,
            ),
            "destination_currency": trip.destination_currency,

            "user_price": currency_service.convert(
                amount=option["price"],
                from_currency=option["currency"],
                to_currency=trip.user_currency,
            ),
            "user_currency": trip.user_currency,
        }
        for option in options
    ]


def _load_transport_cache(
    cache,
    expected_date,
):
    if not cache:
        return None

    data = cache_service.load_data(cache)

    if not isinstance(data, dict):
        return None

    cached_date = data.get("search_date")

    if cached_date != expected_date.isoformat():
        return None

    options = data.get("options")

    if not isinstance(options, list):
        return None

    return options


def generate_transport_options(
    trip,
    db: Session,
    refresh: bool = False,
    search_date=None,
):
    if search_date is None:
        search_date = trip.start_date

    cache = cache_service.get(
        db=db,
        trip_id=trip.id,
        cache_type="transport",
        direction="outbound",
        search_date=search_date,
    )

    if cache and not refresh:
        outdated = cache_service.is_expired(
            cache,
            ttl_minutes=TRANSPORT_CACHE_TTL_MINUTES,
        )

        options = _load_transport_cache(
            cache,
            search_date,
        )

        if options is not None and not outdated:
            return {
                "options": _prepare_transport_options(
                    options,
                    trip,
                ),
                "cached": True,
                "outdated": False,
                "fetched_at": cache.fetched_at,
                "expires_at": cache_service.get_expires_at(
                    cache,
                    ttl_minutes=TRANSPORT_CACHE_TTL_MINUTES,
                ),
            }

    options = transport_provider.get_outbound_options(
        trip,
        search_date=search_date,
    )

    if options is None:
        options = []

    cache = cache_service.save(
        db=db,
        trip_id=trip.id,
        cache_type="transport",
        direction="outbound",
        search_date=search_date,
        data={
            "search_date": search_date.isoformat(),
            "options": options,
        },
    )

    return {
        "options": _prepare_transport_options(
            options,
            trip,
        ),
        "cached": False,
        "outdated": False,
        "fetched_at": cache.fetched_at,
        "expires_at": cache_service.get_expires_at(
            cache,
            ttl_minutes=TRANSPORT_CACHE_TTL_MINUTES,
        ),
    }


def generate_return_transport_options(
    trip,
    db: Session,
    refresh: bool = False,
    search_date=None,
):

    if search_date is None:
        search_date = trip.end_date

    cache = cache_service.get(
        db=db,
        trip_id=trip.id,
        cache_type="transport",
        direction="return",
        search_date=search_date,
    )


    if cache and not refresh:
        outdated = cache_service.is_expired(
            cache,
            ttl_minutes=TRANSPORT_CACHE_TTL_MINUTES,
        )

        options = _load_transport_cache(
            cache,
            search_date,
        )

        if options is not None and not outdated:
            return {
                "options": _prepare_transport_options(
                    options,
                    trip,
                ),
                "cached": True,
                "outdated": False,
                "fetched_at": cache.fetched_at,
                "expires_at": cache_service.get_expires_at(
                    cache,
                    ttl_minutes=TRANSPORT_CACHE_TTL_MINUTES,
                ),
            }

    options = transport_provider.get_return_options(
        trip,
        search_date=search_date,
    )

    if options is None:
        options = []

    cache = cache_service.save(
        db=db,
        trip_id=trip.id,
        cache_type="transport",
        direction="return",
        search_date=search_date,
        data={
            "search_date": search_date.isoformat(),
            "options": options,
        },
    )

    return {
        "options": _prepare_transport_options(
            options,
            trip,
        ),
        "cached": False,
        "outdated": False,
        "fetched_at": cache.fetched_at,
        "expires_at": cache_service.get_expires_at(
            cache,
            ttl_minutes=TRANSPORT_CACHE_TTL_MINUTES,
        ),
    }


def create_transport(
    trip_id: int,
    transport: TransportCreate,
    db: Session,
):
    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )

    new_transport = TripTransport(
        trip_id=trip_id,
        parent_transport_id=transport.parent_transport_id,
        direction=transport.direction,
        transport_type=transport.transport_type,
        transport_price=transport.transport_price,
        currency=transport.currency,

        transfer_data=transport.transfer_data,

        segments=transport.segments,
        stops=transport.stops,
        layovers=transport.layovers,

        transport_duration=transport.transport_duration,
        departure_date=transport.departure_date,
        departure_time=transport.departure_time,
        departure_location=transport.departure_location,
        arrival_date=transport.arrival_date,
        arrival_time=transport.arrival_time,
        arrival_location=transport.arrival_location,
    )

    db.add(new_transport)
    db.flush()

    db.commit()
    db.refresh(new_transport)

    warnings = get_trip_consistency_warnings(
        trip_id=trip_id,
        db=db,
    )

    return {
        "message": "Transport created",
        "transport": {
            "id": new_transport.id,
            "trip_id": new_transport.trip_id,
            "parent_transport_id": new_transport.parent_transport_id,
            "direction": new_transport.direction,
            "type": new_transport.transport_type,
            "price": new_transport.transport_price,
            "currency": new_transport.currency,
            "stops": new_transport.stops or 0,
            "segments": new_transport.segments or [],
            "layovers": new_transport.layovers or [],
            "transfer_data": new_transport.transfer_data,

            "destination_price": currency_service.convert(
                amount=new_transport.transport_price,
                from_currency=new_transport.currency,
                to_currency=trip.destination_currency,
            ),
            "destination_currency": trip.destination_currency,

            "user_price": currency_service.convert(
                amount=new_transport.transport_price,
                from_currency=new_transport.currency,
                to_currency=trip.user_currency,
            ),
            "user_currency": trip.user_currency,

            "duration": new_transport.transport_duration,
            "departure_date": new_transport.departure_date,
            "departure_time": new_transport.departure_time,
            "departure_location": new_transport.departure_location,
            "arrival_date": new_transport.arrival_date,
            "arrival_time": new_transport.arrival_time,
            "arrival_location": new_transport.arrival_location,
        },
        "warnings": warnings,
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
                "parent_transport_id": transport.parent_transport_id,
                "direction": transport.direction,
                "type": transport.transport_type,
                "price": transport.transport_price,
                "currency": transport.currency,
                "stops": transport.stops or 0,
                "segments": transport.segments or [],
                "layovers": transport.layovers or [],
                "transfer_data": transport.transfer_data,

                "destination_price": currency_service.convert(
                    amount=transport.transport_price,
                    from_currency=transport.currency,
                    to_currency=trip.destination_currency,
                ),
                "destination_currency": trip.destination_currency,

                "user_price": currency_service.convert(
                    amount=transport.transport_price,
                    from_currency=transport.currency,
                    to_currency=trip.user_currency,
                ),
                "user_currency": trip.user_currency,

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


def delete_transport(
    trip_id: int,
    transport_id: int,
    db: Session,
):
    transport = (
        db.query(TripTransport)
        .filter(
            TripTransport.id == transport_id,
            TripTransport.trip_id == trip_id,
        )
        .first()
    )

    if transport is None:
        return None

    if transport.transport_type == "Flight":
        transfer = (
            db.query(TripTransport)
            .filter(
                TripTransport.trip_id == trip_id,
                TripTransport.parent_transport_id == transport.id,
            )
            .first()
        )

        if transfer:
            db.delete(transfer)

    db.delete(transport)
    db.commit()

    return {
        "message": "Transport deleted",
        "transport_id": transport_id,
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