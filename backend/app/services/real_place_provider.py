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

    def _get_geoapify_category(
            self,
            category: str | None,
    ):
        categories = {
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

        if not category:
            return (
                "tourism,"
                "catering.restaurant,"
                "entertainment,"
                "beach,"
                "leisure.park,"
                "commercial"
            )

        selected_categories = [
            item.strip().lower()
            for item in category.split(",")
            if item.strip()
        ]

        if not selected_categories:
            return (
                "tourism,"
                "catering.restaurant,"
                "entertainment,"
                "beach,"
                "leisure.park,"
                "commercial"
            )

        geoapify_categories = []

        for selected_category in selected_categories:
            mapped_category = categories.get(
                selected_category,
                selected_category,
            )

            geoapify_categories.append(
                mapped_category
            )

        return ",".join(geoapify_categories)

    def _request(
            self,
            latitude: float | None,
            longitude: float | None,
            radius_km: int | None = None,
            category: str | None = None,
            offset: int = 0,
            limit: int = 50,
            country_place_id: str | None = None,
    ):
        params = {
            "categories": self._get_geoapify_category(
                category
            ),
            "limit": limit,
            "offset": offset,
            "lang": "en",
            "apiKey": self.api_key,
        }

        if country_place_id:
            params["filter"] = (
                f"place:{country_place_id}"
            )
        else:
            params["bias"] = (
                f"proximity:{longitude},{latitude}"
            )

            if radius_km is not None:
                params["filter"] = (
                    f"circle:{longitude},{latitude},{radius_km * 1000}"
                )

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
                data = json.loads(
                    response.read().decode("utf-8")
                )



                return data


        except Exception as e:
            if hasattr(e, "read"):
                try:
                    error_body = e.read().decode("utf-8")
                except Exception:
                    error_body = ""
            else:
                error_body = ""
            raise RuntimeError(
                f"Geoapify API request failed: {e}; "
                f"response: {error_body}"
            ) from e

    def get_place_options(
            self,
            trip,
            latitude: float | None = None,
            longitude: float | None = None,
            radius_km: int | None = None,
            category: str | None = None,
            offset: int = 0,
            limit: int = 500,
            country_place_id: str | None = None,
    ):
        if (
                trip.destination_latitude is None
                or trip.destination_longitude is None
        ):
            raise ValueError(
                "Destination coordinates are required"
            )

        if category:
            data = self._request(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                category=category,
                offset=0,
                limit=limit,
                country_place_id=country_place_id,
            )

            features = data.get(
                "features",
                [],
            )

            options = []

            for feature in features:
                place = self._build_place(
                    feature,
                    latitude,
                    longitude,
                    include_distance=country_place_id is None,
                )

                if place:
                    print(
                        f"DEBUG PLACE: "
                        f"name={place['name']} "
                        f"category={place['category']}"
                    )

                    options.append(place)



            return {
                "options": options,
                "total": len(options),
                "offset": 0,
                "limit": limit,
                "has_more": len(features) >= limit,
            }

        categories = [
            "attractions",
            "nature",
            "entertainment",
            "food",
            "shopping",
        ]

        options = []
        seen_ids = set()

        for place_category in categories:
            data = self._request(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                category=place_category,
                offset=0,
                limit=500,
                country_place_id=country_place_id,
            )

            features = data.get(
                "features",
                [],
            )

            built_count = 0
            skipped_count = 0

            print(
                f"PLACES CATEGORY: {place_category} "
                f"FEATURES: {len(features)}"
            )

            for feature in features:
                place = self._build_place(
                    feature,
                    latitude,
                    longitude,
                    include_distance=country_place_id is None,
                )

                if not place:
                    skipped_count += 1
                    continue

                built_count += 1

                external_id = place.get("external_id")

                if external_id:
                    if external_id in seen_ids:
                        continue

                    seen_ids.add(external_id)

                options.append(place)

            print(
                f"PLACES CATEGORY: {place_category} "
                f"BUILT: {built_count} "
                f"SKIPPED: {skipped_count} "
                f"TOTAL OPTIONS: {len(options)}"
            )

        return {
            "options": options,
            "total": len(options),
            "offset": 0,
            "limit": len(options),
            "has_more": False,
        }

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
                    "commercial"
            ):
                return "Shopping"

            if category.startswith(
                    "leisure.park"
            ):
                return "Nature"

            if category.startswith(
                    "beach"
            ):
                return "Nature"

            if category.startswith(
                    "entertainment"
            ):
                return "Entertainment"

            if category.startswith(
                    "tourism"
            ):
                return "Attractions"

        return "Attractions"

    def _build_place(
            self,
            feature,
            center_latitude,
            center_longitude,
            include_distance=True,
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
            ) or "",
            "country": properties.get(
                "country"
            ),
            "category": self._get_category(
                properties
            ),
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "distance_km": (
                round(
                    self._calculate_distance_km(
                        center_latitude,
                        center_longitude,
                        latitude,
                        longitude,
                    ),
                    1,
                )
                if include_distance
                else None
            ),
            "rating": None,
            "opening_hours": None,
            "opening_time": "09:00",
            "closing_time": "19:00",
            "visit_duration": "1h",
        }


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


