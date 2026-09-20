
import os

import requests


BASE_URL = "https://api.geoapify.com/v2/place-details"
REQUEST_TIMEOUT = 10
DEFAULT_ENRICHMENT_LIMIT = 20


class GeoapifyEnrichmentService:
    """
    Enriches Wikipedia places with optional Geoapify data.

    Wikipedia is the source of truth for place identity.
    Geoapify is used only for practical enrichment,
    such as opening hours.

    Geoapify data is accepted only when its Wikidata ID
    matches the Wikipedia Wikidata ID.
    """

    def __init__(self):
        self.api_key = os.getenv("GEOAPIFY_API_KEY")

    def enrich(
        self,
        places: list[dict],
        limit: int = DEFAULT_ENRICHMENT_LIMIT,
    ) -> list[dict]:
        if not self.api_key:
            return places

        enriched = [
            self._enrich_place(place)
            for place in places[:limit]
        ]

        return enriched + places[limit:]

    def _enrich_place(
        self,
        place: dict,
    ) -> dict:
        latitude = place.get("latitude")
        longitude = place.get("longitude")

        if latitude is None or longitude is None:
            return place

        properties = self._request_details(
            latitude=latitude,
            longitude=longitude,
        )

        if not properties:
            return place

        if not self._is_same_place(
            wikipedia_wikidata_id=place.get("wikidata_id"),
            properties=properties,
        ):
            return place

        opening_hours = properties.get(
            "opening_hours"
        )

        if not opening_hours:
            return place

        enriched = dict(place)
        enriched["opening_hours"] = opening_hours

        return enriched

    def _request_details(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:
        params = {
            "lat": latitude,
            "lon": longitude,
            "features": "details",
            "lang": "en",
            "apiKey": self.api_key,
        }

        try:
            response = requests.get(
                BASE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            features = response.json().get(
                "features",
                [],
            )

            if not features:
                return {}

            return features[0].get(
                "properties"
            ) or {}

        except requests.RequestException:
            return {}

    def _is_same_place(
        self,
        wikipedia_wikidata_id: str | None,
        properties: dict,
    ) -> bool:
        if not wikipedia_wikidata_id:
            return False

        wiki_and_media = (
            properties.get("wiki_and_media")
            or {}
        )

        geoapify_wikidata_id = (
            wiki_and_media.get("wikidata")
        )

        return (
            bool(geoapify_wikidata_id)
            and wikipedia_wikidata_id
            == geoapify_wikidata_id
        )
