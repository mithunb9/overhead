from pydantic import BaseModel


class OverheadRequest(BaseModel):
    lat: float
    lon: float
    count: int = 1


class OverheadResponse(BaseModel):
    flight: str
    callsign: str
    airline: str | None = None
    airline_icao: str | None = None
    reg: str | None = None
    actype: str | None = None
    origin: str | None = None
    origin_city: str | None = None
    dest: str | None = None
    dest_city: str | None = None
    alt_ft: int
    speed_kt: float | None = None
    dist_mi: float
    source: str = "adsb.lol"
    age_s: float
