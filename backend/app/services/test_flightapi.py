from app.database import SessionLocal
from app.models.hotel_content import HotelContent

db = SessionLocal()

hotel = (
    db.query(HotelContent)
    .filter(HotelContent.hotel_code == "426679")
    .first()
)

print("HOTEL:", hotel)
print("CODE:", hotel.hotel_code if hotel else None)
print("NAME:", hotel.name if hotel else None)
print("CITY:", hotel.city if hotel else None)
print("ADDRESS:", hotel.address if hotel else None)
print("LATITUDE:", hotel.latitude if hotel else None)
print("LONGITUDE:", hotel.longitude if hotel else None)

db.close()