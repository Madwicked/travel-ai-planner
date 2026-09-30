from fastapi import APIRouter, HTTPException, Query

from app.services.transfer_service import TransferService


router = APIRouter(
    prefix="/api/transfers",
    tags=["transfers"],
)


@router.get("/options")
def get_transfer_options(
    from_type: str = Query(...),
    from_code: str = Query(...),
    to_type: str = Query(...),
    to_code: str = Query(...),
    outbound: str = Query(...),
    adults: int = Query(..., ge=1),
    children: int = Query(0, ge=0),
    infants: int = Query(0, ge=0),
    inbound: str | None = Query(None),
    language: str = Query("en"),
):
    try:
        options = TransferService.get_transfer_options(
            from_type=from_type,
            from_code=from_code,
            to_type=to_type,
            to_code=to_code,
            outbound=outbound,
            adults=adults,
            children=children,
            infants=infants,
            inbound=inbound,
            language=language,
        )

        return {
            "options": options,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error



    except ValueError as error:

        print(f"TRANSFER VALUE ERROR: {error}")

        raise HTTPException(

            status_code=400,

            detail=str(error),

        ) from error