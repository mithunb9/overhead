from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

import redis.asyncio as redis

REDIS_URL_ENV = "REDIS_URL"
DEFAULT_REDIS_URL = "redis://localhost:6379/0"

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(os.environ.get(REDIS_URL_ENV, DEFAULT_REDIS_URL))
    return _client


async def cached_call(key: str, ttl_s: int, fetch: Callable[[], Awaitable[Any]]) -> Any:
    client = get_redis_client()

    try:
        raw = await client.get(key)
    except redis.RedisError:
        raw = None

    if raw is not None:
        return json.loads(raw)

    value = await fetch()

    try:
        # cache "no result" too, otherwise every miss re-hits the underlying API for
        # the TTL window instead of just the first one
        await client.set(key, json.dumps(value), ex=ttl_s)
    except redis.RedisError:
        pass

    return value
