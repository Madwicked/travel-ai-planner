from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine, Base
from app.models.trip import Trip
from app.models.hotel import TripHotel
from app.models.place import TripPlace
from app.routers.trips import router as trips_router
from app.routers.locations import router as locations_router

app = FastAPI(
    title="Travel AI Planner API",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

app.include_router(trips_router)
app.include_router(locations_router)

@app.get("/")
def root():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "message": "Travel AI Planner API is running",
        "database": "connected",
    }