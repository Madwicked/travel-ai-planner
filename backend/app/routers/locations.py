from fastapi import APIRouter, Query

from app.services.location_provider import location_provider


router = APIRouter(
    prefix="/api/locations",
    tags=["Locations"],
)


@router.get("/search")
def search_cities(
    q: str = Query(min_length=1),
    lang: str = Query(default="en", min_length=2, max_length=2),
):
    cities = location_provider.search_cities(q, lang)

    return {
        "cities": cities,
    }
