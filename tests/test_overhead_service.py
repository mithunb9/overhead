from overhead.services.overhead import build_overhead_response, filter_commercial_airborne, pick_nearest

GROUND_AC = {"flight": "UAL2681 ", "alt_baro": "ground", "seen_pos": 1.0, "dst": 1.0}
GA_AC = {"flight": "N828KP  ", "alt_baro": 900, "seen_pos": 0.5, "dst": 2.0}
STALE_AC = {"flight": "FFT4593 ", "alt_baro": 5000, "seen_pos": 61, "dst": 3.0}
NEAR_AC = {"flight": "AAL2847 ", "r": "N832AA", "t": "B738", "alt_baro": 32000, "gs": 447.0, "seen_pos": 3, "dst": 3.65}
FAR_AC = {"flight": "DAL100  ", "alt_baro": 28000, "seen_pos": 2, "dst": 10.0}


def test_filter_commercial_airborne_drops_ground_ga_and_stale_entries() -> None:
    result = filter_commercial_airborne([GROUND_AC, GA_AC, STALE_AC, NEAR_AC, FAR_AC])

    assert result == [NEAR_AC, FAR_AC]


def test_filter_commercial_airborne_handles_missing_flight_field() -> None:
    result = filter_commercial_airborne([{"alt_baro": 3000, "seen_pos": 1, "dst": 1.0}])

    assert result == []


def test_filter_commercial_airborne_keeps_position_exactly_at_staleness_threshold() -> None:
    ac = {"flight": "AAL2847 ", "alt_baro": 32000, "seen_pos": 60, "dst": 1.0}

    result = filter_commercial_airborne([ac])

    assert result == [ac]


def test_pick_nearest_returns_smallest_dst() -> None:
    assert pick_nearest([FAR_AC, NEAR_AC]) == NEAR_AC


def test_pick_nearest_returns_none_for_empty_list() -> None:
    assert pick_nearest([]) is None


def test_build_overhead_response_uses_adsbdb_route_when_available() -> None:
    route = {
        "airline": {"name": "American Airlines", "icao": "AAL", "iata": "AA"},
        "origin": {"iata_code": "DFW", "municipality": "Dallas-Fort Worth"},
        "destination": {"iata_code": "ORD", "municipality": "Chicago"},
    }

    response = build_overhead_response(NEAR_AC, route, airlines={})

    assert response.flight == "AA2847"
    assert response.callsign == "AAL2847"
    assert response.airline == "American Airlines"
    assert response.airline_icao == "AAL"
    assert response.origin == "DFW"
    assert response.origin_city == "Dallas-Fort Worth"
    assert response.dest == "ORD"
    assert response.dest_city == "Chicago"
    assert response.reg == "N832AA"
    assert response.actype == "B738"
    assert response.alt_ft == 32000
    assert response.speed_kt == 447.0
    assert response.dist_mi == 3.65 * 1.15078
    assert response.source == "adsb.lol"
    assert response.age_s == 3


def test_build_overhead_response_falls_back_to_static_airline_table() -> None:
    airlines = {"AAL": {"name": "American Airlines", "iata": "AA"}}

    response = build_overhead_response(NEAR_AC, route=None, airlines=airlines)

    assert response.flight == "AA2847"
    assert response.airline == "American Airlines"
    assert response.airline_icao == "AAL"
    assert response.origin is None
    assert response.dest is None


def test_build_overhead_response_nulls_airline_when_unresolved() -> None:
    response = build_overhead_response(NEAR_AC, route=None, airlines={})

    assert response.airline is None
    assert response.airline_icao is None
    assert response.flight == "AAL2847"


def test_build_overhead_response_handles_missing_optional_adsb_lol_fields() -> None:
    ac = {"flight": "AAL2847 ", "alt_baro": 32000, "seen_pos": 3, "dst": 3.65}

    response = build_overhead_response(ac, route=None, airlines={})

    assert response.reg is None
    assert response.actype is None
    assert response.speed_kt is None
