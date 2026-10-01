from sqlalchemy import Column, Float, ForeignKey, Integer, JSON, String

from app.database import Base


class TripPlace(Base):
    __tablename__ = "trip_places"

    id = Column(Integer, primary_key=True, index=True)

    trip_id = Column(
        Integer,
        ForeignKey("trips.id"),
        nullable=False,
    )

    stop_id = Column(
        Integer,
        ForeignKey("trip_stops.id"),
        nullable=True,
        index=True,
    )


    external_id = Column(String(255), nullable=True)

    external_id = Column(String(255), nullable=True)
    source = Column(
        String(50),
        nullable=True,
        default="mock",
    )

    name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    country = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    rating = Column(Float, nullable=True)

    opening_hours = Column(JSON, nullable=True)

    opening_time = Column(String(10), nullable=True)
    closing_time = Column(String(10), nullable=True)

    visit_duration = Column(String(20), nullable=True)