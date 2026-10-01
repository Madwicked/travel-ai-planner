from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.routing import (
    get_optimized_walking_route,
    get_optimized_walking_route_for_trip,
    get_walking_route,
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix="/api/routing",
    tags=["routing"],
)


@router.get("/walking")
def walking_route(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
):
    try:
        return get_walking_route(
            origin_latitude=origin_latitude,
            origin_longitude=origin_longitude,
            destination_latitude=destination_latitude,
            destination_longitude=destination_longitude,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )

@router.post("/walking/optimized")
def optimized_walking_route(
    points: list[tuple[float, float]],
):
    try:
        return get_optimized_walking_route(
            points=points,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )

@router.get("/trips/{trip_id}/walking/optimized")
def optimized_trip_places_route(
    trip_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_optimized_walking_route_for_trip(
            trip_id=trip_id,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )

@router.post("/walking/optimized/places")
def optimized_walking_places(
    points: list[tuple[float, float]],
):
    try:
        return get_optimized_walking_route(
            points=points,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )