"""Pydantic models for API responses (fields taken from samples/)."""
from pydantic import BaseModel


class OpenMeteoHourly(BaseModel):
    """Parallel hourly arrays; None marks a missing value."""
    time: list[str]  # local ISO strings, no tz suffix (tz is in the parent)
    pm2_5: list[float | None]


class OpenMeteoLocation(BaseModel):
    """One city's entry in the Open-Meteo list. Modelled data, not measured."""
    latitude: float  # snapped to the model grid, not the lat we asked for
    longitude: float
    elevation: float
    timezone: str
    utc_offset_seconds: int
    hourly_units: dict[str, str]
    hourly: OpenMeteoHourly
    location_id: int | None = None  # absent on the first entry


# multi-city call returns a bare JSON list, one entry per requested city, in request order
OpenMeteoResponse = list[OpenMeteoLocation]
