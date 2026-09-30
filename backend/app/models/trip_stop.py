from sqlalchemy import Column, Date, Float, Integer, String

from app.database import Base


class TripStop(Base):
    __tablename__ = "trip_stops"

    id = Column(Integer, primary_key=True, index=True)

    trip_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    city = Column(
        String(255),
        nullable=False,
    )

    country = Column(
        String(100),
        nullable=True,
    )

    latitude = Column(
        Float,
        nullable=True,
    )

    longitude = Column(
        Float,
        nullable=True,
    )

    start_date = Column(
        Date,
        nullable=False,
    )

    end_date = Column(
        Date,
        nullable=False,
    )

    sort_order = Column(
        Integer,
        nullable=False,
        default=0,
    )