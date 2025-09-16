"""Common fixtures and test utilities for Eaton Battery Storage integration tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Mock classes for Home Assistant components when HA is not available
try:
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry
    HA_AVAILABLE = True
except ImportError:
    HA_AVAILABLE = False
    
    class MockHomeAssistant:
        """Mock HomeAssistant class."""
        pass
    
    class MockConfigEntry:
        """Mock ConfigEntry class."""
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    HomeAssistant = MockHomeAssistant
    ConfigEntry = MockConfigEntry

from custom_components.eaton_battery_storage.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Mock config entry fixture."""
    if HA_AVAILABLE:
        return ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="Eaton xStorage Home",
            data={
                "host": "192.168.1.100",
                "username": "admin",
                "password": "password",
                "inverter_sn": "test_serial",
                "email": "test@example.com",
                "has_pv": True,
            },
            options={},
            entry_id="test_entry_id",
            unique_id="test_unique_id",
        )
    else:
        return MockConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="Eaton xStorage Home",
            data={
                "host": "192.168.1.100",
                "username": "admin",
                "password": "password",
                "inverter_sn": "test_serial",
                "email": "test@example.com",
                "has_pv": True,
            },
            options={},
            entry_id="test_entry_id",
            unique_id="test_unique_id",
        )


@pytest.fixture
def mock_api():
    """Mock EatonBatteryAPI fixture."""
    with patch("custom_components.eaton_battery_storage.api.EatonBatteryAPI") as mock:
        api_instance = AsyncMock()
        api_instance.connect.return_value = None
        api_instance.get_device_status.return_value = {
            "successful": True,
            "result": {
                "status": {
                    "operationMode": "IDLE",
                    "batteryLevel": 85,
                    "energyFlow": {
                        "consumptionValue": 1200,
                        "productionValue": 800,
                        "gridValue": 400,
                        "batteryValue": 0,
                    },
                },
            },
        }
        mock.return_value = api_instance
        yield api_instance


@pytest.fixture
def mock_coordinator(mock_api, hass, mock_config_entry):
    """Mock coordinator fixture."""
    with patch("custom_components.eaton_battery_storage.coordinator.EatonXstorageHomeCoordinator") as mock:
        coordinator_instance = AsyncMock()
        coordinator_instance.hass = hass
        coordinator_instance.api = mock_api
        coordinator_instance.config_entry = mock_config_entry
        coordinator_instance.last_update_success = True
        coordinator_instance.data = {
            "status": {
                "operationMode": "IDLE",
                "batteryLevel": 85,
            }
        }
        coordinator_instance.async_config_entry_first_refresh = AsyncMock()
        mock.return_value = coordinator_instance
        yield coordinator_instance


@pytest.fixture
def hass():
    """Mock HomeAssistant fixture."""
    if HA_AVAILABLE:
        # Return a real mock for when HA is available
        return Mock(spec=HomeAssistant)
    else:
        # Return a simple mock when HA is not available
        return MockHomeAssistant()


@pytest.fixture
def mock_successful_auth_response():
    """Mock successful authentication response."""
    return {
        "successful": True,
        "result": {
            "token": "mock_access_token",
        }
    }


@pytest.fixture
def mock_failed_auth_response():
    """Mock failed authentication response."""
    return {
        "successful": False,
        "error": {
            "description": "Invalid credentials",
            "errCode": "AUTH_FAILED"
        }
    }


@pytest.fixture
def mock_device_status_response():
    """Mock device status response."""
    return {
        "successful": True,
        "result": {
            "status": {
                "operationMode": "IDLE",
                "batteryLevel": 85,
                "energyFlow": {
                    "consumptionValue": 1200,
                    "productionValue": 800,
                    "gridValue": 400,
                    "batteryValue": 0,
                    "acPvValue": 500,
                    "dcPvValue": 300,
                },
                "today": {
                    "gridConsumption": 15.5,
                    "gridInjection": 8.2,
                    "photovoltaicProduction": 12.8,
                },
            },
            "device": {
                "serialNumber": "test_serial",
                "modelName": "xStorage Home",
                "softwareVersion": "1.0.0",
            },
        }
    }