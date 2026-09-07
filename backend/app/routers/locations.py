from fastapi import APIRouter, Query

from app.services.location_provider import location_provider


router = APIRouter(
    prefix="/api/locations",
    tags=["Locations"],
)


@router.get("/search")
def search_cities(
    q: str = Query(min_length=1),
):
    cities = location_provider.search_cities(q)

    return {
        "cities": cities,
    }