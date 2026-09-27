from datetime import datetime, timedelta


from app.services.airport_provider import airport_provider
from app.models.trip import Trip
from app.models.transport import TripTransport
from app.models.hotel import TripHotel
from app.models.place import TripPlace


TRANSFER_MINUTES = 30
LUNCH_START = 13 * 60
LUNCH_END = 14 * 60
MAX_DAILY_ACTIVITY_MINUTES = 6 * 60
ARRIVAL_ACTIVITY_DELAY = 120


def parse_duration(duration):
    if not duration:
        return 60

    duration = str(duration).lower().strip()

    total_minutes = 0

    parts = (
        duration
        .replace("hours", " h ")
        .replace("hour", " h ")
        .replace("hrs", " h ")
        .replace("hr", " h ")
        .replace("minutes", " m ")
        .replace("minute", " m ")
        .replace("mins", " m ")
        .replace("min", " m ")
        .replace("h", " h ")
        .replace("m", " m ")
        .split()
    )

    for index, part in enumerate(parts):
        if part == "h" and index > 0:
            try:
                total_minutes += int(parts[index - 1]) * 60
            except ValueError:
                pass

        elif part == "m" and index > 0:
            try:
                total_minutes += int(parts[index - 1])
            except ValueError:
                pass

    return total_minutes or 60


def format_minutes(minutes):
    hours = minutes // 60
    mins = minutes % 60

    return f"{hours:02d}:{mins:02d}"


def get_opening_hours(place, current_date):
    weekday = current_date.strftime("%A").lower()

    if place.opening_hours:
        hours = place.opening_hours.get(weekday)

        if hours and len(hours) >= 2:
            return hours[0], hours[1]

    opening_time = place.opening_time or "10:00"
    closing_time = place.closing_time or "22:00"

    return opening_time, closing_time


def time_to_minutes(value):
    if not value:
        return 0

    try:
        value = str(value)[:5]
        hour, minute = map(int, value.split(":"))
        return hour * 60 + minute
    except (ValueError, TypeError):
        return 0


def parse_transport_datetime(date_value, time_value):
    if not date_value or not time_value:
        return None

    try:
        if isinstance(date_value, str):
            date_value = datetime.strptime(
                date_value[:10],
                "%Y-%m-%d",
            ).date()

        if isinstance(time_value, str):
            time_value = time_value[:5]

        hour, minute = map(
            int,
            time_value.split(":"),
        )

        return datetime(
            date_value.year,
            date_value.month,
            date_value.day,
            hour,
            minute,
        )

    except (ValueError, TypeError, AttributeError):
        return None


def calculate_day_load(day_places):
    """
    Daily load includes:
    - actual visit durations;
    - 30-minute transfers between places.

    Travel to/from lunch is not counted as activity load.
    """

    if not day_places:
        return 0

    total = sum(
        item["duration_minutes"]
        for item in day_places
    )

    total += (
        max(0, len(day_places) - 1)
        * TRANSFER_MINUTES
    )

    return total


