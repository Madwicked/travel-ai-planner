from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.database import Base


class HotelRoom(Base):
    __tablename__ = "hotel_rooms"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    hotel_content_id = Column(
        Integer,
        ForeignKey("hotel_contents.id"),
        nullable=False,
        index=True,
    )

    room_code = Column(
        String(100),
        nullable=False,
        index=True,
    )

    room_type = Column(
        String(100),
        nullable=True,
    )

    characteristic_code = Column(
        String(100),
        nullable=True,
    )

    pms_room_code = Column(
        String(100),
        nullable=True,
    )

    min_pax = Column(
        Integer,
        nullable=True,
    )

    max_pax = Column(
        Integer,
        nullable=True,
    )

    max_adults = Column(
        Integer,
        nullable=True,
    )

    max_children = Column(
        Integer,
        nullable=True,
    )

    room_facilities = Column(
        Text,
        nullable=True,
    )

    room_stays = Column(
        Text,
        nullable=True,
    )