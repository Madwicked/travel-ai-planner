import json
import os
import urllib.parse
import urllib.request
from datetime import datetime

from dotenv import load_dotenv

from app.services.airport_provider import airport_provider
from app.services.transport_provider import TransportProvider


load_dotenv()


class RealTransportProvider(TransportProvider):
    BASE_URL = "https://api.flightapi.io"

    def __init__(self):
        self.api_key = os.getenv("FLIGHTAPI_KEY")

        if not self.api_key:
            raise RuntimeError("FLIGHTAPI_KEY is not set")

    def _get_airport_code(
        self,
        city: str,
        latitude: float | None,
        longitude: float | None,
    ):
        airport = airport_provider.find_airport(
            city,
            latitude,
            longitude,
        )

        if not airport:
            raise ValueError(
                f"Airport not found for city: {city}"
            )

        return airport["iata_code"]

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

        with urllib.request.urlopen(request) as response:
            return json.loads(
                response.read().decode()
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

        legs = {
            leg["id"]: leg
            for leg in data.get("legs", [])
        }

        return places, carriers, legs

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
        places, carriers, legs = self._build_maps(data)

        options = []

        for itinerary in data.get("itineraries", []):
            leg_ids = itinerary.get("leg_ids", [])

            if not leg_ids:
                continue

            leg = legs.get(leg_ids[0])

            if not leg:
                continue

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

                items = pricing_option.get("items", [])

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
                leg.get("origin_place_id")
            )

            destination_place = places.get(
                leg.get("destination_place_id")
            )

            if not origin_place or not destination_place:
                continue

            departure_date, departure_time = (
                self._format_datetime(
                    leg["departure"]
                )
            )

            arrival_date, arrival_time = (
                self._format_datetime(
                    leg["arrival"]
                )
            )

            carrier_name = None

            carrier_ids = leg.get(
                "marketing_carrier_ids",
                [],
            )

            if carrier_ids:
                carrier = carriers.get(
                    carrier_ids[0]
                )

                if carrier:
                    carrier_name = carrier.get("name")

            transport_type = "Flight"

            if carrier_name:
                transport_type = (
                    f"Flight · {carrier_name}"
                )

            options.append(
                {
                    "type": transport_type,
                    "price": cheapest["amount"],
                    "duration": self._format_duration(
                        leg["duration"]
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

        options.sort(
            key=lambda option: option["price"]
        )

        return options

    def _get_options(self, trip, departure, arrival, date):
        data = self._request(
            departure_airport=self._get_airport_code(
                departure,
                trip.origin_latitude
                if departure == trip.origin
                else trip.destination_latitude,
                trip.origin_longitude
                if departure == trip.origin
                else trip.destination_longitude,
            ),
            arrival_airport=self._get_airport_code(
                arrival,
                trip.destination_latitude
                if arrival == trip.destination
                else trip.origin_latitude,
                trip.destination_longitude
                if arrival == trip.destination
                else trip.origin_longitude,
            ),
            departure_date=date,
        )

        return self._build_options(data)

    def get_outbound_options(self, trip):
        return self._get_options(
            trip=trip,
            departure=trip.origin,
            arrival=trip.destination,
            date=trip.start_date,
        )

    def get_return_options(self, trip):
        return self._get_options(
            trip=trip,
            departure=trip.destination,
            arrival=trip.origin,
            date=trip.end_date,
        )
