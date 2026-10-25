import asyncio

import httpx
import pytest
import respx

from app import client as c
from app.client import RetryConfig, UpstreamError, get_with_retry

URL = "https://example.test/x"
FAST = RetryConfig(max_attempts=3, base_delay=0, max_delay=0)


@pytest.fixture
def sleeps(monkeypatch):
    calls: list[float] = []

    async def fake(seconds):
        calls.append(seconds)

    monkeypatch.setattr(c, "_sleep", fake)
    return calls


@respx.mock
async def test_429_then_success_honours_retry_after(sleeps):
    route = respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    cfg = RetryConfig(max_attempts=3, base_delay=0.1, max_delay=8)
    async with httpx.AsyncClient() as cl:
        resp = await get_with_retry(cl, URL, cfg=cfg)
    assert resp.json() == {"ok": True}
    assert route.call_count == 2
    assert sleeps == [2.0]


@respx.mock
async def test_repeated_500_gives_up(sleeps):
    route = respx.get(URL).mock(return_value=httpx.Response(500))
    async with httpx.AsyncClient() as cl:
        with pytest.raises(UpstreamError) as e:
            await get_with_retry(cl, URL, cfg=FAST)
    assert route.call_count == 3
    assert e.value.status == 500


@respx.mock
async def test_timeout_is_retried_then_flagged(sleeps):
    route = respx.get(URL).mock(side_effect=httpx.ReadTimeout("slow"))
    async with httpx.AsyncClient() as cl:
        with pytest.raises(UpstreamError) as e:
            await get_with_retry(cl, URL, cfg=FAST)
    assert e.value.timed_out
    assert route.call_count == 3


@respx.mock
@pytest.mark.parametrize("status", [400, 401, 404])
async def test_other_4xx_fails_fast(sleeps, status):
    route = respx.get(URL).mock(return_value=httpx.Response(status))
    async with httpx.AsyncClient() as cl:
        with pytest.raises(UpstreamError) as e:
            await get_with_retry(cl, URL, cfg=FAST)
    assert route.call_count == 1
    assert e.value.status == status
    assert sleeps == []


@respx.mock
async def test_semaphore_caps_concurrency():
    active = peak = 0

    async def handler(request):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return httpx.Response(200, json={})

    respx.get(URL).mock(side_effect=handler)
    sem = asyncio.Semaphore(2)
    async with httpx.AsyncClient() as cl:
        await asyncio.gather(*(get_with_retry(cl, URL, cfg=FAST, sem=sem) for _ in range(8)))
    assert peak == 2


def test_backoff_grows_and_is_capped():
    cfg = RetryConfig(base_delay=1, max_delay=4)
    assert 1 <= c.backoff_delay(0, cfg) <= 1.25
    assert 4 <= c.backoff_delay(5, cfg) <= 5.0


@respx.mock
async def test_fetch_open_meteo_maps_cities_in_order():
    import json
    from pathlib import Path

    sample = json.loads((Path(__file__).parent.parent / "samples" / "open_meteo.json").read_text())
    respx.get(c.OPEN_METEO_URL).mock(return_value=httpx.Response(200, json=sample))
    async with httpx.AsyncClient() as cl:
        out = await c.fetch_open_meteo(cl)
    assert list(out) == ["delhi", "chandigarh", "mumbai", "bengaluru"]
    assert out["mumbai"].elevation == 6.0
