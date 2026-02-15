"""Tests for the Eaton Battery Storage __init__ (setup / unload)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_battery_storage.const import DOMAIN

from .conftest import (
    MOCK_CONFIG_DATA_CUSTOMER,
    MOCK_CONFIG_DATA_TECH,
    MOCK_ENTRY_ID,
    MOCK_HOST,
    MOCK_INVERTER_SN,
    build_coordinator_data,
)


def _make_entry(hass: HomeAssistant, data: dict | None = None) -> MockConfigEntry:
    """Create a MockConfigEntry and add it to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Eaton xStorage Home",
        data=data or dict(MOCK_CONFIG_DATA_TECH),
        unique_id=f"{MOCK_HOST}_{MOCK_INVERTER_SN}",
    )
    entry.add_to_hass(hass)
    return entry


async def test_setup_entry_success(hass: HomeAssistant, mock_api: AsyncMock) -> None:
    """Test successful integration setup."""
    entry = _make_entry(hass)

    with (
        patch(
            "custom_components.eaton_battery_storage.EatonBatteryAPI",
            return_value=mock_api,
        ),
        patch(
            "custom_components.eaton_battery_storage.EatonXstorageHomeCoordinator"
        ) as mock_coord_cls,
    ):
        coord_instance = MagicMock()
        coord_instance.data = build_coordinator_data()
        coord_instance.async_config_entry_first_refresh = AsyncMock()
        coord_instance.device_info = {}
        mock_coord_cls.return_value = coord_instance

        result = await hass.config_entries.async_setup(entry.entry_id)

    assert result is True
    assert entry.state is ConfigEntryState.LOADED


async def test_setup_entry_connect_failure(
    hass: HomeAssistant, mock_api: AsyncMock
) -> None:
    """Test that ConfigEntryNotReady is raised when the device is unreachable."""
    mock_api.connect.side_effect = OSError("Network unreachable")
    entry = _make_entry(hass)

    with patch(
        "custom_components.eaton_battery_storage.EatonBatteryAPI",
        return_value=mock_api,
    ):
        await hass.config_entries.async_setup(entry.entry_id)

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_entry_first_refresh_failure(
    hass: HomeAssistant, mock_api: AsyncMock
) -> None:
    """Test that ConfigEntryNotReady is raised when first refresh fails."""
    entry = _make_entry(hass)

    with (
        patch(
            "custom_components.eaton_battery_storage.EatonBatteryAPI",
            return_value=mock_api,
        ),
        patch(
            "custom_components.eaton_battery_storage.EatonXstorageHomeCoordinator"
        ) as mock_coord_cls,
    ):
        coord_instance = MagicMock()
        coord_instance.async_config_entry_first_refresh = AsyncMock(
            side_effect=Exception("API Timeout")
        )
        mock_coord_cls.return_value = coord_instance

        await hass.config_entries.async_setup(entry.entry_id)

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(hass: HomeAssistant, mock_api: AsyncMock) -> None:
    """Test that integration unloads cleanly."""
    entry = _make_entry(hass)

    with (
        patch(
            "custom_components.eaton_battery_storage.EatonBatteryAPI",
            return_value=mock_api,
        ),
        patch(
            "custom_components.eaton_battery_storage.EatonXstorageHomeCoordinator"
        ) as mock_coord_cls,
    ):
        coord_instance = MagicMock()
        coord_instance.data = build_coordinator_data()
        coord_instance.async_config_entry_first_refresh = AsyncMock()
        coord_instance.device_info = {}
        mock_coord_cls.return_value = coord_instance

        await hass.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.LOADED

        result = await hass.config_entries.async_unload(entry.entry_id)

    assert result is True
    assert entry.state is ConfigEntryState.NOT_LOADED
