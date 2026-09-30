from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.hotel import TripHotel
from app.models.transport import TripTransport
from app.models.trip_stop import TripStop


def _parse_transport_datetime(
    date_value,
    time_value,
):
    if date_value is None:
        return None

    if isinstance(date_value, datetime):
        date_part = date_value.date()
    else:
        date_part = date_value

    if isinstance(time_value, str):
        try:
            parsed_time = datetime.strptime(
                time_value,
                "%H:%M",
            ).time()
        except ValueError:
            try:
                parsed_time = datetime.strptime(
                    time_value,
                    "%H:%M:%S",
                ).time()
            except ValueError:
                parsed_time = time.min
    elif time_value is None:
        parsed_time = time.min
    else:
        parsed_time = time_value

    return datetime.combine(
        date_part,
        parsed_time,
    )


def _get_hotel_nights(hotel):
    current_date = hotel.check_in

    while current_date < hotel.check_out:
        yield current_date
        current_date += timedelta(days=1)


def _hotel_overlaps_flight(
    hotel,
    transport,
):
    departure = _parse_transport_datetime(
        transport.departure_date,
        transport.departure_time,
    )

    arrival = _parse_transport_datetime(
        transport.arrival_date,
        transport.arrival_time,
    )

    if departure is None or arrival is None:
        return False

    if arrival <= departure:
        return False

    hotel_nights = list(_get_hotel_nights(hotel))

    if not hotel_nights:
        return False

    if transport.direction == "outbound":
        return any(
            night_date < arrival.date()
            for night_date in hotel_nights
        )

    if transport.direction == "return":
        return any(
            night_date >= departure.date()
            for night_date in hotel_nights
        )

    return False


def _get_hotel_gap_after_outbound_flight(
    hotel,
    transport,
    stops,
):
    if transport.direction != "outbound":
        return None

    arrival = _parse_transport_datetime(
        transport.arrival_date,
        transport.arrival_time,
    )

    if arrival is None:
        return None

    next_stop = next(
        (
            stop
            for stop in stops
            if stop.start_date >= arrival.date()
        ),
        None,
    )

    if next_stop is None:
        return None

    if hotel.stop_id != next_stop.id:
        return None

    if hotel.check_in <= arrival.date():
        return None

    gap_days = (
        hotel.check_in - arrival.date()
    ).days

    if gap_days <= 0:
        return None

    return {
        "type": "hotel_gap_after_flight",
        "hotel_id": hotel.id,
        "hotel_name": hotel.name,
        "transport_id": transport.id,
        "transport_direction": transport.direction,
        "flight_arrival_date": transport.arrival_date,
        "flight_arrival_time": transport.arrival_time,
        "hotel_check_in": hotel.check_in,
        "gap_days": gap_days,
        "message": (
            f"Flight arrives on "
            f"{transport.arrival_date} "
            f"at {transport.arrival_time}, "
            f"but hotel check-in is "
            f"{hotel.check_in}. "
            f"There is a {gap_days}-day gap."
        ),
    }


def _get_hotel_sequence_warnings(
    hotels,
    stops,
):
    hotels_by_stop_id = {
        hotel.stop_id: hotel
        for hotel in hotels
        if hotel.stop_id is not None
    }

    ordered_hotels = []

    for stop in stops:
        hotel = hotels_by_stop_id.get(stop.id)

        if hotel is None:
            continue

        ordered_hotels.append(hotel)

    warnings = []

    for index in range(len(ordered_hotels) - 1):
        current_hotel = ordered_hotels[index]
        next_hotel = ordered_hotels[index + 1]

        if current_hotel.check_out < next_hotel.check_in:
            gap_days = (
                next_hotel.check_in
                - current_hotel.check_out
            ).days

            warnings.append(
                {
                    "type": "hotel_gap_between_stops",
                    "current_hotel_id": current_hotel.id,
                    "current_hotel_name": current_hotel.name,
                    "next_hotel_id": next_hotel.id,
                    "next_hotel_name": next_hotel.name,
                    "current_hotel_check_out": (
                        current_hotel.check_out
                    ),
                    "next_hotel_check_in": (
                        next_hotel.check_in
                    ),
                    "gap_days": gap_days,
                    "message": (
                        f"Hotel '{current_hotel.name}' "
                        f"checks out on "
                        f"{current_hotel.check_out}, "
                        f"but next hotel "
                        f"'{next_hotel.name}' "
                        f"checks in on "
                        f"{next_hotel.check_in}. "
                        f"There is a {gap_days}-day gap."
                    ),
                }
            )

        elif current_hotel.check_out > next_hotel.check_in:
            warnings.append(
                {
                    "type": "hotel_overlap_between_stops",
                    "current_hotel_id": current_hotel.id,
                    "current_hotel_name": current_hotel.name,
                    "next_hotel_id": next_hotel.id,
                    "next_hotel_name": next_hotel.name,
                    "current_hotel_check_out": (
                        current_hotel.check_out
                    ),
                    "next_hotel_check_in": (
                        next_hotel.check_in
                    ),
                    "message": (
                        f"Hotel '{current_hotel.name}' "
                        f"checks out on "
                        f"{current_hotel.check_out}, "
                        f"but next hotel "
                        f"'{next_hotel.name}' "
                        f"checks in on "
                        f"{next_hotel.check_in}. "
                        f"The hotel dates overlap."
                    ),
                }
            )

    return warnings


