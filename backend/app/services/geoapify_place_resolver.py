
class GeoapifyPlaceResolver:
    """
    Converts discovered place data into the internal Place format.
    """

    def resolve(
        self,
        places: list[dict],
    ) -> list[dict]:
        resolved = []

        for place in places:
            latitude = place.get("latitude")
            longitude = place.get("longitude")
            name = place.get("name")

            if (
                not name
                or latitude is None
                or longitude is None
            ):
                continue

            resolved.append(
                {
                    "external_id": place.get(
                        "external_id"
                    ),
                    "source": "geoapify",
                    "name": name,
                    "city": place.get("city"),
                    "country": place.get("country"),
                    "category": place.get("category"),
                    "address": place.get("address"),
                    "latitude": latitude,
                    "longitude": longitude,
                    "distance_km": place.get(
                        "distance_km"
                    ),
                    "wikidata_id": place.get(
                        "wikidata_id"
                    ),
                    "rating": place.get("rating"),
                    "opening_hours": place.get(
                        "opening_hours"
                    ),
                    "opening_time": place.get(
                        "opening_time"
                    ),
                    "closing_time": place.get(
                        "closing_time"
                    ),
                    "visit_duration": place.get(
                        "visit_duration"
                    ),
                }
            )

        return resolved
