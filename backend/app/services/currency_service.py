from datetime import datetime, timedelta
from decimal import Decimal

import requests


class CurrencyService:
    RATES_URL = "https://api.frankfurter.dev/v2/rate"

    CACHE_TTL = timedelta(hours=1)

    _rates_cache: dict[tuple[str, str], tuple[datetime, Decimal]] = {}

    @classmethod
    def _get_rate(
        cls,
        from_currency: str,
        to_currency: str,
    ) -> Decimal:
        cache_key = (
            from_currency,
            to_currency,
        )

        cached = cls._rates_cache.get(cache_key)

        if cached is not None:
            cached_at, rate = cached

            if datetime.utcnow() - cached_at < cls.CACHE_TTL:
                return rate

        response = requests.get(
            f"{cls.RATES_URL}/{from_currency.lower()}/{to_currency.lower()}",
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        rate = data.get("rate")

        if rate is None:
            raise ValueError(
                f"Exchange rate not available: "
                f"{from_currency} -> {to_currency}"
            )

        rate = Decimal(str(rate))

        cls._rates_cache[cache_key] = (
            datetime.utcnow(),
            rate,
        )

        return rate

    @classmethod
    def convert(
        cls,
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> float:
        if not from_currency:
            raise ValueError(
                "Source currency is required"
            )

        if not to_currency:
            raise ValueError(
                "Target currency is required"
            )

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return round(amount, 2)

        rate = cls._get_rate(
            from_currency=from_currency,
            to_currency=to_currency,
        )

        result = (
            Decimal(str(amount))
            * rate
        )

        return float(
            result.quantize(
                Decimal("0.01")
            )
        )


currency_service = CurrencyService()