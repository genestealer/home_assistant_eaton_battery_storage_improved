"""Test the Eaton Battery Storage coordinator."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.eaton_battery_storage.const import DOMAIN
from custom_components.eaton_battery_storage.coordinator import (
    EatonXstorageHomeCoordinator,
)


@pytest.mark.asyncio
class TestEatonXstorageHomeCoordinator:
    """Test the EatonXstorageHomeCoordinator class."""

    @pytest.fixture
    def mock_api(self):
        """Return a mock API instance."""
        api = AsyncMock()
        api.get_status = AsyncMock()
        api.get_device = AsyncMock()
        api.get_config_state = AsyncMock()
        api.get_settings = AsyncMock()
        api.get_metrics = AsyncMock()
        api.get_metrics_daily = AsyncMock()
        api.get_schedule = AsyncMock()
        api.get_technical_status = AsyncMock()
        api.get_maintenance_diagnostics = AsyncMock()
        api.get_notifications = AsyncMock()
        api.get_unread_notifications_count = AsyncMock()
        return api

    @pytest.fixture
    def coordinator(self, hass: HomeAssistant, mock_api, mock_config_entry):
        """Return a coordinator instance for testing."""
        return EatonXstorageHomeCoordinator(hass, mock_api, mock_config_entry)

    async def test_init(self, coordinator, mock_api, mock_config_entry):
        """Test coordinator initialization."""
        assert coordinator.api == mock_api
        assert coordinator.config_entry == mock_config_entry
        assert coordinator.update_interval == timedelta(seconds=30)
        assert coordinator.name == "Eaton xStorage Home"

    async def test_device_info(self, coordinator):
        """Test device info property."""
        # Mock the data with device information
        coordinator.data = {
            "device": {
                "inverterSn": "TEST123456",
                "firmwareVersion": "1.2.3",
                "deviceType": "xStorage Home",
            }
        }

        device_info = coordinator.device_info

        assert device_info["identifiers"] == {(DOMAIN, "TEST123456")}
        assert device_info["name"] == "Eaton xStorage Home"
        assert device_info["manufacturer"] == "Eaton"
        assert device_info["model"] == "xStorage Home"
        assert device_info["sw_version"] == "1.2.3"

    async def test_device_info_missing_data(self, coordinator):
        """Test device info property with missing data."""
        coordinator.data = {}

        device_info = coordinator.device_info

        assert device_info["identifiers"] == {(DOMAIN, "unknown")}
        assert device_info["name"] == "Eaton xStorage Home"
        assert device_info["manufacturer"] == "Eaton"
        assert device_info["model"] == "Unknown"
        assert device_info["sw_version"] == "Unknown"

    async def test_async_update_data_success(self, coordinator, mock_api):
        """Test successful data update."""
        # Mock successful API responses
        mock_api.get_status.return_value = {
            "successful": True,
            "result": {"status": "ok", "battery": {"charge": 75}},
        }
        mock_api.get_device.return_value = {
            "successful": True,
            "result": {"inverterSn": "TEST123456", "firmwareVersion": "1.2.3"},
        }
        mock_api.get_config_state.return_value = {
            "result": {"config": "state"},
        }
        mock_api.get_settings.return_value = {
            "result": {"settings": "data"},
        }
        mock_api.get_metrics.return_value = {
            "result": {"metrics": "data"},
        }
        mock_api.get_metrics_daily.return_value = {
            "result": {"daily": "metrics"},
        }
        mock_api.get_schedule.return_value = {
            "result": {"schedule": "data"},
        }
        mock_api.get_technical_status.return_value = {
            "result": {"technical": "status"},
        }
        mock_api.get_maintenance_diagnostics.return_value = {
            "result": {"diagnostics": "data"},
        }
        mock_api.get_notifications.return_value = {
            "result": {"notifications": ["notification1", "notification2"]},
        }
        mock_api.get_unread_notifications_count.return_value = {
            "result": {"total": 2},
        }

        result = await coordinator._async_update_data()

        assert result["status"] == {"status": "ok", "battery": {"charge": 75}}
        assert result["device"] == {
            "inverterSn": "TEST123456",
            "firmwareVersion": "1.2.3",
        }
        assert result["config_state"] == {"config": "state"}
        assert result["settings"] == {"settings": "data"}
        assert result["metrics"] == {"metrics": "data"}
        assert result["metrics_daily"] == {"daily": "metrics"}
        assert result["schedule"] == {"schedule": "data"}
        assert result["technical_status"] == {"technical": "status"}
        assert result["maintenance_diagnostics"] == {"diagnostics": "data"}
        assert result["notifications"] == {
            "notifications": ["notification1", "notification2"]
        }
        assert result["unread_notifications_count"] == {"total": 2}

    async def test_async_update_data_api_failure(self, coordinator, mock_api):
        """Test data update with API failures."""
        # Mock API responses with some failures
        mock_api.get_status.side_effect = Exception("API Error")
        mock_api.get_device.return_value = {
            "successful": True,
            "result": {"inverterSn": "TEST123456"},
        }
        # Mock other endpoints to return empty data or fail
        mock_api.get_config_state.return_value = {}
        mock_api.get_settings.side_effect = Exception("Settings error")
        mock_api.get_metrics.return_value = None
        mock_api.get_metrics_daily.return_value = {"result": {"daily": "metrics"}}
        mock_api.get_schedule.return_value = {}
        mock_api.get_technical_status.side_effect = Exception("Tech status error")
        mock_api.get_maintenance_diagnostics.side_effect = Exception(
            "Diagnostics error"
        )
        mock_api.get_notifications.return_value = {"result": {"notifications": []}}
        mock_api.get_unread_notifications_count.side_effect = Exception("Count error")

        result = await coordinator._async_update_data()

        # Should have empty data for failed endpoints
        assert result["status"] == {}
        assert result["device"] == {"inverterSn": "TEST123456"}
        assert result["config_state"] == {}
        assert result["settings"] == {}
        assert result["metrics"] == {}
        assert result["metrics_daily"] == {"daily": "metrics"}
        assert result["schedule"] == {}
        assert result["technical_status"] == {}
        assert result["maintenance_diagnostics"] == {}
        assert result["notifications"] == {"notifications": []}
        assert result["unread_notifications_count"] == {}

    async def test_async_update_data_complete_failure(self, coordinator, mock_api):
        """Test data update with complete failure."""
        # Mock all API calls to fail
        mock_api.get_status.side_effect = Exception("Complete failure")
        mock_api.get_device.side_effect = Exception("Complete failure")
        mock_api.get_config_state.side_effect = Exception("Complete failure")
        mock_api.get_settings.side_effect = Exception("Complete failure")
        mock_api.get_metrics.side_effect = Exception("Complete failure")
        mock_api.get_metrics_daily.side_effect = Exception("Complete failure")
        mock_api.get_schedule.side_effect = Exception("Complete failure")
        mock_api.get_technical_status.side_effect = Exception("Complete failure")
        mock_api.get_maintenance_diagnostics.side_effect = Exception("Complete failure")
        mock_api.get_notifications.side_effect = Exception("Complete failure")
        mock_api.get_unread_notifications_count.side_effect = Exception(
            "Complete failure"
        )

        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()

    async def test_async_update_data_partial_responses(self, coordinator, mock_api):
        """Test data update with partial API responses."""
        # Mock responses with missing 'result' keys
        mock_api.get_status.return_value = {"successful": False}
        mock_api.get_device.return_value = {"result": {"inverterSn": "TEST123456"}}
        mock_api.get_config_state.return_value = {"other_key": "value"}
        mock_api.get_settings.return_value = None
        mock_api.get_metrics.return_value = {"successful": True}  # No result key
        mock_api.get_metrics_daily.return_value = {"result": {"daily": "metrics"}}
        mock_api.get_schedule.return_value = {"result": None}
        mock_api.get_technical_status.return_value = {"result": {"status": "ok"}}
        mock_api.get_maintenance_diagnostics.return_value = {"result": {}}
        mock_api.get_notifications.return_value = None
        mock_api.get_unread_notifications_count.return_value = {"result": {"total": 0}}

        result = await coordinator._async_update_data()

        assert result["status"] == {}  # No result key when successful=False
        assert result["device"] == {"inverterSn": "TEST123456"}
        assert result["config_state"] == {
            "other_key": "value"
        }  # Whole response when no result key
        assert result["settings"] == {}  # None response becomes empty dict
        assert result["metrics"] == {
            "successful": True
        }  # Whole response when no result key
        assert result["metrics_daily"] == {"daily": "metrics"}
        assert result["schedule"] == {}  # None result becomes empty dict
        assert result["technical_status"] == {"status": "ok"}
        assert result["maintenance_diagnostics"] == {}
        assert result["notifications"] == {}  # None response becomes empty dict
        assert result["unread_notifications_count"] == {"total": 0}

    async def test_async_update_data_specific_error_handling(
        self, coordinator, mock_api
    ):
        """Test data update with specific error handling for tech endpoints."""
        # Mock normal endpoints to succeed
        mock_api.get_status.return_value = {"result": {"status": "ok"}}
        mock_api.get_device.return_value = {"result": {"inverterSn": "TEST123456"}}
        mock_api.get_config_state.return_value = {"result": {"config": "state"}}
        mock_api.get_settings.return_value = {"result": {"settings": "data"}}
        mock_api.get_metrics.return_value = {"result": {"metrics": "data"}}
        mock_api.get_metrics_daily.return_value = {"result": {"daily": "metrics"}}
        mock_api.get_schedule.return_value = {"result": {"schedule": "data"}}

        # Mock technical endpoints to fail (should be handled gracefully)
        mock_api.get_technical_status.side_effect = Exception(
            "Requires technician account"
        )
        mock_api.get_maintenance_diagnostics.side_effect = Exception(
            "Requires technician account"
        )

        # Mock notification endpoints
        mock_api.get_notifications.return_value = {"result": {"notifications": []}}
        mock_api.get_unread_notifications_count.return_value = {"result": {"total": 0}}

        result = await coordinator._async_update_data()

        # Normal endpoints should work
        assert result["status"] == {"status": "ok"}
        assert result["device"] == {"inverterSn": "TEST123456"}
        assert result["config_state"] == {"config": "state"}
        assert result["settings"] == {"settings": "data"}
        assert result["metrics"] == {"metrics": "data"}
        assert result["metrics_daily"] == {"daily": "metrics"}
        assert result["schedule"] == {"schedule": "data"}

        # Technical endpoints should return empty dicts on failure
        assert result["technical_status"] == {}
        assert result["maintenance_diagnostics"] == {}

        # Notification endpoints should work
        assert result["notifications"] == {"notifications": []}
        assert result["unread_notifications_count"] == {"total": 0}

    async def test_coordinator_alias(self):
        """Test that the backward compatibility alias works."""
        from custom_components.eaton_battery_storage.coordinator import (
            EatonBatteryStorageCoordinator,
        )

        assert EatonBatteryStorageCoordinator == EatonXstorageHomeCoordinator
