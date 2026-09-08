import json
import os
import urllib.parse
import urllib.request
import math

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
        radius_km: int = 10,
    ):
        params = {
            "categories": "tourism,catering.restaurant,entertainment",
            "filter": (
                f"circle:{longitude},{latitude},{radius_km * 1000}"
            ),
            "bias": (
                f"proximity:{longitude},{latitude}"
            ),
            "limit": 50,
            "lang": "en",
            "apiKey": self.api_key,
        }

        print("RADIUS KM:", radius_km)
        print("FILTER:", params["filter"])

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
                    "catering.restaurant"
            ):
                return "Food"

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

    def _build_place(
            self,
            feature,
            center_latitude,
            center_longitude,
    ):
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
            "distance_km": round(
                self._calculate_distance_km(
                    center_latitude,
                    center_longitude,
                    latitude,
                    longitude,
                ),
                1,
            ),
            "rating": None,
            "opening_hours": None,
            "opening_time": "09:00",
            "closing_time": "19:00",
            "visit_duration": "1h",
        }

    def get_place_options(
            self,
            trip,
            radius_km: int = 10,
    ):
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
            radius_km=radius_km,
        )

        options = []

        for feature in data.get(
                "features",
                [],
        ):
            place = self._build_place(
                feature,
                trip.destination_latitude,
                trip.destination_longitude,
            )

            if place:
                options.append(place)

        return options

    def _calculate_distance_km(
            self,
            latitude1: float,
            longitude1: float,
            latitude2: float,
            longitude2: float,
    ):
        earth_radius_km = 6371

        lat1 = math.radians(latitude1)
        lat2 = math.radians(latitude2)

        delta_lat = math.radians(
            latitude2 - latitude1
        )
        delta_lon = math.radians(
            longitude2 - longitude1
        )

        a = (
                math.sin(delta_lat / 2) ** 2
                + math.cos(lat1)
                * math.cos(lat2)
                * math.sin(delta_lon / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )

        return earth_radius_km * c


