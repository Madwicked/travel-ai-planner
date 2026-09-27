from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base


class HotelContent(Base):
    __tablename__ = "hotel_contents"

    id = Column(Integer, primary_key=True, index=True)

    hotel_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
    )

    category_code = Column(
        String(50),
        nullable=True,
    )

    category_name = Column(
        String(255),
        nullable=True,
    )

    accommodation_type = Column(
        String(100),
        nullable=True,
        index=True,
    )

    country_code = Column(
        String(10),
        nullable=True,
    )

    destination_code = Column(
        String(50),
        nullable=True,
        index=True,
    )

    zone_code = Column(
        String(50),
        nullable=True,
    )

    city = Column(
        String(255),
        nullable=True,
    )

    address = Column(
        String(500),
        nullable=True,
    )

    latitude = Column(
        String(50),
        nullable=True,
    )

    longitude = Column(
        String(50),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    facilities = Column(
        Text,
        nullable=True,
    )

    rooms = Column(
        Text,
        nullable=True,
    )

    pets_allowed = Column(
        Boolean,
        nullable=True,
    )

    adults_only = Column(
        Boolean,
        nullable=True,
    )