def find_place_start_time(
    place,
    current_date,
    day_start,
    day_end,
    previous_place=None,
):
    """
    Calculate the earliest valid start time for a Place.

    Rules:
    1. 30 minutes between Places.
    2. Lunch is fixed at 13:00–14:00.
    3. Morning Places must finish by 12:30.
    4. After lunch, the first Place starts at 14:30.
    5. Opening/closing hours are respected.
    6. Arrival/departure day windows are respected.
    """

    visit_minutes = parse_duration(
        place.visit_duration
    )

    opening_time, closing_time = get_opening_hours(
        place,
        current_date,
    )

    opening_minutes = time_to_minutes(
        opening_time
    )

    closing_minutes = time_to_minutes(
        closing_time
    )

    start_minutes = max(
        day_start,
        opening_minutes,
    )

    # ---------------------------------------------------------
    # AFTER PREVIOUS PLACE
    # ---------------------------------------------------------

    if previous_place is not None:
        previous_end = (
            previous_place["start_minutes"]
            + previous_place["duration_minutes"]
        )

        start_minutes = max(
            start_minutes,
            previous_end + TRANSFER_MINUTES,
        )

    # ---------------------------------------------------------
    # MORNING / LUNCH
    # ---------------------------------------------------------

    if (
        start_minutes < LUNCH_START
        and start_minutes + visit_minutes
        > LUNCH_START - TRANSFER_MINUTES
    ):
        start_minutes = (
            LUNCH_END + TRANSFER_MINUTES
        )

    if (
        LUNCH_START
        <= start_minutes
        < LUNCH_END + TRANSFER_MINUTES
    ):
        start_minutes = (
            LUNCH_END + TRANSFER_MINUTES
        )

    end_minutes = (
        start_minutes + visit_minutes
    )

    # ---------------------------------------------------------
    # OPENING HOURS
    # ---------------------------------------------------------

    if start_minutes < opening_minutes:
        start_minutes = opening_minutes

        if (
            start_minutes < LUNCH_START
            and start_minutes + visit_minutes
            > LUNCH_START - TRANSFER_MINUTES
        ):
            start_minutes = (
                LUNCH_END + TRANSFER_MINUTES
            )

        if (
            LUNCH_START
            <= start_minutes
            < LUNCH_END + TRANSFER_MINUTES
        ):
            start_minutes = (
                LUNCH_END + TRANSFER_MINUTES
            )

        end_minutes = (
            start_minutes + visit_minutes
        )

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    if start_minutes < day_start:
        return None

    if end_minutes > day_end:
        return None

    if end_minutes > closing_minutes:
        return None

    if start_minutes < LUNCH_START:
        if (
            end_minutes
            > LUNCH_START - TRANSFER_MINUTES
        ):
            return None

    if start_minutes < LUNCH_END + TRANSFER_MINUTES:
        if end_minutes > LUNCH_START:
            return None

    return start_minutes


def schedule_places_for_day(
    places,
    day,
    day_start,
    day_end,
    trip,
    itinerary_start_date,
):
    """
    Attempts to schedule Places for one specific day.
    """

    current_date = (
        itinerary_start_date
        + timedelta(days=day - 1)
    )

    scheduled = []

    for place in places:
        previous_place = (
            scheduled[-1]
            if scheduled
            else None
        )

        start_minutes = find_place_start_time(
            place=place,
            current_date=current_date,
            day_start=day_start,
            day_end=day_end,
            previous_place=previous_place,
        )

        if start_minutes is None:
            continue

        visit_minutes = parse_duration(
            place.visit_duration
        )

        current_load = calculate_day_load(
            scheduled
        )

        new_load = (
            current_load
            + visit_minutes
        )

        if new_load > MAX_DAILY_ACTIVITY_MINUTES:
            continue

        opening_time, closing_time = (
            get_opening_hours(
                place,
                current_date,
            )
        )

        scheduled.append(
            {
                "place": place,
                "start_minutes": start_minutes,
                "duration_minutes": visit_minutes,
                "transfer_minutes": (
                    TRANSFER_MINUTES
                    if previous_place is not None
                    else 0
                ),
                "opening_time": opening_time,
                "closing_time": closing_time,
            }
        )

    return scheduled


