"""Async HTTP client: timeout, retry with backoff, concurrency cap."""
import asyncio
import os
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from pydantic import TypeAdapter

from app.models import OpenAQHour, OpenAQHoursResponse, OpenMeteoResponse

OPEN_METEO_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPENAQ_URL = "https://api.openaq.org/v3"

# Active Delhi PM2.5 stations, chosen from /v3/locations (data up to 23 Oct 2026).
# Older sensor ids on the same stations return no data, so the live sensor id is pinned.
DELHI_STATIONS: dict[str, int] = {  # station name -> PM2.5 sensor id
    "R K Puram (DPCC)": 12234787,
    "Punjabi Bagh (DPCC)": 12234796,
    "Pusa (IMD)": 12234702,
    "Mandir Marg (DPCC)": 12234778,
    "Anand Vihar (DPCC)": 12235610,
}

# order matters: Open-Meteo returns one entry per city in request order
CITIES: dict[str, tuple[float, float]] = {
    "delhi": (28.6139, 77.2090),
    "chandigarh": (30.7333, 76.7794),
    "mumbai": (19.0760, 72.8777),
    "bengaluru": (12.9716, 77.5946),
}


class UpstreamError(Exception):
    """Upstream API failed for good (after retries, or a non-retryable 4xx)."""

    def __init__(self, message: str, status: int | None = None, timed_out: bool = False):
        super().__init__(message)
        self.status = status
        self.timed_out = timed_out


@dataclass
class RetryConfig:
    max_attempts: int = 4
    base_delay: float = 0.5
    max_delay: float = 8.0
    max_concurrency: int = 5


async def _sleep(seconds: float) -> None:
    await asyncio.sleep(seconds)  # separate function so tests can patch it


def backoff_delay(attempt: int, cfg: RetryConfig) -> float:
    """min(cap, base * 2^attempt) plus a little random jitter."""
    delay = min(cfg.max_delay, cfg.base_delay * 2**attempt)
    return delay + random.uniform(0, delay * 0.25)


def _retry_after(resp: httpx.Response) -> float | None:
    """Seconds to wait: Retry-After, else OpenAQ's x-ratelimit-reset."""
    value = resp.headers.get("Retry-After") or resp.headers.get("x-ratelimit-reset")
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


async def get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    cfg: RetryConfig | None = None,
    sem: asyncio.Semaphore | None = None,
) -> httpx.Response:
    """GET with retry on 429, 5xx, timeouts and connection errors."""
    cfg = cfg or RetryConfig()
    sem = sem or asyncio.Semaphore(cfg.max_concurrency)
    last: UpstreamError | None = None
    for attempt in range(cfg.max_attempts):
        wait = backoff_delay(attempt, cfg)
        try:
            async with sem:
                resp = await client.get(url, params=params, headers=headers)
        except httpx.TimeoutException:
            last = UpstreamError("upstream timed out", timed_out=True)
        except httpx.TransportError as exc:
            last = UpstreamError(f"connection error: {exc}")
        else:
            if resp.status_code < 400:
                return resp
            if resp.status_code != 429 and resp.status_code < 500:
                raise UpstreamError(f"HTTP {resp.status_code}", status=resp.status_code)
            last = UpstreamError(f"HTTP {resp.status_code}", status=resp.status_code)
            if resp.status_code == 429 and (ra := _retry_after(resp)) is not None:
                wait = min(ra, cfg.max_delay)
        if attempt < cfg.max_attempts - 1:
            await _sleep(wait)
    assert last is not None
    raise last


async def fetch_open_meteo(
    client: httpx.AsyncClient,
    cities: dict[str, tuple[float, float]] = CITIES,
    past_days: int = 7,
    cfg: RetryConfig | None = None,
) -> dict[str, "OpenMeteoLocation"]:  # noqa: F821
    """Modelled PM2.5 for all cities in one call. Returns {city: location}."""
    params = {
        "latitude": ",".join(str(lat) for lat, _ in cities.values()),
        "longitude": ",".join(str(lon) for _, lon in cities.values()),
        "hourly": "pm2_5",
        "past_days": past_days,
        "forecast_days": 1,
        "timezone": "Asia/Kolkata",
    }
    resp = await get_with_retry(client, OPEN_METEO_URL, params=params, cfg=cfg)
    locations = TypeAdapter(OpenMeteoResponse).validate_python(resp.json())
    if len(locations) != len(cities):
        raise UpstreamError(f"expected {len(cities)} locations, got {len(locations)}")
    return dict(zip(cities, locations))


def openaq_headers() -> dict[str, str]:
    """API key from .env / environment. Never logged."""
    load_dotenv()
    key = os.getenv("OPENAQ_API_KEY")
    if not key:
        raise RuntimeError("OPENAQ_API_KEY is not set (see .env.example)")
    return {"X-API-Key": key}


async def fetch_sensor_hours(
    client: httpx.AsyncClient,
    sensor_id: int,
    start_utc: str,
    end_utc: str,
    cfg: RetryConfig | None = None,
    sem: asyncio.Semaphore | None = None,
    limit: int = 1000,
) -> list[OpenAQHour]:
    """All hourly PM2.5 rows for one sensor, following pages until a short page."""
    rows: list[OpenAQHour] = []
    page = 1
    while True:
        params = {"datetime_from": start_utc, "datetime_to": end_utc, "limit": limit, "page": page}
        resp = await get_with_retry(client, f"{OPENAQ_URL}/sensors/{sensor_id}/hours",
                                    params=params, headers=openaq_headers(), cfg=cfg, sem=sem)
        batch = OpenAQHoursResponse.model_validate(resp.json()).results
        rows += batch
        if len(batch) < limit:
            return rows
        page += 1


async def fetch_delhi_measured(
    client: httpx.AsyncClient,
    start_utc: str,
    end_utc: str,
    stations: dict[str, int] = DELHI_STATIONS,
    cfg: RetryConfig | None = None,
) -> dict[str, list[OpenAQHour]]:
    """Fetch every station's hours concurrently (capped by one shared semaphore)."""
    cfg = cfg or RetryConfig()
    sem = asyncio.Semaphore(cfg.max_concurrency)
    results = await asyncio.gather(*(
        fetch_sensor_hours(client, sid, start_utc, end_utc, cfg=cfg, sem=sem)
        for sid in stations.values()
    ))
    return dict(zip(stations, results))


def window_utc(past_days: int = 7) -> tuple[str, str]:
    """UTC start/end matching Open-Meteo's window: local midnight `past_days` ago until now."""
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    start = (now - timedelta(days=past_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return start.astimezone(timezone.utc).strftime(fmt), now.astimezone(timezone.utc).strftime(fmt)
