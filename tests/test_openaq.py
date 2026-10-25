import json
from pathlib import Path

import httpx
import pandas as pd
import pytest
import respx

from app import client as c
from app.cleaning import measured_daily, openaq_to_frame
from app.models import OpenAQHoursResponse, OpenAQLocationsResponse

SAMPLES = Path(__file__).parent.parent / "samples"
HOURS = json.loads((SAMPLES / "openaq_hours.json").read_text())


@pytest.fixture(autouse=True)
def fake_key(monkeypatch):
    monkeypatch.setenv("OPENAQ_API_KEY", "test-key")
    monkeypatch.setattr("app.client.load_dotenv", lambda: None)


def _page(rows):
    return {"meta": {"page": 1, "limit": 2, "found": ">2"}, "results": rows}


def test_samples_parse():
    assert len(OpenAQHoursResponse.model_validate(HOURS).results) == 150
    locs = OpenAQLocationsResponse.model_validate_json((SAMPLES / "openaq_locations.json").read_text())
    assert locs.meta.found == ">3" and locs.results[0].timezone == "Asia/Kolkata"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAQ_API_KEY")
    with pytest.raises(RuntimeError, match="OPENAQ_API_KEY"):
        c.openaq_headers()


@respx.mock
async def test_pagination_follows_pages_and_sends_key():
    rows = HOURS["results"]
    route = respx.get(f"{c.OPENAQ_URL}/sensors/1/hours").mock(side_effect=[
        httpx.Response(200, json=_page(rows[:2])),
        httpx.Response(200, json=_page(rows[2:4])),
        httpx.Response(200, json=_page(rows[4:5])),
    ])
    async with httpx.AsyncClient() as cl:
        out = await c.fetch_sensor_hours(cl, 1, "a", "b", limit=2)
    assert len(out) == 5
    assert [r.calls.last.request.url.params["page"] for r in [route]] == ["3"]
    assert route.calls.last.request.headers["X-API-Key"] == "test-key"


@respx.mock
async def test_fetch_delhi_measured_keys_by_station():
    respx.get(url__regex=rf"{c.OPENAQ_URL}/sensors/\d+/hours").mock(
        return_value=httpx.Response(200, json=HOURS))
    async with httpx.AsyncClient() as cl:
        out = await c.fetch_delhi_measured(cl, "a", "b")
    assert list(out) == list(c.DELHI_STATIONS)
    assert all(len(v) == 150 for v in out.values())


def test_openaq_frame_is_ist_and_low_coverage_blanked():
    hours = OpenAQHoursResponse.model_validate(HOURS).results[:2]
    hours[1].coverage.percentComplete = 50.0
    df = openaq_to_frame("s", hours)
    assert str(df["timestamp"].dt.tz) == "Asia/Kolkata"
    assert df["timestamp"].iloc[0].hour == 0  # 2026-10-17T00:00+05:30
    assert pd.isna(df["pm25"].iloc[1]) and not pd.isna(df["pm25"].iloc[0])


def test_measured_daily_averages_across_stations():
    base = OpenAQHoursResponse.model_validate(HOURS).results[:24]
    a = [h.model_copy(deep=True) for h in base]
    b = [h.model_copy(deep=True) for h in base]
    for h in a:
        h.value = 100.0
    for h in b:
        h.value = 200.0
    out = measured_daily({"a": a, "b": b})
    assert out["pm25"].iloc[0] == 150.0 and out["stations"].iloc[0] == 2
