from sqlalchemy import Column, Date, Float, Integer, String, Text
from app.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)

    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    travelers = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    interests = Column(Text, nullable=False)

    transport_type = Column(String(50), nullable=True)
    transport_price = Column(Float, nullable=True)
    transport_duration = Column(String(50), nullable=True)
    transport_departure = Column(String(10), nullable=True)
    transport_arrival = Column(String(10), nullable=True)

    transport_departure_date = Column(Date, nullable=True)
    transport_arrival_date = Column(Date, nullable=True)

    transport_departure_location = Column(String(255), nullable=True)
    transport_arrival_location = Column(String(255), nullable=True)