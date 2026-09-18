import hashlib
import time
from typing import Any

import requests


class HotelContentProvider:
    BASE_URL = "https://api.test.hotelbeds.com"
    ENDPOINT = "/hotel-content-api/1.0/hotels"

    def __init__(
        self,
        api_key: str,
        secret: str,
    ):
        self.api_key = api_key
        self.secret = secret

    def _signature(self) -> str:
        timestamp = str(int(time.time()))

        raw = f"{self.api_key}{self.secret}{timestamp}"

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    def _headers(self) -> dict[str, str]:
        return {
            "Api-key": self.api_key,
            "X-Signature": self._signature(),
            "Accept": "application/json",
        }

    def get_hotels_page(
        self,
        from_hotel: int = 1,
        to_hotel: int = 1000,
        language: str = "ENG",
        last_update_time: str | None = None,
    ) -> dict[str, Any]:

        params: dict[str, Any] = {
            "fields": "all",
            "language": language,
            "from": from_hotel,
            "to": to_hotel,
        }

        if last_update_time:
            params["lastUpdateTime"] = last_update_time

        response = requests.get(
            f"{self.BASE_URL}{self.ENDPOINT}",
            headers=self._headers(),
            params=params,
            timeout=60,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Hotelbeds Content API error "
                f"{response.status_code}: "
                f"{response.text}"
            )

        # response.raise_for_status()

        return response.json()

    # def get_all_hotels(
    #     self,
    #     language: str = "ENG",
    # ) -> list[dict[str, Any]]:
    #
    #     hotels: list[dict[str, Any]] = []
    #
    #     page_size = 1000
    #     start = 1
    #
    #     while True:
    #         data = self.get_hotels_page(
    #             from_hotel=start,
    #             to_hotel=start + page_size - 1,
    #             language=language,
    #         )
    #
    #         page_hotels = data.get("hotels", [])
    #
    #         if not page_hotels:
    #             break
    #
    #         hotels.extend(page_hotels)
    #
    #         if len(page_hotels) < page_size:
    #             break
    #
    #         start += page_size
    #
    #     return hotels
###########
    def get_all_hotels(
            self,
            language: str = "ENG",
            limit: int | None = None,
    ) -> list[dict[str, Any]]:
        hotels: list[dict[str, Any]] = []

        page_size = 1000
        start = 1

        if limit is not None:
            page_size = min(limit, 1000)

        while True:
            end = start + page_size - 1

            data = self.get_hotels_page(
                from_hotel=start,
                to_hotel=end,
                language=language,
            )

            page_hotels = data.get(
                "hotels",
                []
            )

            if not page_hotels:
                break

            hotels.extend(page_hotels)

            if limit is not None:
                hotels = hotels[:limit]
                break

            if len(page_hotels) < page_size:
                break

            start += page_size

        return hotels
###############
    def get_updated_hotels(
        self,
        last_update_time: str,
        language: str = "ENG",
    ) -> list[dict[str, Any]]:

        hotels: list[dict[str, Any]] = []

        page_size = 1000
        start = 1

        while True:
            data = self.get_hotels_page(
                from_hotel=start,
                to_hotel=start + page_size - 1,
                language=language,
                last_update_time=last_update_time,
            )

            page_hotels = data.get("hotels", [])

            if not page_hotels:
                break

            hotels.extend(page_hotels)

            if len(page_hotels) < page_size:
                break

            start += page_size

        return hotels