import json
import os
import urllib.parse
import urllib.request

from dotenv import load_dotenv

from app.services.place_provider import PlaceProvider


load_dotenv()


class RealPlaceProvider(PlaceProvider):
    BASE_URL = "https://api.geoapify.com/v2/places"

    def __init__(self):
        self.api_key = os.getenv("GEOAPIFY_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not set"
            )

    def _request(
        self,
        latitude: float,
        longitude: float,
    ):
        params = {
            "categories": "tourism",
            "filter": (
                f"circle:{longitude},{latitude},10000"
            ),
            "bias": (
                f"proximity:{longitude},{latitude}"
            ),
            "limit": 20,
            "lang": "en",
            "apiKey": self.api_key,
        }

        url = (
            f"{self.BASE_URL}?"
            f"{urllib.parse.urlencode(params)}"
        )

        request = urllib.request.Request(
            url,
            method="GET",
        )

        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(
                    response.read().decode("utf-8")
                )

        except Exception as e:
            raise RuntimeError(
                f"Geoapify API request failed: {e}"
            ) from e

    def _get_category(self, properties):
        categories = properties.get(
            "categories",
            [],
        )

        for category in categories:
            if category.startswith(
                "tourism.sights"
            ):
                return "Sightseeing"

            if category.startswith(
                "tourism.attraction"
            ):
                return "Sightseeing"

            if category.startswith(
                "entertainment"
            ):
                return "Entertainment"

        return "Tourism"

    def _build_place(self, feature):
        properties = feature.get(
            "properties",
            {},
        )

        geometry = feature.get(
            "geometry",
            {},
        )

        coordinates = geometry.get(
            "coordinates",
            [],
        )

        if len(coordinates) < 2:
            return None

        longitude = coordinates[0]
        latitude = coordinates[1]

        name = properties.get("name")

        if not name:
            return None

        address = properties.get(
            "formatted"
        )

        if not address:
            address = ""

        return {
            "external_id": properties.get(
                "place_id"
            ),
            "source": "geoapify",
            "name": name,
            "city": properties.get(
                "city"
            ),
            "category": self._get_category(
                properties
            ),
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "rating": None,
            "opening_hours": None,
            "opening_time": "09:00",
            "closing_time": "19:00",
            "visit_duration": "1h",
        }

    def get_place_options(self, trip):
        if (
            trip.destination_latitude is None
            or trip.destination_longitude is None
        ):
            raise ValueError(
                "Destination coordinates are required"
            )

        data = self._request(
            latitude=trip.destination_latitude,
            longitude=trip.destination_longitude,
        )

        options = []

        for feature in data.get(
            "features",
            [],
        ):
            place = self._build_place(feature)

            if place:
                options.append(place)

        return options


