import re
import unicodedata
from difflib import SequenceMatcher
from math import radians, sin, cos, sqrt, atan2


class PlaceMatcherService:
    def match(
            self,
            wikipedia_candidates: list[dict],
            geoapify_places: list[dict],
            max_distance_km: float = 0.3,
    ) -> list[dict]:
        matched = []

        for wiki in wikipedia_candidates:
            best_match = None
            best_score = 0.0
            best_distance = None

            wiki_name = self._normalize_name(wiki["title"])

            for place in geoapify_places:
                latitude = place.get("latitude")
                longitude = place.get("longitude")
                place_name = place.get("name")

                if (
                        latitude is None
                        or longitude is None
                        or not place_name
                ):
                    continue

                distance_km = self.calculate_distance_km(
                    wiki["latitude"],
                    wiki["longitude"],
                    latitude,
                    longitude,
                )

                if distance_km > max_distance_km:
                    continue

                place_name_normalized = self._normalize_name(place_name)

                name_score = self._calculate_name_similarity(
                    wiki_name,
                    place_name_normalized,
                )

                # Do not match unrelated nearby objects.
                if name_score < 0.45:
                    wiki_tokens = {
                        token
                        for token in wiki_name.split()
                        if len(token) >= 6
                    }

                    place_tokens = {
                        token
                        for token in place_name_normalized.split()
                        if len(token) >= 6
                    }

                    common_tokens = wiki_tokens & place_tokens

                    if not common_tokens or distance_km > 0.1:
                        continue

                # Name similarity is the main signal.
                # Distance is only used to choose between
                # otherwise valid candidates.
                distance_score = max(
                    0.0,
                    1.0 - (distance_km / max_distance_km),
                )

                total_score = (
                        name_score * 0.85
                        + distance_score * 0.15
                )

                if total_score > best_score:
                    best_score = total_score
                    best_distance = distance_km
                    best_match = place

            if best_match:
                matched.append({
                    "wikipedia_title": wiki["title"],
                    "wikipedia_category": wiki["source_category"],
                    "latitude": wiki["latitude"],
                    "longitude": wiki["longitude"],
                    "distance_km": wiki["distance_km"],
                    "geoapify_place": best_match,
                    "match_distance_km": best_distance,
                    "match_score": best_score,
                })

        return matched

    def _normalize_name(self, name: str) -> str:
        """
        Normalize names for generic multilingual comparison.

        Removes accents, punctuation and duplicate whitespace,
        while keeping the actual words.
        """
        value = unicodedata.normalize("NFKD", name)
        value = "".join(
            char for char in value
            if not unicodedata.combining(char)
        )

        value = value.casefold()
        value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
        value = re.sub(r"\s+", " ", value).strip()

        return value

    def _calculate_name_similarity(
            self,
            first: str,
            second: str,
    ) -> float:
        if not first or not second:
            return 0.0

        if first == second:
            return 1.0

        if first in second or second in first:
            return 0.9

        first_tokens = {
            token
            for token in first.split()
            if len(token) >= 4
        }

        second_tokens = {
            token
            for token in second.split()
            if len(token) >= 4
        }

        if not first_tokens or not second_tokens:
            return 0.0

        common_tokens = first_tokens & second_tokens

        if not common_tokens:
            return 0.0

        union = first_tokens | second_tokens
        token_similarity = len(common_tokens) / len(union)

        return token_similarity

    def calculate_distance_km(
        self,
        latitude: float,
        longitude: float,
        target_latitude: float,
        target_longitude: float,
    ) -> float:
        earth_radius_km = 6371.0

        lat1 = radians(latitude)
        lon1 = radians(longitude)
        lat2 = radians(target_latitude)
        lon2 = radians(target_longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return earth_radius_km * c