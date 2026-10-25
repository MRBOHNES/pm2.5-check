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


# ---- OpenAQ v3 (measured). Fields taken from samples/openaq_*.json ----


class OpenAQMeta(BaseModel):
    page: int
    limit: int
    found: int | str  # int, or a string like ">3" when the count is capped


class OpenAQTime(BaseModel):
    utc: str
    local: str  # ISO with +05:30 offset


class OpenAQPeriod(BaseModel):
    label: str
    datetimeFrom: OpenAQTime
    datetimeTo: OpenAQTime


class OpenAQCoverage(BaseModel):
    percentComplete: float  # share of expected readings in this hour that arrived


class OpenAQHour(BaseModel):
    """One hourly PM2.5 average for one sensor."""

    value: float
    period: OpenAQPeriod
    coverage: OpenAQCoverage


class OpenAQHoursResponse(BaseModel):
    meta: OpenAQMeta
    results: list[OpenAQHour]


class OpenAQCoordinates(BaseModel):
    latitude: float
    longitude: float


class OpenAQLocation(BaseModel):
    id: int
    name: str
    timezone: str
    coordinates: OpenAQCoordinates | None = None


class OpenAQLocationsResponse(BaseModel):
    meta: OpenAQMeta
    results: list[OpenAQLocation]
