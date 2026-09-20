from datetime import date


from pydantic import BaseModel, Field, model_validator


class TripCreate(BaseModel):
    origin: str = Field(min_length=1)
    origin_country: str | None = None
    origin_latitude: float | None = None
    origin_longitude: float | None = None

    destination: str = Field(min_length=1)
    destination_country: str | None = None
    destination_latitude: float | None = None
    destination_longitude: float | None = None

    start_date: date
    end_date: date

    travelers: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")

        return self

class TripDatesUpdate(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")


class TransportUpdate(BaseModel):
    transport_type: str
    transport_price: float
    transport_duration: str
    transport_departure: str
    transport_arrival: str

    transport_departure_date: date
    transport_arrival_date: date
    transport_departure_location: str
    transport_arrival_location: str


class TripResponse(BaseModel):
    message: str
    trip_id: int
    trip: TripCreate


class TransportCreate(BaseModel):
    direction: str
    transport_type: str
    transport_price: float
    currency: str

    segments: list[dict] = Field(default_factory=list)
    stops: int = 0
    layovers: list[dict] = Field(default_factory=list)

    transport_duration: str

    departure_date: date
    departure_time: str
    departure_location: str

    arrival_date: date
    arrival_time: str
    arrival_location: str


class HotelCreate(BaseModel):
    name: str
    city: str
    address: str

    price_per_night: float
    nights: int

    total_price: float
    currency: str

    check_in: date
    check_out: date


class PlaceCreate(BaseModel):
    external_id: str | None = None
    source: str = "mock"

    name: str
    city: str
    country: str | None = None
    category: str
    address: str | None = None

    latitude: float | None = None
    longitude: float | None = None


    rating: float | None = None

    opening_hours: dict | None = None

    opening_time: str | None = None
    closing_time: str | None = None

    visit_duration: str | None = None

class CurrencyUpdate(BaseModel):
    user_currency: str

class FoodPreferenceUpdate(BaseModel):
    food_preference: str