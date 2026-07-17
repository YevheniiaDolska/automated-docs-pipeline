"""Pluggable state store for rate limiting and webhook replay protection.

Defaults to per-process in-memory state, which is correct for a single runtime
instance. When ``ASK_AI_REDIS_URL`` is set and the ``redis`` package is
installed, the same limits and replay guard hold across multiple instances, so
horizontal scaling does not weaken protection. Any Redis error falls back to the
in-memory path so a Redis outage never takes the endpoint down.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)


def _make_redis_client() -> Any | None:
    url = os.getenv("ASK_AI_REDIS_URL", "").strip()
    if not url:
        return None
    try:
        import redis  # type: ignore
    except ImportError:
        logger.warning("ASK_AI_REDIS_URL is set but the redis package is not installed; using in-memory state")
        return None
    try:
        client = redis.Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
        client.ping()
        return client
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis unavailable (%s); using in-memory state", exc)
        return None


class RateLimiter:
    """Sliding-window rate limiter. Redis-backed when a client is provided."""

    def __init__(self, client: Any | None = None) -> None:
        self._client = client
        self._mem: dict[str, list[float]] = {}

    @property
    def backend(self) -> str:
        return "redis" if self._client is not None else "memory"

    def allow(self, identity: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds). A limit <= 0 disables limiting."""
        if limit <= 0:
            return True, 0
        now = time.time()
        if self._client is not None:
            try:
                return self._allow_redis(identity, limit, window_seconds, now)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Redis rate-limit error (%s); falling back to memory", exc)
        return self._allow_memory(identity, limit, window_seconds, now)

    def _allow_memory(self, identity: str, limit: int, window: int, now: float) -> tuple[bool, int]:
        start = now - window
        hits = [t for t in self._mem.get(identity, []) if t >= start]
        if len(hits) >= limit:
            return False, max(1, int(window - (now - hits[0])))
        hits.append(now)
        self._mem[identity] = hits
        if len(self._mem) > 4096:
            for key in [k for k, v in self._mem.items() if not v or v[-1] < start]:
                self._mem.pop(key, None)
        return True, 0

    def _allow_redis(self, identity: str, limit: int, window: int, now: float) -> tuple[bool, int]:
        key = f"askai:rl:{identity}"
        start = now - window
        pipe = self._client.pipeline()
        pipe.zremrangebyscore(key, 0, start)
        pipe.zcard(key)
        count = pipe.execute()[1]
        if count >= limit:
            oldest = self._client.zrange(key, 0, 0, withscores=True)
            retry = max(1, int(window - (now - oldest[0][1]))) if oldest else window
            return False, retry
        self._client.zadd(key, {f"{now}:{uuid.uuid4().hex}": now})
        self._client.expire(key, window)
        return True, 0


class ReplayGuard:
    """One-shot key guard for webhook replay protection."""

    def __init__(self, client: Any | None = None) -> None:
        self._client = client
        self._mem: dict[str, float] = {}

    @property
    def backend(self) -> str:
        return "redis" if self._client is not None else "memory"

    def is_new(self, key: str, ttl_seconds: int) -> bool:
        """Return True the first time a key is seen within the TTL, else False."""
        now = time.time()
        if self._client is not None:
            try:
                return bool(self._client.set(f"askai:replay:{key}", "1", nx=True, ex=ttl_seconds))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Redis replay-guard error (%s); falling back to memory", exc)
        stale = [k for k, ts in self._mem.items() if now - ts > ttl_seconds]
        for k in stale:
            self._mem.pop(k, None)
        if key in self._mem:
            return False
        self._mem[key] = now
        return True


# Shared singletons; Redis is auto-detected once at import.
_CLIENT = _make_redis_client()
rate_limiter = RateLimiter(_CLIENT)
replay_guard = ReplayGuard(_CLIENT)
