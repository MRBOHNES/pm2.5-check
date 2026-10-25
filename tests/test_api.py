import json
from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app import client as c
from app.main import app

SAMPLE = json.loads((Path(__file__).parent.parent / "samples" / "open_meteo.json").read_text())


@pytest.fixture
def api(monkeypatch):
    async def no_sleep(_):
        pass

    monkeypatch.setattr(c, "_sleep", no_sleep)
    with TestClient(app) as tc:
        yield tc


@respx.mock
def test_summary_ok(api):
    respx.get(c.OPEN_METEO_URL).mock(return_value=httpx.Response(200, json=SAMPLE))
    body = api.get("/summary/Delhi").json()
    assert body["city"] == "delhi" and "modelled" in body["source"]
    assert body["days"] == 8 and body["daily"][0]["category"] == "Poor"


@respx.mock
def test_compare_subset(api):
    respx.get(c.OPEN_METEO_URL).mock(return_value=httpx.Response(200, json=SAMPLE))
    body = api.get("/compare", params={"cities": "delhi,mumbai"}).json()
    assert [r["city"] for r in body["cities"]] == ["delhi", "mumbai"]


def test_unknown_city_404(api):
    assert api.get("/summary/atlantis").status_code == 404


@respx.mock
def test_upstream_500_is_502(api):
    respx.get(c.OPEN_METEO_URL).mock(return_value=httpx.Response(500))
    assert api.get("/summary/delhi").status_code == 502


@respx.mock
def test_upstream_timeout_is_504(api):
    respx.get(c.OPEN_METEO_URL).mock(side_effect=httpx.ReadTimeout("slow"))
    assert api.get("/summary/delhi").status_code == 504


HOURS = json.loads((Path(__file__).parent.parent / "samples" / "openaq_hours.json").read_text())


@respx.mock
def test_delhi_model_vs_measured(api, monkeypatch):
    monkeypatch.setenv("OPENAQ_API_KEY", "test-key")
    monkeypatch.setattr("app.client.load_dotenv", lambda: None)
    monkeypatch.setattr("app.main.window_utc", lambda: ("a", "b"))
    respx.get(c.OPEN_METEO_URL).mock(return_value=httpx.Response(200, json=SAMPLE))
    respx.get(url__regex=rf"{c.OPENAQ_URL}/sensors/\d+/hours").mock(
        return_value=httpx.Response(200, json=HOURS))
    body = api.get("/delhi/model-vs-measured").json()
    assert "measured" in body["measured_source"] and "modelled" in body["modelled_source"]
    assert body["stats"]["days"] >= 1 and body["stats"]["mae"] >= 0


@respx.mock
def test_missing_openaq_key_is_503(api, monkeypatch):
    monkeypatch.delenv("OPENAQ_API_KEY", raising=False)
    monkeypatch.setattr("app.client.load_dotenv", lambda: None)
    respx.get(c.OPEN_METEO_URL).mock(return_value=httpx.Response(200, json=SAMPLE))
    assert api.get("/delhi/model-vs-measured").status_code == 503
