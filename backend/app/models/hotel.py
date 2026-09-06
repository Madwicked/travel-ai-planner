from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String

from app.database import Base


class TripHotel(Base):
    __tablename__ = "trip_hotels"

    id = Column(Integer, primary_key=True, index=True)

    trip_id = Column(
        Integer,
        ForeignKey("trips.id"),
        nullable=False,
    )

    name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)

    price_per_night = Column(Float, nullable=False)
    nights = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)

    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)