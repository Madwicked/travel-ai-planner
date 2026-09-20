import json
import os
import urllib.parse
import urllib.request
import math
import re
import unicodedata

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
            name: str | None = None,
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

        if name:
            params["name"] = name

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

            options.sort(
                key=lambda place: place.get(
                    "_importance_score",
                    0,
                ),
                reverse=True,
            )

            options = self._deduplicate_and_adjust_subfeatures(
                options
            )

            for place in options:
                place.pop(
                    "_importance_score",
                    None,
                )
                place.pop(
                    "_geo_categories",
                    None,
                )

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

        options.sort(
            key=lambda place: place.get(
                "_importance_score",
                0,
            ),
            reverse=True,
        )

        options = self._deduplicate_and_adjust_subfeatures(
            options
        )

        for place in options[:30]:
            print(
                "RANKED PLACE:",
                place["name"],
                "|",
                place["category"],
                "| SCORE:",
                place.get("_importance_score"),
            )

        for place in options:
            place.pop(
                "_importance_score",
                None,
            )

        return {
            "options": options,
            "total": len(options),
            "offset": 0,
            "limit": len(options),
            "has_more": False,
        }

    def _get_category(
            self,
            properties,
    ):
        categories = [
            category.lower()
            for category in properties.get(
                "categories",
                [],
            )
        ]

        religious_keywords = (
            "church",
            "mosque",
            "cathedral",
            "monastery",
            "synagogue",
            "temple",
            "chapel",
        )

        if any(
                category.startswith("catering.restaurant")
                for category in categories
        ):
            return "Food"

        if any(
                category.startswith("commercial")
                for category in categories
        ):
            return "Shopping"

        if any(
                category.startswith("leisure.park")
                or category.startswith("beach")
                for category in categories
        ):
            return "Nature"

        if any(
                category.startswith("tourism.sights")
                or category.startswith("tourism.attraction")
                for category in categories
        ):
            return "Attractions"

        if any(
                category.startswith("entertainment.museum")
                or category.startswith("entertainment.culture")
                or category.startswith("entertainment.zoo")
                or category.startswith("entertainment.aquarium")
                or category.startswith("entertainment.theme_park")
                or category.startswith("entertainment.water_park")
                for category in categories
        ):
            return "Attractions"

        if any(
                keyword in category
                for category in categories
                for keyword in religious_keywords
        ):
            return "Attractions"

        if any(
                category.startswith("entertainment")
                for category in categories
        ):
            return "Entertainment"

        if any(
                category.startswith("tourism")
                for category in categories
        ):
            return "Attractions"

        return "Attractions"

    def _calculate_importance_score(
            self,
            properties,
    ):
        name = str(
            properties.get("name") or ""
        ).lower().strip()

        name_normalized = re.sub(
            r"[^\w]+",
            " ",
            name,
        ).strip()

        categories = [
            str(category).lower()
            for category in properties.get(
                "categories",
                [],
            )
        ]

        # ---------------------------------------------------------
        # Base score from Geoapify categories.
        #
        # Exact and specific categories have priority.
        # Generic tourism categories receive a lower score.
        # ---------------------------------------------------------

        score = 10

        category_scores = {
            # Major historical / architectural objects
            "tourism.sights.castle": 80,
            "tourism.sights.fortress": 80,
            "tourism.sights.fort": 80,
            "tourism.sights.palace": 80,
            "tourism.sights.manor": 80,

            # Archaeological / ancient sites
            "tourism.sights.archaeological_site": 75,
            "tourism.sights.archaeological": 75,
            "tourism.sights.ancient": 70,

            # Religious buildings
            "tourism.sights.cathedral": 75,
            "tourism.sights.basilica": 70,
            "tourism.sights.monastery": 65,
            "tourism.sights.church": 60,
            "tourism.sights.mosque": 60,
            "tourism.sights.synagogue": 60,
            "tourism.sights.temple": 60,
            "tourism.sights.chapel": 55,

            # Major urban / architectural objects
            "tourism.sights.square": 65,
            "tourism.sights.city_gate": 55,
            "tourism.sights.city_hall": 55,
            "tourism.sights.tower": 55,
            "tourism.sights.bridge": 55,
            "tourism.sights.lighthouse": 55,

            # Historical architecture
            "tourism.sights.historic_building": 45,
            "tourism.sights.historical_building": 45,

            # Generic tourist categories
            "tourism.sights": 25,
            "tourism.attraction": 25,
        }

        for category in categories:
            exact_score = category_scores.get(
                category
            )

            if exact_score is not None:
                score = max(
                    score,
                    exact_score,
                )
                continue

            # Geoapify may return more specific variants
            # that are not explicitly listed above.
            if category.endswith(".castle"):
                score = max(score, 80)

            elif category.endswith(".fortress"):
                score = max(score, 80)

            elif category.endswith(".fort"):
                score = max(score, 80)

            elif category.endswith(".palace"):
                score = max(score, 80)

            elif category.endswith(".manor"):
                score = max(score, 80)

            elif "archaeological" in category:
                score = max(score, 75)

            elif "cathedral" in category:
                score = max(score, 75)

            elif "basilica" in category:
                score = max(score, 70)

            elif "monastery" in category:
                score = max(score, 65)

            elif "church" in category:
                score = max(score, 60)

            elif "mosque" in category:
                score = max(score, 60)

            elif "synagogue" in category:
                score = max(score, 60)

            elif "temple" in category:
                score = max(score, 60)

            elif "chapel" in category:
                score = max(score, 55)

            elif "square" in category:
                score = max(score, 65)

            elif "tower" in category:
                score = max(score, 55)

            elif "bridge" in category:
                score = max(score, 55)

            elif "lighthouse" in category:
                score = max(score, 55)

            elif "historic_building" in category:
                score = max(score, 45)

            elif "historical_building" in category:
                score = max(score, 45)

            elif category.startswith("tourism.sights"):
                score = max(score, 25)

            elif category.startswith("tourism.attraction"):
                score = max(score, 25)

        # ---------------------------------------------------------
        # Name-based refinement.
        #
        # This is deliberately limited to generic object types.
        # It does NOT contain city-specific or language-specific
        # names.
        #
        # Name-based scoring is used only when Geoapify already
        # identifies the object as tourism / attraction / culture.
        # ---------------------------------------------------------

        is_tourism_object = any(
            category.startswith("tourism.sights")
            or category.startswith("tourism.attraction")
            or category.startswith("entertainment.museum")
            or category.startswith("entertainment.culture")
            for category in categories
        )

        if is_tourism_object:
            name_type_scores = {
                "palace": 55,
                "castle": 60,
                "fortress": 60,
                "citadel": 60,

                "cathedral": 55,
                "basilica": 55,
                "monastery": 50,
                "church": 45,
                "mosque": 45,
                "synagogue": 45,
                "temple": 45,
                "chapel": 40,

                "cistern": 50,
                "archaeological": 50,
                "ancient": 45,

                "square": 50,
                "tower": 45,
                "bridge": 45,
                "lighthouse": 45,

                "historic building": 40,
                "historical building": 40,

                "walls": 45,
                "ruins": 40,
                "remains": 40,
                "monument": 35,
                "memorial": 30,
                "viewpoint": 30,
            }

            for marker, name_score in name_type_scores.items():
                if re.search(
                        rf"\b{re.escape(marker)}\b",
                        name_normalized,
                ):
                    score = max(
                        score,
                        name_score,
                    )

        # ---------------------------------------------------------
        # Universal secondary / partial object penalties.
        #
        # Only the strongest applicable penalty is used.
        # ---------------------------------------------------------

        penalty = 0

        partial_markers = (
            "gate",
            "gateway",
            "entrance",
            "passage",
            "substructure",
            "foundation",
            "fragment",
            "part of",
            "section",
        )

        ruins_markers = (
            "ruins",
            "ruin",
            "remains",
            "fragment",
        )

        port_markers = (
            "harbour",
            "harbor",
            "port",
            "dock",
            "pier",
        )

        minor_object_markers = (
            "statue",
            "sculpture",
            "memorial",
            "monument",
        )

        if any(
                re.search(
                    rf"\b{re.escape(marker)}\b",
                    name_normalized,
                )
                for marker in partial_markers
        ):
            penalty = max(
                penalty,
                20,
            )

        if any(
                re.search(
                    rf"\b{re.escape(marker)}\b",
                    name_normalized,
                )
                for marker in ruins_markers
        ):
            penalty = max(
                penalty,
                15,
            )

        if any(
                re.search(
                    rf"\b{re.escape(marker)}\b",
                    name_normalized,
                )
                for marker in port_markers
        ):
            penalty = max(
                penalty,
                15,
            )

        if any(
                re.search(
                    rf"\b{re.escape(marker)}\b",
                    name_normalized,
                )
                for marker in minor_object_markers
        ):
            penalty = max(
                penalty,
                10,
            )

        score -= penalty

        # ---------------------------------------------------------
        # Keep score in a predictable range.
        # ---------------------------------------------------------

        return max(
            0,
            min(score, 100),
        )

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
        ) or ""

        importance_score = (
            self._calculate_importance_score(
                properties,
            )
        )

        print(
            "PLACE GEO:",
            properties.get("name"),
            "|",
            properties.get("categories", []),
            "| SCORE:",
            importance_score,
        )

        geo_categories = [
            category.lower()
            for category in properties.get(
                "categories",
                [],
            )
        ]

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
            "_importance_score": importance_score,
            "_geo_categories": geo_categories,
        }

    def _deduplicate_and_adjust_subfeatures(
            self,
            places,
    ):
        """
        Removes obvious duplicate places and lowers the score
        of obvious sub-features of a larger attraction.

        The logic is generic and does not depend on a specific
        city or language.
        """

        def normalize_name(name):
            name = str(name or "").strip()

            name = unicodedata.normalize(
                "NFKC",
                name,
            ).casefold()

            name = re.sub(
                r"[^\w]+",
                " ",
                name,
                flags=re.UNICODE,
            )

            return " ".join(
                name.split()
            )

        def get_coordinates(place):
            latitude = place.get("latitude")
            longitude = place.get("longitude")

            if latitude is None or longitude is None:
                return None

            try:
                return (
                    float(latitude),
                    float(longitude),
                )
            except (
                    TypeError,
                    ValueError,
            ):
                return None

        def distance_between(
                first_place,
                second_place,
        ):
            first_coordinates = (
                get_coordinates(first_place)
            )
            second_coordinates = (
                get_coordinates(second_place)
            )

            if (
                    not first_coordinates
                    or not second_coordinates
            ):
                return None

            return self._calculate_distance_km(
                first_coordinates[0],
                first_coordinates[1],
                second_coordinates[0],
                second_coordinates[1],
            )

        # ---------------------------------------------------------
        # Remove exact duplicates by external ID and identical
        # name + physical location.
        # ---------------------------------------------------------

        unique_places = []
        seen_external_ids = set()
        seen_name_locations = set()

        for place in places:
            external_id = place.get(
                "external_id"
            )

            if external_id:
                if external_id in seen_external_ids:
                    continue

                seen_external_ids.add(
                    external_id
                )

            normalized_name = normalize_name(
                place.get("name")
            )

            coordinates = get_coordinates(
                place
            )

            if normalized_name and coordinates:
                location_key = (
                    normalized_name,
                    round(
                        coordinates[0],
                        5,
                    ),
                    round(
                        coordinates[1],
                        5,
                    ),
                )

                if location_key in seen_name_locations:
                    continue

                seen_name_locations.add(
                    location_key
                )

            unique_places.append(
                place
            )

        places = unique_places

        # ---------------------------------------------------------
        # Sort first so that when two nearby objects have the same
        # name, the higher-ranked one is kept.
        # ---------------------------------------------------------

        places.sort(
            key=lambda place: place.get(
                "_importance_score",
                0,
            ),
            reverse=True,
        )

        # ---------------------------------------------------------
        # Remove nearby duplicate objects with the same name.
        #
        # If two objects have the same normalized name and are
        # within 300 meters, keep only the first one.
        #
        # This is generic and does not depend on a specific city
        # or language.
        # ---------------------------------------------------------

        deduplicated_places = []

        for place in places:
            place_name = normalize_name(
                place.get("name")
            )

            coordinates = get_coordinates(
                place
            )

            is_duplicate = False

            if place_name and coordinates:
                for existing_place in deduplicated_places:
                    existing_name = normalize_name(
                        existing_place.get("name")
                    )

                    if existing_name != place_name:
                        continue

                    existing_coordinates = get_coordinates(
                        existing_place
                    )

                    if not existing_coordinates:
                        continue

                    distance = self._calculate_distance_km(
                        coordinates[0],
                        coordinates[1],
                        existing_coordinates[0],
                        existing_coordinates[1],
                    )

                    if distance <= 0.3:
                        is_duplicate = True
                        break

            if is_duplicate:
                continue

            deduplicated_places.append(
                place
            )

        places = deduplicated_places

        # ---------------------------------------------------------
        # Lower score for obvious sub-features.
        #
        # Example:
        #
        #   Main Attraction       80
        #   Main Attraction X     60
        #
        # No city-specific or language-specific vocabulary
        # is required here.
        # ---------------------------------------------------------

        for place in places:
            place_name = normalize_name(
                place.get("name")
            )

            if not place_name:
                continue

            place_score = place.get(
                "_importance_score",
                0,
            )

            if place_score < 45:
                continue

            for parent in places:
                if parent is place:
                    continue

                parent_name = normalize_name(
                    parent.get("name")
                )

                if not parent_name:
                    continue

                parent_score = parent.get(
                    "_importance_score",
                    0,
                )

                if parent_score < place_score:
                    continue

                if (
                        parent_score == place_score
                        and len(parent_name) >= len(place_name)
                ):
                    continue

                # The possible child object must have the complete
                # parent name at the beginning of its own name.
                if not place_name.startswith(
                        parent_name + " "
                ):
                    continue

                distance = distance_between(
                    place,
                    parent,
                )

                # If coordinates are available, the objects must
                # be physically close to each other.
                if (
                        distance is not None
                        and distance > 1.0
                ):
                    continue

                place["_importance_score"] = max(
                    0,
                    place_score - 20,
                )

                break

        places.sort(
            key=lambda place: place.get(
                "_importance_score",
                0,
            ),
            reverse=True,
        )

        return places

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