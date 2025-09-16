"""Test coordinator for Eaton Battery Storage integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.eaton_battery_storage.coordinator import EatonXstorageHomeCoordinator
from custom_components.eaton_battery_storage.const import DOMAIN


class TestEatonXstorageHomeCoordinator:
    """Test the coordinator class."""

    @pytest.fixture
    def coordinator(self, hass: HomeAssistant, mock_api, mock_config_entry):
        """Create a coordinator instance for testing."""
        return EatonXstorageHomeCoordinator(hass, mock_api, mock_config_entry)

    async def test_init(self, coordinator, mock_api, mock_config_entry):
        """Test coordinator initialization."""
        assert coordinator.api == mock_api
        assert coordinator.config_entry == mock_config_entry
        assert coordinator.name == "Eaton xStorage Home"
        assert coordinator.update_interval.total_seconds() == 60  # 1 minute

    async def test_battery_level_property(self, coordinator):
        """Test battery level property."""
        # Test with valid data
        coordinator.data = {
            "status": {
                "energyFlow": {
                    "stateOfCharge": 85
                }
            }
        }
        assert coordinator.battery_level == 85

        # Test with missing data
        coordinator.data = {}
        assert coordinator.battery_level is None

        # Test with None data
        coordinator.data = None
        assert coordinator.battery_level is None

        # Test with invalid structure
        coordinator.data = {
            "status": {
                "other": "data"
            }
        }
        assert coordinator.battery_level is None

    async def test_device_info_basic(self, coordinator, mock_api):
        """Test device info with minimal data."""
        coordinator.data = {}
        
        device_info = coordinator.device_info

        assert device_info["identifiers"] == {(DOMAIN, mock_api.host)}
        assert device_info["name"] == "Eaton xStorage Home"
        assert device_info["manufacturer"] == "Eaton"
        assert device_info["model"] == "xStorage Home"
        assert device_info["configuration_url"] == f"https://{mock_api.host}"

    async def test_device_info_full(self, coordinator, mock_api):
        """Test device info with full device data."""
        coordinator.data = {
            "device": {
                "firmwareVersion": "1.2.3",
                "inverterModelName": "Test Inverter",
                "inverterSerialNumber": "INV123456",
                "bmsFirmwareVersion": "2.1.0"
            }
        }
        
        device_info = coordinator.device_info

        assert device_info["sw_version"] == "1.2.3"
        assert device_info["model"] == "xStorage Home (Test Inverter)"
        assert device_info["serial_number"] == "INV123456"
        assert device_info["hw_version"] == "2.1.0"
        assert (DOMAIN, "INV123456") in device_info["identifiers"]

    async def test_async_update_data_success(self, coordinator, mock_api):
        """Test successful data update."""
        # Mock all API methods
        mock_api.get_status.return_value = {"result": {"operationMode": "IDLE"}}
        mock_api.get_device.return_value = {"result": {"serialNumber": "123"}}
        mock_api.get_config_state.return_value = {"result": {"state": "ready"}}
        mock_api.get_settings.return_value = {"result": {"defaultMode": "BASIC"}}
        mock_api.get_metrics.return_value = {"result": {"power": 1000}}
        mock_api.get_metrics_daily.return_value = {"result": {"energy": 25.5}}
        mock_api.get_schedule.return_value = {"result": {"events": []}}
        mock_api.get_technical_status.return_value = {"result": {"voltage": 48.2}}
        mock_api.get_maintenance_diagnostics.return_value = {"result": {"health": "good"}}
        mock_api.get_notifications.return_value = {"result": {"messages": []}}
        mock_api.get_unread_notifications_count.return_value = {"result": {"count": 0}}

        result = await coordinator._async_update_data()

        assert result["status"] == {"operationMode": "IDLE"}
        assert result["device"] == {"serialNumber": "123"}
        assert result["config_state"] == {"state": "ready"}
        assert result["settings"] == {"defaultMode": "BASIC"}
        assert result["metrics"] == {"power": 1000}
        assert result["metrics_daily"] == {"energy": 25.5}
        assert result["schedule"] == {"events": []}
        assert result["technical_status"] == {"voltage": 48.2}
        assert result["maintenance_diagnostics"] == {"health": "good"}
        assert result["notifications"] == {"messages": []}
        assert result["unread_notifications_count"] == {"count": 0}

    async def test_async_update_data_partial_failure(self, coordinator, mock_api):
        """Test data update with some endpoints failing."""
        # Mock successful core endpoints
        mock_api.get_status.return_value = {"result": {"operationMode": "IDLE"}}
        mock_api.get_device.return_value = {"result": {"serialNumber": "123"}}
        
        # Mock failed optional endpoints
        mock_api.get_config_state.side_effect = Exception("Config state error")
        mock_api.get_settings.side_effect = Exception("Settings error")
        mock_api.get_metrics.return_value = {"result": {"power": 1000}}
        mock_api.get_metrics_daily.return_value = None  # No data returned
        mock_api.get_schedule.return_value = {"result": {"events": []}}
        mock_api.get_technical_status.side_effect = Exception("Tech status error")
        mock_api.get_maintenance_diagnostics.side_effect = Exception("Diagnostics error")
        mock_api.get_notifications.side_effect = Exception("Notifications error")
        mock_api.get_unread_notifications_count.side_effect = Exception("Count error")

        result = await coordinator._async_update_data()

        # Core data should be present
        assert result["status"] == {"operationMode": "IDLE"}
        assert result["device"] == {"serialNumber": "123"}
        
        # Failed endpoints should have empty dicts
        assert result["config_state"] == {}
        assert result["settings"] == {}
        assert result["metrics_daily"] == {}
        assert result["technical_status"] == {}
        assert result["maintenance_diagnostics"] == {}
        assert result["notifications"] == {}
        assert result["unread_notifications_count"] == {}
        
        # Successful optional endpoint should have data
        assert result["metrics"] == {"power": 1000}
        assert result["schedule"] == {"events": []}

    async def test_async_update_data_core_failure(self, coordinator, mock_api):
        """Test data update with core endpoints failing."""
        # Mock failed core endpoints (should still not raise UpdateFailed)
        mock_api.get_status.side_effect = Exception("Status error")
        mock_api.get_device.side_effect = Exception("Device error")
        
        # Mock successful optional endpoints
        mock_api.get_config_state.return_value = {"result": {"state": "ready"}}
        mock_api.get_settings.return_value = {"result": {"defaultMode": "BASIC"}}
        mock_api.get_metrics.return_value = {"result": {"power": 1000}}
        mock_api.get_metrics_daily.return_value = {"result": {"energy": 25.5}}
        mock_api.get_schedule.return_value = {"result": {"events": []}}
        mock_api.get_technical_status.return_value = {"result": {"voltage": 48.2}}
        mock_api.get_maintenance_diagnostics.return_value = {"result": {"health": "good"}}
        mock_api.get_notifications.return_value = {"result": {"messages": []}}
        mock_api.get_unread_notifications_count.return_value = {"result": {"count": 0}}

        result = await coordinator._async_update_data()

        # Core endpoints should have empty dicts due to failure
        assert result["status"] == {}
        assert result["device"] == {}
        
        # Optional endpoints should still have data
        assert result["config_state"] == {"state": "ready"}
        assert result["settings"] == {"defaultMode": "BASIC"}

    async def test_async_update_data_api_exception(self, coordinator, mock_api):
        """Test data update when API methods raise exceptions that should cause UpdateFailed."""
        # Mock an exception that should propagate as UpdateFailed
        mock_api.get_status.side_effect = Exception("Critical API error")
        mock_api.get_device.side_effect = Exception("Critical API error")
        
        # This should not raise UpdateFailed since individual endpoint failures are handled
        result = await coordinator._async_update_data()
        
        # Should return empty results for failed endpoints
        assert result["status"] == {}
        assert result["device"] == {}

    async def test_async_update_data_non_dict_response(self, coordinator, mock_api):
        """Test data update with non-dict API responses."""
        # Mock responses that are not dicts
        mock_api.get_status.return_value = "not a dict"
        mock_api.get_device.return_value = ["not", "a", "dict"]
        mock_api.get_config_state.return_value = {"no_result": "here"}
        mock_api.get_settings.return_value = None
        mock_api.get_metrics.return_value = {"result": {"power": 1000}}
        mock_api.get_metrics_daily.return_value = {"result": {"energy": 25.5}}
        mock_api.get_schedule.return_value = {"result": {"events": []}}
        mock_api.get_technical_status.return_value = {"result": {"voltage": 48.2}}
        mock_api.get_maintenance_diagnostics.return_value = {"result": {"health": "good"}}
        mock_api.get_notifications.return_value = {"result": {"messages": []}}
        mock_api.get_unread_notifications_count.return_value = {"result": {"count": 0}}

        result = await coordinator._async_update_data()

        # Non-dict responses should be handled gracefully
        assert result["status"] == {}  # "not a dict" -> no result key
        assert result["device"] == {}  # ["not", "a", "dict"] -> no result key
        assert result["config_state"] == {"no_result": "here"}  # No result key but still a dict
        assert result["settings"] == {}  # None response

    async def test_backward_compatibility_alias(self):
        """Test that the backward compatibility alias exists."""
        from custom_components.eaton_battery_storage.coordinator import EatonBatteryStorageCoordinator
        
        assert EatonBatteryStorageCoordinator is EatonXstorageHomeCoordinator