import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from dotenv import load_dotenv


load_dotenv()


class TransferProvider(ABC):
    @abstractmethod
    def get_transfer_options(
        self,
        *,
        from_type,
        from_code,
        to_type,
        to_code,
        outbound,
        adults,
        children=0,
        infants=0,
        inbound=None,
        language="en",
    ):
        pass


class MockTransferProvider(TransferProvider):
    def get_transfer_options(
        self,
        *,
        from_type,
        from_code,
        to_type,
        to_code,
        outbound,
        adults,
        children=0,
        infants=0,
        inbound=None,
        language="en",
    ):
        return []


class RealTransferProvider(TransferProvider):
    BASE_URL = "https://api.test.hotelbeds.com"

    def __init__(self):
        self.api_key = os.getenv(
            "HOTELBEDS_TRANSFER_API_KEY"
        )
        self.secret = os.getenv(
            "HOTELBEDS_TRANSFER_SECRET"
        )

        if not self.api_key:
            raise RuntimeError(
                "HOTELBEDS_TRANSFER_API_KEY is not set"
            )

        if not self.secret:
            raise RuntimeError(
                "HOTELBEDS_TRANSFER_SECRET is not set"
            )

    def _create_signature(self):
        timestamp = str(int(time.time()))

        value = (
            self.api_key
            + self.secret
            + timestamp
        )

        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

    def _request(
        self,
        *,
        from_type,
        from_code,
        to_type,
        to_code,
        outbound,
        adults,
        children,
        infants,
        inbound,
        language,
    ):
        if adults < 1:
            raise ValueError(
                "At least one adult passenger is required"
            )

        if children < 0:
            raise ValueError(
                "Children cannot be negative"
            )

        if infants < 0:
            raise ValueError(
                "Infants cannot be negative"
            )

        url = (
            f"{self.BASE_URL}"
            f"/transfer-api/1.0/availability/"
            f"{language}"
            f"/from/{from_type}/{from_code}"
            f"/to/{to_type}/{to_code}"
            f"/{outbound}"
        )

        if inbound:
            url += f"/{inbound}"

        url += (
            f"/{adults}"
            f"/{children}"
            f"/{infants}"
        )

        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Api-key": self.api_key,
                "X-Signature": self._create_signature(),
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=30,
            ) as response:
                response_data = response.read()

                return json.loads(
                    response_data.decode("utf-8")
                )

        except urllib.error.HTTPError as error:
            response_data = error.read()

            response_body = response_data.decode(
                "utf-8",
                errors="replace",
            )


            raise RuntimeError(
                f"Hotelbeds Transfers API error "
                f"{error.code}: {response_body}"
            ) from error

        except urllib.error.URLError as error:
            raise RuntimeError(
                f"Hotelbeds Transfers API connection error: "
                f"{error.reason}"
            ) from error

    def _build_options(self, data):
        services = data.get(
            "services",
            []
        )

        options = []

        for service in services:
            price = service.get(
                "price",
                {}
            )

            vehicle = service.get(
                "vehicle",
                {}
            )

            category = service.get(
                "category",
                {}
            )

            options.append(
                {
                    "id": service.get("id"),
                    "service_id": service.get(
                        "serviceId"
                    ),
                    "direction": service.get(
                        "direction"
                    ),
                    "transfer_type": service.get(
                        "transferType"
                    ),
                    "vehicle_code": vehicle.get(
                        "code"
                    ),
                    "vehicle_name": vehicle.get(
                        "name"
                    ),
                    "category_code": category.get(
                        "code"
                    ),
                    "category_name": category.get(
                        "name"
                    ),
                    "price": price.get(
                        "totalAmount"
                    ),
                    "currency": price.get(
                        "currencyId"
                    ),
                    "rate_key": service.get(
                        "rateKey"
                    ),
                    "cancellation_policies": service.get(
                        "cancellationPolicies",
                        []
                    ),
                    "factsheet_id": service.get(
                        "factsheetId"
                    ),
                    "extras": service.get(
                        "extras",
                        []
                    ),
                }
            )

        options.sort(
            key=lambda option: (
                option["price"]
                if option["price"] is not None
                else float("inf")
            )
        )

        return options

    def get_transfer_options(
        self,
        *,
        from_type,
        from_code,
        to_type,
        to_code,
        outbound,
        adults,
        children=0,
        infants=0,
        inbound=None,
        language="en",
    ):
        data = self._request(
            from_type=from_type,
            from_code=from_code,
            to_type=to_type,
            to_code=to_code,
            outbound=outbound,
            adults=adults,
            children=children,
            infants=infants,
            inbound=inbound,
            language=language,
        )


        return self._build_options(data)


transfer_provider = RealTransferProvider()