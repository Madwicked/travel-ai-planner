import json
import os
import urllib.request
from urllib.error import HTTPError
from datetime import datetime

from dotenv import load_dotenv

from app.services.transport_provider import TransportProvider
from app.services.airport_provider import airport_provider


load_dotenv()


class RealFlightProvider(TransportProvider):
    BASE_URL = "https://api.flightapi.io"

    def __init__(self):
        self.api_key = os.getenv("FLIGHTAPI_KEY")

        if not self.api_key:
            raise RuntimeError("FLIGHTAPI_KEY is not set")

    def _get_airports(
            self,
            city: str,
            latitude: float | None,
            longitude: float | None,
            country: str | None,
    ):
        airports = airport_provider.find_airports(
            city,
            latitude,
            longitude,
            country=country,
        )

        if not airports:
            raise ValueError(
                f"Airports not found for city: {city}"
            )

        return airports

    def _request(
        self,
        departure_airport: str,
        arrival_airport: str,
        departure_date,
    ):
        date_value = departure_date.strftime("%Y-%m-%d")

        url = (
            f"{self.BASE_URL}/onewaytrip/"
            f"{self.api_key}/"
            f"{departure_airport}/"
            f"{arrival_airport}/"
            f"{date_value}/"
            "1/"
            "0/"
            "0/"
            "Economy/"
            "EUR"
        )

        request = urllib.request.Request(
            url,
            method="GET",
        )

        try:
            with urllib.request.urlopen(request) as response:
                raw_data = response.read().decode()

            return json.loads(raw_data)

        except HTTPError as error:
            body = error.read().decode()

            raise ValueError(
                f"FlightAPI error {error.code}: {body}"
            )

    def _build_maps(self, data):
        places = {
            place["id"]: place
            for place in data.get("places", [])
        }

        carriers = {
            carrier["id"]: carrier
            for carrier in data.get("carriers", [])
        }

        segments = {
            segment["id"]: segment
            for segment in data.get("segments", [])
        }

        return places, carriers, segments

    def _format_duration(self, minutes: int):
        hours = minutes // 60
        remaining_minutes = minutes % 60

        if hours and remaining_minutes:
            return f"{hours}h {remaining_minutes}m"

        if hours:
            return f"{hours}h"

        return f"{remaining_minutes}m"

    def _format_datetime(self, value: str):
        date_time = datetime.fromisoformat(value)

        return (
            date_time.strftime("%Y-%m-%d"),
            date_time.strftime("%H:%M"),
        )

    def _build_options(self, data):
        places, carriers, segments = self._build_maps(data)

        legs = {
            leg["id"]: leg
            for leg in data.get("legs", [])
        }

        options = []

        for itinerary in data.get("itineraries", []):
            segment_ids = []

            for leg_id in itinerary.get("leg_ids", []):
                leg = legs.get(leg_id)

                if leg:
                    segment_ids.extend(
                        leg.get("segment_ids", [])
                    )

            if not segment_ids:
                continue

            itinerary_segments = []

            for segment_id in segment_ids:
                segment = segments.get(segment_id)

                if segment:
                    itinerary_segments.append(segment)

            if not itinerary_segments:
                continue

            first_segment = itinerary_segments[0]
            last_segment = itinerary_segments[-1]

            pricing_options = itinerary.get(
                "pricing_options",
                [],
            )

            valid_prices = []

            for pricing_option in pricing_options:
                price = pricing_option.get("price")

                if not price:
                    continue

                amount = price.get("amount")

                if amount is None:
                    continue

                items = pricing_option.get(
                    "items",
                    [],
                )

                booking_url = None

                for item in items:
                    item_url = item.get("url")

                    if item_url:
                        booking_url = item_url

                        if booking_url.startswith("/"):
                            booking_url = (
                                "https://www.flightapi.io"
                                + booking_url
                            )

                        break

                valid_prices.append(
                    {
                        "amount": float(amount),
                        "booking_url": booking_url,
                    }
                )

            if not valid_prices:
                continue

            cheapest = min(
                valid_prices,
                key=lambda item: item["amount"],
            )

            origin_place = places.get(
                first_segment.get("origin_place_id")
            )

            destination_place = places.get(
                last_segment.get("destination_place_id")
            )

            if not origin_place or not destination_place:
                continue

            departure_date, departure_time = (
                self._format_datetime(
                    first_segment["departure"]
                )
            )

            arrival_date, arrival_time = (
                self._format_datetime(
                    last_segment["arrival"]
                )
            )

            departure_datetime = datetime.fromisoformat(
                first_segment["departure"]
            )

            arrival_datetime = datetime.fromisoformat(
                last_segment["arrival"]
            )

            total_duration = int(
                (
                    arrival_datetime
                    - departure_datetime
                ).total_seconds()
                // 60
            )

            carrier_name = None

            marketing_carrier_id = first_segment.get(
                "marketing_carrier_id"
            )

            if marketing_carrier_id is not None:
                carrier = carriers.get(
                    marketing_carrier_id
                )

                if carrier:
                    carrier_name = carrier.get(
                        "name"
                    )

            transport_type = "Flight"

            if carrier_name:
                transport_type = (
                    f"Flight · {carrier_name}"
                )

            flight_segments = []

            for segment in itinerary_segments:
                segment_origin = places.get(
                    segment.get("origin_place_id")
                )

                segment_destination = places.get(
                    segment.get("destination_place_id")
                )

                segment_departure = datetime.fromisoformat(
                    segment["departure"]
                )

                segment_arrival = datetime.fromisoformat(
                    segment["arrival"]
                )

                segment_duration = int(
                    (
                        segment_arrival
                        - segment_departure
                    ).total_seconds()
                    // 60
                )

                segment_carrier_name = None
                segment_carrier_code = None
                segment_carrier_code_type = None

                segment_carrier_id = segment.get(
                    "marketing_carrier_id"
                )

                if segment_carrier_id is not None:
                    segment_carrier = carriers.get(
                        segment_carrier_id
                    )

                    if segment_carrier:
                        segment_carrier_name = (
                            segment_carrier.get(
                                "name"
                            )
                        )

                        segment_carrier_code = (
                            segment_carrier.get(
                                "display_code"
                            )
                        )

                        segment_carrier_code_type = (
                            segment_carrier.get(
                                "display_code_type"
                            )
                        )

                (
                    segment_departure_date,
                    segment_departure_time,
                ) = self._format_datetime(
                    segment["departure"]
                )

                (
                    segment_arrival_date,
                    segment_arrival_time,
                ) = self._format_datetime(
                    segment["arrival"]
                )

                flight_segments.append(
                    {
                        "carrier": segment_carrier_name,
                        "carrier_code": segment_carrier_code,
                        "carrier_code_type": segment_carrier_code_type,
                        "flight_number": segment.get(
                            "marketing_flight_number"
                        ),
                        "departure_date": (
                            segment_departure_date
                        ),
                        "departure_time": (
                            segment_departure_time
                        ),
                        "departure_location": (
                            f"{segment_origin['name']} "
                            f"({segment_origin['display_code']})"
                            if segment_origin
                            else ""
                        ),
                        "arrival_date": (
                            segment_arrival_date
                        ),
                        "arrival_time": (
                            segment_arrival_time
                        ),
                        "arrival_location": (
                            f"{segment_destination['name']} "
                            f"({segment_destination['display_code']})"
                            if segment_destination
                            else ""
                        ),
                        "duration": self._format_duration(
                            segment_duration
                        ),
                    }
                )

            stops = max(
                len(flight_segments) - 1,
                0,
            )

            layovers = []

            for index in range(
                len(itinerary_segments) - 1
            ):
                current_segment = (
                    itinerary_segments[index]
                )

                next_segment = (
                    itinerary_segments[index + 1]
                )

                current_arrival = datetime.fromisoformat(
                    current_segment["arrival"]
                )

                next_departure = datetime.fromisoformat(
                    next_segment["departure"]
                )

                layover_minutes = int(
                    (
                        next_departure
                        - current_arrival
                    ).total_seconds()
                    // 60
                )

                layovers.append(
                    {
                        "location": (
                            flight_segments[index][
                                "arrival_location"
                            ]
                        ),
                        "duration": self._format_duration(
                            layover_minutes
                        ),
                    }
                )

            options.append(
                {
                    "type": transport_type,
                    "price": cheapest["amount"],
                    "currency": "EUR",
                    "stops": stops,
                    "segments": flight_segments,
                    "layovers": layovers,
                    "duration": self._format_duration(
                        total_duration
                    ),
                    "departure_date": departure_date,
                    "departure_time": departure_time,
                    "departure_location": (
                        f"{origin_place['name']} "
                        f"({origin_place['display_code']})"
                    ),
                    "arrival_date": arrival_date,
                    "arrival_time": arrival_time,
                    "arrival_location": (
                        f"{destination_place['name']} "
                        f"({destination_place['display_code']})"
                    ),
                    "booking_url": cheapest[
                        "booking_url"
                    ],
                }
            )


        return options

    def _get_options(
        self,
        trip,
        departure,
        arrival,
        date,
    ):
        departure_latitude = (
            trip.origin_latitude
            if departure == trip.origin
            else trip.destination_latitude
        )

        departure_longitude = (
            trip.origin_longitude
            if departure == trip.origin
            else trip.destination_longitude
        )

        arrival_latitude = (
            trip.destination_latitude
            if arrival == trip.destination
            else trip.origin_latitude
        )

        arrival_longitude = (
            trip.destination_longitude
            if arrival == trip.destination
            else trip.origin_longitude
        )

        departure_country = (
            trip.origin_country
            if departure == trip.origin
            else trip.destination_country
        )

        arrival_country = (
            trip.destination_country
            if arrival == trip.destination
            else trip.origin_country
        )

        departure_airports = self._get_airports(
            city=departure,
            latitude=departure_latitude,
            longitude=departure_longitude,
            country=departure_country,
        )

        arrival_airports = self._get_airports(
            city=arrival,
            latitude=arrival_latitude,
            longitude=arrival_longitude,
            country=arrival_country,
        )

        print(
            "FLIGHT API AIRPORTS: "
            f"departure={[(a['iata_code'], a.get('name')) for a in departure_airports]}, "
            f"arrival={[(a['iata_code'], a.get('name')) for a in arrival_airports]}"
        )

        all_options = []
        errors = []

        for departure_airport in departure_airports:
            for arrival_airport in arrival_airports:
                departure_code = departure_airport["iata_code"]
                arrival_code = arrival_airport["iata_code"]

                print(
                    "FLIGHT API REQUEST: "
                    f"{departure_code} -> {arrival_code} "
                    f"date={date}"
                )

                try:
                    data = self._request(
                        departure_airport=departure_code,
                        arrival_airport=arrival_code,
                        departure_date=date,
                    )

                    options = self._build_options(data)

                    all_options.extend(options)

                except ValueError as error:
                    errors.append(
                        f"{departure_code} -> {arrival_code}: {error}"
                    )

        unique_options = []
        seen = set()

        for option in all_options:
            segments = option.get(
                "segments",
                [],
            )

            segment_key = tuple(
                (
                    segment.get("carrier_code"),
                    segment.get("flight_number"),
                    segment.get("departure_date"),
                    segment.get("departure_time"),
                    segment.get("arrival_date"),
                    segment.get("arrival_time"),
                    segment.get("departure_location"),
                    segment.get("arrival_location"),
                )
                for segment in segments
            )

            key = (
                option.get("price"),
                option.get("departure_date"),
                option.get("departure_time"),
                option.get("arrival_date"),
                option.get("arrival_time"),
                segment_key,
            )

            if key in seen:
                continue

            seen.add(key)
            unique_options.append(option)

        if not unique_options and errors:
            raise ValueError(
                "No transport options found. "
                + " | ".join(errors)
            )

        return unique_options

    def get_outbound_options(
            self,
            trip,
            search_date=None,
    ):
        if search_date is None:
            search_date = trip.start_date

        return self._get_options(
            trip=trip,
            departure=trip.origin,
            arrival=trip.destination,
            date=search_date,
        )

    def get_return_options(
            self,
            trip,
            search_date=None,
    ):
        if search_date is None:
            search_date = trip.end_date

        return self._get_options(
            trip=trip,
            departure=trip.destination,
            arrival=trip.origin,
            date=search_date,
        )
