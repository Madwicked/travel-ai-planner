from abc import ABC, abstractmethod
from datetime import timedelta

from app.services.airport_provider import airport_provider


class TransportProvider(ABC):
    @abstractmethod
    def get_outbound_options(self, trip, search_date=None):
        pass

    @abstractmethod
    def get_return_options(self, trip, search_date=None):
        pass


class MockTransportProvider(TransportProvider):
    def get_outbound_options(self, trip, search_date=None):
        origin_airport = airport_provider.find_airport(
            trip.origin,
            trip.origin_latitude,
            trip.origin_longitude,
        )

        destination_airport = airport_provider.find_airport(
            trip.destination,
            trip.destination_latitude,
            trip.destination_longitude,
        )

        origin_location = (
            f"{trip.origin} ({origin_airport['iata_code']})"
            if origin_airport
            else trip.origin
        )

        destination_location = (
            f"{trip.destination} ({destination_airport['iata_code']})"
            if destination_airport
            else trip.destination
        )

        return [
            {
                "type": "Flight",
                "price": 86,
                "currency": "EUR",
                "duration": "2h 30m",
                "departure_date": trip.start_date,
                "departure_time": "10:25",
                "departure_location": origin_location,
                "arrival_date": trip.start_date,
                "arrival_time": "11:55",
                "arrival_location": destination_location,
                "booking_url": "https://example.com/flight/BEG-FCO",
            },
            {
                "type": "Bus",
                "price": 65,
                "currency": "EUR",
                "duration": "14h 30m",
                "departure_date": trip.start_date,
                "departure_time": "18:00",
                "departure_location": f"{trip.origin} Bus Station",
                "arrival_date": trip.end_date,
                "arrival_time": "08:30",
                "arrival_location": f"{trip.destination} Bus Station",
            },
            {
                "type": "Train",
                "price": 120,
                "currency": "EUR",
                "duration": "12h 15m",
                "departure_date": trip.start_date,
                "departure_time": "07:45",
                "departure_location": f"{trip.origin} Railway Station",
                "arrival_date": trip.start_date,
                "arrival_time": "20:00",
                "arrival_location": f"{trip.destination} Railway Station",
            },
        ]

    def get_return_options(self, trip):
        origin_airport = airport_provider.find_airport(
            trip.origin,
            trip.origin_latitude,
            trip.origin_longitude,
        )

        destination_airport = airport_provider.find_airport(
            trip.destination,
            trip.destination_latitude,
            trip.destination_longitude,
        )

        departure_location = (
            f"{trip.destination} ({destination_airport['iata_code']})"
            if destination_airport
            else trip.destination
        )

        arrival_location = (
            f"{trip.origin} ({origin_airport['iata_code']})"
            if origin_airport
            else trip.origin
        )

        return [
            {
                "type": "Flight",
                "price": 92,
                "currency": "EUR",
                "duration": "2h 25m",
                "departure_date": trip.end_date,
                "departure_time": "14:20",
                "departure_location": departure_location,
                "arrival_date": trip.end_date,
                "arrival_time": "16:45",
                "arrival_location": arrival_location,
                "booking_url": "https://example.com/flight/BEG-FCO",
            },
            {
                "type": "Bus",
                "price": 68,
                "currency": "EUR",
                "duration": "15h 10m",
                "departure_date": trip.end_date,
                "departure_time": "20:00",
                "departure_location": f"{trip.destination} Bus Station",
                "arrival_date": trip.end_date + timedelta(days=1),
                "arrival_time": "11:10",
                "arrival_location": f"{trip.origin} Bus Station",
            },
            {
                "type": "Train",
                "price": 115,
                "currency": "EUR",
                "duration": "12h 40m",
                "departure_date": trip.end_date,
                "departure_time": "08:15",
                "departure_location": f"{trip.destination} Railway Station",
                "arrival_date": trip.end_date,
                "arrival_time": "20:55",
                "arrival_location": f"{trip.origin} Railway Station",
            },
        ]


# transport_provider = MockTransportProvider()

from app.services.real_flight_provider import RealFlightProvider


transport_provider = RealFlightProvider()