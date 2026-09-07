from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.transport import TripTransport
from app.models.hotel import TripHotel
from app.models.place import TripPlace


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


def generate_itinerary_data(
    trip_id: int,
    db: Session,
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        return None

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

        max_day_minutes = 6 * 60

        current_day_index = 0

        for place in places:
            visit_minutes = parse_duration(
                place.visit_duration
            )

            assigned = False

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

                if current_places:
                    previous_place = current_places[-1]

                    start_minutes = (
                            previous_place["start_minutes"]
                            + previous_place["duration_minutes"]
                            + 30
                    )

                    if (
                            start_minutes > lunch_start
                            and start_minutes < lunch_end
                    ):
                        start_minutes = lunch_end + 30

                    elif (
                            start_minutes <= lunch_start
                            and start_minutes
                            + visit_minutes
                            > lunch_start
                    ):
                        start_minutes = lunch_end + 30
                else:
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

                if end_minutes > closing_minutes:
                    continue

                day_load = sum(
                    item["duration_minutes"]
                    for item in current_places
                )

                if current_places:
                    day_load += (
                        len(current_places) * 30
                    )

                new_day_load = (
                    day_load
                    + visit_minutes
                )

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
                current_day_index = day_index

                break

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

    for day in range(1, number_of_days + 1):

        current_date = (
            trip.start_date
            + timedelta(days=day - 1)
        )

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

        else:
            title = f"Explore {trip.destination}"

            scheduled_places = places_by_day.get(
                day,
                [],
            )

            if scheduled_places:
                morning_places = []
                afternoon_places = []

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

                    if index > 0:
                        transfer_minutes = item.get(
                            "transfer_minutes",
                            0,
                        )

                        transfer_start = (
                                start_minutes
                                - transfer_minutes
                        )

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
                morning_place_items = [
                    item
                    for item in scheduled_places
                    if item["start_minutes"] < lunch_start
                ]

                if morning_place_items:
                    last_morning_place = morning_place_items[-1]

                    travel_start = (
                            last_morning_place["start_minutes"]
                            + last_morning_place["duration_minutes"]
                    )

                    travel_end = travel_start + 30

                    if travel_start < lunch_start:
                        travel_text = (
                            f"{format_minutes(travel_start)}–"
                            f"{format_minutes(travel_end)} "
                            "Travel to lunch."
                        )

                        morning_places.append(
                            travel_text
                        )

                if morning_places:
                    morning = "\n ".join(
                        morning_places
                    )
                else:
                    morning = (
                        f"Free morning in "
                        f"{trip.destination}."
                    )

                if afternoon_places:
                    afternoon = "\n".join(
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

            if "Nightlife" in interests:
                evening = (
                    "Enjoy the local nightlife "
                    "and evening atmosphere."
                )
            else:
                evening = (
                    "Dinner and a relaxed evening walk."
                )

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