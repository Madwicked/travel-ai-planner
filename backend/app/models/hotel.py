from sqlalchemy import Column, Date, Float, ForeignKey, Integer, JSON, String

from app.database import Base


class TripHotel(Base):
    __tablename__ = "trip_hotels"

    id = Column(Integer, primary_key=True, index=True)

    trip_id = Column(
        Integer,
        ForeignKey("trips.id"),
        nullable=False,
    )

    stop_id = Column(Integer, ForeignKey("trip_stops.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    price_per_night = Column(Float, nullable=False)
    nights = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)

    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)

    hotel_data = Column(JSON, nullable=False, default=dict)