import gzip
import hashlib
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


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


class RealHotelProvider(HotelProvider):
    BASE_URL = (
        "https://api-mtls.test.hotelbeds.com"
    )

    def __init__(self):
        self.api_key = os.getenv(
            "HOTELBEDS_API_KEY"
        )
        self.secret = os.getenv(
            "HOTELBEDS_SECRET"
        )
        self.cert_password = os.getenv(
            "HOTELBEDS_CERT_PASSWORD"
        )

        backend_dir = Path(__file__).resolve().parents[2]

        self.cert_path = (
            backend_dir
            / "certs"
            / "hotelbeds"
            / "hotelbeds.pem"
        )

        self.key_path = (
            backend_dir
            / "certs"
            / "hotelbeds"
            / "hotelbeds_private.key"
        )

        if not self.api_key:
            raise RuntimeError(
                "HOTELBEDS_API_KEY is not set"
            )

        if not self.secret:
            raise RuntimeError(
                "HOTELBEDS_SECRET is not set"
            )

        if not self.cert_password:
            raise RuntimeError(
                "HOTELBEDS_CERT_PASSWORD is not set"
            )

        if not self.cert_path.exists():
            raise RuntimeError(
                f"Hotelbeds certificate not found: "
                f"{self.cert_path}"
            )

        if not self.key_path.exists():
            raise RuntimeError(
                f"Hotelbeds private key not found: "
                f"{self.key_path}"
            )

    def _create_signature(self):
        timestamp = str(
            int(time.time())
        )

        value = (
            self.api_key
            + self.secret
            + timestamp
        )

        return hashlib.sha256(
            value.encode()
        ).hexdigest()

    def _create_ssl_context(self):
        context = ssl.create_default_context()

        context.load_cert_chain(
            certfile=str(self.cert_path),
            keyfile=str(self.key_path),
            password=self.cert_password,
        )

        return context

    def _request(self, trip):
        if (
            trip.destination_latitude is None
            or trip.destination_longitude is None
        ):
            raise ValueError(
                "Destination coordinates are required "
                "for Hotelbeds hotel search"
            )

        number_of_nights = (
            trip.end_date - trip.start_date
        ).days

        if number_of_nights <= 0:
            raise ValueError(
                "Trip must be at least one night"
            )

        payload = {
            "stay": {
                "checkIn": trip.start_date.strftime(
                    "%Y-%m-%d"
                ),
                "checkOut": trip.end_date.strftime(
                    "%Y-%m-%d"
                ),
            },
            "occupancies": [
                {
                    "rooms": 1,
                    "adults": 2,
                    "children": 0,
                }
            ],
            "geolocation": {
                "latitude": trip.destination_latitude,
                "longitude": trip.destination_longitude,
                "radius": 20,
                "unit": "km",
            },
        }

        body = json.dumps(
            payload
        ).encode("utf-8")

        request = urllib.request.Request(
            f"{self.BASE_URL}/hotel-api/1.0/hotels",
            data=body,
            method="POST",
            headers={
                "Api-key": self.api_key,
                "X-Signature": self._create_signature(),
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Accept-Encoding": "gzip",
            },
        )

        ssl_context = self._create_ssl_context()

        try:
            with urllib.request.urlopen(
                    request,
                    context=ssl_context,
                    timeout=30,
            ) as response:
                response_data = response.read()

                if response.headers.get(
                        "Content-Encoding"
                ) == "gzip":
                    response_data = gzip.decompress(
                        response_data
                    )

                return json.loads(
                    response_data.decode(
                        "utf-8"
                    )
                )


        except urllib.error.HTTPError as error:

            response_data = error.read()

            if error.headers.get(

                    "Content-Encoding"

            ) == "gzip":
                response_data = gzip.decompress(

                    response_data

                )

            response_body = response_data.decode(

                "utf-8",

                errors="replace",

            )

            raise RuntimeError(

                f"Hotelbeds API error "

                f"{error.code}: {response_body}"

            ) from error

    def _build_options(
        self,
        data,
        trip,
    ):
        hotels_data = data.get(
            "hotels",
            {}
        )

        hotels = hotels_data.get(
            "hotels",
            []
        )

        number_of_nights = (
            trip.end_date - trip.start_date
        ).days

        options = []

        for hotel in hotels:
            rooms = hotel.get(
                "rooms",
                []
            )

            rates = []

            for room in rooms:
                rates.extend(
                    room.get(
                        "rates",
                        []
                    )
                )

            valid_rates = []

            for rate in rates:
                net = rate.get("net")

                if net is None:
                    continue

                try:
                    total_price = float(net)
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                valid_rates.append(
                    total_price
                )

            if not valid_rates:
                continue

            total_price = min(
                valid_rates
            )

            price_per_night = (
                total_price
                / number_of_nights
            )

            options.append(
                {
                    "name": hotel.get(
                        "name",
                        "Hotel",
                    ),
                    "city": hotel.get(
                        "destinationName",
                        trip.destination,
                    ),
                    "address": "",
                    "price_per_night": (
                        round(
                            price_per_night,
                            2,
                        )
                    ),
                    "nights": number_of_nights,
                    "total_price": round(
                        total_price,
                        2,
                    ),
                    "check_in": (
                        trip.start_date
                    ),
                    "check_out": (
                        trip.end_date
                    ),
                }
            )

        options.sort(
            key=lambda option: option[
                "total_price"
            ]
        )

        return options

    def get_hotel_options(self, trip):
        data = self._request(trip)

        return self._build_options(
            data,
            trip,
        )

hotel_provider = MockHotelProvider()

# hotel_provider = RealHotelProvider()