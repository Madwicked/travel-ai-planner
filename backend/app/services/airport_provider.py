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


class FreeAirportDbProvider(AirportProvider):

    BASE_URL = "https://api.freeairportdb.com/v1"

    def find_airports(self, city, latitude, longitude):
        if latitude is not None and longitude is not None:
            airports = self._find_nearby(
                city=city,
                latitude=latitude,
                longitude=longitude,
            )

            if airports:
                return airports

        return self._find_by_city(
            city=city,
            latitude=latitude,
            longitude=longitude,
        )

    def _find_nearby(self, city, latitude, longitude):
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
            if airport.get("iata")
            and airport.get("type")
            in {"large_airport", "medium_airport"}
        ]

        if not airports:
            return []

        city_lower = city.lower()

        city_related_airports = [
            airport
            for airport in airports
            if airport.get("municipality")
               and city_lower in airport["municipality"].lower()
        ]

        if city_related_airports:
            airports = city_related_airports

        airports.sort(
            key=lambda item: item.get(
                "distance_km",
                float("inf"),
            )
        )

        return [
            self._format_airport(airport)
            for airport in airports
        ]

    def _find_by_city(
        self,
        city,
        latitude=None,
        longitude=None,
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
            if airport.get("iata")
            and airport.get("type")
            in {"large_airport", "medium_airport"}
        ]

        if not airports:
            return []

        city_lower = city.lower()

        municipality_matches = [
            airport
            for airport in airports
            if airport.get("municipality")
            and airport["municipality"].lower() == city_lower
        ]

        if municipality_matches:
            airports = municipality_matches

        if latitude is not None and longitude is not None:
            airports.sort(
                key=lambda item: (
                    (item.get("latitude", 0) - latitude) ** 2
                    + (item.get("longitude", 0) - longitude) ** 2
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
            "latitude": airport.get("latitude"),
            "longitude": airport.get("longitude"),
        }


airport_provider = FreeAirportDbProvider()