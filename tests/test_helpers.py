"""Tests for the Eaton Battery Storage helpers module."""

from __future__ import annotations

from custom_components.eaton_battery_storage.helpers import transform_settings_for_put


def test_transform_settings_country() -> None:
    """Test country dict is flattened to geonameId string."""
    settings = {
        "country": {"geonameId": "2635167", "name": "United Kingdom"},
    }
    result = transform_settings_for_put(settings)
    assert result["country"] == "2635167"


def test_transform_settings_city() -> None:
    """Test city dict is flattened to geonameId string."""
    settings = {
        "city": {"geonameId": "2643743", "name": "London"},
    }
    result = transform_settings_for_put(settings)
    assert result["city"] == "2643743"


def test_transform_settings_timezone() -> None:
    """Test timezone dict is flattened to id string."""
    settings = {
        "timezone": {"id": "Europe/London", "name": "GMT"},
    }
    result = transform_settings_for_put(settings)
    assert result["timezone"] == "Europe/London"


def test_transform_settings_already_strings() -> None:
    """Test no-op when values are already strings."""
    settings = {
        "country": "2635167",
        "city": "2643743",
        "timezone": "Europe/London",
    }
    result = transform_settings_for_put(settings)
    assert result["country"] == "2635167"


def test_transform_settings_missing_keys() -> None:
    """Test no error when keys are absent."""
    settings = {"someOtherKey": "value"}
    result = transform_settings_for_put(settings)
    assert result == {"someOtherKey": "value"}


def test_transform_returns_same_dict() -> None:
    """Test function modifies in-place and returns same dict."""
    settings = {"timezone": {"id": "UTC", "name": "UTC"}}
    result = transform_settings_for_put(settings)
    assert result is settings
