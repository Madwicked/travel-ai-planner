import re
import requests
from math import atan2, cos, log2, radians, sin, sqrt

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
        "Q570116",
        "Q4989906",
        "Q839954",
        "Q811979",
        "Q2977",
    ],
    "Nature": [
        "Q46169",
        "Q22698",
        "Q167346",
        "Q179049",
        "Q4421",
        "Q40080",
    ],
    "Entertainment": [
        "Q194195",
        "Q24354",
        "Q107898",
        "Q1060829",
        "Q43501",
        "Q16521",
        "Q41253",
    ],
}


# ---------------------------------------------------------
# Ranking
# ---------------------------------------------------------

RANKING_TYPE_SCORES = {
    "Q57831": 100,
    "Q23413": 96,
    "Q16560": 92,
    "Q839954": 90,
    "Q4989906": 84,
    "Q570116": 78,

    "Q33506": 76,
    "Q16970": 72,
    "Q24354": 68,
    "Q107898": 68,
    "Q1060829": 66,
    "Q41253": 64,

    "Q46169": 78,
    "Q179049": 72,
    "Q22698": 64,
    "Q167346": 64,
    "Q40080": 60,
    "Q4421": 52,

    "Q194195": 68,
    "Q43501": 66,
    "Q16521": 66,

    "Q483110": -35,
    "Q16917": -45,
    "Q79007": -50,
    "Q12280": 38,
}


GENERIC_TYPE_SCORES = {
    "Q811979": 25,
}


STRONG_NEGATIVE_TYPES = {
    "Q483110",
    "Q16917",
    "Q79007",
}


POSITIVE_NAME_PATTERNS = (
    r"\bfortress\b",
    r"\bcastle\b",
    r"\bpalace\b",
    r"\bfort\b",
    r"\bmuseum\b",
    r"\bcathedral\b",
    r"\bchurch\b",
    r"\bmonument\b",
    r"\bmemorial\b",
    r"\bsynagogue\b",
    r"\bmosque\b",
    r"\btheatre\b",
    r"\btheater\b",
    r"\bopera\b",
    r"\btower\b",
    r"\bsquare\b",
)

NEGATIVE_NAME_PATTERNS = (
    r"\bhospital\b",
    r"\bstadium\b",
    r"\bport\b",
    r"\bstreet\b",
    r"\broad\b",
    r"\bboulevard\b",
    r"\bclinic\b",
    r"\bparking\b",
    r"\bgarage\b",
    r"\bterminal\b",
    r"\bstation\b",
)


