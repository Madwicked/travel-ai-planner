from app.database import SessionLocal
from app.models.hotel_content import HotelContent

db = SessionLocal()

hotel = (
    db.query(HotelContent)
    .filter(HotelContent.hotel_code == "426679")
    .first()
)

db.close()