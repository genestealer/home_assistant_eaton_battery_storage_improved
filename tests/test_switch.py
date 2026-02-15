"""Tests for the Eaton Battery Storage switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.eaton_battery_storage.switch import (
    EatonXStorageEnergySavingModeSwitch,
    EatonXStoragePowerSwitch,
)

from .conftest import (
    MOCK_ENTRY_ID,
    MOCK_SETTINGS_DATA,
    _build_api_response,
    build_coordinator_data,
)


# ---------------------------------------------------------------------------
# Power switch tests
# ---------------------------------------------------------------------------


def test_power_switch_is_on(mock_coordinator: MagicMock) -> None:
    """Test power switch reads powerState from data."""
    sw = EatonXStoragePowerSwitch(mock_coordinator)
    assert sw.is_on is True


def test_power_switch_is_off(mock_coordinator: MagicMock) -> None:
    """Test power switch off when powerState is False."""
    data = build_coordinator_data()
    data["device"]["powerState"] = False
    mock_coordinator.data = data
    sw = EatonXStoragePowerSwitch(mock_coordinator)
    assert sw.is_on is False


def test_power_switch_unique_id(mock_coordinator: MagicMock) -> None:
    """Test power switch unique_id is scoped to entry."""
    sw = EatonXStoragePowerSwitch(mock_coordinator)
    assert sw.unique_id == f"{MOCK_ENTRY_ID}_inverter_power"


@pytest.mark.parametrize("turn_on", [True, False])
async def test_power_switch_turn_on_off(
    mock_coordinator: MagicMock, turn_on: bool
) -> None:
    """Test turning the power switch on and off calls the API."""
    sw = EatonXStoragePowerSwitch(mock_coordinator)
    sw.hass = mock_coordinator.hass
    sw.async_write_ha_state = MagicMock()

    with patch("custom_components.eaton_battery_storage.switch.asyncio.sleep"):
        if turn_on:
            await sw.async_turn_on()
        else:
            await sw.async_turn_off()

    mock_coordinator.api.set_device_power.assert_awaited_once_with(turn_on)
    mock_coordinator.async_request_refresh.assert_awaited()


async def test_power_switch_turn_on_error(mock_coordinator: MagicMock) -> None:
    """Test that API error raises HomeAssistantError."""
    mock_coordinator.api.set_device_power.side_effect = Exception("API down")
    sw = EatonXStoragePowerSwitch(mock_coordinator)
    sw.hass = mock_coordinator.hass
    sw.async_write_ha_state = MagicMock()

    with pytest.raises(HomeAssistantError, match="Failed to turn on device"):
        await sw.async_turn_on()


def test_power_switch_optimistic_cleared_on_update(
    mock_coordinator: MagicMock,
) -> None:
    """Test optimistic state cleared when coordinator updates."""
    sw = EatonXStoragePowerSwitch(mock_coordinator)
    sw._optimistic_state = True
    sw.async_write_ha_state = MagicMock()
    sw._handle_coordinator_update()
    assert sw._optimistic_state is None


# ---------------------------------------------------------------------------
# Energy Saving Mode switch tests
# ---------------------------------------------------------------------------


def test_energy_saving_mode_is_off(mock_coordinator: MagicMock) -> None:
    """Test ESM is off (default MOCK_SETTINGS_DATA has enabled=False)."""
    sw = EatonXStorageEnergySavingModeSwitch(mock_coordinator)
    assert sw.is_on is False


def test_energy_saving_mode_is_on(mock_coordinator: MagicMock) -> None:
    """Test ESM is on when enabled."""
    data = build_coordinator_data()
    data["settings"]["energySavingMode"]["enabled"] = True
    mock_coordinator.data = data
    sw = EatonXStorageEnergySavingModeSwitch(mock_coordinator)
    assert sw.is_on is True


async def test_energy_saving_mode_turn_on(mock_coordinator: MagicMock) -> None:
    """Test turning on energy saving mode."""
    mock_coordinator.api.get_settings.return_value = _build_api_response(
        dict(MOCK_SETTINGS_DATA)
    )
    sw = EatonXStorageEnergySavingModeSwitch(mock_coordinator)
    sw.hass = mock_coordinator.hass
    sw.async_write_ha_state = MagicMock()

    with patch("custom_components.eaton_battery_storage.switch.asyncio.sleep"):
        await sw.async_turn_on()

    mock_coordinator.api.update_settings.assert_awaited_once()
    call_args = mock_coordinator.api.update_settings.call_args[0][0]
    assert call_args["settings"]["energySavingMode"]["enabled"] is True


async def test_energy_saving_mode_turn_off(mock_coordinator: MagicMock) -> None:
    """Test turning off energy saving mode."""
    mock_coordinator.api.get_settings.return_value = _build_api_response(
        dict(MOCK_SETTINGS_DATA)
    )
    sw = EatonXStorageEnergySavingModeSwitch(mock_coordinator)
    sw.hass = mock_coordinator.hass
    sw.async_write_ha_state = MagicMock()

    with patch("custom_components.eaton_battery_storage.switch.asyncio.sleep"):
        await sw.async_turn_off()

    call_args = mock_coordinator.api.update_settings.call_args[0][0]
    assert call_args["settings"]["energySavingMode"]["enabled"] is False


async def test_energy_saving_mode_error(mock_coordinator: MagicMock) -> None:
    """Test ESM turn on raises HomeAssistantError on API failure."""
    mock_coordinator.api.get_settings.side_effect = Exception("API timeout")
    sw = EatonXStorageEnergySavingModeSwitch(mock_coordinator)
    sw.hass = mock_coordinator.hass
    sw.async_write_ha_state = MagicMock()

    with pytest.raises(HomeAssistantError, match="Failed to enable energy saving mode"):
        await sw.async_turn_on()


def test_energy_saving_mode_available(mock_coordinator: MagicMock) -> None:
    """Test ESM availability check."""
    sw = EatonXStorageEnergySavingModeSwitch(mock_coordinator)
    assert sw.available is True
    mock_coordinator.data = None
    assert sw.available is False
