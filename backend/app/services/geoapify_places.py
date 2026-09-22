import os
import re
from math import atan2, cos, radians, sin, sqrt

import requests


BASE_URL = "https://api.geoapify.com/v2/places"

REQUEST_TIMEOUT = 20
DEFAULT_LIMIT_PER_CATEGORY = 500
EARTH_RADIUS_KM = 6371.0


CATEGORY_MAP = {
    "attractions": (
        "tourism.sights,"
        "tourism.attraction"
    ),
    "nature": (
        "beach,"
        "leisure.park"
    ),
    "entertainment": (
        "entertainment.cinema,"
        "entertainment.culture,"
        "entertainment.bowling_alley,"
        "entertainment.escape_game,"
        "entertainment.museum,"
        "entertainment.zoo,"
        "entertainment.aquarium,"
        "entertainment.theme_park,"
        "entertainment.water_park"
    ),
    "food": (
        "catering.restaurant"
    ),
    "shopping": (
        "commercial"
    ),
}


class GeoapifyPlacesService:
    """
    Gets places from Geoapify Places API.

    Geoapify is the source of the full Places list.
    No importance scoring is performed here.
    """

    def __init__(self):
        self.api_key = os.getenv(
            "GEOAPIFY_API_KEY"
        )

    def get_places(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        category: str | None = None,
        limit: int = DEFAULT_LIMIT_PER_CATEGORY,
    ) -> list[dict]:
        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not configured"
            )

        if category:
            categories = CATEGORY_MAP.get(
                category
            )

            if not categories:
                return []

            places = self._request(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                categories=categories,
                limit=limit,
            )

            for place in places:
                place["category"] = category

            return self._deduplicate(
                places
            )

        places = []

        for category_name, categories in CATEGORY_MAP.items():
            category_places = self._request(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                categories=categories,
                limit=limit,
            )

            for place in category_places:
                place["category"] = category_name

            places.extend(category_places)

        return self._deduplicate(
            places
        )

    def get_places_by_categories(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        categories: list[str],
        limit: int = DEFAULT_LIMIT_PER_CATEGORY,
    ) -> list[dict]:
        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not configured"
            )

        places = []

        for category in categories:
            category_mapping = CATEGORY_MAP.get(
                category
            )

            if not category_mapping:
                continue

            category_places = self._request(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                categories=category_mapping,
                limit=limit,
            )

            for place in category_places:
                place["category"] = (
                    "Food"
                    if category == "food"
                    else "Shopping"
                    if category == "shopping"
                    else category
                )

            places.extend(category_places)

        return self._deduplicate(
            places
        )

    def get_places_by_country(
        self,
        country_place_id: str,
        category: str | None = None,
        limit: int = DEFAULT_LIMIT_PER_CATEGORY,
    ) -> list[dict]:
        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not configured"
            )

        if not country_place_id:
            return []

        if category:
            categories = CATEGORY_MAP.get(
                category
            )

            if not categories:
                return []

            places = self._request(
                categories=categories,
                limit=limit,
                country_place_id=country_place_id,
            )

            for place in places:
                place["category"] = category

            return self._deduplicate(
                places
            )

        places = []

        for category_name, categories in CATEGORY_MAP.items():
            category_places = self._request(
                categories=categories,
                limit=limit,
                country_place_id=country_place_id,
            )

            for place in category_places:
                place["category"] = category_name

            places.extend(category_places)

        return self._deduplicate(
            places
        )

    def get_places_by_country_categories(
        self,
        country_place_id: str,
        categories: list[str],
        limit: int = DEFAULT_LIMIT_PER_CATEGORY,
    ) -> list[dict]:
        if not self.api_key:
            raise RuntimeError(
                "GEOAPIFY_API_KEY is not configured"
            )

        if not country_place_id:
            return []

        places = []

        for category in categories:
            category_mapping = CATEGORY_MAP.get(
                category
            )

            if not category_mapping:
                continue

            category_places = self._request(
                categories=category_mapping,
                limit=limit,
                country_place_id=country_place_id,
            )

            for place in category_places:
                place["category"] = (
                    "Food"
                    if category == "food"
                    else "Shopping"
                    if category == "shopping"
                    else category
                )

            places.extend(category_places)

        return self._deduplicate(
            places
        )

    def _request(
        self,
        categories: str,
        limit: int,
        latitude: float | None = None,
        longitude: float | None = None,
        radius_km: float | None = None,
        country_place_id: str | None = None,
    ) -> list[dict]:
        params = {
            "categories": categories,
            "limit": limit,
            "lang": "en",
            "apiKey": self.api_key,
        }

        if latitude is not None and longitude is not None:
            params["bias"] = (
                f"proximity:"
                f"{longitude},"
                f"{latitude}"
            )

            if radius_km is not None:
                params["filter"] = (
                    f"circle:"
                    f"{longitude},"
                    f"{latitude},"
                    f"{radius_km * 1000}"
                )

        elif country_place_id:
            params["filter"] = (
                f"place:{country_place_id}"
            )

        try:
            response = requests.get(
                BASE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

        except requests.RequestException:
            return []

        data = response.json()

        places = []

        for feature in data.get(
            "features",
            [],
        ):
            place = self._build_place(
                feature
            )

            if place is None:
                continue

            if (
                latitude is not None
                and longitude is not None
            ):
                place["distance_km"] = (
                    self._calculate_distance_km(
                        latitude=place["latitude"],
                        longitude=place["longitude"],
                        target_latitude=latitude,
                        target_longitude=longitude,
                    )
                )

            places.append(place)

        return places

    def _build_place(
        self,
        feature: dict,
    ) -> dict | None:
        properties = feature.get(
            "properties",
            {},
        )

        geometry = feature.get(
            "geometry",
            {},
        )

        coordinates = geometry.get(
            "coordinates"
        )

        if (
            not coordinates
            or len(coordinates) < 2
        ):
            return None

        longitude = coordinates[0]
        latitude = coordinates[1]

        name = properties.get(
            "name"
        )

        if not name:
            return None

        categories = properties.get(
            "categories",
            [],
        )

        opening_hours = properties.get(
            "opening_hours"
        )

        opening_time, closing_time = (
            self._parse_opening_hours(
                opening_hours
            )
        )

        opening_time, closing_time = (
            self._parse_opening_hours(
                opening_hours
            )
        )

        return {
            "external_id": properties.get(
                "place_id"
            ),
            "source": "geoapify",
            "name": name,
            "city": properties.get(
                "city"
            ),
            "country": properties.get(
                "country"
            ),
            "category": None,
            "address": properties.get(
                "formatted"
            ),
            "latitude": latitude,
            "longitude": longitude,
            "distance_km": None,
            "rating": properties.get(
                "rating"
            ),
            "opening_hours": opening_hours,
            "opening_time": opening_time,
            "closing_time": closing_time,
            "visit_duration": None,
            "_geo_categories": categories,
        }

    def _parse_opening_hours(
        self,
        opening_hours,
    ) -> tuple[str | None, str | None]:
        if not opening_hours:
            return None, None

        if isinstance(opening_hours, dict):
            time_ranges = []

            for value in opening_hours.values():
                if isinstance(value, str):
                    time_ranges.extend(
                        re.findall(
                            r"\b\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\b",
                            value,
                        )
                    )

            if time_ranges:
                return self._extract_time_range(
                    time_ranges[0]
                )

            return None, None

        if not isinstance(opening_hours, str):
            return None, None

        match = re.search(
            r"\b(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\b",
            opening_hours,
        )

        if not match:
            return None, None

        return (
            self._normalize_time(
                match.group(1)
            ),
            self._normalize_time(
                match.group(2)
            ),
        )

    def _extract_time_range(
        self,
        value: str,
    ) -> tuple[str | None, str | None]:
        match = re.search(
            r"\b(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\b",
            value,
        )

        if not match:
            return None, None

        return (
            self._normalize_time(
                match.group(1)
            ),
            self._normalize_time(
                match.group(2)
            ),
        )

    def _normalize_time(
        self,
        value: str,
    ) -> str:
        hour, minute = value.split(":")

        return (
            f"{int(hour):02d}:{int(minute):02d}"
        )

    def _deduplicate(
        self,
        places: list[dict],
    ) -> list[dict]:
        unique = {}
        fallback = set()

        for place in places:
            external_id = place.get(
                "external_id"
            )

            category = place.get(
                "category"
            )

            if external_id:
                key = (
                    category,
                    external_id,
                )

                if key in unique:
                    continue

                unique[key] = place
                continue

            key = (
                category,
                place.get("name"),
                place.get("latitude"),
                place.get("longitude"),
            )

            if key in fallback:
                continue

            fallback.add(key)
            unique[key] = place

        return list(
            unique.values()
        )

    def _calculate_distance_km(
        self,
        latitude: float,
        longitude: float,
        target_latitude: float,
        target_longitude: float,
    ) -> float:
        lat1 = radians(latitude)
        lon1 = radians(longitude)

        lat2 = radians(target_latitude)
        lon2 = radians(target_longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a),
        )

        return EARTH_RADIUS_KM * c