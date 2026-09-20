from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date

from app.database import SessionLocal
from app.models.trip import Trip
from app.schemas.trip import TransportCreate, TransportUpdate
from app.services.transport import (
    create_transport,
    get_transports,
    generate_transport_options,
    generate_return_transport_options,
    update_transport,
    delete_transport,
)


router = APIRouter(
    prefix="/api/trips",
    tags=["Transports"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{trip_id}/transports")
def create_transport_endpoint(
    trip_id: int,
    transport: TransportCreate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return create_transport(
        trip_id=trip_id,
        transport=transport,
        db=db,
    )


@router.get("/{trip_id}/transports")
def get_transports_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return get_transports(
        trip_id=trip_id,
        db=db,
    )


@router.delete("/{trip_id}/transports/{transport_id}")
def delete_transport_endpoint(
    trip_id: int,
    transport_id: int,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    result = delete_transport(
        trip_id=trip_id,
        transport_id=transport_id,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Transport not found",
        )

    return result


@router.get("/{trip_id}/transports/options")
def get_transport_options(
    trip_id: int,
    refresh: bool = Query(False),
    search_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    result = generate_transport_options(
        trip,
        db,
        refresh=refresh,
        search_date=search_date,
    )

    return {
        "trip_id": trip.id,
        "origin": trip.origin,
        "destination": trip.destination,
        **result,
    }


@router.get("/{trip_id}/transports/return-options")
def get_return_transport_options(
    trip_id: int,
    refresh: bool = Query(False),
    search_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    result = generate_return_transport_options(
        trip,
        db,
        refresh=refresh,
        search_date=search_date,
    )

    return {
        "trip_id": trip.id,
        "origin": trip.destination,
        "destination": trip.origin,
        **result,
    }


@router.put("/{trip_id}/transport")
def update_transport_endpoint(
    trip_id: int,
    transport: TransportUpdate,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return update_transport(
        trip_id=trip_id,
        transport=transport,
        db=db,
    )