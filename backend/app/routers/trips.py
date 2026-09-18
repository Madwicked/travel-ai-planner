from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.trip import Trip
from app.schemas.trip import (
    TripCreate,
    TripResponse,
    CurrencyUpdate,
    FoodPreferenceUpdate,
)
from app.services.trips import (
    create_trip,
    get_trips,
    delete_trip,
    update_user_currency,
    update_food_preference,
)
from app.services.budget import calculate_budget


router = APIRouter(
    prefix="/api/trips",
    tags=["Trips"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=TripResponse)
def create_trip_endpoint(
    trip: TripCreate,
    db: Session = Depends(get_db),
):
    return create_trip(
        trip=trip,
        db=db,
    )


@router.get("")
def get_trips_endpoint(
    db: Session = Depends(get_db),
):
    return get_trips(
        db=db,
    )


@router.put("/{trip_id}/currency")
def update_currency_endpoint(
    trip_id: int,
    currency: CurrencyUpdate,
    db: Session = Depends(get_db),
):
    result = update_user_currency(
        trip_id=trip_id,
        user_currency=currency.user_currency,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return result


@router.put("/{trip_id}/food")
def update_food_preference_endpoint(
    trip_id: int,
    food: FoodPreferenceUpdate,
    db: Session = Depends(get_db),
):
    result = update_food_preference(
        trip_id=trip_id,
        food_preference=food.food_preference,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return result


@router.get("/{trip_id}/budget")
def get_budget_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    result = calculate_budget(
        trip_id=trip_id,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return result


@router.delete("/{trip_id}")
def delete_trip_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    result = delete_trip(
        trip_id=trip_id,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return result