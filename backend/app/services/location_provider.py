import os
from abc import ABC, abstractmethod

import requests


class LocationProvider(ABC):
    @abstractmethod
    def search_cities(self, query: str):
        pass

    @abstractmethod
    def search_locations(
        self,
        query: str,
        location_type: str,
    ):
        pass

    @abstractmethod
    def get_country_code(self, country: str):
        pass


class GeoapifyLocationProvider(LocationProvider):
    def __init__(self):
        self.api_key = os.getenv("GEOAPIFY_API_KEY")

    def search_cities(self, query: str):
        query = query.strip()

        if not query:
            return []

        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not configured"
            )

        url = "https://api.geoapify.com/v1/geocode/autocomplete"

        params = {
            "text": query,
            "type": "city",
            "limit": 10,
            "lang": "en",
            "apiKey": self.api_key,
        }

        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()


        cities = []
        seen = set()

        for feature in data.get("features", []):
            properties = feature.get(
                "properties",
                {}
            )

            city = properties.get("city")
            country = properties.get("country")
            country_code = properties.get(
                "country_code"
            )

            latitude = properties.get("lat")
            longitude = properties.get("lon")

            result_type = properties.get(
                "result_type"
            )

            if not city:
                continue

            if latitude is None or longitude is None:
                continue

            if result_type not in {
                "city",
                "town",
                "village",
                "municipality",
            }:
                continue

            key = (
                city.lower(),
                (country_code or "").lower(),
            )

            if key in seen:
                continue

            seen.add(key)

            cities.append(
                {
                    "name": city,
                    "country": country,
                    "country_code": (
                        country_code.upper()
                        if country_code
                        else None
                    ),
                    "latitude": latitude,
                    "longitude": longitude,
                    "_popularity": (
                        properties
                        .get("rank", {})
                        .get("popularity", 0)
                    ),
                    "_importance": (
                        properties
                        .get("rank", {})
                        .get("importance", 0)
                    ),
                    "_confidence": (
                        properties
                        .get("rank", {})
                        .get(
                            "confidence_city_level",
                            0,
                        )
                    ),
                }
            )

        cities.sort(
            key=lambda city: (
                city["_confidence"],
                city["_popularity"],
                city["_importance"],
            ),
            reverse=True,
        )

        for city in cities:
            city.pop("_popularity", None)
            city.pop("_importance", None)
            city.pop("_confidence", None)

        return cities

    def search_locations(
        self,
        query: str,
        location_type: str,
    ):
        query = query.strip()

        if not query:
            return None

        if location_type not in {
            "city",
            "country",
        }:
            raise ValueError(
                "location_type must be 'city' or 'country'"
            )

        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not configured"
            )

        url = "https://api.geoapify.com/v1/geocode/search"

        params = {
            "text": query,
            "type": location_type,
            "limit": 1,
            "lang": "en",
            "apiKey": self.api_key,
        }

        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        features = data.get(
            "features",
            [],
        )

        if not features:
            return None

        properties = features[0].get(
            "properties",
            {},
        )

        latitude = properties.get("lat")
        longitude = properties.get("lon")

        if latitude is None or longitude is None:
            return None

        return {
            "name": (
                properties.get("city")
                if location_type == "city"
                else properties.get("country")
            ),
            "country": properties.get("country"),
            "country_code": (
                properties.get("country_code", "").upper()
                if properties.get("country_code")
                else None
            ),
            "latitude": latitude,
            "longitude": longitude,
        }

    def get_country_code(self, country: str):
        location = self.search_locations(
            country,
            "country",
        )

        if location is None:
            return None

        return location["country_code"]

    def get_country_bbox(self, country: str):
        query = country.strip()

        if not query:
            return None

        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not configured"
            )

        url = "https://api.geoapify.com/v1/geocode/search"

        params = {
            "text": query,
            "type": "country",
            "limit": 1,
            "lang": "en",
            "apiKey": self.api_key,
        }

        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        features = data.get("features", [])

        if not features:
            return None

        bbox = features[0].get("bbox")

        if not bbox or len(bbox) != 4:
            return None

        return bbox

    def get_country_place_id(self, country: str):
        query = country.strip()

        if not query:
            return None

        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not configured"
            )

        url = "https://api.geoapify.com/v1/geocode/search"

        params = {
            "text": query,
            "type": "country",
            "limit": 10,
            "lang": "en",
            "apiKey": self.api_key,
        }

        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        for feature in data.get("features", []):
            properties = feature.get("properties", {})

            if properties.get("result_type") != "country":
                continue

            if (
                    properties.get("country", "").lower()
                    != country.lower()
            ):
                continue

            place_id = properties.get("place_id")

            if place_id:
                return place_id

        return None


location_provider = GeoapifyLocationProvider()

# location_provider = MockLocationProvider()