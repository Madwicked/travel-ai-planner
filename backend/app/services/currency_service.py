from decimal import Decimal


class CurrencyService:

    RATES_TO_EUR = {
        "EUR": Decimal("1"),
        "USD": Decimal("0.86"),
        "GBP": Decimal("1.16"),
        "RSD": Decimal("0.00853"),
        "CHF": Decimal("1.09"),
        "CAD": Decimal("0.63"),
        "AUD": Decimal("0.57"),
        "JPY": Decimal("0.0058"),
        "CNY": Decimal("0.12"),
        "TRY": Decimal("0.022"),
        "AED": Decimal("0.234"),
        "THB": Decimal("0.027"),
    }

    @classmethod
    def convert(
        cls,
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> float:
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return round(amount, 2)

        if from_currency not in cls.RATES_TO_EUR:
            raise ValueError(
                f"Unsupported source currency: {from_currency}"
            )

        if to_currency not in cls.RATES_TO_EUR:
            raise ValueError(
                f"Unsupported target currency: {to_currency}"
            )

        amount_eur = (
            Decimal(str(amount))
            * cls.RATES_TO_EUR[from_currency]
        )

        result = (
            amount_eur
            / cls.RATES_TO_EUR[to_currency]
        )

        return float(result.quantize(Decimal("0.01")))


currency_service = CurrencyService()