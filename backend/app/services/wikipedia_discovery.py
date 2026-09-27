import requests
from math import atan2, cos, radians, sin, sqrt


API_URL = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

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
SPARQL_TIMEOUT = 30
EARTH_RADIUS_KM = 6371.0


WIKIDATA_CATEGORY_CLASSES = {
    "Attractions": [
        "Q570116",    # tourist attraction
        "Q4989906",   # monument
        "Q839954",    # historic site
        "Q811979",    # architectural structure
    ],
    "Nature": [
        "Q46169",     # national park
        "Q22698",     # park
        "Q167346",    # botanical garden
        "Q179049",    # nature reserve
        "Q4421",      # forest
        "Q40080",     # beach
    ],
    "Entertainment": [
        "Q194195",    # amusement park
        "Q24354",     # theatre
        "Q107898",    # opera house
        "Q1060829",   # concert hall
        "Q43501",     # zoo
        "Q16521",     # aquarium
        "Q41253",     # cinema
    ],
}


class WikipediaDiscoveryService:

    def get_city_categories(
        self,
        city: str,
        country: str,
        category: str | None = None,
    ) -> list[str]:

        if category == "Nature":
            return [
                f"Parks in {city}",
                f"Gardens in {city}",
                f"Forests in {city}",
            ]

        if category == "Entertainment":
            return [
                f"Theatres in {city}",
                f"Opera houses in {city}",
                f"Concert halls in {city}",
                f"Entertainment venues in {city}",
            ]

        return [
            f"Tourist attractions in {city}",
            f"Museums in {city}",
            f"Monuments and memorials in {city}",
            f"Historic sites in {city}",
            f"Historical buildings and structures in {city}",
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
                data.get("query", {}).get("categorymembers", [])
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

        for start in range(0, len(titles), PAGE_BATCH_SIZE):
            batch = titles[start:start + PAGE_BATCH_SIZE]

            params = {
                "action": "query",
                "titles": "|".join(batch),
                "prop": "coordinates|pageprops",
                "redirects": 1,
                "format": "json",
                "formatversion": 2,
                "maxlag": 5,
            }

            response = None

            for attempt in range(3):
                try:
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
                    break

                except requests.RequestException:
                    if attempt == 2:
                        response = None

            if response is None:
                continue

            data = response.json()

            pages = data.get("query", {}).get("pages", [])

            for page in pages:
                coordinates = page.get("coordinates", [])

                if not coordinates:
                    continue

                coordinate = coordinates[0]
                pageprops = page.get("pageprops") or {}

                page_data[page["title"]] = {
                    "coordinates": (
                        coordinate["lat"],
                        coordinate["lon"],
                    ),
                    "wikidata_id": pageprops.get("wikibase_item"),
                }

        return page_data

    def get_country_wikidata_id(
        self,
        country: str,
    ) -> str | None:

        params = {
            "action": "wbsearchentities",
            "search": country,
            "language": "en",
            "uselang": "en",
            "type": "item",
            "limit": 10,
            "format": "json",
        }

        response = requests.get(
            WIKIDATA_API_URL,
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("search", [])

        if not results:
            return None

        country_normalized = country.strip().casefold()

        for result in results:
            label = (
                result.get("label") or ""
            ).strip().casefold()

            if label == country_normalized:
                return result.get("id")

        return results[0].get("id")

    def discover_by_country(
        self,
        country: str,
        category: str,
    ) -> list[dict]:

        country_id = self.get_country_wikidata_id(country)

        if not country_id:
            return []

        class_ids = WIKIDATA_CATEGORY_CLASSES.get(
            category,
            [],
        )

        if not class_ids:
            return []

        candidates = []
        seen_ids = set()

        for class_id in class_ids:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": (
                    f"haswbstatement:P31={class_id} "
                    f"haswbstatement:P17={country_id}"
                ),
                "srlimit": 100,
                "format": "json",
            }

            try:
                response = requests.get(
                    WIKIDATA_API_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )

                response.raise_for_status()

            except requests.RequestException:
                continue

            data = response.json()

            for item in data.get("query", {}).get("search", []):
                title = item.get("title")

                if not title:
                    continue

                if not title.startswith("Q"):
                    continue

                if title in seen_ids:
                    continue

                seen_ids.add(title)

                candidates.append(
                    {
                        "wikidata_id": title,
                    }
                )

        if not candidates:
            return []

        wikidata_ids = [
            candidate["wikidata_id"]
            for candidate in candidates
        ]

        entities = {}

        for start in range(0, len(wikidata_ids), 50):
            batch = wikidata_ids[start:start + 50]

            params = {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "labels|claims|sitelinks",
                "languages": "en",
                "languagefallback": 1,
                "format": "json",
            }

            try:
                response = requests.get(
                    WIKIDATA_API_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )

                response.raise_for_status()

            except requests.RequestException:
                continue

            data = response.json()

            entities.update(
                data.get("entities", {})
            )

        results = []

        for wikidata_id, entity in entities.items():

            claims = entity.get("claims", {})

            coordinates_claims = claims.get(
                "P625",
                [],
            )

            if not coordinates_claims:
                continue

            coordinate_value = (
                coordinates_claims[0]
                .get("mainsnak", {})
                .get("datavalue", {})
                .get("value", {})
            )

            latitude = coordinate_value.get("latitude")
            longitude = coordinate_value.get("longitude")

            if latitude is None or longitude is None:
                continue

            labels = entity.get("labels", {})

            label_data = labels.get("en")

            if not label_data:
                continue

            title = label_data.get("value")

            if not title:
                continue

            sitelinks = entity.get("sitelinks", {})

            wikipedia_link = sitelinks.get("enwiki")

            if not wikipedia_link:
                continue

            results.append(
                {
                    "title": title,
                    "source_category": category,
                    "latitude": latitude,
                    "longitude": longitude,
                    "distance_km": None,
                    "wikidata_id": wikidata_id,
                    "wikidata_sitelinks": len(sitelinks),
                }
            )

        results.sort(
            key=lambda item: (
                -item["wikidata_sitelinks"],
                item["title"].casefold(),
            )
        )

        return results

    def get_city_wikidata_id(
        self,
        city: str,
    ) -> str | None:

        params = {
            "action": "wbsearchentities",
            "search": city,
            "language": "en",
            "uselang": "en",
            "type": "item",
            "limit": 10,
            "format": "json",
        }

        response = requests.get(
            WIKIDATA_API_URL,
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("search", [])

        if not results:
            return None

        city_normalized = city.strip().casefold()

        for result in results:
            label = (
                result.get("label") or ""
            ).strip().casefold()

            if label == city_normalized:
                return result.get("id")

        return results[0].get("id")

    def discover_city_attractions(
        self,
        city: str,
    ) -> list[dict]:

        city_id = self.get_city_wikidata_id(city)

        if not city_id:
            return []

        class_ids = WIKIDATA_CATEGORY_CLASSES.get(
            "Attractions",
            [],
        )

        if not class_ids:
            return []

        values = " ".join(
            f"wd:{class_id}"
            for class_id in class_ids
        )

        query = f"""
        SELECT DISTINCT ?item ?itemLabel ?coordinate ?article
        WHERE {{
            ?item wdt:P31/wdt:P279* ?class .
            VALUES ?class {{
                {values}
            }}

            ?item wdt:P625 ?coordinate .

            ?item wdt:P131* wd:{city_id} .

            ?article schema:about ?item ;
                     schema:isPartOf <https://en.wikipedia.org/> .

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "en" .
            }}
        }}
        LIMIT 500
        """

        try:
            response = requests.get(
                WIKIDATA_SPARQL_URL,
                params={
                    "query": query,
                    "format": "json",
                },
                headers={
                    **HEADERS,
                    "Accept": "application/sparql-results+json",
                },
                timeout=SPARQL_TIMEOUT,
            )

            response.raise_for_status()

        except requests.RequestException:
            return []

        data = response.json()

        results = []

        for result in (
            data.get("results", {})
            .get("bindings", [])
        ):
            item_uri = result.get(
                "item",
                {},
            ).get("value")

            label = result.get(
                "itemLabel",
                {},
            ).get("value")

            coordinate = result.get(
                "coordinate",
                {},
            ).get("value")

            if not item_uri or not label or not coordinate:
                continue

            wikidata_id = item_uri.rsplit(
                "/",
                1,
            )[-1]

            if not wikidata_id.startswith("Q"):
                continue

            try:
                latitude_text, longitude_text = (
                    coordinate
                    .replace("Point(", "")
                    .replace(")", "")
                    .split()
                )

                longitude = float(longitude_text)
                latitude = float(latitude_text)

            except (ValueError, AttributeError):
                continue

            results.append(
                {
                    "title": label,
                    "source_category": "Attractions",
                    "latitude": latitude,
                    "longitude": longitude,
                    "distance_km": None,
                    "wikidata_id": wikidata_id,
                    "wikidata_sitelinks": 0,
                }
            )

        return results

    def discover_all_categories(
        self,
        city: str,
        country: str,
        target_latitude: float,
        target_longitude: float,
        radius_km: float = 25,
    ) -> list[dict]:

        categories = (
            "Attractions",
            "Nature",
            "Entertainment",
        )

        pages = []

        for category in categories:
            wikipedia_categories = self.get_city_categories(
                city=city,
                country=country,
                category=category,
            )

            seen_titles = set()

            for category_name in wikipedia_categories:
                members = self.get_category_members(
                    category_name
                )

                for item in members:
                    title = item.get("title")

                    if not title:
                        continue

                    if title.startswith(
                        (
                            "List of ",
                            "Lists of ",
                        )
                    ):
                        continue

                    if title in seen_titles:
                        continue

                    seen_titles.add(title)

                    pages.append(
                        {
                            "title": title,
                            "source_category": category,
                        }
                    )

        if "Attractions" in categories:
            wikidata_attractions = (
                self.discover_city_attractions(city)
            )

            existing_wikidata_ids = set()

            for page in pages:
                wikidata_id = page.get(
                    "wikidata_id"
                )

                if wikidata_id:
                    existing_wikidata_ids.add(
                        wikidata_id
                    )

            for item in wikidata_attractions:
                if item["wikidata_id"] in existing_wikidata_ids:
                    continue

                pages.append(item)

                existing_wikidata_ids.add(
                    item["wikidata_id"]
                )

        titles = list(
            dict.fromkeys(
                page["title"]
                for page in pages
            )
        )

        if not titles:
            return []

        page_data = self.get_page_data(titles)

        candidates = []

        for page in pages:
            title = page["title"]
            data = page_data.get(title)

            if not data:
                continue

            coordinates = data.get("coordinates")

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

            candidates.append(
                {
                    "title": title,
                    "source_category": page["source_category"],
                    "latitude": latitude,
                    "longitude": longitude,
                    "distance_km": distance_km,
                    "wikidata_id": data.get("wikidata_id"),
                    "wikidata_sitelinks": 0,
                }
            )

        # Remove duplicates only inside the same category.
        # The same place is intentionally allowed in different categories.
        unique_candidates = []
        seen_candidates = set()
        fallback_seen = set()

        for candidate in candidates:
            category = candidate.get(
                "source_category"
            )

            wikidata_id = candidate.get(
                "wikidata_id"
            )

            if wikidata_id:
                key = (
                    category,
                    wikidata_id,
                )

                if key in seen_candidates:
                    continue

                seen_candidates.add(key)
                unique_candidates.append(candidate)
                continue

            fallback_key = (
                category,
                candidate.get("title"),
                candidate.get("latitude"),
                candidate.get("longitude"),
            )

            if fallback_key in fallback_seen:
                continue

            fallback_seen.add(fallback_key)
            unique_candidates.append(candidate)

        candidates = unique_candidates

        wikidata_ids = [
            candidate["wikidata_id"]
            for candidate in candidates
            if candidate.get("wikidata_id")
        ]

        significance = self.get_wikidata_significance(
            wikidata_ids
        )

        for candidate in candidates:
            wikidata_id = candidate.get(
                "wikidata_id"
            )

            candidate["wikidata_sitelinks"] = (
                significance.get(
                    wikidata_id,
                    0,
                )
            )

        candidates.sort(
            key=lambda item: (
                -item["wikidata_sitelinks"],
                item["distance_km"],
                item["title"].casefold(),
            )
        )

        return candidates

    def get_wikidata_significance(
        self,
        wikidata_ids: list[str],
    ) -> dict[str, int]:

        significance = {}

        unique_ids = list(
            dict.fromkeys(wikidata_ids)
        )

        for start in range(0, len(unique_ids), 50):

            batch = unique_ids[start:start + 50]

            params = {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "sitelinks",
                "format": "json",
            }

            response = requests.get(
                WIKIDATA_API_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()

            for wikidata_id in batch:

                entity = (
                    data.get("entities", {})
                    .get(wikidata_id, {})
                )

                sitelinks = entity.get(
                    "sitelinks",
                    {},
                )

                significance[wikidata_id] = len(
                    sitelinks
                )

        return significance

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

    def debug_country_discovery(
        self,
        country: str,
        category: str,
    ) -> dict:

        country_id = self.get_country_wikidata_id(
            country
        )

        if not country_id:
            return {
                "country": country,
                "country_id": None,
                "category": category,
                "message": "Country Wikidata ID not found",
            }

        class_ids = WIKIDATA_CATEGORY_CLASSES.get(
            category,
            [],
        )

        values = " ".join(
            f"wd:{class_id}"
            for class_id in class_ids
        )

        query = f"""
        SELECT DISTINCT ?item ?itemLabel ?coordinate
        WHERE {{
            VALUES ?class {{
                {values}
            }}

            ?item wdt:P31/wdt:P279* ?class .
            ?item wdt:P625 ?coordinate .
            ?item wdt:P17 wd:{country_id} .

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "en" .
            }}
        }}
        LIMIT 20
        """

        try:
            response = requests.get(
                WIKIDATA_SPARQL_URL,
                params={
                    "query": query,
                    "format": "json",
                },
                headers={
                    **HEADERS,
                    "Accept": "application/sparql-results+json",
                },
                timeout=SPARQL_TIMEOUT,
            )

            response.raise_for_status()

        except requests.RequestException as exc:

            return {
                "country": country,
                "country_id": country_id,
                "category": category,
                "error": str(exc),
            }

        data = response.json()

        results = []

        for result in (
            data.get("results", {})
            .get("bindings", [])
        ):

            results.append(
                {
                    "id": result.get(
                        "item",
                        {},
                    ).get("value"),
                    "label": result.get(
                        "itemLabel",
                        {},
                    ).get("value"),
                    "coordinate": result.get(
                        "coordinate",
                        {},
                    ).get("value"),
                }
            )

        return {
            "country": country,
            "country_id": country_id,
            "category": category,
            "count": len(results),
            "results": results,
        }