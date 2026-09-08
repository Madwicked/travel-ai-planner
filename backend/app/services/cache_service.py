import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.api_cache import ApiCache


class CacheService:
    def get(
        self,
        db: Session,
        trip_id: int,
        cache_type: str,
        direction: str | None = None,
    ):
        query = (
            db.query(ApiCache)
            .filter(
                ApiCache.trip_id == trip_id,
                ApiCache.cache_type == cache_type,
            )
        )

        if direction is None:
            query = query.filter(
                ApiCache.direction.is_(None)
            )
        else:
            query = query.filter(
                ApiCache.direction == direction
            )

        return query.first()

    def save(
        self,
        db: Session,
        trip_id: int,
        cache_type: str,
        data,
        direction: str | None = None,
    ):
        cache = self.get(
            db=db,
            trip_id=trip_id,
            cache_type=cache_type,
            direction=direction,
        )

        now = datetime.now(timezone.utc).replace(
            tzinfo=None
        )

        if cache:
            cache.data = json.dumps(data, default=str)
            cache.fetched_at = now
        else:
            cache = ApiCache(
                trip_id=trip_id,
                cache_type=cache_type,
                direction=direction,
                data=json.dumps(data, default=str),
                fetched_at=now,
            )

            db.add(cache)

        db.commit()
        db.refresh(cache)

        return cache

    def load_data(self, cache):
        return json.loads(cache.data)

    def is_expired(
        self,
        cache,
        ttl_minutes: int,
    ):
        now = datetime.now(timezone.utc).replace(
            tzinfo=None
        )

        expires_at = (
            cache.fetched_at
            + timedelta(minutes=ttl_minutes)
        )

        return now >= expires_at

    def get_expires_at(
        self,
        cache,
        ttl_minutes: int,
    ):
        return (
            cache.fetched_at
            + timedelta(minutes=ttl_minutes)
        )


cache_service = CacheService()