"""Tests for the Eaton Battery Storage binary sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.eaton_battery_storage.binary_sensor import (
    DESCRIPTIONS,
    EatonBatteryStorageBinarySensorEntity,
)

from .conftest import build_coordinator_data, MOCK_ENTRY_ID


def _make_binary_sensor(
    coordinator: MagicMock, key: str
) -> EatonBatteryStorageBinarySensorEntity:
    """Create a binary sensor entity for the given key."""
    for desc in DESCRIPTIONS:
        if desc.key == key:
            return EatonBatteryStorageBinarySensorEntity(coordinator, desc)
    raise ValueError(f"Unknown binary sensor key: {key}")


def test_battery_charging_on(mock_coordinator: MagicMock) -> None:
    """Test battery_charging is True when status is BAT_CHARGING."""
    sensor = _make_binary_sensor(mock_coordinator, "battery_charging")
    assert sensor.is_on is True


def test_battery_charging_off(mock_coordinator: MagicMock) -> None:
    """Test battery_charging is False when status is not BAT_CHARGING."""
    data = build_coordinator_data()
    data["status"]["energyFlow"]["batteryStatus"] = "BAT_IDLE"
    mock_coordinator.data = data
    sensor = _make_binary_sensor(mock_coordinator, "battery_charging")
    assert sensor.is_on is False


def test_battery_discharging_on(mock_coordinator: MagicMock) -> None:
    """Test battery_discharging is True when discharging."""
    data = build_coordinator_data()
    data["status"]["energyFlow"]["batteryStatus"] = "BAT_DISCHARGING"
    mock_coordinator.data = data
    sensor = _make_binary_sensor(mock_coordinator, "battery_discharging")
    assert sensor.is_on is True


def test_battery_discharging_off(mock_coordinator: MagicMock) -> None:
    """Test battery_discharging is False when not discharging."""
    sensor = _make_binary_sensor(mock_coordinator, "battery_discharging")
    # Default data has BAT_CHARGING, so discharging should be False
    assert sensor.is_on is False


def test_inverter_power_state_on(mock_coordinator: MagicMock) -> None:
    """Test inverter power state is True when powered on."""
    sensor = _make_binary_sensor(mock_coordinator, "inverter_power_state")
    assert sensor.is_on is True


def test_inverter_power_state_off(mock_coordinator: MagicMock) -> None:
    """Test inverter power state is False when powered off."""
    data = build_coordinator_data()
    data["device"]["powerState"] = False
    mock_coordinator.data = data
    sensor = _make_binary_sensor(mock_coordinator, "inverter_power_state")
    assert sensor.is_on is False


def test_has_unread_notifications_on(mock_coordinator: MagicMock) -> None:
    """Test has_unread_notifications is True when total > 0."""
    sensor = _make_binary_sensor(mock_coordinator, "has_unread_notifications")
    assert sensor.is_on is True


def test_has_unread_notifications_off(mock_coordinator: MagicMock) -> None:
    """Test has_unread_notifications is False when total is 0."""
    data = build_coordinator_data(unread_notifications_count={"total": 0})
    mock_coordinator.data = data
    sensor = _make_binary_sensor(mock_coordinator, "has_unread_notifications")
    assert sensor.is_on is False


def test_unique_id_scoped_to_entry(mock_coordinator: MagicMock) -> None:
    """Test unique_id is scoped to config entry."""
    sensor = _make_binary_sensor(mock_coordinator, "battery_charging")
    assert sensor.unique_id == f"{MOCK_ENTRY_ID}_battery_charging"


def test_is_on_returns_none_on_missing_data(mock_coordinator: MagicMock) -> None:
    """Test is_on returns None when coordinator data is None."""
    mock_coordinator.data = None
    sensor = _make_binary_sensor(mock_coordinator, "battery_charging")
    # With data=None the lambda should get {} via `or {}` and return False
    assert sensor.is_on is False