def _get_last_hotel_flight_warnings(
    hotels,
    stops,
    transports,
):
    hotels_by_stop_id = {
        hotel.stop_id: hotel
        for hotel in hotels
        if hotel.stop_id is not None
    }

    ordered_hotels = []

    for stop in stops:
        hotel = hotels_by_stop_id.get(stop.id)

        if hotel is None:
            continue

        ordered_hotels.append(hotel)

    if not ordered_hotels:
        return []

    last_hotel = ordered_hotels[-1]

    return_flights = [
        transport
        for transport in transports
        if transport.direction == "return"
    ]

    if not return_flights:
        return []

    return_flights.sort(
        key=lambda transport: (
            transport.departure_date,
            transport.departure_time,
        )
    )

    return_flight = return_flights[0]

    warnings = []

    if last_hotel.check_out < return_flight.departure_date:
        gap_days = (
            return_flight.departure_date
            - last_hotel.check_out
        ).days

        warnings.append(
            {
                "type": "hotel_gap_before_return_flight",
                "hotel_id": last_hotel.id,
                "hotel_name": last_hotel.name,
                "transport_id": return_flight.id,
                "transport_direction": return_flight.direction,
                "hotel_check_out": last_hotel.check_out,
                "flight_departure_date": (
                    return_flight.departure_date
                ),
                "flight_departure_time": (
                    return_flight.departure_time
                ),
                "gap_days": gap_days,
                "message": (
                    f"Hotel '{last_hotel.name}' "
                    f"checks out on "
                    f"{last_hotel.check_out}, "
                    f"but return flight departs on "
                    f"{return_flight.departure_date} "
                    f"at {return_flight.departure_time}. "
                    f"There is a {gap_days}-day gap."
                ),
            }
        )

    elif last_hotel.check_out > return_flight.departure_date:
        warnings.append(
            {
                "type": "hotel_during_return_flight",
                "hotel_id": last_hotel.id,
                "hotel_name": last_hotel.name,
                "transport_id": return_flight.id,
                "transport_direction": return_flight.direction,
                "hotel_check_out": last_hotel.check_out,
                "flight_departure_date": (
                    return_flight.departure_date
                ),
                "flight_departure_time": (
                    return_flight.departure_time
                ),
                "message": (
                    f"Hotel '{last_hotel.name}' "
                    f"checks out on "
                    f"{last_hotel.check_out}, "
                    f"but return flight departs on "
                    f"{return_flight.departure_date} "
                    f"at {return_flight.departure_time}. "
                    f"The hotel overlaps with the return flight."
                ),
            }
        )

    return warnings


def _get_hotel_flight_warnings(
    db: Session,
    trip_id: int,
):
    hotels = (
        db.query(TripHotel)
        .filter(TripHotel.trip_id == trip_id)
        .all()
    )

    transports = (
        db.query(TripTransport)
        .filter(
            TripTransport.trip_id == trip_id,
            TripTransport.transport_type.like("Flight%"),
        )
        .order_by(
            TripTransport.departure_date,
            TripTransport.departure_time,
        )
        .all()
    )

    stops = (
        db.query(TripStop)
        .filter(
            TripStop.trip_id == trip_id,
        )
        .order_by(
            TripStop.start_date,
            TripStop.id,
        )
        .all()
    )

    warnings = []

    warnings.extend(
        _get_hotel_sequence_warnings(
            hotels=hotels,
            stops=stops,
        )
    )

    warnings.extend(
        _get_last_hotel_flight_warnings(
            hotels=hotels,
            stops=stops,
            transports=transports,
        )
    )

    for hotel in hotels:
        for transport in transports:

            gap_warning = _get_hotel_gap_after_outbound_flight(
                hotel=hotel,
                transport=transport,
                stops=stops,
            )

            if gap_warning is not None:
                warnings.append(gap_warning)

            if not _hotel_overlaps_flight(
                hotel,
                transport,
            ):
                continue

            warnings.append(
                {
                    "type": "hotel_during_flight",
                    "hotel_id": hotel.id,
                    "hotel_name": hotel.name,
                    "transport_id": transport.id,
                    "transport_direction": transport.direction,
                    "flight_departure_date": (
                        transport.departure_date
                    ),
                    "flight_departure_time": (
                        transport.departure_time
                    ),
                    "flight_arrival_date": (
                        transport.arrival_date
                    ),
                    "flight_arrival_time": (
                        transport.arrival_time
                    ),
                    "hotel_check_in": hotel.check_in,
                    "hotel_check_out": hotel.check_out,
                    "message": (
                        f"Hotel '{hotel.name}' overlaps "
                        f"with the selected flight."
                    ),
                }
            )

    return warnings


def get_trip_consistency_warnings(
    trip_id: int,
    db: Session,
):
    return _get_hotel_flight_warnings(
        trip_id=trip_id,
        db=db,
    )