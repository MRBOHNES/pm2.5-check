import asyncio

import pytest

from app.cache import TTLCache


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


def counter():
    calls = []

    async def fetch():
        calls.append(1)
        await asyncio.sleep(0)
        return len(calls)

    return calls, fetch


async def test_second_call_is_served_from_cache():
    calls, fetch = counter()
    cache = TTLCache(10, Clock())
    assert await cache.get_or_fetch("k", fetch) == 1
    assert await cache.get_or_fetch("k", fetch) == 1
    assert len(calls) == 1


async def test_entry_expires_after_ttl():
    calls, fetch = counter()
    clock = Clock()
    cache = TTLCache(10, clock)
    await cache.get_or_fetch("k", fetch)
    clock.now = 10.0
    assert await cache.get_or_fetch("k", fetch) == 2


async def test_concurrent_callers_share_one_fetch():
    calls, fetch = counter()
    cache = TTLCache(10, Clock())
    assert await asyncio.gather(*(cache.get_or_fetch("k", fetch) for _ in range(3))) == [1, 1, 1]
    assert len(calls) == 1


async def test_failed_fetch_is_not_cached():
    attempts = []

    async def flaky():
        attempts.append(1)
        if len(attempts) == 1:
            raise ValueError("boom")
        return "ok"

    cache = TTLCache(10, Clock())
    with pytest.raises(ValueError):
        await cache.get_or_fetch("k", flaky)
    assert await cache.get_or_fetch("k", flaky) == "ok"
