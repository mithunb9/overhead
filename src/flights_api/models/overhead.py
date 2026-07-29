from pydantic import BaseModel


class OverheadResponse(BaseModel):
    """Response for the /overhead endpoint.

    Stub for now — will carry the nearest overhead flight(s) once ADS-B
    lookups land (see README milestones).
    """

    message: str
