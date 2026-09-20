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

from app.database import SessionLocal
from app.models.hotel_content import HotelContent


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
                "currency": "EUR",
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
                "currency": "EUR",
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
                "currency": "EUR",
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
            / "hotelbeds_final.pem"
        )

        self.key_path = (
            backend_dir
            / "certs"
            / "hotelbeds"
            / "hotelbeds_final_private.key"
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

    def _get_content_data(
        self,
        hotel_code,
    ):
        if not hotel_code:
            return None

        db = SessionLocal()

        try:
            return (
                db.query(HotelContent)
                .filter(
                    HotelContent.hotel_code
                    == str(hotel_code)
                )
                .first()
            )
        finally:
            db.close()

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
            hotel_code = hotel.get(
                "code"
            )

            content = self._get_content_data(
                hotel_code
            )

            rooms = hotel.get(
                "rooms",
                []
            )

            rate_options = []

            for room in rooms:
                room_name = room.get(
                    "name",
                    "Room",
                )

                rates = room.get(
                    "rates",
                    []
                )

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

                    cancellation_policies = rate.get(
                        "cancellationPolicies",
                        []
                    )

                    is_refundable = bool(
                        cancellation_policies
                    ) and rate.get(
                        "rateClass"
                    ) != "NRF"

                    taxes = rate.get(
                        "taxes",
                        {}
                    )

                    tax_options = taxes.get(
                        "taxes",
                        []
                    )

                    total_taxes = 0.0

                    for tax in tax_options:
                        tax_amount = tax.get(
                            "amount"
                        )

                        try:
                            total_taxes += float(
                                tax_amount
                            )
                        except (
                            TypeError,
                            ValueError,
                        ):
                            continue

                    rate_options.append(
                        {
                            "room_name": room_name,
                            "board_code": rate.get(
                                "boardCode",
                                "",
                            ),
                            "board_name": rate.get(
                                "boardName",
                                "",
                            ),
                            "rate_class": rate.get(
                                "rateClass",
                                "",
                            ),
                            "rate_type": rate.get(
                                "rateType",
                                "",
                            ),
                            "payment_type": rate.get(
                                "paymentType",
                                "",
                            ),
                            "total_price": round(
                                total_price,
                                2,
                            ),
                            "price_per_night": round(
                                total_price
                                / number_of_nights,
                                2,
                            ),
                            "currency": hotels_data.get(
                                "currency",
                                "EUR",
                            ),
                            "allotment": rate.get(
                                "allotment",
                                0,
                            ),
                            "rooms": rate.get(
                                "rooms",
                                0,
                            ),
                            "adults": rate.get(
                                "adults",
                                0,
                            ),
                            "children": rate.get(
                                "children",
                                0,
                            ),
                            "refundable": is_refundable,
                            "cancellation_policies": (
                                cancellation_policies
                            ),
                            "taxes": tax_options,
                            "taxes_included": taxes.get(
                                "allIncluded",
                                False,
                            ),
                            "total_taxes": round(
                                total_taxes,
                                2,
                            ),
                        }
                    )

            if not rate_options:
                continue

            min_rate = min(
                rate["total_price"]
                for rate in rate_options
            )

            options.append(
                {
                    "hotel_code": hotel_code,
                    "name": hotel.get(
                        "name",
                        "Hotel",
                    ),
                    "city": (
                        content.city
                        if content
                        and content.city
                        else hotel.get(
                            "destinationName",
                            trip.destination,
                        )
                    ),
                    "address": (
                        content.address
                        if content
                        and content.address
                        else hotel.get(
                            "address",
                            "",
                        )
                    ),
                    "description": (
                        content.description
                        if content
                        else None
                    ),
                    "category_code": (
                        content.category_code
                        if content
                        else hotel.get(
                            "categoryCode"
                        )
                    ),
                    "category_name": (
                        content.category_name
                        if content
                        else hotel.get(
                            "categoryName"
                        )
                    ),
                    "accommodation_type": (
                        content.accommodation_type
                        if content
                        else None
                    ),
                    "facilities": (
                        json.loads(
                            content.facilities
                        )
                        if content
                        and content.facilities
                        else []
                    ),
                    "pets_allowed": (
                        content.pets_allowed
                        if content
                        else None
                    ),
                    "adults_only": (
                        content.adults_only
                        if content
                        else None
                    ),
                    "latitude": (
                        content.latitude
                        if content
                        else hotel.get(
                            "latitude"
                        )
                    ),
                    "longitude": (
                        content.longitude
                        if content
                        else hotel.get(
                            "longitude"
                        ),
                    ),
                    "price_per_night": round(
                        min_rate
                        / number_of_nights,
                        2,
                    ),
                    "currency": hotels_data.get(
                        "currency",
                        "EUR",
                    ),
                    "nights": number_of_nights,
                    "total_price": round(
                        min_rate,
                        2,
                    ),
                    "check_in": trip.start_date,
                    "check_out": trip.end_date,
                    "rate_options": rate_options,
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


# hotel_provider = MockHotelProvider()

hotel_provider = RealHotelProvider()