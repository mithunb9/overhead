from fastapi import APIRouter

from flights_api.models.overhead import OverheadResponse

router = APIRouter(prefix="/overhead", tags=["overhead"])


@router.post("", response_model=OverheadResponse)
async def get_overhead() -> OverheadResponse:
    """Stub endpoint — returns a placeholder response.

    Will eventually accept lat/long and return the nearest overhead
    commercial flight (see README v0.1/v0.2 milestones).
    """
    return OverheadResponse(message="Hello World")
