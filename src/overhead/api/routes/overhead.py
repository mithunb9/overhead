import httpx
from fastapi import APIRouter

from overhead.clients.adsb_lol import fetch_nearby_aircraft
from overhead.clients.adsbdb import fetch_flight_route
from overhead.config import settings
from overhead.data.airlines import load_airlines
from overhead.models.overhead import OverheadRequest, OverheadResponse
from overhead.services.overhead import build_overhead_response, filter_commercial_airborne, pick_nearest

router = APIRouter(prefix="/overhead", tags=["overhead"])


@router.post("", response_model=OverheadResponse | None)
async def get_overhead(request: OverheadRequest) -> OverheadResponse | None:
    async with httpx.AsyncClient() as client:
        aircraft = await fetch_nearby_aircraft(
            request.lat, request.lon, settings.overhead.radius_nm, client
        )
        nearest = pick_nearest(filter_commercial_airborne(aircraft))

        # 200 + null keeps this consistent with v0.2's list endpoint, where an
        # empty result is naturally `200 []` rather than a 404.
        if nearest is None:
            return None

        route = await fetch_flight_route(nearest["flight"].strip(), client)

    return build_overhead_response(nearest, route, load_airlines())
