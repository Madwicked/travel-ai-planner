from abc import ABC, abstractmethod
from math import sqrt


class AirportProvider(ABC):
    @abstractmethod
    def find_airport(
        self,
        city: str,
        latitude: float | None,
        longitude: float | None,
    ):
        pass


class MockAirportProvider(AirportProvider):
    def __init__(self):
        self.airports = [
            {
                "name": "Belgrade Nikola Tesla Airport",
                "iata_code": "BEG",
                "city": "Belgrade",
                "latitude": 44.8184,
                "longitude": 20.3091,
            },
            {
                "name": "Berlin Brandenburg Airport",
                "iata_code": "BER",
                "city": "Berlin",
                "latitude": 52.3667,
                "longitude": 13.5033,
            },
            {
                "name": "Budapest Ferenc Liszt International Airport",
                "iata_code": "BUD",
                "city": "Budapest",
                "latitude": 47.4369,
                "longitude": 19.2556,
            },
            {
                "name": "Leonardo da Vinci–Fiumicino Airport",
                "iata_code": "FCO",
                "city": "Rome",
                "latitude": 41.8003,
                "longitude": 12.2389,
            },
            {
                "name": "Paris Charles de Gaulle Airport",
                "iata_code": "CDG",
                "city": "Paris",
                "latitude": 49.0097,
                "longitude": 2.5479,
            },
        ]

    def find_airport(
        self,
        city: str,
        latitude: float | None,
        longitude: float | None,
    ):
        if latitude is None or longitude is None:
            return None

        city_airports = [
            airport
            for airport in self.airports
            if airport["city"].lower() == city.lower()
        ]

        if not city_airports:
            return None

        return min(
            city_airports,
            key=lambda airport: sqrt(
                (airport["latitude"] - latitude) ** 2
                + (airport["longitude"] - longitude) ** 2
            ),
        )


airport_provider = MockAirportProvider()