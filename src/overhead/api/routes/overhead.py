import httpx
from fastapi import APIRouter

from overhead.clients.adsb_lol import fetch_nearby_aircraft
from overhead.clients.adsbdb import fetch_flight_route
from overhead.config import settings
from overhead.data.airlines import load_airlines
from overhead.models.overhead import OverheadRequest, OverheadResponse
from overhead.services.overhead import build_overhead_response, filter_commercial_airborne, pick_nearest_n

router = APIRouter(prefix="/overhead", tags=["overhead"])


@router.post("", response_model=list[OverheadResponse])
async def get_overhead(request: OverheadRequest) -> list[OverheadResponse]:
    # Clamp here so a client-requested count never bypasses the operator-configured ceiling.
    count = min(request.count, settings.overhead.count_max)

    async with httpx.AsyncClient() as client:
        aircraft = await fetch_nearby_aircraft(
            request.lat, request.lon, settings.overhead.radius_nm, client
        )
        nearest = pick_nearest_n(filter_commercial_airborne(aircraft), count)

        airlines = load_airlines()
        responses = []
        for ac in nearest:
            route = await fetch_flight_route(ac["flight"].strip(), client)
            responses.append(build_overhead_response(ac, route, airlines))

    return responses
