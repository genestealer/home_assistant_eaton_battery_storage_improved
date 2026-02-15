"""Tests for the Eaton Battery Storage sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.eaton_battery_storage.sensor import (
    SENSOR_TYPES,
    EatonXStorageNotificationsSensor,
    EatonXStorageSensor,
)
from custom_components.eaton_battery_storage.const import (
    ACCOUNT_TYPE_CUSTOMER,
    ACCOUNT_TYPE_TECHNICIAN,
    TECHNICIAN_ONLY_SENSORS,
)

from .conftest import (
    MOCK_ENTRY_ID,
    MOCK_NOTIFICATIONS_DATA,
    build_coordinator_data,
)


# ---------------------------------------------------------------------------
# EatonXStorageSensor basic tests
# ---------------------------------------------------------------------------


def test_sensor_unique_id(mock_coordinator: MagicMock) -> None:
    """Test sensor unique_id is scoped to entry."""
    key = "status.energyFlow.stateOfCharge"
    desc = SENSOR_TYPES[key]
    sensor = EatonXStorageSensor(mock_coordinator, key, desc, has_pv=False)
    assert sensor.unique_id == f"{MOCK_ENTRY_ID}_{key}"


def test_sensor_state_of_charge_value(mock_coordinator: MagicMock) -> None:
    """Test state_of_charge returns 72 from mock data."""
    key = "status.energyFlow.stateOfCharge"
    desc = SENSOR_TYPES[key]
    sensor = EatonXStorageSensor(mock_coordinator, key, desc, has_pv=False)
    assert sensor.native_value == 72


def test_sensor_battery_status_mapped(mock_coordinator: MagicMock) -> None:
    """Test battery status is mapped to human-readable string."""
    key = "status.energyFlow.batteryStatus"
    desc = SENSOR_TYPES[key]
    sensor = EatonXStorageSensor(mock_coordinator, key, desc, has_pv=False)
    # BAT_CHARGING should map via BMS_STATE_MAP to "Charging"
    assert sensor.native_value == "Charging"


def test_sensor_none_when_data_empty(mock_coordinator: MagicMock) -> None:
    """Test sensor returns None when coordinator data is empty."""
    mock_coordinator.data = {}
    key = "status.energyFlow.stateOfCharge"
    desc = SENSOR_TYPES[key]
    sensor = EatonXStorageSensor(mock_coordinator, key, desc, has_pv=False)
    assert sensor.native_value is None


# ---------------------------------------------------------------------------
# Notifications sensor tests
# ---------------------------------------------------------------------------


def test_notifications_sensor_count(mock_coordinator: MagicMock) -> None:
    """Test notifications sensor returns count of notifications."""
    sensor = EatonXStorageNotificationsSensor(mock_coordinator)
    assert sensor.native_value == 1


def test_notifications_sensor_empty(mock_coordinator: MagicMock) -> None:
    """Test notifications sensor returns 0 when empty."""
    data = build_coordinator_data(notifications={"results": []})
    mock_coordinator.data = data
    sensor = EatonXStorageNotificationsSensor(mock_coordinator)
    assert sensor.native_value == 0


def test_notifications_sensor_unique_id(mock_coordinator: MagicMock) -> None:
    """Test notifications sensor unique_id."""
    sensor = EatonXStorageNotificationsSensor(mock_coordinator)
    assert sensor.unique_id == f"{MOCK_ENTRY_ID}_notifications"


def test_notifications_sensor_attributes(mock_coordinator: MagicMock) -> None:
    """Test notifications sensor extra state attributes."""
    sensor = EatonXStorageNotificationsSensor(mock_coordinator)
    attrs = sensor.extra_state_attributes
    assert "notifications" in attrs
    assert isinstance(attrs["notifications"], list)


# ---------------------------------------------------------------------------
# Sensor setup filtering tests
# ---------------------------------------------------------------------------


def test_technician_only_sensors_defined() -> None:
    """Test all TECHNICIAN_ONLY_SENSORS exist in SENSOR_TYPES."""
    for key in TECHNICIAN_ONLY_SENSORS:
        assert key in SENSOR_TYPES, f"Missing sensor key: {key}"


def test_pv_related_sensors_marked() -> None:
    """Test that PV-related sensors have pv_related=True."""
    pv_sensors = [k for k, v in SENSOR_TYPES.items() if v.get("pv_related", False)]
    assert len(pv_sensors) > 0
