from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from app.database import SessionLocal
from app.models.trip import Trip
from app.models.transport import TripTransport
from app.models.hotel import TripHotel
from app.models.place import TripPlace
from app.schemas.trip import (
    TripCreate,
    TripResponse,
    TransportCreate,
    TransportUpdate,
    HotelCreate,
    PlaceCreate,
)

router = APIRouter(
    prefix="/api/trips",
    tags=["Trips"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=TripResponse)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    new_trip = Trip(
        origin=trip.origin,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        travelers=trip.travelers,
        budget=trip.budget,
        interests=", ".join(trip.interests),
    )

    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    return {
        "message": "Trip created",
        "trip_id": new_trip.id,
        "trip": trip,
    }

@router.post("/{trip_id}/transports")
def create_transport(
    trip_id: int,
    transport: TransportCreate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    new_transport = TripTransport(
        trip_id=trip_id,
        direction=transport.direction,
        transport_type=transport.transport_type,
        transport_price=transport.transport_price,
        transport_duration=transport.transport_duration,
        departure_date=transport.departure_date,
        departure_time=transport.departure_time,
        departure_location=transport.departure_location,
        arrival_date=transport.arrival_date,
        arrival_time=transport.arrival_time,
        arrival_location=transport.arrival_location,
    )

    db.add(new_transport)
    db.commit()
    db.refresh(new_transport)

    return {
        "message": "Transport created",
        "transport": {
            "id": new_transport.id,
            "trip_id": new_transport.trip_id,
            "direction": new_transport.direction,
            "type": new_transport.transport_type,
            "price": new_transport.transport_price,
            "duration": new_transport.transport_duration,
            "departure_date": new_transport.departure_date,
            "departure_time": new_transport.departure_time,
            "departure_location": new_transport.departure_location,
            "arrival_date": new_transport.arrival_date,
            "arrival_time": new_transport.arrival_time,
            "arrival_location": new_transport.arrival_location,
        },
    }

@router.get("/{trip_id}/transports")
def get_transports(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

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
                "direction": transport.direction,
                "type": transport.transport_type,
                "price": transport.transport_price,
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
@router.get("/{trip_id}/transports/options")
def get_transport_options(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    options = [
        {
            "type": "Flight",
            "price": 86,
            "duration": "2h 30m",
            "departure_date": trip.start_date,
            "departure_time": "10:25",
            "departure_location": f"{trip.origin} Airport",
            "arrival_date": trip.start_date,
            "arrival_time": "11:55",
            "arrival_location": f"{trip.destination} Airport",
        },
        {
            "type": "Bus",
            "price": 65,
            "duration": "14h 30m",
            "departure_date": trip.start_date,
            "departure_time": "18:00",
            "departure_location": f"{trip.origin} Bus Station",
            "arrival_date": trip.end_date,
            "arrival_time": "08:30",
            "arrival_location": f"{trip.destination} Bus Station",
        },
        {
            "type": "Train",
            "price": 120,
            "duration": "12h 15m",
            "departure_date": trip.start_date,
            "departure_time": "07:45",
            "departure_location": f"{trip.origin} Railway Station",
            "arrival_date": trip.start_date,
            "arrival_time": "20:00",
            "arrival_location": f"{trip.destination} Railway Station",
        },
    ]

    return {
        "trip_id": trip.id,
        "origin": trip.origin,
        "destination": trip.destination,
        "options": options,
    }

@router.get("/{trip_id}/transports/return-options")
def get_return_transport_options(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    options = [
        {
            "type": "Flight",
            "price": 92,
            "duration": "2h 25m",
            "departure_date": trip.end_date,
            "departure_time": "14:20",
            "departure_location": f"{trip.destination} Airport",
            "arrival_date": trip.end_date,
            "arrival_time": "16:45",
            "arrival_location": f"{trip.origin} Airport",
        },
        {
            "type": "Bus",
            "price": 68,
            "duration": "15h 10m",
            "departure_date": trip.end_date,
            "departure_time": "20:00",
            "departure_location": f"{trip.destination} Bus Station",
            "arrival_date": trip.end_date + timedelta(days=1),
            "arrival_time": "11:10",
            "arrival_location": f"{trip.origin} Bus Station",
        },
        {
            "type": "Train",
            "price": 115,
            "duration": "12h 40m",
            "departure_date": trip.end_date,
            "departure_time": "08:15",
            "departure_location": f"{trip.destination} Railway Station",
            "arrival_date": trip.end_date,
            "arrival_time": "20:55",
            "arrival_location": f"{trip.origin} Railway Station",
        },
    ]

    return {
        "trip_id": trip.id,
        "origin": trip.destination,
        "destination": trip.origin,
        "options": options,
    }

@router.put("/{trip_id}/transport")
def update_transport(
    trip_id: int,
    transport: TransportUpdate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    trip.transport_type = transport.transport_type
    trip.transport_price = transport.transport_price
    trip.transport_duration = transport.transport_duration
    trip.transport_departure = transport.transport_departure
    trip.transport_arrival = transport.transport_arrival
    trip.transport_departure_date = transport.transport_departure_date
    trip.transport_arrival_date = transport.transport_arrival_date
    trip.transport_departure_location = transport.transport_departure_location
    trip.transport_arrival_location = transport.transport_arrival_location

    db.commit()
    db.refresh(trip)

    return {
        "message": "Transport updated",
        "trip_id": trip.id,
        "transport": transport,
    }
@router.get("/{trip_id}/hotels/options")
def get_hotel_options(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    number_of_nights = (
        trip.end_date - trip.start_date
    ).days

    options = [
        {
            "name": "Rome Central Hotel",
            "city": trip.destination,
            "address": "Via Roma 25",
            "price_per_night": 85,
            "nights": number_of_nights,
            "total_price": 85 * number_of_nights,
            "check_in": trip.start_date,
            "check_out": trip.end_date,
        },
        {
            "name": "Hotel Imperial",
            "city": trip.destination,
            "address": "Via Nazionale 42",
            "price_per_night": 110,
            "nights": number_of_nights,
            "total_price": 110 * number_of_nights,
            "check_in": trip.start_date,
            "check_out": trip.end_date,
        },
        {
            "name": "Budget Stay Rome",
            "city": trip.destination,
            "address": "Via Milano 18",
            "price_per_night": 65,
            "nights": number_of_nights,
            "total_price": 65 * number_of_nights,
            "check_in": trip.start_date,
            "check_out": trip.end_date,
        },
    ]

    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "options": options,
    }


@router.post("/{trip_id}/hotels")
def create_hotel(
    trip_id: int,
    hotel: HotelCreate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

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

@router.get("/{trip_id}/hotels")
def get_hotels(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
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
                "price_per_night": hotel.price_per_night,
                "nights": hotel.nights,
                "total_price": hotel.total_price,
                "check_in": hotel.check_in,
                "check_out": hotel.check_out,
            }
            for hotel in hotels
        ],
    }

@router.get("/{trip_id}/places/options")
def get_place_options(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    options = [
        {
            "external_id": "mock-colosseum",
            "source": "mock",
            "name": "Colosseum",
            "city": trip.destination,
            "category": "Culture",
            "address": "Piazza del Colosseo",
            "latitude": 41.8902,
            "longitude": 12.4922,
            "rating": 4.7,
            "opening_hours": {
                "monday": ["08:30", "19:00"],
                "tuesday": ["08:30", "19:00"],
                "wednesday": ["08:30", "19:00"],
                "thursday": ["08:30", "19:00"],
                "friday": ["08:30", "19:00"],
                "saturday": ["08:30", "19:00"],
                "sunday": ["08:30", "19:00"],
            },
            "opening_time": "08:30",
            "closing_time": "19:00",
            "visit_duration": "2h",
        },
        {
            "external_id": "mock-roman-forum",
            "source": "mock",
            "name": "Roman Forum",
            "city": trip.destination,
            "category": "Culture",
            "address": "Via della Salara Vecchia 5/6",
            "latitude": 41.8925,
            "longitude": 12.4853,
            "rating": 4.8,
            "opening_hours": {
                "monday": ["09:00", "19:15"],
                "tuesday": ["09:00", "19:15"],
                "wednesday": ["09:00", "19:15"],
                "thursday": ["09:00", "19:15"],
                "friday": ["09:00", "19:15"],
                "saturday": ["09:00", "19:15"],
                "sunday": ["09:00", "19:15"],
            },
            "opening_time": "09:00",
            "closing_time": "19:15",
            "visit_duration": "1h 30m",
        },
        {
            "external_id": "mock-trevi-fountain",
            "source": "mock",
            "name": "Trevi Fountain",
            "city": trip.destination,
            "category": "Sightseeing",
            "address": "Piazza di Trevi",
            "latitude": 41.9009,
            "longitude": 12.4833,
            "rating": 4.8,
            "opening_hours": {
                "monday": ["00:00", "23:59"],
                "tuesday": ["00:00", "23:59"],
                "wednesday": ["00:00", "23:59"],
                "thursday": ["00:00", "23:59"],
                "friday": ["00:00", "23:59"],
                "saturday": ["00:00", "23:59"],
                "sunday": ["00:00", "23:59"],
            },
            "opening_time": "00:00",
            "closing_time": "23:59",
            "visit_duration": "30m",
        },
        {
            "external_id": "mock-villa-borghese",
            "source": "mock",
            "name": "Villa Borghese",
            "city": trip.destination,
            "category": "Nature",
            "address": "Piazzale Scipione Borghese 5",
            "latitude": 41.9142,
            "longitude": 12.4923,
            "rating": 4.6,
            "opening_hours": {
                "monday": ["09:00", "19:00"],
                "tuesday": ["09:00", "19:00"],
                "wednesday": ["09:00", "19:00"],
                "thursday": ["09:00", "19:00"],
                "friday": ["09:00", "19:00"],
                "saturday": ["09:00", "19:00"],
                "sunday": ["09:00", "19:00"],
            },
            "opening_time": "09:00",
            "closing_time": "19:00",
            "visit_duration": "2h",
        },
        {
            "external_id": "mock-pantheon",
            "source": "mock",
            "name": "Pantheon",
            "city": trip.destination,
            "category": "Culture",
            "address": "Piazza della Rotonda",
            "latitude": 41.8986,
            "longitude": 12.4769,
            "rating": 4.7,
            "opening_hours": {
                "monday": ["09:00", "19:00"],
                "tuesday": ["09:00", "19:00"],
                "wednesday": ["09:00", "19:00"],
                "thursday": ["09:00", "19:00"],
                "friday": ["09:00", "19:00"],
                "saturday": ["09:00", "19:00"],
                "sunday": ["09:00", "19:00"],
            },
            "opening_time": "09:00",
            "closing_time": "19:00",
            "visit_duration": "1h",
        },
    ]

    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "options": options,
    }

@router.delete("/{trip_id}/places")
def delete_places(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    db.query(TripPlace).filter(
        TripPlace.trip_id == trip_id
    ).delete(
        synchronize_session=False
    )

    db.commit()

    return {
        "message": "Places deleted",
        "trip_id": trip_id,
    }

@router.post("/{trip_id}/places")
def create_place(
    trip_id: int,
    place: PlaceCreate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    new_place = TripPlace(
        trip_id=trip_id,
        external_id=place.external_id,
        source=place.source,
        name=place.name,
        city=place.city,
        category=place.category,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        rating=place.rating,
        opening_hours=place.opening_hours,
        opening_time=place.opening_time,
        closing_time=place.closing_time,
        visit_duration=place.visit_duration,
    )

    db.add(new_place)
    db.commit()
    db.refresh(new_place)

    return {
        "message": "Place saved",
        "place": {
            "id": new_place.id,
            "trip_id": new_place.trip_id,
            "external_id": new_place.external_id,
            "source": new_place.source,
            "name": new_place.name,
            "city": new_place.city,
            "category": new_place.category,
            "address": new_place.address,
            "latitude": new_place.latitude,
            "longitude": new_place.longitude,
            "rating": new_place.rating,
            "opening_hours": new_place.opening_hours,
            "opening_time": new_place.opening_time,
            "closing_time": new_place.closing_time,
            "visit_duration": new_place.visit_duration,
        },
    }

@router.get("/{trip_id}/places")
def get_places(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    places = (
        db.query(TripPlace)
        .filter(TripPlace.trip_id == trip_id)
        .order_by(TripPlace.id)
        .all()
    )


    return {
        "trip_id": trip.id,
        "places": [
            {
                "id": place.id,
                "trip_id": place.trip_id,
                "external_id": place.external_id,
                "source": place.source,
                "name": place.name,
                "city": place.city,
                "category": place.category,
                "address": place.address,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "rating": place.rating,
                "opening_hours": place.opening_hours,
                "opening_time": place.opening_time,
                "closing_time": place.closing_time,
                "visit_duration": place.visit_duration,
            }
            for place in places
        ],
    }
@router.get("/{trip_id}/itinerary")
def generate_itinerary(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    transports = (
        db.query(TripTransport)
        .filter(TripTransport.trip_id == trip_id)
        .order_by(TripTransport.id)
        .all()
    )

    outbound_transport = next(
        (
            transport
            for transport in transports
            if transport.direction == "outbound"
        ),
        None,
    )

    return_transport = next(
        (
            transport
            for transport in transports
            if transport.direction == "return"
        ),
        None,
    )

    hotel = (
        db.query(TripHotel)
        .filter(TripHotel.trip_id == trip_id)
        .order_by(TripHotel.id.desc())
        .first()
    )

    places = (
        db.query(TripPlace)
        .filter(TripPlace.trip_id == trip_id)
        .order_by(TripPlace.id)
        .all()
    )

    number_of_days = (
        trip.end_date - trip.start_date
    ).days + 1

    interests = [
        interest.strip()
        for interest in trip.interests.split(",")
    ]

    itinerary = []

    # ---------------------------------------------------------
    # Helper functions
    # ---------------------------------------------------------

    def parse_duration(duration):
        if not duration:
            return 60

        duration = duration.lower().strip()

        total_minutes = 0

        parts = duration.replace("h", " h ")
        parts = parts.replace("m", " m ")
        parts = parts.split()

        for index, part in enumerate(parts):
            if part == "h" and index > 0:
                total_minutes += int(parts[index - 1]) * 60

            elif part == "m" and index > 0:
                total_minutes += int(parts[index - 1])

        return total_minutes or 60

    def format_minutes(minutes):
        hours = minutes // 60
        mins = minutes % 60

        return f"{hours:02d}:{mins:02d}"

    def get_opening_hours(place, current_date):
        weekday = current_date.strftime("%A").lower()

        if place.opening_hours:
            hours = place.opening_hours.get(weekday)

            if hours:
                return hours[0], hours[1]

        return place.opening_time, place.closing_time

    def time_to_minutes(value):
        hour, minute = map(int, value.split(":"))
        return hour * 60 + minute

    # ---------------------------------------------------------
    # Distribute selected places between trip days
    # ---------------------------------------------------------

    places_by_day = {
        day: []
        for day in range(1, number_of_days + 1)
    }

    if places:
        usable_days = list(
            range(
                2,
                number_of_days,
            )
        )

        if not usable_days:
            usable_days = [1]

        lunch_start = 13 * 60
        lunch_end = 14 * 60

        # Maximum sightseeing load for one day.
        max_day_minutes = 6 * 60

        current_day_index = 0

        for place in places:
            visit_minutes = parse_duration(
                place.visit_duration
            )

            assigned = False

            # First try the current day.
            for day_offset in range(
                    len(usable_days)
            ):
                day_index = (
                                    current_day_index
                                    + day_offset
                            ) % len(usable_days)

                day = usable_days[day_index]

                current_date = (
                        trip.start_date
                        + timedelta(days=day - 1)
                )

                opening_time, closing_time = (
                    get_opening_hours(
                        place,
                        current_date,
                    )
                )

                opening_minutes = time_to_minutes(
                    opening_time
                )

                closing_minutes = time_to_minutes(
                    closing_time
                )

                current_places = places_by_day[day]

                # Calculate start time.
                if current_places:
                    previous_place = current_places[-1]

                    start_minutes = (
                            previous_place["start_minutes"]
                            + previous_place["duration_minutes"]
                            + 30
                    )
                else:
                    start_minutes = max(
                        opening_minutes,
                        10 * 60,
                    )

                # Move activities away from lunch.
                if (
                        start_minutes < lunch_start
                        and
                        start_minutes + visit_minutes
                        > lunch_start
                ):
                    start_minutes = lunch_end

                elif (
                        start_minutes >= lunch_start
                        and
                        start_minutes < lunch_end
                ):
                    start_minutes = lunch_end

                if start_minutes < opening_minutes:
                    start_minutes = opening_minutes

                end_minutes = (
                        start_minutes
                        + visit_minutes
                )

                # Check opening hours.
                if end_minutes > closing_minutes:
                    continue

                # Calculate current day load.
                day_load = sum(
                    item["duration_minutes"]
                    for item in current_places
                )

                # Add transfer time between places.
                if current_places:
                    day_load += (
                            len(current_places) * 30
                    )

                new_day_load = (
                        day_load
                        + visit_minutes
                )

                # Do not overload the day.
                if new_day_load > max_day_minutes:
                    continue

                current_places.append(
                    {
                        "place": place,
                        "start_minutes": start_minutes,
                        "duration_minutes": visit_minutes,
                        "transfer_minutes": (
                            30
                            if current_places
                            else 0
                        ),
                        "opening_time": opening_time,
                        "closing_time": closing_time,
                    }
                )

                assigned = True

                # Stay on the same day.
                # The next place will try this day first.
                current_day_index = day_index

                break

            # If the place does not fit into the current
            # day or any other normal day, try a fresh day.
            if not assigned:
                for day_offset in range(
                        len(usable_days)
                ):
                    day_index = (
                                        current_day_index
                                        + day_offset
                                        + 1
                                ) % len(usable_days)

                    day = usable_days[day_index]

                    current_date = (
                            trip.start_date
                            + timedelta(
                        days=day - 1
                    )
                    )

                    opening_time, closing_time = (
                        get_opening_hours(
                            place,
                            current_date,
                        )
                    )

                    opening_minutes = (
                        time_to_minutes(
                            opening_time
                        )
                    )

                    closing_minutes = (
                        time_to_minutes(
                            closing_time
                        )
                    )

                    start_minutes = max(
                        opening_minutes,
                        10 * 60,
                    )

                    if (
                            start_minutes < lunch_start
                            and
                            start_minutes + visit_minutes
                            > lunch_start
                    ):
                        start_minutes = lunch_end

                    end_minutes = (
                            start_minutes
                            + visit_minutes
                    )

                    if end_minutes > closing_minutes:
                        continue

                    places_by_day[day].append(
                        {
                            "place": place,
                            "start_minutes": start_minutes,
                            "duration_minutes": visit_minutes,
                            "transfer_minutes": 0,
                            "opening_time": opening_time,
                            "closing_time": closing_time,
                        }
                    )

                    current_day_index = day_index

                    assigned = True

                    break
    # ---------------------------------------------------------
    # Build itinerary
    # ---------------------------------------------------------

    for day in range(1, number_of_days + 1):

        current_date = (
            trip.start_date
            + timedelta(days=day - 1)
        )

        # -----------------------------------------------------
        # FIRST DAY
        # -----------------------------------------------------

        if day == 1:
            title = "Arrival and first impressions"

            if outbound_transport and hotel:
                morning = (
                    f"Arrive in {trip.destination} "
                    f"at {outbound_transport.arrival_time} "
                    f"and travel to {hotel.name}."
                )
            elif outbound_transport:
                morning = (
                    f"Arrive in {trip.destination} "
                    f"at {outbound_transport.arrival_time}."
                )
            elif hotel:
                morning = (
                    f"Arrive in {trip.destination} "
                    f"and check in at {hotel.name}."
                )
            else:
                morning = (
                    f"Arrival in {trip.destination} "
                    "and check-in at the hotel."
                )

            if "Food" in interests:
                lunch = (
                    "Have lunch at a local restaurant "
                    "and try traditional specialties."
                )
            else:
                lunch = (
                    "Have a meal at a local cafe."
                )

            afternoon = (
                f"Relax after arrival and explore "
                f"the area around {trip.destination}."
            )

            evening = (
                "Enjoy a relaxed evening "
                "and prepare for the next day."
            )
        # -----------------------------------------------------
        # LAST DAY
        # -----------------------------------------------------

        elif day == number_of_days:
            title = "Final day and departure"

            if hotel:
                morning = (
                    f"Check out from {hotel.name} "
                    "and prepare for departure."
                )
            else:
                morning = (
                    "Breakfast and free time "
                    "before departure."
                )

            if return_transport:
                departure_time = time_to_minutes(
                    return_transport.departure_time
                )

                # Leave enough time for the transfer
                # and arrival before departure.
                transfer_start = max(
                    8 * 60,
                    departure_time - 120,
                )

                if "Food" in interests:
                    lunch = (
                        f"Have lunch before "
                        f"{format_minutes(transfer_start)}."
                    )
                else:
                    lunch = (
                        f"Free time before "
                        f"{format_minutes(transfer_start)}."
                    )

                afternoon = (
                    f"Travel to "
                    f"{return_transport.departure_location} "
                    f"for departure at "
                    f"{return_transport.departure_time}."
                )

                evening = ""

            else:
                if "Food" in interests:
                    lunch = (
                        "Have lunch at a local restaurant "
                        "and try traditional specialties."
                    )
                else:
                    lunch = (
                        "Have lunch at a popular local cafe."
                    )

                afternoon = (
                    f"Final walk around "
                    f"{trip.destination} "
                    "and prepare for departure."
                )

                evening = (
                    "Travel to the airport or station "
                    "and depart."
                )
        # -----------------------------------------------------
        # MIDDLE DAYS
        # -----------------------------------------------------

        else:
            title = f"Explore {trip.destination}"

            scheduled_places = places_by_day.get(
                day,
                [],
            )


            # -------------------------------------------------
            # Places
            # -------------------------------------------------

            if scheduled_places:
                morning_places = []
                afternoon_places = []

                for index, item in enumerate(scheduled_places):
                    place = item["place"]

                    start_minutes = item["start_minutes"]

                    end_minutes = (
                            start_minutes
                            + item["duration_minutes"]
                    )

                    # Add transfer before the place.
                    if index > 0:
                        transfer_minutes = item.get(
                            "transfer_minutes",
                            0,
                        )

                        transfer_start = (
                                start_minutes
                                - transfer_minutes
                        )

                        # Do not display transfers that overlap lunch.
                        if (
                                transfer_start >= lunch_start
                                and
                                transfer_start < lunch_end
                        ):
                            transfer_text = None

                        elif (
                                transfer_start < lunch_start
                                and
                                start_minutes > lunch_start
                        ):
                            transfer_text = None

                        else:
                            transfer_start_time = format_minutes(
                                transfer_start
                            )

                            transfer_end_time = format_minutes(
                                start_minutes
                            )

                            transfer_text = (
                                f"{transfer_start_time}–"
                                f"{transfer_end_time} "
                                f"Travel to {place.name}."
                            )

                        if transfer_text:
                            if transfer_start < lunch_start:
                                morning_places.append(
                                    transfer_text
                                )
                            else:
                                afternoon_places.append(
                                    transfer_text
                                )

                    start_time = format_minutes(
                        start_minutes
                    )

                    end_time = format_minutes(
                        end_minutes
                    )

                    place_text = (
                        f"{start_time}–{end_time} "
                        f"{place.name}."
                    )

                    if start_minutes < lunch_start:
                        morning_places.append(
                            place_text
                        )
                    else:
                        afternoon_places.append(
                            place_text
                        )

                if morning_places:
                    morning = " ".join(
                        morning_places
                    )
                else:
                    morning = (
                        f"Free morning in "
                        f"{trip.destination}."
                    )

                if afternoon_places:
                    afternoon = " ".join(
                        afternoon_places
                    )
                else:
                    afternoon = (
                        f"Continue exploring "
                        f"{trip.destination} "
                        "at your own pace."
                    )

            else:
                morning = (
                    f"Explore an interesting area "
                    f"of {trip.destination}."
                )

                afternoon = (
                    f"Continue exploring "
                    f"{trip.destination} "
                    "at your own pace."
                )



            # -------------------------------------------------
            # Lunch
            # -------------------------------------------------

            if scheduled_places:
                lunch = (
                    "13:00–14:00 "
                    "Lunch at a local restaurant "
                    "and try traditional specialties."
                )
            elif "Food" in interests:
                lunch = (
                    "Have lunch at a local restaurant "
                    "and try traditional specialties."
                )
            else:
                lunch = (
                    "Have lunch at a popular local cafe."
                )

            # -------------------------------------------------
            # Evening
            # -------------------------------------------------

            if "Nightlife" in interests:
                evening = (
                    "Enjoy the local nightlife "
                    "and evening atmosphere."
                )
            else:
                evening = (
                    "Dinner and a relaxed evening walk."
                )

        # -----------------------------------------------------
        # Add day
        # -----------------------------------------------------

        itinerary.append(
            {
                "day": day,
                "date": current_date,
                "title": title,
                "morning": morning,
                "lunch": lunch,
                "afternoon": afternoon,
                "evening": evening,
            }
        )

    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "itinerary": itinerary,
    }

@router.get("")
def get_trips(db: Session = Depends(get_db)):
    trips = db.query(Trip).all()

    return [
        {
            "id": trip.id,
            "origin": trip.origin,
            "destination": trip.destination,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "travelers": trip.travelers,
            "budget": trip.budget,
            "interests": trip.interests,
            "transport": (
                {
                    "type": trip.transport_type,
                    "price": trip.transport_price,
                    "duration": trip.transport_duration,
                    "departure": trip.transport_departure,
                    "arrival": trip.transport_arrival,
                    "departure_date": trip.transport_departure_date,
                    "arrival_date": trip.transport_arrival_date,
                    "departure_location": trip.transport_departure_location,
                    "arrival_location": trip.transport_arrival_location,
                }
                if trip.transport_type
                else None
            ),
        }
        for trip in trips
    ]


