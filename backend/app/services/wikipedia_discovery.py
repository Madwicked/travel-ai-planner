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
CATEGORY_MEMBER_LIMIT = 200
PAGE_BATCH_SIZE = 50
REQUEST_TIMEOUT = 20
SPARQL_TIMEOUT = 20
EARTH_RADIUS_KM = 6371.0

# NEARBY_SPARQL_RADIUS_KM and discover_all_categories' radius_km are two
# intentionally different radii, not a duplicated/conflicting setting:
#
# - NEARBY_SPARQL_RADIUS_KM (10 km) bounds the SPARQL
#   wikibase:around service in discover_city_attractions(). It is a
#   narrow, city-core "catch-all" net: anything with enough sitelinks
#   near the city center, regardless of whether it ended up in any
#   Wikipedia category.
# - radius_km (default 25 km, a discover_all_categories() parameter)
#   bounds the FINAL candidate pool, after Wikipedia category discovery
#   has already supplied most candidates (which can be anywhere in the
#   city, not just within 10 km of the given point).
#
# This means nearby-Wikidata-sourced candidates can only come from
# within 10 km, while Wikipedia-category-sourced candidates can come
# from anywhere within 25 km. That asymmetry is intentional: nearby
# discovery is a supplementary safety net near a specific point (e.g.
# a hotel), not the primary discovery mechanism, so it does not need to
# match the wider final radius.
NEARBY_SPARQL_RADIUS_KM = 10
NEARBY_MIN_SITELINKS = 15
NEARBY_RESULT_LIMIT = 120

LIST_PAGE_LINK_LIMIT = 200

WIKIDATA_CLASS_MAX_DEPTH = 2


# ---------------------------------------------------------------------------
# Semantic exclusions.
#
# These are not ranking rules.
# They prevent generic/non-visitable Wikidata entities from becoming Places.
# ---------------------------------------------------------------------------

NON_PLACE_INSTANCE_IDS = {
    "Q5",          # human
    "Q515",        # city
    "Q1549591",    # big city
    "Q3957",       # town
    "Q486972",     # human settlement
    "Q6256",       # country
    "Q3624078",    # sovereign state
    "Q34770",      # language
    "Q33742",      # natural language
    "Q11424",      # film
    "Q5398426",    # television series
    "Q1656682",    # event
    "Q1190554",    # occurrence
    "Q431289",     # brand
}


# ---------------------------------------------------------------------------
# Explicit non-place / low-value physical entity classes.
#
# These are deliberately small semantic exclusions.
# They are NOT a ranking table.
#
# They prevent broad Q811979 architectural-structure inheritance from
# turning hotels, restaurants, schools, institutes, companies, etc. into
# tourist Places.
# ---------------------------------------------------------------------------

NON_VISITABLE_PHYSICAL_CLASSES = {
    "Q27686",      # hotel
    "Q11707",      # restaurant
    "Q30022",      # cafe
    "Q3914",       # school
    "Q3918",       # university
    "Q55488",      # railway station
    "Q182060",     # office
    "Q31855",      # research institute
    "Q2385804",    # educational institution
    # "Q4830453",    # business
}


# ---------------------------------------------------------------------------
# Wikipedia/Wikidata discovery classes.
#
# These are used for country-level Wikidata discovery.
# They do not assign ranking scores.
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Semantic roots used for classification.
#
# The important distinction:
#
# Q618123 (natural geographic feature) is intentionally NOT used as a
# generic "nature" signal. It is too broad and can be inherited by objects
# that are not useful natural Places.
# ---------------------------------------------------------------------------

WIKIDATA_CLASS_ROOTS = {
    "settlement": "Q486972",
    "human": "Q5",
    "organization": "Q43229",
    "event": "Q1656682",
    "battle": "Q178561",
    "administrative_entity": "Q56061",
    "tourist_attraction": "Q570116",

    # NOTE: "architectural_structure" (Q811979) is deliberately NOT
    # defined here. It is still used in WIKIDATA_CATEGORY_CLASSES below
    # to cast a wide net during country-level Discovery, but it must
    # never be used as a standalone positive Classification signal —
    # it is too broad (hotels, offices, university buildings all
    # inherit from it) and that is what previously let organizations
    # and generic buildings pass as Places. See
    # _classify_wikidata_entity for the rationale.
}


# ---------------------------------------------------------------------------
# Positive physical/touristic semantic classes.
#
# These are classification signals, not ranking scores.
# ---------------------------------------------------------------------------

PHYSICAL_PLACE_CLASSES = {
    # Historical / cultural
    "Q57831",      # castle
    "Q57821",      # fortress
    "Q16560",      # palace
    "Q34627",      # synagogue
    "Q16970",      # church
    "Q1088552",    # church (specific Wikidata class)
    "Q2977",       # cathedral
    "Q32815",      # mosque
    "Q44613",      # monastery
    "Q1370598",    # basilica
    "Q108325",     # chapel
    "Q44539",      # temple
    "Q4989906",    # monument
    "Q839954",    # historic site

    # Cultural / entertainment
    "Q33506",      # museum
    "Q24354",      # theatre
    "Q107898",    # opera house
    "Q1060829",   # concert hall
    "Q194195",    # amusement park
    "Q43501",      # zoo
    "Q16521",     # aquarium
    "Q41253",     # cinema

    # Other physical landmarks
    # "Q12280",      # bridge
    # "Q1154710",    # stadium
}


# ---------------------------------------------------------------------------
# Explicit nature classes.
#
# This intentionally avoids using Q618123 as a broad inherited nature root.
# ---------------------------------------------------------------------------

