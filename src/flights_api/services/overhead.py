from __future__ import annotations

import re
from typing import Any

from flights_api.data.airlines import AirlineEntry
from flights_api.models.overhead import OverheadResponse

CALLSIGN_PATTERN = re.compile(r"^[A-Z]{3}\d+")
STALE_POSITION_THRESHOLD_S = 60  # older position reports are likely a stale "ghost" hit, not the aircraft's current spot
NM_TO_MI = 1.15078


def filter_commercial_airborne(aircraft: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered = []
    for ac in aircraft:
        if ac.get("alt_baro") == "ground":
            continue

        callsign = (ac.get("flight") or "").strip()
        if not CALLSIGN_PATTERN.match(callsign):
            continue

        if ac.get("seen_pos", float("inf")) > STALE_POSITION_THRESHOLD_S:
            continue

        filtered.append(ac)
    return filtered


def pick_nearest(aircraft: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not aircraft:
        return None
    return min(aircraft, key=lambda ac: ac["dst"])


def _resolve_airline(
    icao_prefix: str, route: dict[str, Any] | None, airlines: dict[str, AirlineEntry]
) -> tuple[str | None, str | None, str | None]:
    """Returns (name, icao, iata), preferring adsbdb's route lookup over the bundled table."""
    if route and route.get("airline"):
        airline = route["airline"]
        return airline.get("name"), airline.get("icao"), airline.get("iata")

    entry = airlines.get(icao_prefix)
    if entry:
        return entry["name"], icao_prefix, entry["iata"]

    return None, None, None


def build_overhead_response(
    aircraft: dict[str, Any], route: dict[str, Any] | None, airlines: dict[str, AirlineEntry]
) -> OverheadResponse:
    callsign = aircraft["flight"].strip()
    icao_prefix, numeric_part = callsign[:3], callsign[3:]

    airline_name, airline_icao, airline_iata = _resolve_airline(icao_prefix, route, airlines)
    flight = f"{airline_iata}{numeric_part}" if airline_iata else callsign

    origin = route.get("origin") if route else None
    destination = route.get("destination") if route else None

    return OverheadResponse(
        flight=flight,
        callsign=callsign,
        airline=airline_name,
        airline_icao=airline_icao,
        reg=aircraft.get("r"),
        actype=aircraft.get("t"),
        origin=origin.get("iata_code") if origin else None,
        origin_city=origin.get("municipality") if origin else None,
        dest=destination.get("iata_code") if destination else None,
        dest_city=destination.get("municipality") if destination else None,
        alt_ft=aircraft["alt_baro"],
        speed_kt=aircraft.get("gs"),
        dist_mi=aircraft["dst"] * NM_TO_MI,
        source="adsb.lol",
        age_s=aircraft["seen_pos"],
    )
