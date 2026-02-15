"""Tests for the Eaton Battery Storage number platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.eaton_battery_storage.number import (
    EatonBatteryNumberEntity,
    EatonXStorageBatteryBackupLevelNumber,
    EatonXStorageHouseConsumptionThresholdNumber,
)
from custom_components.eaton_battery_storage.number_constants import NUMBER_ENTITIES

from .conftest import (
    MOCK_ENTRY_ID,
    MOCK_SETTINGS_DATA,
    _build_api_response,
    build_coordinator_data,
)


# ---------------------------------------------------------------------------
# EatonBatteryNumberEntity (configurable / stored values)
# ---------------------------------------------------------------------------


def test_number_entity_attributes(mock_coordinator: MagicMock) -> None:
    """Test number entity has correct attributes from description."""
    desc = NUMBER_ENTITIES[0]  # first definition
    entity = EatonBatteryNumberEntity(mock_coordinator, desc)
    assert entity.unique_id == f"{MOCK_ENTRY_ID}_{desc['key']}"
    assert entity.name == desc["name"]
    assert entity.native_min_value == float(desc["min"])
    assert entity.native_max_value == float(desc["max"])
    assert entity.native_step == float(desc["step"])


def test_number_entity_native_value_from_storage(mock_coordinator: MagicMock) -> None:
    """Test native_value reads from coordinator.number_values."""
    desc = NUMBER_ENTITIES[0]
    mock_coordinator.number_values = {desc["key"]: 42.0}
    entity = EatonBatteryNumberEntity(mock_coordinator, desc)
    assert entity.native_value == 42.0


def test_number_entity_native_value_none(mock_coordinator: MagicMock) -> None:
    """Test native_value returns None when key not in storage."""
    desc = NUMBER_ENTITIES[0]
    mock_coordinator.number_values = {}
    entity = EatonBatteryNumberEntity(mock_coordinator, desc)
    assert entity.native_value is None


def test_number_entity_charge_power_extra_attrs(mock_coordinator: MagicMock) -> None:
    """Test extra_state_attributes shows wattage for charge_power."""
    # Find the charge_power description
    desc = next(d for d in NUMBER_ENTITIES if d["key"] == "charge_power")
    mock_coordinator.number_values = {"charge_power": 50}
    entity = EatonBatteryNumberEntity(mock_coordinator, desc)
    attrs = entity.extra_state_attributes
    assert attrs is not None
    assert "wattage" in attrs
    assert attrs["wattage"] == int(round((50 / 100) * 3600))


# ---------------------------------------------------------------------------
# House Consumption Threshold number
# ---------------------------------------------------------------------------


def test_house_consumption_unique_id(mock_coordinator: MagicMock) -> None:
    """Test unique_id is scoped to entry."""
    entity = EatonXStorageHouseConsumptionThresholdNumber(mock_coordinator)
    assert entity.unique_id == f"{MOCK_ENTRY_ID}_set_house_consumption_threshold"


def test_house_consumption_native_value(mock_coordinator: MagicMock) -> None:
    """Test native_value reads from settings."""
    entity = EatonXStorageHouseConsumptionThresholdNumber(mock_coordinator)
    assert entity.native_value == 500


async def test_house_consumption_set_value(mock_coordinator: MagicMock) -> None:
    """Test setting house consumption calls update_settings."""
    mock_coordinator.api.get_settings.return_value = _build_api_response(
        dict(MOCK_SETTINGS_DATA)
    )
    entity = EatonXStorageHouseConsumptionThresholdNumber(mock_coordinator)
    entity.hass = mock_coordinator.hass
    entity.async_write_ha_state = MagicMock()

    with patch("custom_components.eaton_battery_storage.number.asyncio.sleep"):
        await entity.async_set_native_value(750)

    mock_coordinator.api.update_settings.assert_awaited_once()
    payload = mock_coordinator.api.update_settings.call_args[0][0]
    assert payload["settings"]["energySavingMode"]["houseConsumptionThreshold"] == 750


async def test_house_consumption_set_value_error(mock_coordinator: MagicMock) -> None:
    """Test error raises HomeAssistantError."""
    mock_coordinator.api.get_settings.side_effect = Exception("Boom")
    entity = EatonXStorageHouseConsumptionThresholdNumber(mock_coordinator)
    entity.hass = mock_coordinator.hass
    entity.async_write_ha_state = MagicMock()

    with pytest.raises(HomeAssistantError, match="Failed to set house consumption"):
        await entity.async_set_native_value(750)


def test_house_consumption_available(mock_coordinator: MagicMock) -> None:
    """Test availability check."""
    entity = EatonXStorageHouseConsumptionThresholdNumber(mock_coordinator)
    assert entity.available is True
    mock_coordinator.data = None
    assert entity.available is False


# ---------------------------------------------------------------------------
# Battery Backup Level number
# ---------------------------------------------------------------------------


def test_battery_backup_unique_id(mock_coordinator: MagicMock) -> None:
    """Test unique_id is scoped to entry."""
    entity = EatonXStorageBatteryBackupLevelNumber(mock_coordinator)
    assert entity.unique_id == f"{MOCK_ENTRY_ID}_set_battery_backup_level"


def test_battery_backup_native_value(mock_coordinator: MagicMock) -> None:
    """Test native_value reads bmsBackupLevel from settings."""
    entity = EatonXStorageBatteryBackupLevelNumber(mock_coordinator)
    assert entity.native_value == 10


async def test_battery_backup_set_value(mock_coordinator: MagicMock) -> None:
    """Test setting battery backup calls update_settings."""
    mock_coordinator.api.get_settings.return_value = _build_api_response(
        dict(MOCK_SETTINGS_DATA)
    )
    entity = EatonXStorageBatteryBackupLevelNumber(mock_coordinator)
    entity.hass = mock_coordinator.hass
    entity.async_write_ha_state = MagicMock()

    with patch("custom_components.eaton_battery_storage.number.asyncio.sleep"):
        await entity.async_set_native_value(25)

    mock_coordinator.api.update_settings.assert_awaited_once()
    payload = mock_coordinator.api.update_settings.call_args[0][0]
    assert payload["settings"]["bmsBackupLevel"] == 25


async def test_battery_backup_set_value_error(mock_coordinator: MagicMock) -> None:
    """Test error raises HomeAssistantError."""
    mock_coordinator.api.get_settings.side_effect = Exception("Boom")
    entity = EatonXStorageBatteryBackupLevelNumber(mock_coordinator)
    entity.hass = mock_coordinator.hass
    entity.async_write_ha_state = MagicMock()

    with pytest.raises(HomeAssistantError, match="Failed to set battery backup level"):
        await entity.async_set_native_value(25)


def test_battery_backup_optimistic_cleared_on_update(
    mock_coordinator: MagicMock,
) -> None:
    """Test optimistic value cleared on coordinator update."""
    entity = EatonXStorageBatteryBackupLevelNumber(mock_coordinator)
    entity._optimistic_value = 50
    entity.async_write_ha_state = MagicMock()
    entity._handle_coordinator_update()
    assert entity._optimistic_value is None
