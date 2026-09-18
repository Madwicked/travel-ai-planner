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
    )

    return {
        "status": "ok",
        "saved": count,
    }