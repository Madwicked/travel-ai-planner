from abc import ABC, abstractmethod


class HotelProvider(ABC):
    @abstractmethod
    def get_hotel_options(self, trip):
        pass


class MockHotelProvider(HotelProvider):
    def get_hotel_options(self, trip):
        number_of_nights = (
            trip.end_date - trip.start_date
        ).days

        return [
            {
                "name": "Rome Central Hotel",
                "city": trip.destination,
                "address": "Via Roma 25",
                "price_per_night": 85,
                "nights": number_of_nights,
                "total_price": 85 * number_of_nights,
                "check_in": trip.start_date,
                "check_out": trip.end_date,
            },
            {
                "name": "Hotel Imperial",
                "city": trip.destination,
                "address": "Via Nazionale 42",
                "price_per_night": 110,
                "nights": number_of_nights,
                "total_price": 110 * number_of_nights,
                "check_in": trip.start_date,
                "check_out": trip.end_date,
            },
            {
                "name": "Budget Stay Rome",
                "city": trip.destination,
                "address": "Via Milano 18",
                "price_per_night": 65,
                "nights": number_of_nights,
                "total_price": 65 * number_of_nights,
                "check_in": trip.start_date,
                "check_out": trip.end_date,
            },
        ]


hotel_provider = MockHotelProvider()