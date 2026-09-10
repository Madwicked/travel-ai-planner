from abc import ABC, abstractmethod


class PlaceProvider(ABC):
    @abstractmethod
    def get_place_options(self, trip):
        pass


class MockPlaceProvider(PlaceProvider):
    def get_place_options(self, trip):
        return [
            {
                "external_id": "mock-colosseum",
                "source": "mock",
                "name": "Colosseum",
                "city": trip.destination,
                "category": "Culture",
                "address": "Piazza del Colosseo",
                "latitude": 41.8902,
                "longitude": 12.4922,
                "rating": 4.7,
                "opening_hours": {
                    "monday": ["08:30", "19:00"],
                    "tuesday": ["08:30", "19:00"],
                    "wednesday": ["08:30", "19:00"],
                    "thursday": ["08:30", "19:00"],
                    "friday": ["08:30", "19:00"],
                    "saturday": ["08:30", "19:00"],
                    "sunday": ["08:30", "19:00"],
                },
                "opening_time": "08:30",
                "closing_time": "19:00",
                "visit_duration": "2h",
            },
            {
                "external_id": "mock-roman-forum",
                "source": "mock",
                "name": "Roman Forum",
                "city": trip.destination,
                "category": "Culture",
                "address": "Via della Salara Vecchia 5/6",
                "latitude": 41.8925,
                "longitude": 12.4853,
                "rating": 4.8,
                "opening_hours": {
                    "monday": ["09:00", "19:15"],
                    "tuesday": ["09:00", "19:15"],
                    "wednesday": ["09:00", "19:15"],
                    "thursday": ["09:00", "19:15"],
                    "friday": ["09:00", "19:15"],
                    "saturday": ["09:00", "19:15"],
                    "sunday": ["09:00", "19:15"],
                },
                "opening_time": "09:00",
                "closing_time": "19:15",
                "visit_duration": "1h 30m",
            },
            {
                "external_id": "mock-trevi-fountain",
                "source": "mock",
                "name": "Trevi Fountain",
                "city": trip.destination,
                "category": "Sightseeing",
                "address": "Piazza di Trevi",
                "latitude": 41.9009,
                "longitude": 12.4833,
                "rating": 4.8,
                "opening_hours": {
                    "monday": ["00:00", "23:59"],
                    "tuesday": ["00:00", "23:59"],
                    "wednesday": ["00:00", "23:59"],
                    "thursday": ["00:00", "23:59"],
                    "friday": ["00:00", "23:59"],
                    "saturday": ["00:00", "23:59"],
                    "sunday": ["00:00", "23:59"],
                },
                "opening_time": "00:00",
                "closing_time": "23:59",
                "visit_duration": "30m",
            },
            {
                "external_id": "mock-villa-borghese",
                "source": "mock",
                "name": "Villa Borghese",
                "city": trip.destination,
                "category": "Nature",
                "address": "Piazzale Scipione Borghese 5",
                "latitude": 41.9142,
                "longitude": 12.4923,
                "rating": 4.6,
                "opening_hours": {
                    "monday": ["09:00", "19:00"],
                    "tuesday": ["09:00", "19:00"],
                    "wednesday": ["09:00", "19:00"],
                    "thursday": ["09:00", "19:00"],
                    "friday": ["09:00", "19:00"],
                    "saturday": ["09:00", "19:00"],
                    "sunday": ["09:00", "19:00"],
                },
                "opening_time": "09:00",
                "closing_time": "19:00",
                "visit_duration": "2h",
            },
            {
                "external_id": "mock-pantheon",
                "source": "mock",
                "name": "Pantheon",
                "city": trip.destination,
                "category": "Culture",
                "address": "Piazza della Rotonda",
                "latitude": 41.8986,
                "longitude": 12.4769,
                "rating": 4.7,
                "opening_hours": {
                    "monday": ["09:00", "19:00"],
                    "tuesday": ["09:00", "19:00"],
                    "wednesday": ["09:00", "19:00"],
                    "thursday": ["09:00", "19:00"],
                    "friday": ["09:00", "19:00"],
                    "saturday": ["09:00", "19:00"],
                    "sunday": ["09:00", "19:00"],
                },
                "opening_time": "09:00",
                "closing_time": "19:00",
                "visit_duration": "1h",
            },
        ]

from app.services.real_place_provider import RealPlaceProvider


place_provider = RealPlaceProvider()

# place_provider = MockPlaceProvider()