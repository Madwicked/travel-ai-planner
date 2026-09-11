from sqlalchemy import Column, Date, Float, Integer, String, Text
from app.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)

    origin = Column(String(255), nullable=False)
    origin_country = Column(String(100), nullable=True)
    origin_latitude = Column(Float, nullable=True)
    origin_longitude = Column(Float, nullable=True)

    destination = Column(String(255), nullable=False)
    destination_country = Column(String(100), nullable=True)
    destination_currency = Column(
        String(3),
        nullable=True,
    )

    user_currency = Column(
        String(3),
        nullable=True,
    )
    destination_latitude = Column(Float, nullable=True)
    destination_longitude = Column(Float, nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    travelers = Column(Integer, nullable=False)
    food_preference = Column(String(50), nullable=True)
    budget = Column(Float, nullable=True)
    interests = Column(Text, nullable=True)

    transport_type = Column(String(50), nullable=True)
    transport_price = Column(Float, nullable=True)
    transport_duration = Column(String(50), nullable=True)
    transport_departure = Column(String(10), nullable=True)
    transport_arrival = Column(String(10), nullable=True)

    transport_departure_date = Column(Date, nullable=True)
    transport_arrival_date = Column(Date, nullable=True)

    transport_departure_location = Column(String(255), nullable=True)
    transport_arrival_location = Column(String(255), nullable=True)