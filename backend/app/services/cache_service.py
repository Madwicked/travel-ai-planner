import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.api_cache import ApiCache


class CacheService:
    def get(
        self,
        db: Session,
        trip_id: int,
        cache_type: str,
        direction: str | None = None,
        search_date=None,
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

        if search_date is not None:
            query = query.filter(
                ApiCache.search_date == search_date
            )

        return query.first()

    def save(
        self,
        db: Session,
        trip_id: int,
        cache_type: str,
        data,
        direction: str | None = None,
        search_date=None,
    ):
        cache = self.get(
            db=db,
            trip_id=trip_id,
            cache_type=cache_type,
            direction=direction,
            search_date=search_date,
        )

        now = datetime.now(timezone.utc).replace(
            tzinfo=None
        )

        if cache:
            cache.data = json.dumps(
                data,
                default=str,
            )
            cache.fetched_at = now

            db.commit()
            db.refresh(cache)

            return cache

        cache = ApiCache(
            trip_id=trip_id,
            cache_type=cache_type,
            direction=direction,
            search_date=search_date,
            data=json.dumps(
                data,
                default=str,
            ),
            fetched_at=now,
        )

        db.add(cache)

        try:
            db.commit()
            db.refresh(cache)

            return cache

        except IntegrityError:
            db.rollback()

            cache = self.get(
                db=db,
                trip_id=trip_id,
                cache_type=cache_type,
                direction=direction,
                search_date=search_date,
            )

            if cache is None:
                raise

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