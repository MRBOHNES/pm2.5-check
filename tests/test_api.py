import json
from pathlib import Path

import httpx
import pandas as pd
import pytest
import respx
from fastapi.testclient import TestClient

from app import client as c
from app.main import app, cors_settings

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


def _peak_setup(monkeypatch):
    monkeypatch.setenv("OPENAQ_API_KEY", "test-key")
    monkeypatch.setattr("app.client.load_dotenv", lambda: None)
    monkeypatch.setattr("app.main.window_utc", lambda days: ("a", "b"))
    monkeypatch.setattr("app.main.ist_today", lambda: pd.Timestamp("2026-10-24"))
    respx.get(c.OPEN_METEO_URL).mock(return_value=httpx.Response(200, json=SAMPLE))
    respx.get(url__regex=rf"{c.OPENAQ_URL}/sensors/\d+/hours").mock(
        return_value=httpx.Response(200, json=HOURS))


@respx.mock
def test_peak_delhi_uses_measured(api, monkeypatch):
    _peak_setup(monkeypatch)
    body = api.get("/peak", params={"city": "Delhi", "days": 7}).json()
    assert body["city"] == "delhi" and body["source"] == "measured"
    assert body["peak"]["measured"] == body["peak"]["value"]
    assert body["peak"]["modelled"] is not None and body["standard"] == 60
    assert body["peak"]["date"] < "2026-10-24"  # today is never the peak


@respx.mock
def test_peak_other_city_falls_back_to_modelled(api, monkeypatch):
    _peak_setup(monkeypatch)
    body = api.get("/peak", params={"city": "mumbai", "days": 7}).json()
    assert body["source"] == "modelled" and body["peak"]["measured"] is None


def test_peak_unknown_city_404_and_bad_days_422(api):
    assert api.get("/peak", params={"city": "atlantis"}).status_code == 404
    assert api.get("/peak", params={"city": "delhi", "days": 0}).status_code == 422
    assert api.get("/peak", params={"city": "delhi", "days": 93}).status_code == 422


def test_health_makes_no_upstream_calls(api):
    body = api.get("/health").json()
    assert body["status"] == "ok" and body["version"] and "T" in body["time"]


def test_cities_lists_supported_with_measured_flag(api):
    body = api.get("/cities").json()
    assert [c["name"] for c in body] == ["delhi", "chandigarh", "mumbai", "bengaluru"]
    assert [c["name"] for c in body if c["has_measured"]] == ["delhi"]


def test_cors_settings_splits_exact_and_wildcard():
    import re
    exact, regex = cors_settings("https://a.example.com, https://pm25-*-me.vercel.app,")
    assert exact == ["https://a.example.com"]
    assert re.fullmatch(regex, "https://pm25-abc123-me.vercel.app")
    assert not re.fullmatch(regex, "https://pm25-abc.evil.com-me.vercel.app")  # '*' never spans a dot
    assert cors_settings("") == ([], None)


def test_cors_allows_dev_origin_only(api):
    ok = api.get("/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
    bad = api.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers
