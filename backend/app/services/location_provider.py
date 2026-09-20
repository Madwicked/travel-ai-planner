
import os
from abc import ABC, abstractmethod

import requests


GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
AUTOCOMPLETE_URL = (
    "https://api.geoapify.com/v1/geocode/autocomplete"
)

REQUEST_TIMEOUT = 10
DEFAULT_LANGUAGE = "en"


class LocationProvider(ABC):
    @abstractmethod
    def search_cities(
        self,
        query: str,
    ):
        pass

    @abstractmethod
    def search_locations(
        self,
        query: str,
        location_type: str,
    ):
        pass

    @abstractmethod
    def get_country_code(
        self,
        country: str,
    ):
        pass


class GeoapifyLocationProvider(LocationProvider):
    def __init__(self):
        self.api_key = os.getenv(
            "GEOAPIFY_API_KEY"
        )

    def _require_api_key(self):
        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not configured"
            )

    def _search(
        self,
        query: str,
        location_type: str,
        limit: int = 1,
    ) -> list[dict]:
        self._require_api_key()

        response = requests.get(
            GEOCODING_URL,
            params={
                "text": query,
                "type": location_type,
                "limit": limit,
                "lang": DEFAULT_LANGUAGE,
                "apiKey": self.api_key,
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json().get(
            "features",
            [],
        )

    def search_cities(
        self,
        query: str,
    ):
        query = query.strip()

        if not query:
            return []

        self._require_api_key()

        response = requests.get(
            AUTOCOMPLETE_URL,
            params={
                "text": query,
                "type": "city",
                "limit": 10,
                "lang": DEFAULT_LANGUAGE,
                "apiKey": self.api_key,
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        cities = []
        seen = set()

        for feature in response.json().get(
            "features",
            [],
        ):
            properties = feature.get(
                "properties",
                {},
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

            rank = properties.get(
                "rank",
                {},
            )

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
                    "_popularity": rank.get(
                        "popularity",
                        0,
                    ),
                    "_importance": rank.get(
                        "importance",
                        0,
                    ),
                    "_confidence": rank.get(
                        "confidence_city_level",
                        0,
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

        features = self._search(
            query=query,
            location_type=location_type,
            limit=1,
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
                properties.get(
                    "country_code",
                    "",
                ).upper()
                if properties.get("country_code")
                else None
            ),
            "latitude": latitude,
            "longitude": longitude,
        }

    def get_country_code(
        self,
        country: str,
    ):
        location = self.search_locations(
            country,
            "country",
        )

        if location is None:
            return None

        return location["country_code"]

    # def get_country_bbox(
    #     self,
    #     country: str,
    # ):
    #     query = country.strip()
    #
    #     if not query:
    #         return None
    #
    #     features = self._search(
    #         query=query,
    #         location_type="country",
    #         limit=1,
    #     )
    #
    #     if not features:
    #         return None
    #
    #     bbox = features[0].get("bbox")
    #
    #     if not bbox or len(bbox) != 4:
    #         return None
    #
    #     return bbox

    def get_country_place_id(
        self,
        country: str,
    ):
        query = country.strip()

        if not query:
            return None

        features = self._search(
            query=query,
            location_type="country",
            limit=10,
        )

        for feature in features:
            properties = feature.get(
                "properties",
                {},
            )

            if properties.get(
                "result_type"
            ) != "country":
                continue

            if (
                properties.get(
                    "country",
                    "",
                ).lower()
                != country.lower()
            ):
                continue

            place_id = properties.get(
                "place_id"
            )

            if place_id:
                return place_id

        return None


location_provider = GeoapifyLocationProvider()
