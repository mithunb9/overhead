from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import flights_api.cache as cache_module


@pytest.fixture(autouse=True)
def stub_redis(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Replace the shared redis client with a mock defaulting to a cache miss.

    Applies to every test so none of them depend on (or accidentally pollute) a
    real Redis instance; individual tests override .get/.set to exercise hits
    and failures.
    """
    client = AsyncMock()
    client.get.return_value = None
    monkeypatch.setattr(cache_module, "_client", client)
    return client
