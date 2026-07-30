import importlib
import logging
from unittest.mock import patch

import pytest

import overhead.main as main_module
from overhead.clients.aeroapi import AEROAPI_KEY_ENV
from overhead.config import settings


@pytest.fixture(autouse=True)
def reload_main_after_test() -> None:
    """Module-level startup checks in overhead.main only run on import; reload
    once after each test so a later test's fresh reload isn't left stale."""
    yield
    with patch.object(settings.overhead, "route_source", "adsbdb"):
        importlib.reload(main_module)


def test_warns_when_aeroapi_selected_without_api_key(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv(AEROAPI_KEY_ENV, raising=False)

    with patch.object(settings.overhead, "route_source", "aeroapi"):
        with caplog.at_level(logging.WARNING):
            importlib.reload(main_module)

    assert any(AEROAPI_KEY_ENV in record.getMessage() for record in caplog.records)


def test_no_warning_when_aeroapi_selected_with_api_key_set(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv(AEROAPI_KEY_ENV, "secret")

    with patch.object(settings.overhead, "route_source", "aeroapi"):
        with caplog.at_level(logging.WARNING):
            importlib.reload(main_module)

    assert caplog.records == []


def test_no_warning_when_adsbdb_selected_without_api_key(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv(AEROAPI_KEY_ENV, raising=False)

    with patch.object(settings.overhead, "route_source", "adsbdb"):
        with caplog.at_level(logging.WARNING):
            importlib.reload(main_module)

    assert caplog.records == []
