from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.trip import (
    TripCreate,
    TripResponse,
    CurrencyUpdate,
    FoodPreferenceUpdate,
    TripDatesUpdate,
    TripStopCreate,
    TripStopUpdate,
)
from app.services.trips import (
    create_trip,
    get_trips,
    delete_trip,
    update_user_currency,
    update_food_preference,
    update_trip_dates,
    create_trip_stop,
    get_trip_stops,
    update_trip_stop,
    delete_trip_stop,
)
from app.services.budget import calculate_budget
from app.services.trip_consistency import get_trip_consistency_warnings


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

@router.put("/{trip_id}/dates")
def update_trip_dates_endpoint(
    trip_id: int,
    dates: TripDatesUpdate,
    db: Session = Depends(get_db),
):
    result = update_trip_dates(
        trip_id=trip_id,
        start_date=dates.start_date,
        end_date=dates.end_date,
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

@router.get("/{trip_id}/consistency-warnings")
def get_consistency_warnings_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    warnings = get_trip_consistency_warnings(
        trip_id=trip_id,
        db=db,
    )

    return {
        "warnings": warnings,
    }

@router.post("/{trip_id}/stops")
def create_trip_stop_endpoint(
    trip_id: int,
    stop: TripStopCreate,
    db: Session = Depends(get_db),
):
    try:
        result = create_trip_stop(
            trip_id=trip_id,
            city=stop.city,
            country=stop.country,
            latitude=stop.latitude,
            longitude=stop.longitude,
            start_date=stop.start_date,
            end_date=stop.end_date,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return {
        "stop": {
            "id": result.id,
            "trip_id": result.trip_id,
            "city": result.city,
            "country": result.country,
            "latitude": result.latitude,
            "longitude": result.longitude,
            "start_date": result.start_date,
            "end_date": result.end_date,
            "sort_order": result.sort_order,
        }
    }


@router.get("/{trip_id}/stops")
def get_trip_stops_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
):
    result = get_trip_stops(
        trip_id=trip_id,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return {
        "stops": result,
    }


@router.put("/{trip_id}/stops/{stop_id}")
def update_trip_stop_endpoint(
    trip_id: int,
    stop_id: int,
    stop: TripStopUpdate,
    db: Session = Depends(get_db),
):
    try:
        result = update_trip_stop(
            trip_id=trip_id,
            stop_id=stop_id,
            city=stop.city,
            country=stop.country,
            latitude=stop.latitude,
            longitude=stop.longitude,
            start_date=stop.start_date,
            end_date=stop.end_date,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Trip stop not found",
        )

    return {
        "message": "Trip stop updated",
        "stop": {
            "id": result["stop"].id,
            "trip_id": result["stop"].trip_id,
            "city": result["stop"].city,
            "country": result["stop"].country,
            "latitude": result["stop"].latitude,
            "longitude": result["stop"].longitude,
            "start_date": result["stop"].start_date,
            "end_date": result["stop"].end_date,
            "sort_order": result["stop"].sort_order,
        },
        "hotel_status": result["hotel_status"],
        "warnings": result["warnings"],
    }


@router.delete("/{trip_id}/stops/{stop_id}")
def delete_trip_stop_endpoint(
    trip_id: int,
    stop_id: int,
    db: Session = Depends(get_db),
):
    result = delete_trip_stop(
        trip_id=trip_id,
        stop_id=stop_id,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Trip stop not found",
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