def generate_itinerary_data(
    trip_id,
    db,
    include_arrival_day=False,
    include_departure_day=False,
):
    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )

    if not trip:
        return None

    # =========================================================
    # TRANSPORT
    # =========================================================

    transports = (
        db.query(TripTransport)
        .filter(
            TripTransport.trip_id == trip_id
        )
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

    # =========================================================
    # TRANSPORT DATETIME
    # =========================================================

    arrival_datetime = None
    departure_datetime = None

    if outbound_transport:
        arrival_datetime = parse_transport_datetime(
            outbound_transport.arrival_date,
            outbound_transport.arrival_time,
        )

    if return_transport:
        departure_datetime = parse_transport_datetime(
            return_transport.departure_date,
            return_transport.departure_time,
        )

    # =========================================================
    # AIRPORTS
    # =========================================================

    def extract_iata_code(location):
        if not location:
            return None

        location = str(location).strip()

        if "(" not in location or ")" not in location:
            return None

        code = (
            location.rsplit("(", 1)[-1]
            .split(")", 1)[0]
            .strip()
        )

        if len(code) != 3:
            return None

        return code.upper()

    arrival_airport = None
    departure_airport = None

    # Arrival airport:
    # last segment of outbound transport.
    if (
        outbound_transport
        and outbound_transport.segments
    ):
        segments = outbound_transport.segments

        if isinstance(segments, list) and segments:
            last_segment = segments[-1]

            if isinstance(last_segment, dict):
                arrival_iata = extract_iata_code(
                    last_segment.get(
                        "arrival_location"
                    )
                )

                if arrival_iata:
                    arrival_airport = (
                        airport_provider.find_airport_by_iata(
                            arrival_iata
                        )
                    )

    # Departure airport:
    # first segment of return transport.
    if (
        return_transport
        and return_transport.segments
    ):
        segments = return_transport.segments

        if isinstance(segments, list) and segments:
            first_segment = segments[0]

            if isinstance(first_segment, dict):
                departure_iata = extract_iata_code(
                    first_segment.get(
                        "departure_location"
                    )
                )

                if departure_iata:
                    departure_airport = (
                        airport_provider.find_airport_by_iata(
                            departure_iata
                        )
                    )

    # =========================================================
    # HOTEL
    # =========================================================

    hotel = (
        db.query(TripHotel)
        .filter(
            TripHotel.trip_id == trip_id
        )
        .order_by(TripHotel.id.desc())
        .first()
    )

    # =========================================================
    # PLACES
    # =========================================================

    places = (
        db.query(TripPlace)
        .filter(
            TripPlace.trip_id == trip_id
        )
        .order_by(TripPlace.id)
        .all()
    )

    # =========================================================
    # DEDUPLICATE PHYSICAL PLACES
    # =========================================================

    unique_places = []
    seen_coordinates = set()

    for place in places:
        if (
            place.latitude is None
            or place.longitude is None
        ):
            unique_places.append(place)
            continue

        coordinates = (
            float(place.latitude),
            float(place.longitude),
        )

        if coordinates in seen_coordinates:
            continue

        seen_coordinates.add(coordinates)
        unique_places.append(place)

    places = unique_places

    # =========================================================
    # BASIC DATA
    # =========================================================

    itinerary_start_date = (
        arrival_datetime.date()
        if arrival_datetime is not None
        else trip.start_date
    )

    number_of_days = (
        trip.end_date - itinerary_start_date
    ).days + 1

    if number_of_days < 1:
        number_of_days = 1

    interests = [
        interest.strip()
        for interest in (
            trip.interests or ""
        ).split(",")
        if interest.strip()
    ]

    itinerary = []

    places_by_day = {
        day: []
        for day in range(
            1,
            number_of_days + 1,
        )
    }

    # =========================================================
    # DAY WINDOWS
    # =========================================================

    day_windows = {}

    for day in range(
        1,
        number_of_days + 1,
    ):
        current_date = (
            itinerary_start_date
            + timedelta(days=day - 1)
        )

        day_start = 10 * 60
        day_end = 22 * 60

        is_arrival_day = (
            arrival_datetime is not None
            and arrival_datetime.date()
            == current_date
        )

        is_departure_day = (
            departure_datetime is not None
            and departure_datetime.date()
            == current_date
        )

        # ---------------------------------------------------------
        # ARRIVAL DAY WINDOW
        # ---------------------------------------------------------

        if is_arrival_day:
            if include_arrival_day:
                arrival_minutes = (
                        arrival_datetime.hour * 60
                        + arrival_datetime.minute
                )

                day_start = (
                        arrival_minutes
                        + ARRIVAL_ACTIVITY_DELAY
                )
            else:
                continue

        # ---------------------------------------------------------
        # DEPARTURE DAY WINDOW
        # ---------------------------------------------------------

        if is_departure_day:
            if include_departure_day:
                departure_minutes = (
                    departure_datetime.hour * 60
                    + departure_datetime.minute
                )

                day_end = min(
                    22 * 60,
                    departure_minutes - 120,
                )
            else:
                continue

        # ---------------------------------------------------------
        # VALID WINDOW
        # ---------------------------------------------------------

        if day_start < day_end:
            day_windows[day] = (
                day_start,
                day_end,
            )

    # =========================================================
    # DISTRIBUTE PLACES
    # =========================================================

    if places and day_windows:
        usable_days = list(
            day_windows.keys()
        )

        current_day_index = 0

        for place in places:
            assigned = False

            # -------------------------------------------------
            # FIRST PASS
            # -------------------------------------------------

            for offset in range(
                len(usable_days)
            ):
                day_index = (
                    current_day_index
                    + offset
                ) % len(usable_days)

                day = usable_days[
                    day_index
                ]

                day_start, day_end = (
                    day_windows[day]
                )

                scheduled = (
                    schedule_places_for_day(
                        places=[place],
                        day=day,
                        day_start=day_start,
                        day_end=day_end,
                        trip=trip,
                        itinerary_start_date=(
                            itinerary_start_date
                        ),
                    )
                )

                if not scheduled:
                    continue

                existing_places = (
                    places_by_day[day]
                )

                previous_place = (
                    existing_places[-1]
                    if existing_places
                    else None
                )

                current_date = (
                    itinerary_start_date
                    + timedelta(days=day - 1)
                )

                start_minutes = (
                    find_place_start_time(
                        place=place,
                        current_date=current_date,
                        day_start=day_start,
                        day_end=day_end,
                        previous_place=previous_place,
                    )
                )

                if start_minutes is None:
                    continue

                visit_minutes = parse_duration(
                    place.visit_duration
                )

                current_load = (
                    calculate_day_load(
                        existing_places
                    )
                )

                if (
                    current_load
                    + visit_minutes
                    > MAX_DAILY_ACTIVITY_MINUTES
                ):
                    continue

                opening_time, closing_time = (
                    get_opening_hours(
                        place,
                        current_date,
                    )
                )

                existing_places.append(
                    {
                        "place": place,
                        "start_minutes": start_minutes,
                        "duration_minutes": visit_minutes,
                        "transfer_minutes": (
                            TRANSFER_MINUTES
                            if previous_place is not None
                            else 0
                        ),
                        "opening_time": opening_time,
                        "closing_time": closing_time,
                    }
                )

                assigned = True
                current_day_index = day_index

                break

            # -------------------------------------------------
            # SECOND PASS
            # -------------------------------------------------

            if not assigned:
                for day_index, day in enumerate(
                    usable_days
                ):
                    day_start, day_end = (
                        day_windows[day]
                    )

                    existing_places = (
                        places_by_day[day]
                    )

                    previous_place = (
                        existing_places[-1]
                        if existing_places
                        else None
                    )

                    current_date = (
                        itinerary_start_date
                        + timedelta(days=day - 1)
                    )

                    start_minutes = (
                        find_place_start_time(
                            place=place,
                            current_date=current_date,
                            day_start=day_start,
                            day_end=day_end,
                            previous_place=previous_place,
                        )
                    )

                    if start_minutes is None:
                        continue

                    visit_minutes = parse_duration(
                        place.visit_duration
                    )

                    current_load = (
                        calculate_day_load(
                            existing_places
                        )
                    )

                    if (
                        current_load
                        + visit_minutes
                        > MAX_DAILY_ACTIVITY_MINUTES
                    ):
                        continue

                    opening_time, closing_time = (
                        get_opening_hours(
                            place,
                            current_date,
                        )
                    )

                    existing_places.append(
                        {
                            "place": place,
                            "start_minutes": start_minutes,
                            "duration_minutes": visit_minutes,
                            "transfer_minutes": (
                                TRANSFER_MINUTES
                                if previous_place is not None
                                else 0
                            ),
                            "opening_time": opening_time,
                            "closing_time": closing_time,
                        }
                    )

                    assigned = True
                    current_day_index = day_index

                    break

    # =========================================================
    # BUILD PLACE EVENTS
    # =========================================================

    def build_place_events(
        scheduled_places,
    ):
        events = []

        for index, item in enumerate(
            scheduled_places
        ):
            place = item["place"]

            start_minutes = item[
                "start_minutes"
            ]

            end_minutes = (
                start_minutes
                + item["duration_minutes"]
            )

            # -------------------------------------------------
            # TRAVEL BETWEEN PLACES
            # -------------------------------------------------

            if index > 0:
                transfer_start = (
                    start_minutes
                    - TRANSFER_MINUTES
                )

                previous_end = (
                    scheduled_places[index - 1][
                        "start_minutes"
                    ]
                    + scheduled_places[index - 1][
                        "duration_minutes"
                    ]
                )

                transfer_start = max(
                    transfer_start,
                    previous_end,
                )

                events.append(
                    {
                        "start": transfer_start,
                        "end": start_minutes,
                        "text": (
                            f"{format_minutes(transfer_start)}–"
                            f"{format_minutes(start_minutes)} "
                            f"Travel to {place.name}."
                        ),
                        "type": "travel",
                    }
                )

            # -------------------------------------------------
            # PLACE
            # -------------------------------------------------

            events.append(
                {
                    "start": start_minutes,
                    "end": end_minutes,
                    "text": (
                        f"{format_minutes(start_minutes)}–"
                        f"{format_minutes(end_minutes)} "
                        f"{place.name}."
                    ),
                    "type": "place",
                }
            )

        return events

    # =========================================================
    # BUILD ITINERARY
    # =========================================================

    for day in range(
        1,
        number_of_days + 1,
    ):
        current_date = (
            itinerary_start_date
            + timedelta(days=day - 1)
        )

        scheduled_places = (
            places_by_day.get(day, [])
        )

        is_arrival_day = (
            arrival_datetime is not None
            and arrival_datetime.date()
            == current_date
        )

        is_departure_day = (
            departure_datetime is not None
            and departure_datetime.date()
            == current_date
        )

        place_events = build_place_events(
            scheduled_places
        )

        # =====================================================
        # ARRIVAL DAY
        # =====================================================

        if is_arrival_day:
            title = (
                "Arrival and first impressions"
            )

            morning = ""
            lunch = ""
            afternoon = ""
            evening = ""

            arrival_minutes = None

            if arrival_datetime:
                arrival_minutes = (
                    arrival_datetime.hour * 60
                    + arrival_datetime.minute
                )

            if outbound_transport:
                arrival_text = (
                    f"Arrive in "
                    f"{trip.destination} "
                    f"at "
                    f"{outbound_transport.arrival_time}"
                )

                if hotel:
                    arrival_text += (
                        f" and travel to "
                        f"{hotel.name}."
                    )
                else:
                    arrival_text += "."

            elif hotel:
                arrival_text = (
                    f"Arrive in "
                    f"{trip.destination} "
                    f"and check in at "
                    f"{hotel.name}."
                )

            else:
                arrival_text = (
                    f"Arrival in "
                    f"{trip.destination} "
                    "and check-in."
                )

            # -------------------------------------------------
            # ARRIVAL → MORNING / AFTERNOON / EVENING
            # -------------------------------------------------

            if arrival_minutes is None:
                morning = arrival_text

            elif arrival_minutes < 12 * 60:
                morning = arrival_text

            elif arrival_minutes < 18 * 60:
                afternoon = arrival_text

            else:
                evening = arrival_text

            # -------------------------------------------------
            # LUNCH
            # -------------------------------------------------

            if arrival_minutes is not None:
                if arrival_minutes >= 12 * 60:
                    lunch = (
                        "Lunch will be skipped "
                        "because of the arrival time."
                    )
                else:
                    lunch = (
                        "Have lunch at a local "
                        "restaurant and try "
                        "traditional specialties."
                    )
            else:
                lunch = (
                    "Have a meal at a local cafe."
                )

            # -------------------------------------------------
            # ACTIVITIES
            # -------------------------------------------------

            if include_arrival_day:
                if place_events:
                    activity_text = "\n".join(
                        event["text"]
                        for event in place_events
                    )

                    if arrival_minutes is not None:
                        if arrival_minutes >= 18 * 60:
                            evening += (
                                "\n"
                                if evening
                                else ""
                            )
                            evening += activity_text
                        else:
                            afternoon += (
                                "\n"
                                if afternoon
                                else ""
                            )
                            afternoon += activity_text
                    else:
                        afternoon = activity_text

                else:
                    no_activity_text = (
                        "No activities fit in "
                        "the available time window "
                        "after arrival."
                    )

                    if arrival_minutes is not None:
                        if arrival_minutes >= 18 * 60:
                            evening += (
                                "\n"
                                if evening
                                else ""
                            )
                            evening += no_activity_text
                        else:
                            afternoon += (
                                "\n"
                                if afternoon
                                else ""
                            )
                            afternoon += no_activity_text

            else:
                no_activity_text = (
                    "No activities planned on "
                    "the arrival day."
                )

                if arrival_minutes is not None:
                    if arrival_minutes >= 18 * 60:
                        evening += (
                            "\n"
                            if evening
                            else ""
                        )
                        evening += no_activity_text
                    else:
                        afternoon += (
                            "\n"
                            if afternoon
                            else ""
                        )
                        afternoon += no_activity_text

        # =====================================================
        # DEPARTURE DAY
        # =====================================================

        elif is_departure_day:
            title = (
                "Final day and departure"
            )

            morning = ""
            lunch = ""
            afternoon = ""
            evening = ""

            # -------------------------------------------------
            # MORNING
            # -------------------------------------------------

            if hotel:
                morning = (
                    f"Check out from "
                    f"{hotel.name} "
                    "and prepare for departure."
                )
            else:
                morning = (
                    "Breakfast and free time "
                    "before departure."
                )

            # -------------------------------------------------
            # ACTIVITIES
            # -------------------------------------------------

            if include_departure_day:
                morning_events = [
                    event["text"]
                    for event in place_events
                    if event["start"] < LUNCH_START
                ]

                afternoon_events = [
                    event["text"]
                    for event in place_events
                    if event["start"] >= LUNCH_END
                ]

                if morning_events:
                    morning += (
                        "\n"
                        + "\n".join(
                            morning_events
                        )
                    )

                if return_transport:
                    departure_minutes = (
                        time_to_minutes(
                            return_transport.departure_time
                        )
                    )

                    transfer_start = (
                        departure_minutes - 120
                    )

                    if transfer_start >= LUNCH_END:
                        lunch = (
                            "13:00–14:00 Lunch at a "
                            "local restaurant and try "
                            "traditional specialties."
                        )
                    elif transfer_start > LUNCH_START:
                        lunch = (
                            "Limited lunch time before "
                            f"{format_minutes(transfer_start)}."
                        )
                    else:
                        lunch = (
                            "No lunch planned before "
                            "departure."
                        )

                elif "Food" in interests:
                    lunch = (
                        "13:00–14:00 Lunch at a local "
                        "restaurant and try traditional "
                        "specialties."
                    )
                else:
                    lunch = (
                        "13:00–14:00 Lunch before departure."
                    )

                if afternoon_events:
                    afternoon = "\n".join(
                        afternoon_events
                    )
                else:
                    afternoon = (
                        "Free time before departure."
                    )

            else:
                lunch = (
                    "No activities planned on "
                    "the departure day."
                )

                afternoon = (
                    "Free time before departure."
                )

            # -------------------------------------------------
            # TRANSFER TO AIRPORT / STATION
            # -------------------------------------------------

            if return_transport:
                departure_minutes = (
                    time_to_minutes(
                        return_transport.departure_time
                    )
                )

                transfer_start = max(
                    8 * 60,
                    departure_minutes - 120,
                )

                transfer_text = (
                    f"{format_minutes(transfer_start)} "
                    f"Travel to "
                    f"{return_transport.departure_location} "
                    f"for departure at "
                    f"{return_transport.departure_time}."
                )

                if afternoon:
                    afternoon += (
                        "\n"
                        + transfer_text
                    )
                else:
                    afternoon = transfer_text

                evening = ""

            else:
                evening = (
                    "Travel to the airport or "
                    "station and depart."
                )

        # =====================================================
        # NORMAL DAY
        # =====================================================

        else:
            title = (
                f"Explore {trip.destination}"
            )

            # -------------------------------------------------
            # MORNING
            # -------------------------------------------------

            morning_events = [
                event["text"]
                for event in place_events
                if event["start"] < LUNCH_START
            ]

            if morning_events:
                morning_places = [
                    item
                    for item in scheduled_places
                    if item["start_minutes"]
                    < LUNCH_START
                ]

                if morning_places:
                    last_morning_place = (
                        morning_places[-1]
                    )

                    last_end = (
                        last_morning_place[
                            "start_minutes"
                        ]
                        + last_morning_place[
                            "duration_minutes"
                        ]
                    )

                    travel_to_lunch_start = last_end

                    travel_to_lunch_end = (
                        travel_to_lunch_start
                        + TRANSFER_MINUTES
                    )

                    if (
                        travel_to_lunch_end
                        <= LUNCH_START
                    ):
                        morning_events.append(
                            f"{format_minutes(travel_to_lunch_start)}–"
                            f"{format_minutes(travel_to_lunch_end)} "
                            "Travel to lunch."
                        )

                morning = "\n".join(
                    morning_events
                )

            else:
                morning = (
                    f"Free morning in "
                    f"{trip.destination}."
                )

            # -------------------------------------------------
            # LUNCH
            # -------------------------------------------------

            lunch = (
                "13:00–14:00 Lunch at a "
                "local restaurant and try "
                "traditional specialties."
            )

            # -------------------------------------------------
            # AFTERNOON
            # -------------------------------------------------

            afternoon_events = [
                event["text"]
                for event in place_events
                if event["start"] >= LUNCH_END
            ]

            if afternoon_events:
                afternoon = "\n".join(
                    afternoon_events
                )
            else:
                afternoon = (
                    f"Continue exploring "
                    f"{trip.destination} "
                    "at your own pace."
                )

            # -------------------------------------------------
            # EVENING
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

        # =====================================================
        # SAVE DAY
        # =====================================================

        itinerary.append(
            {
                "day": day,
                "date": current_date,
                "title": title,
                "morning": morning,
                "lunch": lunch,
                "afternoon": afternoon,
                "evening": evening,

                "arrival_airport": (
                    {
                        "name": arrival_airport["name"],
                        "code": arrival_airport["iata_code"],
                        "latitude": arrival_airport["latitude"],
                        "longitude": arrival_airport["longitude"],
                    }
                    if (
                        is_arrival_day
                        and arrival_airport is not None
                        and arrival_airport.get(
                            "latitude"
                        ) is not None
                        and arrival_airport.get(
                            "longitude"
                        ) is not None
                    )
                    else None
                ),

                "departure_airport": (
                    {
                        "name": departure_airport["name"],
                        "code": departure_airport["iata_code"],
                        "latitude": departure_airport["latitude"],
                        "longitude": departure_airport["longitude"],
                    }
                    if (
                        is_departure_day
                        and departure_airport is not None
                        and departure_airport.get(
                            "latitude"
                        ) is not None
                        and departure_airport.get(
                            "longitude"
                        ) is not None
                    )
                    else None
                ),

                "map_places": [
                    {
                        "id": item["place"].id,
                        "name": item["place"].name,
                        "latitude": item["place"].latitude,
                        "longitude": item["place"].longitude,
                    }
                    for item in {
                        (
                            item["place"].name,
                            item["place"].latitude,
                            item["place"].longitude,
                        ): item
                        for item in scheduled_places
                        if item["place"].latitude is not None
                        and item["place"].longitude is not None
                    }.values()
                ],
            }
        )


    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "hotel": (
            {
                "id": hotel.id,
                "name": hotel.name,
                "latitude": hotel.latitude,
                "longitude": hotel.longitude,
            }
            if (
                hotel is not None
                and hotel.latitude is not None
                and hotel.longitude is not None
            )
            else None
        ),
        "itinerary": itinerary,
    }
