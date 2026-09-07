from abc import ABC, abstractmethod


class LocationProvider(ABC):
    @abstractmethod
    def search_cities(self, query: str):
        pass


class MockLocationProvider(LocationProvider):
    def search_cities(self, query: str):
        cities = [
            {
                "name": "Belgrade",
                "country": "Serbia",
                "country_code": "RS",
                "latitude": 44.7866,
                "longitude": 20.4489,
            },
            {
                "name": "Berlin",
                "country": "Germany",
                "country_code": "DE",
                "latitude": 52.5200,
                "longitude": 13.4050,
            },
            {
                "name": "Budapest",
                "country": "Hungary",
                "country_code": "HU",
                "latitude": 47.4979,
                "longitude": 19.0402,
            },
            {
                "name": "Rome",
                "country": "Italy",
                "country_code": "IT",
                "latitude": 41.9028,
                "longitude": 12.4964,
            },
            {
                "name": "Paris",
                "country": "France",
                "country_code": "FR",
                "latitude": 48.8566,
                "longitude": 2.3522,
            },
        ]

        query = query.strip().lower()

        return [
            city
            for city in cities
            if city["name"].lower().startswith(query)
        ]


location_provider = MockLocationProvider()