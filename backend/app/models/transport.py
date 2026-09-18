from sqlalchemy import Column, Date, Float, ForeignKey, Integer, JSON, String

from app.database import Base


class TripTransport(Base):
    __tablename__ = "trip_transports"

    id = Column(Integer, primary_key=True, index=True)

    trip_id = Column(
        Integer,
        ForeignKey("trips.id"),
        nullable=False,
    )

    parent_transport_id = Column(
        Integer,
        ForeignKey("trip_transports.id"),
        nullable=True,
    )

    direction = Column(String(20), nullable=False)

    transport_type = Column(String(50), nullable=False)
    transport_price = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    segments = Column(JSON, nullable=True)
    stops = Column(Integer, nullable=True)
    layovers = Column(JSON, nullable=True)
    transport_duration = Column(String(50), nullable=False)

    departure_date = Column(Date, nullable=False)
    departure_time = Column(String(10), nullable=False)
    departure_location = Column(String(255), nullable=False)

    arrival_date = Column(Date, nullable=False)
    arrival_time = Column(String(10), nullable=False)
    arrival_location = Column(String(255), nullable=False)