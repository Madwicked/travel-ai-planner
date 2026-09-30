from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.hotel import TripHotel
from app.models.transport import TripTransport
from app.models.trip import Trip
from app.models.trip_stop import TripStop


def _format_date(value):
    if value is None:
        return ""

    if isinstance(value, datetime):
        value = value.date()

    return value.strftime("%d.%m.%Y")


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
    hotels,
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

    hotel_stop = next(
        (
            stop
            for stop in stops
            if stop.id == hotel.stop_id
        ),
        None,
    )

    if hotel_stop is None:
        return None

    if hotel_stop.start_date < arrival.date():
        return None

    if hotel.check_in <= arrival.date():
        return None

    previous_hotels = []

    for stop in stops:
        if stop.start_date >= hotel_stop.start_date:
            continue

        previous_hotel = next(
            (
                item
                for item in hotels
                if item.stop_id == stop.id
            ),
            None,
        )

        if previous_hotel is not None:
            previous_hotels.append(previous_hotel)

    previous_hotels.sort(
        key=lambda item: (
            item.check_out,
            item.check_in,
        )
    )

    if previous_hotels:
        last_previous_hotel = previous_hotels[-1]

        if last_previous_hotel.check_out >= hotel.check_in:
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
            f"{_format_date(transport.arrival_date)} "
            f"at {transport.arrival_time}, "
            f"but hotel check-in is "
            f"{_format_date(hotel.check_in)}. "
            f"There is a {gap_days}-day gap."
        ),
    }

def _get_hotel_before_outbound_arrival_warning(
    hotel,
    transport,
):
    if transport.direction != "outbound":
        return None

    arrival = _parse_transport_datetime(
        transport.arrival_date,
        transport.arrival_time,
    )

    if arrival is None:
        return None

    if hotel.check_in >= arrival.date():
        return None

    unused_nights = (
        arrival.date() - hotel.check_in
    ).days

    if unused_nights <= 0:
        return None

    return {
        "type": "hotel_check_in_before_flight_arrival",
        "severity": "important",
        "hotel_id": hotel.id,
        "hotel_name": hotel.name,
        "transport_id": transport.id,
        "transport_direction": transport.direction,
        "flight_arrival_date": transport.arrival_date,
        "flight_arrival_time": transport.arrival_time,
        "hotel_check_in": hotel.check_in,
        "unused_nights": unused_nights,
        "message": (
            f"Hotel check-in is on "
            f"{_format_date(hotel.check_in)}, "
            f"but the outbound flight arrives on "
            f"{_format_date(transport.arrival_date)} "
            f"at {transport.arrival_time}. "
            f"You may miss {unused_nights} "
            f"hotel night(s). "
            f"If you do not arrive on the "
            f"check-in date, the booking may be "
            f"treated as a no-show and charges "
            f"or cancellation may apply."
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
                        f"{_format_date(current_hotel.check_out)}, "
                        f"but next hotel "
                        f"'{next_hotel.name}' "
                        f"checks in on "
                        f"{_format_date(next_hotel.check_in)}. "
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
                        f"{_format_date(current_hotel.check_out)}, "
                        f"but next hotel "
                        f"'{next_hotel.name}' "
                        f"checks in on "
                        f"{_format_date(next_hotel.check_in)}. "
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
                    f"{_format_date(last_hotel.check_out)}, "
                    f"but return flight departs on "
                    f"{_format_date(return_flight.departure_date)} "
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
                    f"{_format_date(last_hotel.check_out)}, "
                    f"but return flight departs on "
                    f"{_format_date(return_flight.departure_date)} "
                    f"at {return_flight.departure_time}. "
                    f"The hotel overlaps with the return flight."
                ),
            }
        )

    return warnings


def _get_return_flight_after_trip_end_warning(
    transports,
    trip_end_date,
):
    if trip_end_date is None:
        return []

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

    if return_flight.arrival_date is None:
        return []

    if return_flight.arrival_date <= trip_end_date:
        return []

    gap_days = (
        return_flight.arrival_date
        - trip_end_date
    ).days

    return [
        {
            "type": "return_flight_after_trip_end",
            "severity": "info",
            "transport_id": return_flight.id,
            "transport_direction": return_flight.direction,
            "trip_end_date": trip_end_date,
            "flight_arrival_date": (
                return_flight.arrival_date
            ),
            "flight_arrival_time": (
                return_flight.arrival_time
            ),
            "gap_days": gap_days,
            "message": (
                f"Trip ends on "
                f"{_format_date(trip_end_date)}, "
                f"but the return flight arrives on "
                f"{_format_date(return_flight.arrival_date)} "
                f"at {return_flight.arrival_time}. "
                f"The return journey extends "
                f"{gap_days} day(s) beyond the trip end."
            ),
        }
    ]

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

    trip = (
        db.query(Trip)
        .filter(
            Trip.id == trip_id,
        )
        .first()
    )

    has_outbound = any(
        transport.direction == "outbound"
        for transport in transports
    )

    has_return = any(
        transport.direction == "return"
        for transport in transports
    )

    if not hotels or not has_outbound or not has_return:
        return []

    print("=== CONSISTENCY DEBUG ===")

    for hotel in hotels:
        print(
            "HOTEL:",
            hotel.id,
            hotel.name,
            "stop_id=", hotel.stop_id,
            "check_in=", hotel.check_in,
            "check_out=", hotel.check_out,
        )

    for transport in transports:
        print(
            "FLIGHT:",
            transport.id,
            transport.direction,
            "departure=", transport.departure_date,
            transport.departure_time,
            "arrival=", transport.arrival_date,
            transport.arrival_time,
        )

    for stop in stops:
        print(
            "STOP:",
            stop.id,
            stop.city,
            "start=", stop.start_date,
            "end=", stop.end_date,
        )

    print("=== END CONSISTENCY DEBUG ===")

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

    warnings.extend(
        _get_return_flight_after_trip_end_warning(
            transports=transports,
            trip_end_date=trip.end_date if trip else None,
        )
    )

    for hotel in hotels:
        for transport in transports:

            gap_warning = _get_hotel_gap_after_outbound_flight(
                hotel=hotel,
                transport=transport,
                hotels=hotels,
                stops=stops,
            )

            if gap_warning is not None:
                warnings.append(gap_warning)

            before_arrival_warning = (
                _get_hotel_before_outbound_arrival_warning(
                    hotel=hotel,
                    transport=transport,
                )
            )

            if before_arrival_warning is not None:
                warnings.append(before_arrival_warning)

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