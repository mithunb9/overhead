from overhead.clients.adsbdb import fetch_flight_route
from overhead.clients.aeroapi import fetch_aeroapi_route

ROUTE_PROVIDERS = {"adsbdb": fetch_flight_route, "aeroapi": fetch_aeroapi_route}
