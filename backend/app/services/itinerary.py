from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.transport import TripTransport
from app.models.hotel import TripHotel
from app.models.place import TripPlace


TRANSFER_MINUTES = 30
LUNCH_START = 13 * 60
LUNCH_END = 14 * 60
MAX_DAILY_ACTIVITY_MINUTES = 6 * 60


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

    Travel to/from lunch is not counted as activity load,
    because it is part of the fixed daily schedule.
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

    Important rules:

    1. 30 minutes between Places.
    2. Lunch is fixed at 13:00–14:00.
    3. If a morning Place is scheduled, it must leave
       30 minutes for travel to lunch.
    4. After lunch, the first Place starts at 14:30
       because 14:00–14:30 is travel.
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
    # BEFORE / DURING LUNCH
    # ---------------------------------------------------------

    # If the activity would cross lunch, move it
    # to the afternoon.
    if (
        start_minutes < LUNCH_START
        and start_minutes + visit_minutes > LUNCH_START
    ):
        start_minutes = max(
            start_minutes,
            LUNCH_END + TRANSFER_MINUTES,
        )

    # If the activity would finish after 12:30,
    # there would not be 30 minutes left to travel to lunch.
    #
    # Therefore morning activities must satisfy:
    #
    # Place ends <= 12:30
    # Travel to lunch 12:30–13:00
    # Lunch 13:00–14:00
    #
    if (
        start_minutes < LUNCH_START
        and start_minutes + visit_minutes
        > LUNCH_START - TRANSFER_MINUTES
    ):
        start_minutes = (
            LUNCH_END + TRANSFER_MINUTES
        )

    # If we are already inside lunch,
    # move to 14:30.
    if (
        LUNCH_START
        <= start_minutes
        < LUNCH_END + TRANSFER_MINUTES
    ):
        start_minutes = (
            LUNCH_END + TRANSFER_MINUTES
        )

    # ---------------------------------------------------------
    # AFTERNOON ACTIVITY
    # ---------------------------------------------------------

    end_minutes = (
        start_minutes + visit_minutes
    )

    # Respect opening hours.
    if start_minutes < opening_minutes:
        start_minutes = opening_minutes

        # Re-check lunch after applying opening time.
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

    # Morning activity must leave 30 minutes
    # before lunch.
    if start_minutes < LUNCH_START:
        if (
            end_minutes
            > LUNCH_START - TRANSFER_MINUTES
        ):
            return None

    # Afternoon activity cannot overlap lunch
    # or the 14:00–14:30 transfer.
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
):
    """
    Attempts to schedule Places for one specific day.

    Returns the scheduled Places for that day.
    """

    current_date = (
        trip.start_date
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
                    if scheduled
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
    # BASIC DATA
    # =========================================================

    number_of_days = (
        trip.end_date - trip.start_date
    ).days + 1

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
            trip.start_date
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

        # -----------------------------------------------------
        # ARRIVAL DAY
        # -----------------------------------------------------

        if is_arrival_day:
            if not include_arrival_day:
                continue

            arrival_minutes = (
                arrival_datetime.hour * 60
                + arrival_datetime.minute
            )

            if arrival_minutes < 6 * 60:
                day_start = 10 * 60
            else:
                day_start = max(
                    10 * 60,
                    arrival_minutes + 120,
                )

        # -----------------------------------------------------
        # DEPARTURE DAY
        # -----------------------------------------------------

        if is_departure_day:
            if not include_departure_day:
                continue

            departure_minutes = (
                departure_datetime.hour * 60
                + departure_datetime.minute
            )

            day_end = min(
                22 * 60,
                departure_minutes - 120,
            )

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
                        places=[
                            place
                        ],
                        day=day,
                        day_start=day_start,
                        day_end=day_end,
                        trip=trip,
                    )
                )

                if not scheduled:
                    continue

                candidate = scheduled[0]

                # Existing places must be taken
                # into account as well.
                existing_places = (
                    places_by_day[day]
                )

                previous_place = (
                    existing_places[-1]
                    if existing_places
                    else None
                )

                start_minutes = (
                    find_place_start_time(
                        place=place,
                        current_date=(
                            trip.start_date
                            + timedelta(
                                days=day - 1
                            )
                        ),
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
                        trip.start_date
                        + timedelta(
                            days=day - 1
                        ),
                    )
                )

                existing_places.append(
                    {
                        "place": place,
                        "start_minutes":
                            start_minutes,
                        "duration_minutes":
                            visit_minutes,
                        "transfer_minutes":
                            (
                                TRANSFER_MINUTES
                                if existing_places
                                else 0
                            ),
                        "opening_time":
                            opening_time,
                        "closing_time":
                            closing_time,
                    }
                )

                assigned = True

                current_day_index = (
                    day_index
                )

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

                    start_minutes = (
                        find_place_start_time(
                            place=place,
                            current_date=(
                                trip.start_date
                                + timedelta(
                                    days=day - 1
                                )
                            ),
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
                            trip.start_date
                            + timedelta(
                                days=day - 1
                            ),
                        )
                    )

                    existing_places.append(
                        {
                            "place": place,
                            "start_minutes":
                                start_minutes,
                            "duration_minutes":
                                visit_minutes,
                            "transfer_minutes":
                                (
                                    TRANSFER_MINUTES
                                    if existing_places
                                    else 0
                                ),
                            "opening_time":
                                opening_time,
                            "closing_time":
                                closing_time,
                        }
                    )

                    assigned = True

                    current_day_index = (
                        day_index
                    )

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

                # The transfer must begin after the
                # previous Place has finished.
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
            trip.start_date
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

            # -------------------------------------------------
            # MORNING
            # -------------------------------------------------

            if outbound_transport:
                morning = (
                    f"Arrive in "
                    f"{trip.destination} "
                    f"at "
                    f"{outbound_transport.arrival_time}"
                )

                if hotel:
                    morning += (
                        f" and travel to "
                        f"{hotel.name}."
                    )
                else:
                    morning += "."

            elif hotel:
                morning = (
                    f"Arrive in "
                    f"{trip.destination} "
                    f"and check in at "
                    f"{hotel.name}."
                )

            else:
                morning = (
                    f"Arrival in "
                    f"{trip.destination} "
                    "and check-in."
                )

            # -------------------------------------------------
            # LUNCH
            # -------------------------------------------------

            if arrival_datetime:
                arrival_minutes = (
                    arrival_datetime.hour * 60
                    + arrival_datetime.minute
                )

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
                    activity_texts = [
                        event["text"]
                        for event in place_events
                    ]

                    afternoon = "\n".join(
                        activity_texts
                    )

                    evening = (
                        "Enjoy the evening in "
                        f"{trip.destination}."
                    )

                else:
                    afternoon = (
                        "No activities fit in "
                        "the available time window "
                        "after arrival."
                    )

                    evening = (
                        "Enjoy a relaxed evening "
                        "and prepare for the next day."
                    )

            else:
                afternoon = (
                    "No activities planned on "
                    "the arrival day."
                )

                evening = (
                    "Enjoy a relaxed evening and "
                    "prepare for the next day."
                )

        # =====================================================
        # DEPARTURE DAY
        # =====================================================

        elif is_departure_day:
            title = (
                "Final day and departure"
            )

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

                    # Lunch has its normal fixed window
                    # of 13:00–14:00 if there is enough
                    # time before the airport/station transfer.
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
                # Add travel to lunch after the last
                # morning Place, if applicable.
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

                    travel_to_lunch_start = (
                        last_end
                    )

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

            # The first afternoon Place requires
            # 30 minutes of travel after lunch.
            #
            # This is already included in the scheduling
            # calculation because the earliest afternoon
            # start is 14:30.

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
            }
        )

    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "itinerary": itinerary,
    }