import requests
from math import atan2, cos, radians, sin, sqrt


API_URL = "https://en.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "TravelAIPlanner/0.1 "
        "(https://github.com/Madwicked/travel-ai-planner; "
        "Python requests)"
    )
}

CATEGORY_PAGE_LIMIT = 100
PAGE_BATCH_SIZE = 5
REQUEST_TIMEOUT = 20
EARTH_RADIUS_KM = 6371.0


class WikipediaDiscoveryService:
    def get_city_categories(
        self,
        city: str,
        country: str,
    ) -> list[str]:
        return [
            f"Tourist attractions in {city}",
            f"Museums in {city}",
            f"Monuments and memorials in {city}",
            f"Landmarks in {country}",
        ]

    def get_category_members(
        self,
        category: str,
    ) -> list[dict]:
        members = []
        continue_token = None

        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": CATEGORY_PAGE_LIMIT,
                "cmtype": "page",
                "format": "json",
                "formatversion": 2,
            }

            if continue_token:
                params["cmcontinue"] = continue_token

            response = requests.get(
                API_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()

            members.extend(
                data.get(
                    "query",
                    {},
                ).get(
                    "categorymembers",
                    [],
                )
            )

            if "continue" not in data:
                break

            continue_token = data["continue"]["cmcontinue"]

        return members

    def get_page_data(
        self,
        titles: list[str],
    ) -> dict[str, dict]:
        page_data = {}

        for start in range(
            0,
            len(titles),
            PAGE_BATCH_SIZE,
        ):
            batch = titles[
                start:start + PAGE_BATCH_SIZE
            ]

            params = {
                "action": "query",
                "titles": "|".join(batch),
                "prop": "coordinates|pageprops",
                "redirects": 1,
                "format": "json",
                "formatversion": 2,
                "maxlag": 5,
            }

            response = requests.post(
                API_URL,
                data=params,
                headers={
                    **HEADERS,
                    "Promise-Non-Write-API-Action": "true",
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()

            pages = (
                data.get("query", {})
                .get("pages", [])
            )

            for page in pages:
                coordinates = page.get(
                    "coordinates",
                    [],
                )

                if not coordinates:
                    continue

                coordinate = coordinates[0]

                pageprops = (
                    page.get("pageprops")
                    or {}
                )

                page_data[page["title"]] = {
                    "coordinates": (
                        coordinate["lat"],
                        coordinate["lon"],
                    ),
                    "wikidata_id": pageprops.get(
                        "wikibase_item"
                    ),
                }

        return page_data

    def discover(
        self,
        city: str,
        country: str,
        target_latitude: float,
        target_longitude: float,
        radius_km: float = 25,
    ) -> list[dict]:
        categories = self.get_city_categories(
            city,
            country,
        )

        unique_pages = {}

        for category in categories:
            members = self.get_category_members(
                category
            )

            for item in members:
                title = item.get("title")

                if not title:
                    continue

                if title.startswith(
                    ("List of ", "Lists of ")
                ):
                    continue

                unique_pages[title] = {
                    "title": title,
                    "source_category": category,
                }

        titles = list(unique_pages)

        page_data = self.get_page_data(
            titles
        )

        candidates = []

        for title, item in unique_pages.items():
            data = page_data.get(title)

            if not data:
                continue

            coordinates = data.get(
                "coordinates"
            )

            if not coordinates:
                continue

            latitude, longitude = coordinates

            distance_km = self.calculate_distance_km(
                latitude=latitude,
                longitude=longitude,
                target_latitude=target_latitude,
                target_longitude=target_longitude,
            )

            if distance_km > radius_km:
                continue

            candidates.append({
                "title": title,
                "source_category": item[
                    "source_category"
                ],
                "latitude": latitude,
                "longitude": longitude,
                "distance_km": distance_km,
                "wikidata_id": data.get(
                    "wikidata_id"
                ),
            })

        candidates.sort(
            key=lambda item: item["distance_km"]
        )

        return candidates

    def calculate_distance_km(
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
