from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class ApiCache(Base):
    __tablename__ = "api_cache"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    trip_id = Column(
        Integer,
        ForeignKey("trips.id"),
        nullable=False,
        index=True,
    )

    cache_type = Column(
        String(50),
        nullable=False,
    )

    direction = Column(
        String(20),
        nullable=True,
    )

    data = Column(
        Text,
        nullable=False,
    )

    fetched_at = Column(
        DateTime,
        nullable=False,
    )