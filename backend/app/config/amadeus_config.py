import os


AMADEUS_CLIENT_ID = os.getenv(
    "AMADEUS_CLIENT_ID",
)

AMADEUS_CLIENT_SECRET = os.getenv(
    "AMADEUS_CLIENT_SECRET",
)

AMADEUS_BASE_URL = os.getenv(
    "AMADEUS_BASE_URL",
    "https://test.api.amadeus.com",
)