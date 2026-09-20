from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine, Base
from app.routers.trips import router as trips_router
from app.routers.locations import router as locations_router
from app.routers.hotel_content import router as hotel_content_router
from app.routers.places import router as places_router
from app.routers.transports import router as transports_router
from app.routers.hotels import router as hotels_router
from app.routers.itinerary import router as itinerary_router


app = FastAPI(
    title="Travel AI Planner API",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)
app.include_router(
    hotel_content_router
)
app.include_router(trips_router)
app.include_router(locations_router)
app.include_router(places_router)
app.include_router(transports_router)
app.include_router(hotels_router)
app.include_router(itinerary_router)

@app.get("/")
def root():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "message": "Travel AI Planner API is running",
        "database": "connected",
    }