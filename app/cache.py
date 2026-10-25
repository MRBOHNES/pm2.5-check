"""Best-effort in-process cache with a time-to-live.

On serverless every instance has its own copy and it disappears with the instance,
so this only saves repeat calls while an instance stays warm. Never rely on it.
"""
import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any


class TTLCache:
    """Cache async results for `ttl` seconds; concurrent callers share one in-flight fetch."""

    def __init__(self, ttl: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.ttl = ttl
        self._clock = clock
        self._items: dict[Any, tuple[float, asyncio.Future]] = {}

    async def get_or_fetch(self, key: Any, fetch: Callable[[], Awaitable[Any]]) -> Any:
        """Return the cached value for `key`, or await `fetch()` and remember it."""
        now = self._clock()
        entry = self._items.get(key)
        if entry is None or entry[0] <= now:
            entry = (now + self.ttl, asyncio.ensure_future(fetch()))
            self._items[key] = entry
        try:
            return await asyncio.shield(entry[1])  # one caller leaving doesn't cancel the fetch
        except Exception:
            if self._items.get(key) is entry:  # a failed fetch must not be served again
                del self._items[key]
            raise
