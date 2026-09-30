import json
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod


class AirportProvider(ABC):

    @abstractmethod
    def find_airports(
        self,
        city: str,
        latitude: float | None,
        longitude: float | None,
    ):
        pass

    @abstractmethod
    def find_airport_by_iata(
            self,
            iata_code: str,
    ):
        pass


class FreeAirportDbProvider(AirportProvider):

    BASE_URL = "https://api.freeairportdb.com/v1"

    def find_airport_by_iata(self, iata_code):
        if not iata_code:
            return None

        query = urllib.parse.urlencode({
            "q": iata_code.upper(),
            "limit": 100,
        })

        url = f"{self.BASE_URL}/airports?{query}"

        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "TravelAIPlanner/1.0",
            },
        )

        with urllib.request.urlopen(request) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        for airport in data.get("data", []):
            if (
                airport.get("iata")
                and airport["iata"].upper() == iata_code.upper()
                and airport.get("type")
                in {"large_airport", "medium_airport"}
            ):
                return self._format_airport(airport)

        return None

    def find_airports(
        self,
        city,
        latitude,
        longitude,
        country=None,
    ):
        if latitude is not None and longitude is not None:
            airports = self._find_nearby(
                city=city,
                latitude=latitude,
                longitude=longitude,
                country=country,
            )

            if airports:
                return airports

        return self._find_by_city(
            city=city,
            latitude=latitude,
            longitude=longitude,
            country=country,
        )

    def _find_nearby(
        self,
        city,
        latitude,
        longitude,
        country=None,
    ):
        params = urllib.parse.urlencode({
            "lat": latitude,
            "lng": longitude,
            "limit": 20,
        })

        url = f"{self.BASE_URL}/airports/nearby?{params}"

        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "TravelAIPlanner/1.0",
            },
            method="GET",
        )

        with urllib.request.urlopen(request) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        airports = [
            airport
            for airport in data.get("data", [])
            if (
                airport.get("iata")
                and airport.get("type")
                in {"large_airport", "medium_airport"}
            )
        ]

        if not airports:
            return []

        if country:
            country_lower = country.strip().casefold()

            airports = [
                airport
                for airport in airports
                if (
                    airport.get("country_name")
                    and airport["country_name"].strip().casefold()
                    == country_lower
                )
            ]

        if not airports:
            return []

        city_lower = city.strip().casefold()

        city_related_airports = [
            airport
            for airport in airports
            if (
                airport.get("municipality")
                and airport["municipality"].strip().casefold()
                == city_lower
            )
        ]

        # Если аэропорты находятся непосредственно в этом городе,
        # возвращаем все аэропорты города.
        #
        # Например:
        # Москва -> SVO, DME, VKO, ...
        # Лондон -> несколько аэропортов Лондона
        if city_related_airports:
            city_related_airports.sort(
                key=lambda item: (
                    0
                    if item.get("type") == "large_airport"
                    else 1,
                    item.get(
                        "distance_km",
                        float("inf"),
                    ),
                )
            )

            return [
                self._format_airport(airport)
                for airport in city_related_airports
            ]

        # Если в самом городе подходящего аэропорта нет,
        # используем только ближайший аэропорт.
        #
        # Например:
        # Novi Sad -> BEG
        airports.sort(
            key=lambda item: (
                0
                if item.get("type") == "large_airport"
                else 1,
                item.get(
                    "distance_km",
                    float("inf"),
                ),
            )
        )

        return [
            self._format_airport(airports[0])
        ]

    def _find_by_city(
        self,
        city,
        latitude=None,
        longitude=None,
        country=None,
    ):
        query = urllib.parse.urlencode({
            "q": city,
            "limit": 100,
        })

        url = f"{self.BASE_URL}/airports?{query}"

        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "TravelAIPlanner/1.0",
            },
        )

        with urllib.request.urlopen(request) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        airports = [
            airport
            for airport in data.get("data", [])
            if (
                airport.get("iata")
                and airport.get("type")
                in {"large_airport", "medium_airport"}
            )
        ]

        if not airports:
            return []

        if country:
            country_lower = country.strip().casefold()

            airports = [
                airport
                for airport in airports
                if (
                    airport.get("country_name")
                    and airport["country_name"].strip().casefold()
                    == country_lower
                )
            ]

        if not airports:
            return []

        city_lower = city.strip().casefold()

        municipality_matches = [
            airport
            for airport in airports
            if (
                airport.get("municipality")
                and airport["municipality"].strip().casefold()
                == city_lower
            )
        ]

        # Если нашли аэропорты непосредственно в городе,
        # используем все аэропорты города.
        if municipality_matches:
            airports = municipality_matches

        elif latitude is not None and longitude is not None:
            # Если аэропортов непосредственно в городе нет,
            # выбираем ближайший.
            airports.sort(
                key=lambda item: (
                    0
                    if item.get("type") == "large_airport"
                    else 1,
                    (
                        (item.get("latitude", 0) - latitude) ** 2
                        + (
                            item.get("longitude", 0)
                            - longitude
                        ) ** 2
                    ),
                )
            )

            airports = airports[:1]

        if latitude is not None and longitude is not None:
            airports.sort(
                key=lambda item: (
                    0
                    if item.get("type") == "large_airport"
                    else 1,
                    (
                        (item.get("latitude", 0) - latitude) ** 2
                        + (
                            item.get("longitude", 0)
                            - longitude
                        ) ** 2
                    ),
                )
            )

        return [
            self._format_airport(airport)
            for airport in airports
        ]

    @staticmethod
    def _format_airport(airport):
        return {
            "name": airport.get("name"),
            "iata_code": airport.get("iata"),
            "city": airport.get("municipality"),
            "country_code": airport.get("iso_country"),
            "latitude": airport.get("latitude"),
            "longitude": airport.get("longitude"),
        }


airport_provider = FreeAirportDbProvider()