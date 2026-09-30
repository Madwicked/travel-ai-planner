from app.services.transfer_provider import transfer_provider


class TransferService:
    @staticmethod
    def get_transfer_options(
        *,
        from_type: str,
        from_code: str,
        to_type: str,
        to_code: str,
        outbound: str,
        adults: int,
        children: int = 0,
        infants: int = 0,
        inbound: str | None = None,
        language: str = "en",
    ):
        return transfer_provider.get_transfer_options(
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