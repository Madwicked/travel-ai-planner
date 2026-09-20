import re
import unicodedata


SIGNIFICANT_CATEGORIES = {
     "attractions",
     "entertainment",
}


class WikipediaPlaceMatcher:
    """
    Matches significant Wikipedia places with Geoapify places.

    Wikipedia is used only to identify significant places.
    Geoapify remains the source of the final place data.
    """

    def prioritize(
        self,
        geoapify_places: list[dict],
        wikipedia_candidates: list[dict],
    ) -> list[dict]:
        if not geoapify_places:
            return []

        if not wikipedia_candidates:
            return geoapify_places

        matched = []
        matched_geoapify_ids = set()

        for wikipedia_candidate in wikipedia_candidates:
            geoapify_place = self._find_match(
                wikipedia_candidate,
                geoapify_places,
                matched_geoapify_ids,
            )

            if geoapify_place is None:
                continue

            external_id = geoapify_place.get(
                "external_id"
            )

            if external_id:
                matched_geoapify_ids.add(
                    external_id
                )

            matched.append(
                geoapify_place
            )

        unmatched = [
            place
            for place in geoapify_places
            if place.get("external_id")
            not in matched_geoapify_ids
        ]

        return matched + unmatched

    def _find_match(
        self,
        wikipedia_candidate: dict,
        geoapify_places: list[dict],
        matched_geoapify_ids: set,
    ) -> dict | None:
        wikipedia_name = self._normalize_name(
            wikipedia_candidate.get("title")
        )

        if not wikipedia_name:
            return None

        candidates = []

        for place in geoapify_places:
            external_id = place.get(
                "external_id"
            )

            if (
                external_id
                and external_id in matched_geoapify_ids
            ):
                continue

            category = place.get(
                "category"
            )

            if category not in SIGNIFICANT_CATEGORIES:
                continue

            place_name = self._normalize_name(
                place.get("name")
            )

            if not place_name:
                continue

            candidates.append(
                {
                    "place": place,
                    "name": place_name,
                }
            )

        exact_matches = [
            candidate
            for candidate in candidates
            if candidate["name"] == wikipedia_name
        ]

        if exact_matches:
            return self._closest_match(
                wikipedia_candidate,
                exact_matches,
            )

        partial_matches = [
            candidate
            for candidate in candidates
            if (
                wikipedia_name in candidate["name"]
                or candidate["name"] in wikipedia_name
            )
        ]

        if partial_matches:
            return self._closest_match(
                wikipedia_candidate,
                partial_matches,
            )

        return None

    def _closest_match(
        self,
        wikipedia_candidate: dict,
        candidates: list[dict],
    ) -> dict | None:
        latitude = wikipedia_candidate.get(
            "latitude"
        )
        longitude = wikipedia_candidate.get(
            "longitude"
        )

        if latitude is None or longitude is None:
            return candidates[0]["place"]

        closest_place = None
        closest_distance = None

        for candidate in candidates:
            place = candidate["place"]

            place_latitude = place.get(
                "latitude"
            )
            place_longitude = place.get(
                "longitude"
            )

            if (
                place_latitude is None
                or place_longitude is None
            ):
                continue

            distance = self._calculate_distance_km(
                latitude,
                longitude,
                place_latitude,
                place_longitude,
            )

            if distance > 0.5:
                continue

            if (
                closest_distance is None
                or distance < closest_distance
            ):
                closest_distance = distance
                closest_place = place

        return closest_place

    def _normalize_name(
        self,
        name: str | None,
    ) -> str:
        if not name:
            return ""

        value = unicodedata.normalize(
            "NFKC",
            name,
        ).casefold()

        value = re.sub(
            r"[^\w\s]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    def _calculate_distance_km(
        self,
        latitude: float,
        longitude: float,
        target_latitude: float,
        target_longitude: float,
    ) -> float:
        from math import (
            atan2,
            cos,
            radians,
            sin,
            sqrt,
        )

        earth_radius_km = 6371.0

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

        return earth_radius_km * c