"""FastAPI app. Modelled data (Open-Meteo) for all cities; measured (OpenAQ) for Delhi."""
import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.analysis import (aqi_category, city_comparison, compare_model_measured,
                          model_vs_measured, peak_day)
from app.client import CITIES, UpstreamError, fetch_delhi_measured, fetch_open_meteo, window_utc
from app.cleaning import ist_today, measured_daily, modelled_daily

SOURCE = "modelled (Open-Meteo / CAMS)"
MEASURED_CITY = "delhi"  # OpenAQ stations are only configured for Delhi
MAX_DAYS = 92  # Open-Meteo's past_days limit


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=10) as client:
        app.state.client = client
        yield


app = FastAPI(title="PM2.5 check", lifespan=lifespan)


@app.exception_handler(UpstreamError)
async def upstream_error(_: Request, exc: UpstreamError) -> JSONResponse:
    """Timeout -> 504, any other upstream failure -> 502."""
    status = 504 if exc.timed_out else 502
    return JSONResponse({"detail": f"upstream error: {exc}"}, status_code=status)


@app.exception_handler(RuntimeError)
async def missing_config(_: Request, exc: RuntimeError) -> JSONResponse:
    """E.g. OPENAQ_API_KEY not set."""
    return JSONResponse({"detail": str(exc)}, status_code=503)


def _check_city(city: str) -> str:
    """Lower-case the name or raise 404 if the backend doesn't support it."""
    name = city.strip().lower()
    if name not in CITIES:
        raise HTTPException(404, f"unknown city: {name}; try {list(CITIES)}")
    return name


async def _daily(request: Request, cities: list[str]):
    unknown = [c for c in cities if c not in CITIES]
    if unknown:
        raise HTTPException(404, f"unknown city: {', '.join(unknown)}; try {list(CITIES)}")
    locations = await fetch_open_meteo(request.app.state.client)
    return modelled_daily({c: locations[c] for c in cities})


@app.get("/summary/{city}")
async def summary(city: str, request: Request) -> dict:
    daily = await _daily(request, [city.lower()])
    valid = daily.dropna(subset=["pm25"])
    return {
        "city": city.lower(),
        "source": SOURCE,
        "days": int(len(valid)),
        "mean_pm25": round(float(valid["pm25"].mean()), 1),
        "daily": [
            {"date": str(r.date.date()), "pm25": round(r.pm25, 1), "category": c}
            for r, c in zip(valid.itertuples(), aqi_category(valid["pm25"]))
        ],
    }


@app.get("/delhi/model-vs-measured")
async def delhi_model_vs_measured(request: Request) -> dict:
    """Delhi modelled vs measured (mean of 5 stations) on daily means."""
    client = request.app.state.client
    start, end = window_utc()
    locations, hours = await asyncio.gather(
        fetch_open_meteo(client), fetch_delhi_measured(client, start, end))
    joined = model_vs_measured(modelled_daily({"delhi": locations["delhi"]}), measured_daily(hours))
    return {
        "modelled_source": SOURCE,
        "measured_source": f"measured (OpenAQ, {len(hours)} Delhi stations)",
        "stats": compare_model_measured(joined),
        "daily": [
            {"date": str(r.date.date()), "modelled": round(r.modelled, 1),
             "measured": None if r.measured != r.measured else round(r.measured, 1)}
            for r in joined.itertuples()
        ],
    }


@app.get("/compare")
async def compare(request: Request, cities: str = Query(",".join(CITIES))) -> dict:
    names = [c.strip().lower() for c in cities.split(",") if c.strip()]
    daily = await _daily(request, names)
    table = city_comparison(daily).round(1)
    return {"source": SOURCE, "cities": table.to_dict(orient="records")}


@app.get("/health")
async def health() -> dict:
    """Liveness check. Makes no upstream calls."""
    sha = os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("GIT_SHA") or "dev"
    return {"status": "ok", "version": sha[:7], "time": datetime.now(timezone.utc).isoformat()}


@app.get("/cities")
async def cities() -> list[dict]:
    """Cities the backend supports; has_measured says whether station data exists."""
    return [{"name": c, "label": c.title(), "has_measured": c == MEASURED_CITY} for c in CITIES]


@app.get("/peak")
async def peak(request: Request, city: str = "Delhi", days: int = Query(30, ge=1, le=MAX_DAYS)) -> dict:
    """Peak daily PM2.5 over the last `days` days (measured if available, else modelled)."""
    name = _check_city(city)
    client = request.app.state.client
    if name == MEASURED_CITY:
        start, end = window_utc(days)
        locations, hours = await asyncio.gather(
            fetch_open_meteo(client, past_days=days), fetch_delhi_measured(client, start, end))
    else:
        locations, hours = await fetch_open_meteo(client, past_days=days), None
    modelled = modelled_daily({name: locations[name]})[["date", "pm25"]].rename(columns={"pm25": "modelled"})
    if hours is None:
        daily = modelled.assign(measured=float("nan"))
    else:
        measured = measured_daily(hours)[["date", "pm25"]].rename(columns={"pm25": "measured"})
        daily = modelled.merge(measured, on="date", how="left")  # keep days without station data
    return {"city": name, **peak_day(daily, days, today=ist_today())}