NATURE_CLASSES = {
    "Q46169",      # national park
    "Q22698",      # park
    "Q167346",     # botanical garden
    "Q179049",     # nature reserve
    "Q4421",       # forest
    "Q40080",      # beach
    "Q8502",       # mountain
    "Q23397",      # lake
    "Q4022",       # river
    "Q23442",      # island
    "Q34038",      # waterfall
}

WIKIDATA_CHARACTERISTICS = {
    "tourist_attraction": "Q570116",
}


class WikipediaDiscoveryService:

    # -----------------------------------------------------------------------
    # Wikipedia discovery
    # -----------------------------------------------------------------------

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

            # Religious / cultural discovery.
            #
            # These are intentionally city-independent templates.
            # They solve the discovery gap without loosening Wikidata
            # classification.
            f"Churches in {city}",
            f"Cathedrals in {city}",
            f"Basilicas in {city}",
            f"Religious buildings and structures in {city}",
            f"Synagogues in {city}",
            f"Mosques in {city}",
            f"Monasteries in {city}",
            f"Temples in {city}",
        ]

    def _response_json(
        self,
        response: requests.Response,
    ) -> dict | None:

        try:
            data = response.json()
        except ValueError:
            return None

        if not isinstance(data, dict):
            return None

        return data

    def _is_list_page(
        self,
        title: str,
    ) -> bool:

        return title.startswith(
            (
                "List of ",
                "Lists of ",
            )
        )

    def get_category_members(
        self,
        category: str,
        max_members: int = CATEGORY_MEMBER_LIMIT,
    ) -> list[dict]:

        members = []
        continue_token = None

        while True:

            remaining = max_members - len(members)

            if remaining <= 0:
                break

            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": min(
                    CATEGORY_PAGE_LIMIT,
                    remaining,
                ),
                "cmtype": "page",
                "format": "json",
                "formatversion": 2,
            }

            if continue_token:
                params["cmcontinue"] = continue_token

            try:
                response = requests.get(
                    API_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )

                response.raise_for_status()

            except requests.RequestException:
                break

            data = self._response_json(response)

            if not data:
                break

            members.extend(
                data.get("query", {}).get(
                    "categorymembers",
                    [],
                )
            )

            if len(members) >= max_members:
                break

            if "continue" not in data:
                break

            continue_token = (
                data.get("continue", {})
                .get("cmcontinue")
            )

            if not continue_token:
                break

        return members[:max_members]

    def get_page_links(
        self,
        title: str,
        max_links: int = LIST_PAGE_LINK_LIMIT,
    ) -> list[str]:

        titles = []
        continue_token = None

        while True:

            remaining = max_links - len(titles)

            if remaining <= 0:
                break

            params = {
                "action": "query",
                "titles": title,
                "generator": "links",
                "gplnamespace": 0,
                "gpllimit": min(
                    100,
                    remaining,
                ),
                "format": "json",
                "formatversion": 2,
            }

            if continue_token:
                params["gplcontinue"] = continue_token

            try:
                response = requests.get(
                    API_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )

                response.raise_for_status()

            except requests.RequestException:
                break

            data = self._response_json(response)

            if not data:
                break

            pages = (
                data.get("query", {})
                .get("pages", [])
            )

            for page in pages:

                page_title = page.get("title")

                if not page_title:
                    continue

                if self._is_list_page(page_title):
                    continue

                titles.append(page_title)

                if len(titles) >= max_links:
                    break

            if len(titles) >= max_links:
                break

            if "continue" not in data:
                break

            continue_token = (
                data.get("continue", {})
                .get("gplcontinue")
            )

            if not continue_token:
                break

        return titles[:max_links]

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

            data = self._response_json(response)

            if not data:
                continue

            pages = (
                data.get("query", {})
                .get("pages", [])
            )

            for page in pages:

                page_title = page.get("title")

                if not page_title:
                    continue

                pageprops = (
                    page.get("pageprops")
                    or {}
                )

                wikidata_id = pageprops.get(
                    "wikibase_item"
                )

                # A Wikipedia article can have a Wikidata ID without
                # having {{coord}}-tagged coordinates of its own (common
                # for some religious/cultural buildings). Previously this
                # branch was skipped entirely, silently dropping the
                # wikidata_id along with the missing coordinates. The
                # candidate pipeline already knows how to fall back to
                # coordinates obtained directly from Wikidata discovery
                # (see discover_all_categories, step 4), so here we only
                # need to stop throwing away the wikidata_id.
                coordinates_list = page.get(
                    "coordinates",
                    [],
                )

                coordinates = None

                if coordinates_list:

                    coordinate = coordinates_list[0]

                    coordinates = (
                        coordinate.get("lat"),
                        coordinate.get("lon"),
                    )

                if not coordinates and not wikidata_id:
                    continue

                page_data[page_title] = {
                    "coordinates": coordinates,
                    "wikidata_id": wikidata_id,
                }

        return page_data

    # -----------------------------------------------------------------------
    # Wikidata lookup helpers
    # -----------------------------------------------------------------------

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

        try:
            response = requests.get(
                WIKIDATA_API_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

        except requests.RequestException:
            return None

        data = self._response_json(response)

        if not data:
            return None

        results = data.get("search", [])

        if not results:
            return None

        country_normalized = (
            country.strip().casefold()
        )

        for result in results:

            label = (
                result.get("label") or ""
            ).strip().casefold()

            if label == country_normalized:
                return result.get("id")

        return results[0].get("id")

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

        try:
            response = requests.get(
                WIKIDATA_API_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

        except requests.RequestException:
            return None

        data = self._response_json(response)

        if not data:
            return None

        results = data.get("search", [])

        if not results:
            return None

        city_normalized = (
            city.strip().casefold()
        )

        for result in results:

            label = (
                result.get("label") or ""
            ).strip().casefold()

            if label == city_normalized:
                return result.get("id")

        return results[0].get("id")

    def _parse_wkt_point(
        self,
        coordinate: str,
    ) -> tuple[float, float] | None:

        try:

            longitude_text, latitude_text = (
                coordinate
                .replace("Point(", "")
                .replace(")", "")
                .split()
            )

            return (
                float(latitude_text),
                float(longitude_text),
            )

        except (
            ValueError,
            AttributeError,
        ):
            return None

    def _entity_instance_ids(
        self,
        entity: dict,
    ) -> set[str]:

        instance_ids = set()

        for claim in entity.get(
            "claims",
            {},
        ).get("P31", []):

            instance_id = (
                claim
                .get("mainsnak", {})
                .get("datavalue", {})
                .get("value", {})
                .get("id")
            )

            if instance_id:
                instance_ids.add(instance_id)

        return instance_ids

    def _entity_characteristic_ids(
            self,
            entity: dict,
    ) -> set[str]:

        claims = entity.get(
            "claims",
            {},
        )

        characteristic_claims = claims.get(
            "P1552",
            [],
        )

        result = set()

        for claim in characteristic_claims:
            mainsnak = claim.get(
                "mainsnak",
                {},
            )

            datavalue = mainsnak.get(
                "datavalue",
                {},
            )

            value = datavalue.get(
                "value"
            )

            if not isinstance(value, dict):
                continue

            wikidata_id = value.get(
                "id"
            )

            if wikidata_id:
                result.add(wikidata_id)

        return result

    def _hydrate_wikidata_entities(
        self,
        wikidata_ids: list[str],
    ) -> dict[str, dict]:

        entities = {}

        unique_ids = list(
            dict.fromkeys(wikidata_ids)
        )

        for start in range(
            0,
            len(unique_ids),
            50,
        ):

            batch = unique_ids[
                start:start + 50
            ]

            if not batch:
                continue

            params = {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "labels|claims|sitelinks",
                "languages": "en",
                "languagefallback": 1,
                "format": "json",
            }

            # A single transient RequestException used to drop this
            # entire batch of up to 50 Wikidata entities silently and
            # permanently, with no retry — unlike get_page_data() above,
            # which already retries. This function is called far more
            # often and over far more batches for large, candidate-heavy
            # cities (many Wikipedia categories + nearby-Wikidata
            # candidates), so a transient failure here had a
            # disproportionate chance of silently removing an otherwise
            # perfectly valid candidate (its hierarchy would resolve to
            # an empty set, and it would fail Classification not because
            # it is a bad candidate, but because its own data never
            # arrived). Retrying mirrors the existing get_page_data()
            # pattern already used in this file.
            response = None

            for attempt in range(3):

                try:
                    response = requests.get(
                        WIKIDATA_API_URL,
                        params=params,
                        headers=HEADERS,
                        timeout=REQUEST_TIMEOUT,
                    )

                    response.raise_for_status()
                    break

                except requests.RequestException:

                    if attempt == 2:
                        response = None

            if response is None:
                continue

            data = self._response_json(response)

            if not data:
                continue

            entities.update(
                data.get("entities", {})
            )

        return entities

    # -----------------------------------------------------------------------
    # Country-level Wikidata discovery
    # -----------------------------------------------------------------------

    def discover_by_country(
        self,
        country: str,
        category: str,
    ) -> list[dict]:

        country_id = self.get_country_wikidata_id(
            country
        )

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

            data = self._response_json(response)

            if not data:
                continue

            for item in (
                data.get("query", {})
                .get("search", [])
            ):

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

        entities = self._hydrate_wikidata_entities(
            wikidata_ids
        )

        results = []

        for wikidata_id, entity in entities.items():

            claims = entity.get(
                "claims",
                {},
            )

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

            latitude = coordinate_value.get(
                "latitude"
            )
            longitude = coordinate_value.get(
                "longitude"
            )

            if latitude is None or longitude is None:
                continue

            labels = entity.get(
                "labels",
                {},
            )

            label_data = labels.get("en")

            if not label_data:
                continue

            title = label_data.get("value")

            if not title:
                continue

            sitelinks = entity.get(
                "sitelinks",
                {},
            )

            wikipedia_link = sitelinks.get(
                "enwiki"
            )

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
                    "wikidata_sitelinks": len(
                        sitelinks
                    ),
                }
            )

        results.sort(
            key=lambda item: (
                -item["wikidata_sitelinks"],
                item["title"].casefold(),
            )
        )

        return results

    # -----------------------------------------------------------------------
    # Wikidata hierarchy
    # -----------------------------------------------------------------------

    def _get_wikidata_class_hierarchy(
        self,
        wikidata_ids: list[str],
        max_depth: int = WIKIDATA_CLASS_MAX_DEPTH,
        entities: dict[str, dict] | None = None,
    ) -> dict[str, set[str]]:

        unique_ids = list(
            dict.fromkeys(wikidata_ids)
        )

        if not unique_ids:
            return {}

        # Entities for the base P31 classes can be supplied by the caller
        # (e.g. already hydrated during the main discovery pipeline) to
        # avoid re-fetching the same Wikidata items twice.
        if entities is None:
            entities = self._hydrate_wikidata_entities(
                unique_ids
            )
        else:
            missing_ids = [
                wikidata_id
                for wikidata_id in unique_ids
                if wikidata_id not in entities
            ]

            if missing_ids:
                entities = {
                    **entities,
                    **self._hydrate_wikidata_entities(
                        missing_ids
                    ),
                }

        hierarchy = {}
        all_p31_ids = set()

        # P31 of original entities.
        for wikidata_id in unique_ids:

            entity = entities.get(
                wikidata_id,
                {},
            )

            p31_ids = self._entity_instance_ids(
                entity
            )

            hierarchy[wikidata_id] = set(
                p31_ids
            )

            all_p31_ids.update(
                p31_ids
            )

        current_ids = set(all_p31_ids)
        visited_ids = set()

        # Follow P279 upward.
        for _ in range(
            1,
            max_depth + 1,
        ):

            current_ids -= visited_ids

            if not current_ids:
                break

            class_entities = (
                self._hydrate_wikidata_entities(
                    list(current_ids)
                )
            )

            next_ids = set()

            for class_id in current_ids:

                visited_ids.add(class_id)

                entity = class_entities.get(
                    class_id,
                    {},
                )

                parent_ids = set()

                for claim in (
                    entity.get("claims", {})
                    .get("P279", [])
                ):

                    value = (
                        claim
                        .get("mainsnak", {})
                        .get("datavalue", {})
                        .get("value", {})
                    )

                    if not isinstance(value, dict):
                        continue

                    parent_id = value.get("id")

                    if parent_id:
                        parent_ids.add(parent_id)

                if not parent_ids:
                    continue

                for entity_id in hierarchy:

                    if class_id in hierarchy[
                        entity_id
                    ]:

                        hierarchy[
                            entity_id
                        ].update(parent_ids)

                next_ids.update(parent_ids)

            current_ids = next_ids

        return hierarchy

    # -----------------------------------------------------------------------
    # Classification
    # -----------------------------------------------------------------------

    def _classify_wikidata_entity(
            self,
            wikidata_id: str,
            hierarchy: dict[str, set[str]],
            characteristics: dict[str, set[str]] | None = None,
    ) -> dict[str, bool]:

        classes = hierarchy.get(
            wikidata_id,
            set(),
        )

        characteristic_ids = (
            characteristics.get(
                wikidata_id,
                set(),
            )
            if characteristics
            else set()
        )

        settlement_root = (
            WIKIDATA_CLASS_ROOTS["settlement"]
        )

        human_root = (
            WIKIDATA_CLASS_ROOTS["human"]
        )

        organization_root = (
            WIKIDATA_CLASS_ROOTS["organization"]
        )

        event_root = (
            WIKIDATA_CLASS_ROOTS["event"]
        )

        battle_root = (
            WIKIDATA_CLASS_ROOTS["battle"]
        )

        administrative_root = (
            WIKIDATA_CLASS_ROOTS[
                "administrative_entity"
            ]
        )

        tourist_attraction_root = (
            WIKIDATA_CLASS_ROOTS[
                "tourist_attraction"
            ]
        )

        # -------------------------------------------------------------------
        # Negative semantic classification.
        # -------------------------------------------------------------------

        is_settlement = (
            settlement_root in classes
        )

        is_event = (
            event_root in classes
            or battle_root in classes
        )

        is_administrative = (
            administrative_root in classes
        )

        is_person = (
            human_root in classes
        )

        is_organization = (
            organization_root in classes
        )

        # -------------------------------------------------------------------
        # Explicit non-visitable classes.
        #
        # These take precedence over any positive signal below, including
        # a curated physical/touristic class — a hotel that happens to
        # also carry a castle-like label is still not a visitable Place
        # for our purposes.
        # -------------------------------------------------------------------

        is_non_visitable_physical = bool(
            classes
            & NON_VISITABLE_PHYSICAL_CLASSES
        )

        # -------------------------------------------------------------------
        # Positive physical/touristic signals.
        #
        # IMPORTANT:
        # Q811979 (architectural structure) is deliberately NOT used as a
        # positive signal here, not even combined with other checks.
        #
        # It is too broad on its own: hotels, offices, university
        # buildings, and most other built structures inherit from it
        # through P279. Using it as a standalone positive signal is what
        # previously let organizations and generic buildings pass as
        # Places. Positive evidence instead comes only from:
        #
        #   - a specific, curated physical/touristic class
        #     (PHYSICAL_PLACE_CLASSES — castle, church, museum, etc.)
        #   - an explicit tourist attraction class (Q570116)
        #
        # Real cultural/religious landmarks (church, cathedral, mosque,
        # synagogue, monastery, basilica, chapel, temple, ...) are already
        # direct members of PHYSICAL_PLACE_CLASSES, so they pass without
        # ever touching the architectural-structure hierarchy.
        # -------------------------------------------------------------------

        is_physical_place = bool(
            classes
            & PHYSICAL_PLACE_CLASSES
        )

        is_tourist_attraction = (
                tourist_attraction_root in classes
                or WIKIDATA_CHARACTERISTICS[
                    "tourist_attraction"
                ] in characteristic_ids
        )

        # -------------------------------------------------------------------
        # Nature.
        #
        # IMPORTANT:
        # Q618123 is deliberately NOT used here.
        #
        # A generic P279 chain to "natural geographic feature" is too broad
        # and caused cultural/built Paris objects to receive is_nature=True.
        # -------------------------------------------------------------------

        is_nature = bool(
            classes
            & NATURE_CLASSES
        )

        # -------------------------------------------------------------------
        # Place decision.
        #
        # Positive (only these two — see note above on Q811979):
        #   - tourist attraction
        #   - known physical cultural/entertainment structure
        #
        # Negative always wins, regardless of any positive signal:
        #   - settlement
        #   - administrative entity
        #   - event
        #   - person
        #   - explicit non-visitable physical class
        #
        # Organizations (Q43229) are intentionally absent from both lists.
        # is_organization is reported below for diagnostics/callers, but it
        # never contributes a positive signal, and it needs no separate
        # negative check either: an organization-only entity already has
        # is_place=False by construction, since neither positive signal
        # above is organization-based. An organization-linked entity can
        # still be a Place, but only when the same Wikidata item
        # independently carries is_tourist_attraction or
        # is_physical_place (e.g. a cathedral that is also linked to a
        # diocese as an organization).
        # -------------------------------------------------------------------

        is_place = (
            is_tourist_attraction
            or is_physical_place
        )

        if (
            is_settlement
            or is_administrative
            or is_event
            or is_person
            or is_non_visitable_physical
        ):
            is_place = False

        return {
            "is_place": is_place,
            "is_nature": is_nature,
            "is_settlement": is_settlement,
            "is_event": is_event,
            "is_organization": is_organization,
            "is_administrative": is_administrative,
            "is_person": is_person,
        }

    # -----------------------------------------------------------------------
    # Nearby Wikidata discovery
    # -----------------------------------------------------------------------

    def discover_city_attractions(
        self,
        city: str,
        latitude: float,
        longitude: float,
    ) -> list[dict]:

        city_id = self.get_city_wikidata_id(
            city
        )

        city_filter = ""

        if city_id:
            city_filter = (
                f"FILTER(?item != wd:{city_id})"
            )

        query = f"""
        SELECT DISTINCT ?item ?itemLabel ?coord ?sitelinks WHERE {{
            SERVICE wikibase:around {{
                ?item wdt:P625 ?coord .

                bd:serviceParam wikibase:center
                    "Point({longitude} {latitude})"^^geo:wktLiteral .

                bd:serviceParam wikibase:radius
                    "{NEARBY_SPARQL_RADIUS_KM}" .
            }}

            ?item wikibase:sitelinks ?sitelinks .

            FILTER(
                ?sitelinks >= {NEARBY_MIN_SITELINKS}
            )

            {city_filter}

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "en" .
            }}
        }}

        ORDER BY DESC(?sitelinks)

        LIMIT {NEARBY_RESULT_LIMIT}
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
                    "Accept": (
                        "application/sparql-results+json"
                    ),
                },
                timeout=SPARQL_TIMEOUT,
            )

            response.raise_for_status()

        except requests.RequestException:
            return []

        data = self._response_json(response)

        if not data:
            return []

        raw_results = (
            data.get("results", {})
            .get("bindings", [])
        )

        results = []

        for result in raw_results:

            item_uri = (
                result.get("item", {})
                .get("value")
            )

            label = (
                result.get("itemLabel", {})
                .get("value")
            )

            coordinate = (
                result.get("coord", {})
                .get("value")
            )

            sitelinks_value = (
                result.get("sitelinks", {})
                .get("value")
            )

            if not item_uri or not label or not coordinate:
                continue

            wikidata_id = item_uri.rsplit(
                "/",
                1,
            )[-1]

            if not wikidata_id.startswith("Q"):
                continue

            parsed_coordinate = self._parse_wkt_point(
                coordinate
            )

            if not parsed_coordinate:
                continue

            item_latitude, item_longitude = (
                parsed_coordinate
            )

            try:
                sitelinks = int(
                    sitelinks_value or 0
                )
            except (
                ValueError,
                TypeError,
            ):
                sitelinks = 0

            distance_km = (
                self.calculate_distance_km(
                    latitude=item_latitude,
                    longitude=item_longitude,
                    target_latitude=latitude,
                    target_longitude=longitude,
                )
            )

            results.append(
                {
                    "title": label,
                    "source_category": "Attractions",
                    "latitude": item_latitude,
                    "longitude": item_longitude,
                    "distance_km": distance_km,
                    "wikidata_id": wikidata_id,
                    "wikidata_sitelinks": sitelinks,
                }
            )

        return results

    # -----------------------------------------------------------------------
    # Full discovery pipeline
    # -----------------------------------------------------------------------

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

        # -------------------------------------------------------------------
        # 1. Wikipedia category discovery.
        # -------------------------------------------------------------------

        for category in categories:

            wikipedia_categories = (
                self.get_city_categories(
                    city=city,
                    country=country,
                    category=category,
                )
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

                    if self._is_list_page(title):
                        continue

                    title_key = title.casefold()

                    if title_key in seen_titles:
                        continue

                    seen_titles.add(title_key)

                    pages.append(
                        {
                            "title": title,
                            "source_category": category,
                        }
                    )

        # -------------------------------------------------------------------
        # 2. Direct nearby Wikidata discovery.
        # -------------------------------------------------------------------

        if "Attractions" in categories:

            wikidata_attractions = (
                self.discover_city_attractions(
                    city=city,
                    latitude=target_latitude,
                    longitude=target_longitude,
                )
            )

            existing_wikidata_ids = set()
            existing_titles = set()

            for page in pages:

                wikidata_id = page.get(
                    "wikidata_id"
                )

                if wikidata_id:
                    existing_wikidata_ids.add(
                        wikidata_id
                    )

                title = page.get("title")

                if title:
                    existing_titles.add(
                        title.casefold()
                    )

            for item in wikidata_attractions:

                wikidata_id = item.get(
                    "wikidata_id"
                )

                title = item.get(
                    "title"
                )

                if not wikidata_id or not title:
                    continue

                if wikidata_id in existing_wikidata_ids:
                    continue

                if title.casefold() in existing_titles:
                    continue

                pages.append(item)

                existing_wikidata_ids.add(
                    wikidata_id
                )

                existing_titles.add(
                    title.casefold()
                )

        if not pages:
            return []

        # -------------------------------------------------------------------
        # 3. Wikipedia page data.
        # -------------------------------------------------------------------

        titles = list(
            dict.fromkeys(
                page["title"]
                for page in pages
                if page.get("title")
            )
        )

        if not titles:
            return []

        page_data = self.get_page_data(
            titles
        )

        # -------------------------------------------------------------------
        # 4. Build candidates.
        #
        # Coordinate priority: Wikipedia {{coord}} first, then direct
        # Wikidata coordinates already attached to the page (from nearby /
        # country discovery).
        #
        # If neither source has coordinates yet, the candidate is NOT
        # dropped here as long as it has a wikidata_id — it is kept with
        # latitude/longitude/distance_km set to None. Step 6 below
        # resolves those from the Wikidata entity's own P625 claim once
        # that entity is hydrated anyway (every candidate gets hydrated
        # for classification regardless), and applies the same radius
        # filter at that point. A candidate with neither coordinates nor
        # a wikidata_id has no way to ever be resolved and is dropped now.
        # -------------------------------------------------------------------

        candidates = []

        for page in pages:

            title = page.get("title")

            if not title:
                continue

            data = page_data.get(
                title
            )

            coordinates = None

            if data:
                coordinates = data.get(
                    "coordinates"
                )

            if not coordinates:

                page_latitude = page.get(
                    "latitude"
                )

                page_longitude = page.get(
                    "longitude"
                )

                if (
                    page_latitude is not None
                    and page_longitude is not None
                ):
                    coordinates = (
                        page_latitude,
                        page_longitude,
                    )

            wikidata_id = None

            if data:
                wikidata_id = data.get(
                    "wikidata_id"
                )

            if not wikidata_id:
                wikidata_id = page.get(
                    "wikidata_id"
                )

            if not coordinates and not wikidata_id:
                continue

            latitude = None
            longitude = None
            distance_km = None

            if coordinates:

                candidate_latitude, candidate_longitude = coordinates

                if (
                    candidate_latitude is not None
                    and candidate_longitude is not None
                ):

                    distance_km = (
                        self.calculate_distance_km(
                            latitude=candidate_latitude,
                            longitude=candidate_longitude,
                            target_latitude=target_latitude,
                            target_longitude=target_longitude,
                        )
                    )

                    if distance_km > radius_km:
                        continue

                    latitude = candidate_latitude
                    longitude = candidate_longitude

            if (
                latitude is None
                and not wikidata_id
            ):
                # Had coordinates but they were malformed (None/None
                # tuple), and there is no wikidata_id to fall back to.
                continue

            candidates.append(
                {
                    "title": title,
                    "source_category": page.get(
                        "source_category"
                    ),
                    "latitude": latitude,
                    "longitude": longitude,
                    "distance_km": distance_km,
                    "wikidata_id": wikidata_id,
                    "wikidata_sitelinks": page.get(
                        "wikidata_sitelinks",
                        0,
                    ),
                }
            )

        # -------------------------------------------------------------------
        # 5. Global deduplication.
        #
        # One real Wikidata object should become one candidate even if it was
        # discovered through several Wikipedia categories.
        # -------------------------------------------------------------------

        unique_candidates = []
        seen_wikidata_ids = set()
        seen_fallback = set()

        for candidate in candidates:

            wikidata_id = candidate.get(
                "wikidata_id"
            )

            if wikidata_id:

                if wikidata_id in seen_wikidata_ids:
                    continue

                seen_wikidata_ids.add(
                    wikidata_id
                )

                unique_candidates.append(
                    candidate
                )

                continue

            fallback_key = (
                candidate.get("title", "").casefold(),
                round(
                    candidate.get(
                        "latitude",
                        0,
                    ),
                    5,
                ),
                round(
                    candidate.get(
                        "longitude",
                        0,
                    ),
                    5,
                ),
            )

            if fallback_key in seen_fallback:
                continue

            seen_fallback.add(
                fallback_key
            )

            unique_candidates.append(
                candidate
            )

        candidates = unique_candidates

        if not candidates:
            return []

        # -------------------------------------------------------------------
        # 6. Wikidata entity hydration.
        #
        # Entities are fetched once and reused below for both significance
        # and the P31/P279 hierarchy, instead of hydrating the same
        # Wikidata items through three separate round trips.
        # -------------------------------------------------------------------

        wikidata_ids = list(
            dict.fromkeys(
                candidate["wikidata_id"]
                for candidate in candidates
                if candidate.get("wikidata_id")
            )
        )

        entities = self._hydrate_wikidata_entities(
            wikidata_ids
        )

        characteristics = {
            wikidata_id: self._entity_characteristic_ids(
                entity
            )
            for wikidata_id, entity in entities.items()
        }

        # -------------------------------------------------------------------
        # 6b. Resolve coordinate-pending candidates.
        #
        # A small number of candidates reach this point with a
        # wikidata_id but no coordinates yet (Wikipedia article had no
        # {{coord}} tag, and it was not discovered directly from nearby/
        # country Wikidata). Their entity is already hydrated above for
        # classification regardless, so its own P625 claim is used as a
        # last-resort coordinate source. The same radius filter used in
        # step 4 is applied here too — it was only deferred, not skipped.
        # -------------------------------------------------------------------

        coordinate_resolved_candidates = []

        for candidate in candidates:

            if (
                candidate["latitude"] is not None
                and candidate["longitude"] is not None
            ):
                coordinate_resolved_candidates.append(
                    candidate
                )
                continue

            wikidata_id = candidate.get(
                "wikidata_id"
            )

            entity = entities.get(
                wikidata_id,
                {},
            )

            coordinate_claims = (
                entity.get("claims", {})
                .get("P625", [])
            )

            if not coordinate_claims:
                continue

            coordinate_value = (
                coordinate_claims[0]
                .get("mainsnak", {})
                .get("datavalue", {})
                .get("value", {})
            )

            latitude = coordinate_value.get(
                "latitude"
            )

            longitude = coordinate_value.get(
                "longitude"
            )

            if latitude is None or longitude is None:
                continue

            distance_km = (
                self.calculate_distance_km(
                    latitude=latitude,
                    longitude=longitude,
                    target_latitude=target_latitude,
                    target_longitude=target_longitude,
                )
            )

            if distance_km > radius_km:
                continue

            candidate["latitude"] = latitude
            candidate["longitude"] = longitude
            candidate["distance_km"] = distance_km

            coordinate_resolved_candidates.append(
                candidate
            )

        candidates = coordinate_resolved_candidates

        if not candidates:
            return []

        # -------------------------------------------------------------------
        # 7. Wikidata significance.
        #
        # Derived directly from the entities hydrated above (sitelinks are
        # already part of that payload) rather than a separate
        # wbgetentities call for the same ids.
        # -------------------------------------------------------------------

        significance = {
            wikidata_id: len(
                entity.get("sitelinks", {})
            )
            for wikidata_id, entity in entities.items()
        }

        # -------------------------------------------------------------------
        # 8. P31/P279 hierarchy.
        #
        # Reuses the entities hydrated in step 6 for the base P31 classes;
        # only ancestor classes discovered while walking P279 require new
        # fetches.
        # -------------------------------------------------------------------

        hierarchy = (
            self._get_wikidata_class_hierarchy(
                wikidata_ids,
                entities=entities,
            )
        )

        # -------------------------------------------------------------------
        # 9. Classification.
        #
        # Discovery and classification remain separate:
        #
        # Discovery decides what enters the candidate pool.
        # Classification decides whether the candidate is semantically
        # usable as a Place/Nature object.
        # -------------------------------------------------------------------

        classified_candidates = []

        for candidate in candidates:

            wikidata_id = candidate.get(
                "wikidata_id"
            )

            if not wikidata_id:
                continue

            entity = entities.get(
                wikidata_id,
                {}
            )

            p31_values = sorted(
                self._entity_instance_ids(
                    entity
                )
            )

            classification = self._classify_wikidata_entity(
                wikidata_id,
                hierarchy,
                characteristics,
            )

            if not (
                classification["is_place"]
                or classification["is_nature"]
            ):
                continue

            candidate["classification"] = (
                classification
            )

            candidate[
                "wikidata_classification"
            ] = classification

            candidate[
                "wikidata_p31"
            ] = p31_values

            candidate[
                "wikidata_sitelinks"
            ] = significance.get(
                wikidata_id,
                0,
            )

            classified_candidates.append(
                candidate
            )

        candidates = classified_candidates

        # -------------------------------------------------------------------
        # 10. Ranking.
        #
        # Intentionally unchanged at this stage.
        #
        # Sitelinks = popularity/data-quality signal.
        # Distance = proximity.
        # Title = deterministic tie-breaker.
        # -------------------------------------------------------------------

        candidates.sort(
            key=lambda item: (
                -item["wikidata_sitelinks"],
                item["distance_km"],
                item["title"].casefold(),
            )
        )

        return candidates

    # -----------------------------------------------------------------------
    # Significance
    #
    # Kept as a standalone public method for backward compatibility with
    # any other backend code that calls it directly. The main discovery
    # pipeline no longer calls this itself — see step 7 above, which
    # derives the same numbers from entities it already hydrated.
    # -----------------------------------------------------------------------

    def get_wikidata_significance(
        self,
        wikidata_ids: list[str],
    ) -> dict[str, int]:

        significance = {}

        unique_ids = list(
            dict.fromkeys(wikidata_ids)
        )

        for start in range(
            0,
            len(unique_ids),
            50,
        ):

            batch = unique_ids[
                start:start + 50
            ]

            if not batch:
                continue

            params = {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "sitelinks",
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

            data = self._response_json(response)

            if not data:
                continue

            entities = data.get(
                "entities",
                {},
            )

            for wikidata_id in batch:

                entity = entities.get(
                    wikidata_id,
                    {}
                )

                sitelinks = entity.get(
                    "sitelinks",
                    {}
                )

                significance[wikidata_id] = len(
                    sitelinks
                )

        return significance

    # -----------------------------------------------------------------------
    # Distance
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Optional country-level diagnostic method.
    #
    # No console output. Returns structured data instead.
    # -----------------------------------------------------------------------

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
                "message": (
                    "Country Wikidata ID not found"
                ),
            }

        class_ids = WIKIDATA_CATEGORY_CLASSES.get(
            category,
            [],
        )

        if not class_ids:
            return {
                "country": country,
                "country_id": country_id,
                "category": category,
                "count": 0,
                "results": [],
            }

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
                    "Accept": (
                        "application/sparql-results+json"
                    ),
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

        data = self._response_json(response)

        if not data:
            return {
                "country": country,
                "country_id": country_id,
                "category": category,
                "count": 0,
                "results": [],
            }

        results = []

        for result in (
                data.get("results", {})
                        .get("bindings", [])
        ):
            results.append(
                {
                    "id": (
                        result.get("item", {})
                        .get("value")
                    ),
                    "label": (
                        result.get("itemLabel", {})
                        .get("value")
                    ),
                    "coordinate": (
                        result.get("coordinate", {})
                        .get("value")
                    ),
                }
            )

        return {
            "country": country,
            "country_id": country_id,
            "category": category,
            "count": len(results),
            "results": results,
        }

    def debug_candidate(
            self,
            wikidata_id: str,
    ) -> dict:

        result = {
            "wikidata_id": wikidata_id,
            "steps": {},
        }

        # 1. Find Wikipedia pages that point to this Wikidata entity
        response = requests.get(
            API_URL,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": wikidata_id,
                "gsrlimit": 20,
                "prop": "pageprops|coordinates",
                "ppprop": "wikibase_item",
                "format": "json",
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        pages = response.json().get(
            "query",
            {},
        ).get(
            "pages",
            {},
        )

        matching_pages = []

        for page in pages.values():
            pageprops = page.get(
                "pageprops",
                {},
            )

            if pageprops.get(
                    "wikibase_item"
            ) == wikidata_id:
                matching_pages.append(
                    {
                        "title": page.get(
                            "title"
                        ),
                        "wikibase_item": pageprops.get(
                            "wikibase_item"
                        ),
                        "coordinates": page.get(
                            "coordinates"
                        ),
                    }
                )

        result["steps"]["wikipedia"] = {
            "found": bool(matching_pages),
            "pages": matching_pages,
        }

        # 2. Hydrate Wikidata entity
        entities = self._hydrate_wikidata_entities(
            {wikidata_id}
        )

        entity = entities.get(
            wikidata_id
        )

        result["steps"]["hydration"] = {
            "found": entity is not None,
        }

        if entity is None:
            return result

        # 3. Basic Wikidata data
        claims = entity.get(
            "claims",
            {},
        )

        p31_ids = []

        for claim in claims.get(
                "P31",
                [],
        ):
            value = (
                claim
                .get("mainsnak", {})
                .get("datavalue", {})
                .get("value")
            )

            if (
                    isinstance(value, dict)
                    and value.get("id")
            ):
                p31_ids.append(
                    value["id"]
                )

        coordinates = None

        p625 = claims.get(
            "P625",
            [],
        )

        if p625:
            value = (
                p625[0]
                .get("mainsnak", {})
                .get("datavalue", {})
                .get("value")
            )

            if isinstance(value, dict):
                coordinates = {
                    "latitude": value.get(
                        "latitude"
                    ),
                    "longitude": value.get(
                        "longitude"
                    ),
                }

        sitelinks = entity.get(
            "sitelinks",
            {},
        )

        result["steps"]["wikidata"] = {
            "label": (
                entity
                .get("labels", {})
                .get("en", {})
                .get("value")
            ),
            "description": (
                entity
                .get("descriptions", {})
                .get("en", {})
                .get("value")
            ),
            "p31": p31_ids,
            "coordinates": coordinates,
            "sitelinks": len(sitelinks),
            "has_enwiki": "enwiki" in sitelinks,
        }

        # 4. Wikidata characteristics
        characteristics = (
            self._entity_characteristic_ids(
                entity
            )
        )

        result["steps"]["characteristics"] = {
            "ids": sorted(
                characteristics
            ),
            "tourist_attraction": (
                    WIKIDATA_CHARACTERISTICS[
                        "tourist_attraction"
                    ]
                    in characteristics
            ),
        }

        # 5. Class hierarchy
        hierarchy = (
            self._get_wikidata_class_hierarchy(
                {wikidata_id}
            )
        )

        result["steps"]["hierarchy"] = {
            "classes": sorted(
                hierarchy.get(
                    wikidata_id,
                    set(),
                )
            ),
        }

        # 6. Classification
        classification = (
            self._classify_wikidata_entity(
                wikidata_id,
                hierarchy,
                {
                    wikidata_id: characteristics,
                },
            )
        )

        result["steps"]["classification"] = (
            classification
        )

        result["steps"]["classification_debug"] = {
            "classes": sorted(
                hierarchy.get(
                    wikidata_id,
                    set(),
                )
            ),
            "physical_place_matches": sorted(
                hierarchy.get(
                    wikidata_id,
                    set(),
                )
                & PHYSICAL_PLACE_CLASSES
            ),
            "non_visitable_matches": sorted(
                hierarchy.get(
                    wikidata_id,
                    set(),
                )
                & NON_VISITABLE_PHYSICAL_CLASSES
            ),
            "tourist_attraction_match": (
                    WIKIDATA_CLASS_ROOTS[
                        "tourist_attraction"
                    ]
                    in hierarchy.get(
                wikidata_id,
                set(),
            )
            ),
            "tourist_attraction_characteristic": (
                    WIKIDATA_CHARACTERISTICS[
                        "tourist_attraction"
                    ]
                    in characteristics
            ),
            "physical_place_classes": sorted(
                PHYSICAL_PLACE_CLASSES
            ),
        }

        return result