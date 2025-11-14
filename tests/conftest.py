"""Common test fixtures and configuration for Eaton Battery Storage tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from custom_components.eaton_battery_storage.config_flow import CONF_INVERTER_SN
from custom_components.eaton_battery_storage.const import DOMAIN


@pytest.fixture
async def hass():
    """Return a Home Assistant instance for testing."""
    # Create a minimal mock Home Assistant instance
    hass = Mock(spec=HomeAssistant)
    hass.data = {}
    hass.config = Mock()
    hass.config.config_dir = "/tmp/test_config"
    hass.config.path = lambda *args: "/tmp/test_config/" + "/".join(args)

    # Mock config entries
    hass.config_entries = Mock()
    hass.config_entries.flow = Mock()
    hass.config_entries.flow.async_init = AsyncMock()
    hass.config_entries.flow.async_configure = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_setup = AsyncMock(return_value=True)

    # Mock options flow
    hass.config_entries.options = Mock()
    hass.config_entries.options.async_init = AsyncMock()
    hass.config_entries.options.async_configure = AsyncMock()

    # Mock services
    hass.services = Mock()
    hass.services.async_register = Mock()

    # Mock states
    hass.states = Mock()
    hass.states.async_set = Mock()

    return hass


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Return a mock config entry."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Eaton xStorage Home",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
            CONF_INVERTER_SN: "TEST123456",
            "email": "test@example.com",
        },
        options={},
        entry_id="test_entry_id",
        unique_id="192.168.1.100_TEST123456",
    )


@pytest.fixture
def mock_api_response_success() -> dict[str, Any]:
    """Return a successful API response."""
    return {
        "successful": True,
        "result": {
            "token": "test_access_token",
            "refreshToken": "test_refresh_token",
            "expiresIn": 3600,
        },
    }


@pytest.fixture
def mock_device_status() -> dict[str, Any]:
    """Return mock device status data."""
    return {
        "successful": True,
        "result": {
            "energyFlow": {
                "consumption": 1500,
                "production": 2000,
                "gridRole": "consumption",
                "gridValue": 500,
                "batteryRole": "charging",
                "batteryValue": 1000,
            },
            "battery": {
                "charge": 75,
                "status": "CHARGING",
            },
            "today": {
                "consumption": 25.5,
                "production": 30.2,
                "gridFeedin": 4.7,
                "gridConsumption": 0.0,
                "photovoltaicProduction": 30.2,
                "batteryCharging": 20.0,
                "batteryDischarging": 15.5,
            },
        },
    }


@pytest.fixture
def mock_device_info() -> dict[str, Any]:
    """Return mock device information."""
    return {
        "successful": True,
        "result": {
            "inverterSn": "TEST123456",
            "firmwareVersion": "1.2.3",
            "deviceType": "xStorage Home",
            "inverterNominalVac": 230,
            "inverterNominalVpv": 450,
            "timezone": {"name": "Europe/London"},
        },
    }


@pytest.fixture
def mock_api():
    """Return a mock API instance."""
    with patch("custom_components.eaton_battery_storage.api.EatonBatteryAPI") as mock:
        api_instance = AsyncMock()
        api_instance.connect = AsyncMock()
        api_instance.get_status = AsyncMock()
        api_instance.get_device = AsyncMock()
        api_instance.get_config_state = AsyncMock()
        api_instance.get_settings = AsyncMock()
        api_instance.get_metrics = AsyncMock()
        api_instance.get_metrics_daily = AsyncMock()
        api_instance.get_schedule = AsyncMock()
        api_instance.get_technical_status = AsyncMock()
        api_instance.get_maintenance_diagnostics = AsyncMock()
        api_instance.get_notifications = AsyncMock()
        api_instance.get_unread_notifications_count = AsyncMock()
        mock.return_value = api_instance
        yield api_instance


@pytest.fixture
def mock_storage():
    """Mock storage for token persistence."""
    with patch("homeassistant.helpers.storage.Store") as mock_store_class:
        mock_store = AsyncMock(spec=Store)
        mock_store.async_load = AsyncMock(return_value=None)
        mock_store.async_save = AsyncMock()
        mock_store_class.return_value = mock_store
        yield mock_store
