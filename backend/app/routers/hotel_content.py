import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.hotel_content import HotelContentProvider
from app.services.hotel_content_service import HotelContentService


router = APIRouter(
    prefix="/api/hotel-content",
    tags=["Hotel Content"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/sync")
def sync_hotel_content(
    language: str = "ENG",
    hotel_code: str | None = None,
    db: Session = Depends(get_db),
):
    api_key = os.getenv("HOTELBEDS_API_KEY")
    secret = os.getenv("HOTELBEDS_SECRET")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="HOTELBEDS_API_KEY is not configured",
        )

    if not secret:
        raise HTTPException(
            status_code=500,
            detail="HOTELBEDS_SECRET is not configured",
        )

    provider = HotelContentProvider(
        api_key=api_key,
        secret=secret,
    )

    service = HotelContentService(
        db=db,
        provider=provider,
    )

    count = service.sync_hotels(
        language=language,
        hotel_code=hotel_code,
    )

    return {
        "status": "ok",
        "saved": count,
    }

@router.get("/{hotel_code}")
def get_hotel_content(
    hotel_code: str,
    db: Session = Depends(get_db),
):
    from app.models.hotel_content import HotelContent

    hotel = (
        db.query(HotelContent)
        .filter(
            HotelContent.hotel_code == str(hotel_code)
        )
        .first()
    )

    if hotel is None:
        raise HTTPException(
            status_code=404,
            detail="Hotel content not found",
        )

    return {
        "hotel_code": hotel.hotel_code,
        "name": hotel.name,
        "rooms": hotel.rooms,
    }