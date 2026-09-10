import os
from abc import ABC, abstractmethod

import requests


class LocationProvider(ABC):
    @abstractmethod
    def search_cities(self, query: str):
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


location_provider = GeoapifyLocationProvider()

# location_provider = MockLocationProvider()