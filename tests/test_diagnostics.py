"""Tests for the Eaton Battery Storage diagnostics."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.eaton_battery_storage.diagnostics import (
    TO_REDACT,
    async_get_config_entry_diagnostics,
)

from .conftest import MOCK_CONFIG_DATA_TECH, build_coordinator_data


async def test_diagnostics_output(hass) -> None:
    """Test diagnostics returns entry and coordinator data."""
    # Build a mock config entry with as_dict()
    entry = MagicMock()
    entry.as_dict.return_value = {
        "data": dict(MOCK_CONFIG_DATA_TECH),
        "domain": "eaton_battery_storage",
        "title": "Eaton xStorage Home",
    }
    coord = MagicMock()
    coord.data = build_coordinator_data()
    entry.runtime_data = coord

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert "entry" in result
    assert "data" in result
    # Verify structure is present
    assert "status" in result["data"] or "device" in result["data"]


async def test_diagnostics_redacts_sensitive_fields(hass) -> None:
    """Test that sensitive fields are redacted."""
    entry = MagicMock()
    entry.as_dict.return_value = {
        "data": {
            "username": "secret_user",
            "password": "secret_pass",
            "email": "user@example.com",
            "inverter_sn": "SN123",
            "host": "192.168.1.100",
        },
        "domain": "eaton_battery_storage",
    }
    coord = MagicMock()
    coord.data = {
        "device": {"inverterSerialNumber": "SN123", "powerState": True},
    }
    entry.runtime_data = coord

    result = await async_get_config_entry_diagnostics(hass, entry)

    # Check that sensitive fields are redacted (replaced with **REDACTED**)
    entry_data = result["entry"]["data"]
    assert entry_data["username"] == "**REDACTED**"
    assert entry_data["password"] == "**REDACTED**"
    assert entry_data["email"] == "**REDACTED**"
    assert entry_data["inverter_sn"] == "**REDACTED**"
    # Non-sensitive fields should remain
    assert entry_data["host"] == "192.168.1.100"

    # Device data should have serial redacted
    assert result["data"]["device"]["inverterSerialNumber"] == "**REDACTED**"
    assert result["data"]["device"]["powerState"] is True


def test_to_redact_set() -> None:
    """Test that TO_REDACT contains expected keys."""
    expected = {"email", "inverterSerialNumber", "inverter_sn", "password", "token", "username"}
    assert TO_REDACT == expected
