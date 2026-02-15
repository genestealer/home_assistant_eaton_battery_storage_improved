"""Tests for the Eaton Battery Storage data update coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_battery_storage.const import DOMAIN
from custom_components.eaton_battery_storage.coordinator import (
    EatonXstorageHomeCoordinator,
)

from .conftest import (
    MOCK_CONFIG_DATA_CUSTOMER,
    MOCK_CONFIG_DATA_TECH,
    MOCK_DEVICE_DATA,
    MOCK_HOST,
    MOCK_INVERTER_SN,
    MOCK_STATUS_DATA,
    _build_api_response,
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


async def test_coordinator_update_success(
    hass: HomeAssistant, mock_api: AsyncMock
) -> None:
    """Test successful data update includes all expected keys."""
    entry = _make_entry(hass)
    coordinator = EatonXstorageHomeCoordinator(hass, mock_api, entry)

    data = await coordinator._async_update_data()

    assert "status" in data
    assert "device" in data
    assert "settings" in data
    assert "config_state" in data
    assert "notifications" in data
    assert "unread_notifications_count" in data
    # Tech account should have technical endpoints
    assert "technical_status" in data
    assert "maintenance_diagnostics" in data


async def test_coordinator_update_customer_skips_tech_endpoints(
    hass: HomeAssistant, mock_api: AsyncMock
) -> None:
    """Test customer account skips technical endpoints."""
    entry = _make_entry(hass, data=dict(MOCK_CONFIG_DATA_CUSTOMER))
    coordinator = EatonXstorageHomeCoordinator(hass, mock_api, entry)

    data = await coordinator._async_update_data()

    assert data["technical_status"] == {}
    assert data["maintenance_diagnostics"] == {}
    # Core data should still be present
    assert data["status"] == MOCK_STATUS_DATA
    # API should NOT have been called for technical endpoints
    mock_api.get_technical_status.assert_not_called()
    mock_api.get_maintenance_diagnostics.assert_not_called()


async def test_coordinator_update_failed_on_status_error(
    hass: HomeAssistant, mock_api: AsyncMock
) -> None:
    """Test UpdateFailed when status endpoint returns error."""
    mock_api.get_status.return_value = {
        "successful": False,
        "result": None,
        "error": "Device offline",
    }
    entry = _make_entry(hass)
    coordinator = EatonXstorageHomeCoordinator(hass, mock_api, entry)

    with pytest.raises(UpdateFailed, match="status"):
        await coordinator._async_update_data()


async def test_coordinator_update_failed_on_device_error(
    hass: HomeAssistant, mock_api: AsyncMock
) -> None:
    """Test UpdateFailed when device endpoint returns error."""
    mock_api.get_device.return_value = {
        "successful": False,
        "result": None,
        "error": "Device offline",
    }
    entry = _make_entry(hass)
    coordinator = EatonXstorageHomeCoordinator(hass, mock_api, entry)

    with pytest.raises(UpdateFailed, match="device"):
        await coordinator._async_update_data()


async def test_coordinator_optional_endpoint_graceful_degradation(
    hass: HomeAssistant, mock_api: AsyncMock
) -> None:
    """Test that optional endpoint failures don't cause UpdateFailed."""
    # Make optional endpoints fail
    mock_api.get_config_state.side_effect = Exception("Boom")
    mock_api.get_settings.side_effect = Exception("Boom")
    mock_api.get_metrics.side_effect = Exception("Boom")
    mock_api.get_metrics_daily.side_effect = Exception("Boom")
    mock_api.get_schedule.side_effect = Exception("Boom")
    mock_api.get_notifications.side_effect = Exception("Boom")
    mock_api.get_unread_notifications_count.side_effect = Exception("Boom")

    entry = _make_entry(hass)
    coordinator = EatonXstorageHomeCoordinator(hass, mock_api, entry)

    data = await coordinator._async_update_data()

    # Core data still present
    assert data["status"] == MOCK_STATUS_DATA
    assert data["device"] == MOCK_DEVICE_DATA
    # Failed optionals default to empty dicts
    assert data["config_state"] == {}
    assert data["settings"] == {}
    assert data["notifications"] == {}


async def test_coordinator_device_info(
    hass: HomeAssistant, mock_api: AsyncMock
) -> None:
    """Test coordinator device_info property."""
    entry = _make_entry(hass)
    coordinator = EatonXstorageHomeCoordinator(hass, mock_api, entry)
    coordinator.data = {
        "device": MOCK_DEVICE_DATA,
        "status": MOCK_STATUS_DATA,
    }

    info = coordinator.device_info
    assert (DOMAIN, MOCK_HOST) in info["identifiers"]
    assert info["name"] == "Eaton xStorage Home"
    assert info["manufacturer"] == "Eaton"
    assert info["sw_version"] == MOCK_DEVICE_DATA["firmwareVersion"]
    assert info["hw_version"] == MOCK_DEVICE_DATA["bmsFirmwareVersion"]
    assert info["serial_number"] == MOCK_INVERTER_SN


async def test_coordinator_device_info_empty_data(
    hass: HomeAssistant, mock_api: AsyncMock
) -> None:
    """Test device_info when data is empty."""
    entry = _make_entry(hass)
    coordinator = EatonXstorageHomeCoordinator(hass, mock_api, entry)
    coordinator.data = {}

    info = coordinator.device_info
    assert info["name"] == "Eaton xStorage Home"
    assert "sw_version" not in info