class WikipediaDiscoveryService:
    def get_city_categories(self, city, country, category=None):
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

    def get_category_members(self, category):
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

    def get_page_data(self, titles):
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

    def get_country_wikidata_id(self, country):
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
                (result.get("label") or "")
                .strip()
                .casefold()
            )

            if label == country_normalized:
                return result.get("id")

        return results[0].get("id")

    def discover_by_country(self, country, category):
        country_id = self.get_country_wikidata_id(country)

        if not country_id:
            return []

        class_ids = WIKIDATA_CATEGORY_CLASSES.get(category, [])

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

                candidates.append({
                    "wikidata_id": title,
                })

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
            entities.update(data.get("entities", {}))

        results = []

        for wikidata_id, entity in entities.items():
            claims = entity.get("claims", {})

            coordinates_claims = claims.get("P625", [])

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

            if not sitelinks.get("enwiki"):
                continue

            results.append({
                "title": title,
                "source_category": category,
                "latitude": latitude,
                "longitude": longitude,
                "distance_km": 0,
                "wikidata_id": wikidata_id,
                "wikidata_sitelinks": len(sitelinks),
                "wikidata_claims": claims,
            })

        results = self._rank_candidates(
            results,
            category=category,
        )

        return results

    def get_city_wikidata_id(self, city):
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
                (result.get("label") or "")
                .strip()
                .casefold()
            )

            if label == city_normalized:
                return result.get("id")

        return results[0].get("id")

    def discover_city_wikidata_category(
        self,
        category,
        target_latitude,
        target_longitude,
        radius_km,
    ):
        class_ids = WIKIDATA_CATEGORY_CLASSES.get(
            category,
            [],
        )

        if not class_ids:
            return []

        values = " ".join(
            f"wd:{class_id}"
            for class_id in class_ids
        )

        center = (
            f"Point({target_longitude} {target_latitude})"
        )

        query = f"""
        SELECT DISTINCT ?item ?itemLabel ?coordinate ?distance
        WHERE {{
            SERVICE wikibase:around {{
                ?item wdt:P625 ?coordinate .
                bd:serviceParam wikibase:center
                    "Point({target_longitude} {target_latitude})"^^geo:wktLiteral .
                bd:serviceParam wikibase:radius
                    "{radius_km}" .
                bd:serviceParam wikibase:distance
                    ?distance .
            }}

            ?item wdt:P31/wdt:P279* ?class .

            VALUES ?class {{
                {values}
            }}

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "en" .
            }}
        }}
        ORDER BY ?distance
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

        except requests.RequestException as exc:
            print(
                "WIKIDATA CATEGORY ERROR:",
                category,
                type(exc).__name__,
                str(exc),
            )
            return []

        data = response.json()

        bindings = data.get(
            "results",
            {},
        ).get(
            "bindings",
            [],
        )

        results = []

        for result in bindings:
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

            distance = result.get(
                "distance",
                {},
            ).get("value")

            if not item_uri or not label or not coordinate:
                continue

            wikidata_id = item_uri.rsplit("/", 1)[-1]

            if not wikidata_id.startswith("Q"):
                continue

            if label.strip().casefold() == wikidata_id.casefold():
                continue

            try:
                longitude_text, latitude_text = (
                    coordinate
                    .replace("Point(", "")
                    .replace(")", "")
                    .split()
                )

                longitude = float(longitude_text)
                latitude = float(latitude_text)

            except (ValueError, AttributeError):
                continue

            try:
                distance_km = float(distance)
            except (ValueError, TypeError):
                distance_km = self.calculate_distance_km(
                    latitude=latitude,
                    longitude=longitude,
                    target_latitude=target_latitude,
                    target_longitude=target_longitude,
                )

            results.append({
                "title": label,
                "source_category": category,
                "latitude": latitude,
                "longitude": longitude,
                "distance_km": distance_km,
                "wikidata_id": wikidata_id,
                "wikidata_sitelinks": 0,
            })

        return results

    def discover_city_attractions(
        self,
        city,
        target_latitude,
        target_longitude,
        radius_km,
    ):
        return self.discover_city_wikidata_category(
            category="Attractions",
            target_latitude=target_latitude,
            target_longitude=target_longitude,
            radius_km=radius_km,
        )

    def _extract_claim_ids(self, claims, property_id):
        values = []

        for claim in claims.get(property_id, []):
            value = (
                claim.get("mainsnak", {})
                .get("datavalue", {})
                .get("value")
            )

            if isinstance(value, dict):
                entity_id = value.get("id")

                if entity_id and entity_id.startswith("Q"):
                    values.append(entity_id)

        return values

    def _get_entities(self, wikidata_ids, props="claims"):
        entities = {}

        ids = list(dict.fromkeys(
            wikidata_id
            for wikidata_id in wikidata_ids
            if wikidata_id
        ))

        for start in range(0, len(ids), 50):
            batch = ids[start:start + 50]

            params = {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": props,
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

        return entities

    def _load_type_hierarchy(self, direct_type_ids, max_depth=3):
        hierarchy = {
            wikidata_id: 0
            for wikidata_id in direct_type_ids
            if wikidata_id
        }

        current_level = set(hierarchy.keys())

        for depth in range(1, max_depth + 1):
            if not current_level:
                break

            entities = self._get_entities(
                current_level,
                props="claims",
            )

            next_level = set()

            for entity in entities.values():
                claims = entity.get("claims", {})

                parent_ids = self._extract_claim_ids(
                    claims,
                    "P279",
                )

                for parent_id in parent_ids:
                    if parent_id in hierarchy:
                        continue

                    hierarchy[parent_id] = depth
                    next_level.add(parent_id)

            current_level = next_level

        return hierarchy

    def _get_candidate_metadata(self, candidates):
        wikidata_ids = list({
            candidate.get("wikidata_id")
            for candidate in candidates
            if candidate.get("wikidata_id")
        })

        if not wikidata_ids:
            return {}

        entities = self._get_entities(
            wikidata_ids,
            props="claims|sitelinks",
        )

        metadata = {}

        all_direct_types = set()

        for wikidata_id, entity in entities.items():
            claims = entity.get("claims", {})

            direct_types = self._extract_claim_ids(
                claims,
                "P31",
            )

            all_direct_types.update(
                direct_types
            )

            metadata[wikidata_id] = {
                "claims": claims,
                "direct_types": direct_types,
                "sitelinks": len(
                    entity.get("sitelinks", {})
                ),
            }

        type_entities = {}

        current_ids = set(all_direct_types)

        for _ in range(3):
            if not current_ids:
                break

            missing_ids = {
                wikidata_id
                for wikidata_id in current_ids
                if wikidata_id not in type_entities
            }

            if not missing_ids:
                break

            loaded_entities = self._get_entities(
                missing_ids,
                props="claims",
            )

            type_entities.update(
                loaded_entities
            )

            next_ids = set()

            for entity in loaded_entities.values():
                claims = entity.get(
                    "claims",
                    {},
                )

                parent_ids = self._extract_claim_ids(
                    claims,
                    "P279",
                )

                next_ids.update(
                    parent_ids
                )

            current_ids = next_ids

        for wikidata_id, item in metadata.items():
            direct_types = item.get(
                "direct_types",
                [],
            )

            hierarchy = {}

            current_level = set(
                direct_types
            )

            for direct_type in current_level:
                hierarchy[direct_type] = 0

            for depth in range(1, 4):
                if not current_level:
                    break

                next_level = set()

                for type_id in current_level:
                    entity = type_entities.get(
                        type_id
                    )

                    if not entity:
                        continue

                    claims = entity.get(
                        "claims",
                        {},
                    )

                    parent_ids = self._extract_claim_ids(
                        claims,
                        "P279",
                    )

                    for parent_id in parent_ids:
                        if parent_id in hierarchy:
                            continue

                        hierarchy[parent_id] = depth
                        next_level.add(parent_id)

                current_level = next_level

            item["type_hierarchy"] = hierarchy

        return metadata

    def _score_type(self, direct_types, type_hierarchy):
        if not direct_types:
            return 0, False

        best_positive = 0
        strongest_negative = 0
        has_strong_negative = False

        for type_id in direct_types:
            score = RANKING_TYPE_SCORES.get(
                type_id
            )

            if score is None:
                continue

            if type_id in STRONG_NEGATIVE_TYPES:
                strongest_negative = min(
                    strongest_negative,
                    score,
                )
                has_strong_negative = True
            else:
                best_positive = max(
                    best_positive,
                    score,
                )

        if has_strong_negative:
            return strongest_negative, True

        for type_id, depth in type_hierarchy.items():
            if depth <= 0:
                continue

            base_score = RANKING_TYPE_SCORES.get(
                type_id
            )

            if base_score is None:
                base_score = GENERIC_TYPE_SCORES.get(
                    type_id
                )

            if base_score is None:
                continue

            hierarchy_score = max(
                0,
                base_score - depth * 12,
            )

            best_positive = max(
                best_positive,
                hierarchy_score,
            )

        return best_positive, False

    def _score_name_fallback(self, title):
        normalized = (
            title or ""
        ).strip().casefold()

        positive_score = 0
        negative_score = 0

        for pattern in POSITIVE_NAME_PATTERNS:
            if re.search(pattern, normalized):
                positive_score = max(
                    positive_score,
                    6,
                )

        for pattern in NEGATIVE_NAME_PATTERNS:
            if re.search(pattern, normalized):
                negative_score = min(
                    negative_score,
                    -8,
                )

        return positive_score + negative_score

    def _score_sitelinks(self, sitelinks):
        if not sitelinks or sitelinks < 1:
            return 0

        return min(
            18,
            round(log2(sitelinks + 1) * 3),
        )

    def _score_heritage(self, claims):
        heritage_claims = claims.get("P1435", [])

        if not heritage_claims:
            return 0

        return 12

    def _score_distance(self, distance_km):
        if distance_km is None:
            return 0

        try:
            distance = float(distance_km)
        except (TypeError, ValueError):
            return 0

        return max(
            0,
            round(8 - distance * 0.4),
        )

    def _rank_candidates(self, candidates, category=None):
        if not candidates:
            return candidates

        metadata = self._get_candidate_metadata(
            candidates
        )

        ranked = []

        for candidate in candidates:
            wikidata_id = candidate.get(
                "wikidata_id"
            )

            item_metadata = metadata.get(
                wikidata_id,
                {},
            )

            claims = item_metadata.get(
                "claims",
                {},
            )

            direct_types = item_metadata.get(
                "direct_types",
                [],
            )

            type_hierarchy = (
                item_metadata.get(
                    "type_hierarchy",
                    {},
                )
            )

            type_score, strong_negative = (
                self._score_type(
                    direct_types=direct_types,
                    type_hierarchy=type_hierarchy,
                )
            )

            name_score = self._score_name_fallback(
                candidate.get("title")
            )

            sitelinks = item_metadata.get(
                "sitelinks",
                candidate.get(
                    "wikidata_sitelinks",
                    0,
                ),
            )

            sitelinks_score = self._score_sitelinks(
                sitelinks
            )

            heritage_score = self._score_heritage(
                claims
            )

            distance_score = self._score_distance(
                candidate.get("distance_km")
            )

            if strong_negative:
                final_score = (
                    type_score
                    + min(name_score, 0)
                )
            else:
                final_score = (
                    type_score
                    + sitelinks_score
                    + heritage_score
                    + distance_score
                    + name_score
                )

            candidate["wikidata_sitelinks"] = sitelinks
            candidate["wikidata_types"] = direct_types
            candidate["type_hierarchy"] = type_hierarchy
            candidate["rank_type_score"] = type_score
            candidate["rank_sitelinks_score"] = (
                sitelinks_score
            )
            candidate["rank_heritage_score"] = (
                heritage_score
            )
            candidate["rank_distance_score"] = (
                distance_score
            )
            candidate["rank_name_score"] = (
                name_score
            )
            candidate["rank_score"] = final_score

            ranked.append(candidate)

        ranked.sort(
            key=lambda item: (
                -item.get("rank_score", 0),
                item.get("distance_km", float("inf")),
                item.get("title", "").casefold(),
            )
        )
        debug_keywords = (
            "hotel",
            "hostel",
            "apart",
            "palace",
            "bridge",
            "stadium",
            "building",
            "bazar",
        )

        for candidate in candidates:
            title = candidate.get("title", "")
            title_lower = title.casefold()

            if not any(
                    keyword in title_lower
                    for keyword in debug_keywords
            ):
                continue

            print(
                "\n=== RANK DEBUG ===",
                "\nTITLE:", title,
                "\nWIKIDATA ID:", candidate.get("wikidata_id"),
                "\nDIRECT TYPES:", candidate.get("wikidata_types"),
                "\nTYPE HIERARCHY:", candidate.get("type_hierarchy"),
                "\nTYPE SCORE:", candidate.get("rank_type_score"),
                "\nNAME SCORE:", candidate.get("rank_name_score"),
                "\nSITELINKS SCORE:",
                candidate.get("rank_sitelinks_score"),
                "\nHERITAGE SCORE:",
                candidate.get("rank_heritage_score"),
                "\nDISTANCE SCORE:",
                candidate.get("rank_distance_score"),
                "\nFINAL SCORE:", candidate.get("rank_score"),
            )

        return ranked

    def discover_all_categories(
            self,
            city,
            country,
            target_latitude,
            target_longitude,
            radius_km=25,
    ):
        pages = []

        # ---------------------------------------------------------
        # Attractions -> Wikidata
        # ---------------------------------------------------------
        wikidata_attractions = (
            self.discover_city_wikidata_category(
                category="Attractions",
                target_latitude=target_latitude,
                target_longitude=target_longitude,
                radius_km=radius_km,
            )
        )

        pages.extend(
            wikidata_attractions
        )

        # ---------------------------------------------------------
        # Nature -> Wikidata
        # ---------------------------------------------------------
        wikidata_nature = (
            self.discover_city_wikidata_category(
                category="Nature",
                target_latitude=target_latitude,
                target_longitude=target_longitude,
                radius_km=radius_km,
            )
        )

        pages.extend(
            wikidata_nature
        )

        # ---------------------------------------------------------
        # Entertainment -> Wikidata
        # ---------------------------------------------------------
        wikidata_entertainment = (
            self.discover_city_wikidata_category(
                category="Entertainment",
                target_latitude=target_latitude,
                target_longitude=target_longitude,
                radius_km=radius_km,
            )
        )

        pages.extend(
            wikidata_entertainment
        )

        candidates = []

        for page in pages:
            title = page.get("title")

            if not title:
                continue

            latitude = page.get("latitude")
            longitude = page.get("longitude")

            if latitude is None or longitude is None:
                continue

            distance_km = page.get(
                "distance_km"
            )

            if distance_km is None:
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

            candidates.append({
                "title": title,
                "source_category": page[
                    "source_category"
                ],
                "latitude": latitude,
                "longitude": longitude,
                "distance_km": distance_km,
                "wikidata_id": page.get(
                    "wikidata_id"
                ),
                "wikidata_sitelinks": page.get(
                    "wikidata_sitelinks",
                    0,
                ),
            })

        # ---------------------------------------------------------
        # Deduplication
        # ---------------------------------------------------------
        deduplicated = {}

        for candidate in candidates:
            wikidata_id = candidate.get(
                "wikidata_id"
            )
            source_category = candidate.get(
                "source_category"
            )

            if wikidata_id:
                key = (
                    source_category,
                    wikidata_id,
                )
            else:
                key = (
                    source_category,
                    candidate["title"]
                    .strip()
                    .casefold(),
                )

            existing = deduplicated.get(key)

            if existing is None:
                deduplicated[key] = candidate
                continue

            if (
                    candidate["distance_km"]
                    < existing["distance_km"]
            ):
                deduplicated[key] = candidate

        candidates = list(
            deduplicated.values()
        )

        # ---------------------------------------------------------
        # Ranking
        # ---------------------------------------------------------
        candidates = self._rank_candidates(
            candidates
        )

        # ---------------------------------------------------------
        # Remove Nature objects accidentally discovered
        # through Attractions.
        # ---------------------------------------------------------
        nature_classes = set(
            WIKIDATA_CATEGORY_CLASSES.get(
                "Nature",
                [],
            )
        )

        filtered_candidates = []

        for candidate in candidates:
            if (
                    candidate.get("source_category")
                    == "Attractions"
            ):
                type_hierarchy = candidate.get(
                    "type_hierarchy",
                    {},
                )

                is_nature = any(
                    class_id in nature_classes
                    and depth <= 1
                    for class_id, depth
                    in type_hierarchy.items()
                )

                if is_nature:
                    continue

            filtered_candidates.append(
                candidate
            )

        candidates = filtered_candidates

        return candidates

    def get_wikidata_significance(self, wikidata_id):
        if not wikidata_id:
            return 0

        params = {
            "action": "wbgetentities",
            "ids": wikidata_id,
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
            return 0

        data = response.json()

        entity = (
            data.get("entities", {})
            .get(wikidata_id, {})
        )

        sitelinks = entity.get(
            "sitelinks",
            {},
        )

        return len(sitelinks)

    def calculate_distance_km(
        self,
        latitude,
        longitude,
        target_latitude,
        target_longitude,
    ):
        lat1 = radians(latitude)
        lon1 = radians(longitude)
        lat2 = radians(target_latitude)
        lon2 = radians(target_longitude)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a),
        )

        return EARTH_RADIUS_KM * c

    def debug_country_discovery(self, country):
        for category in WIKIDATA_CATEGORY_CLASSES:
            results = self.discover_by_country(
                country=country,
                category=category,
            )

            print(
                "WIKIDATA COUNTRY:",
                country,
                category,
                len(results),
            )

            for item in results[:10]:
                print(
                    item.get("wikidata_id"),
                    item.get("title"),
                    item.get("latitude"),
                    item.get("longitude"),
                )