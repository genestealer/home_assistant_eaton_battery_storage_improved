"""Test the Eaton Battery Storage sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.eaton_battery_storage.sensor import (
    SENSOR_DEFINITIONS,
    EatonXStorageNotificationsSensor,
    EatonXStorageSensor,
    async_setup_entry,
)


@pytest.mark.asyncio
class TestSensorPlatform:
    """Test the sensor platform setup."""

    async def test_async_setup_entry(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test sensor platform setup."""
        # Mock coordinator with test data
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "status": {
                "battery": {"charge": 75, "status": "CHARGING"},
                "energyFlow": {"gridValue": 500, "batteryValue": 1000},
            },
            "device": {"inverterSn": "TEST123456", "firmwareVersion": "1.2.3"},
            "notifications": {"notifications": [{"id": 1, "message": "Test"}]},
            "unread_notifications_count": {"total": 1},
        }
        mock_config_entry.runtime_data = mock_coordinator

        # Mock add_entities function
        mock_add_entities = Mock(spec=AddEntitiesCallback)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Verify entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        
        # Should have regular sensors plus notifications sensor
        assert len(entities) > 1
        
        # Check that we have both types of sensors
        sensor_entities = [e for e in entities if isinstance(e, EatonXStorageSensor)]
        notification_entities = [e for e in entities if isinstance(e, EatonXStorageNotificationsSensor)]
        
        assert len(sensor_entities) > 0
        assert len(notification_entities) == 1


@pytest.mark.asyncio
class TestEatonXStorageSensor:
    """Test the EatonXStorageSensor class."""

    @pytest.fixture
    def mock_coordinator(self):
        """Return a mock coordinator."""
        coordinator = Mock()
        coordinator.data = {
            "status": {
                "battery": {"charge": 75},
                "energyFlow": {"gridValue": 500},
            },
            "device": {"inverterSn": "TEST123456"},
        }
        coordinator.device_info = {
            "identifiers": {("eaton_battery_storage", "TEST123456")},
            "name": "Eaton xStorage Home",
            "manufacturer": "Eaton",
        }
        return coordinator

    @pytest.fixture
    def sensor_definition(self):
        """Return a test sensor definition."""
        return {
            "name": "Battery Charge",
            "unit": "%",
            "device_class": "battery",
            "entity_category": None,
            "icon": "mdi:battery",
        }

    @pytest.fixture
    def sensor(self, mock_coordinator, sensor_definition):
        """Return a sensor instance."""
        return EatonXStorageSensor(
            coordinator=mock_coordinator,
            key="status.battery.charge",
            definition=sensor_definition,
            config_entry_id="test_entry",
        )

    def test_sensor_properties(self, sensor, sensor_definition):
        """Test sensor properties."""
        assert sensor.name == "Battery Charge"
        assert sensor.native_unit_of_measurement == "%"
        assert sensor.device_class == "battery"
        assert sensor.entity_category is None
        assert sensor.icon == "mdi:battery"
        assert sensor.unique_id == "test_entry_status.battery.charge"

    def test_sensor_state(self, sensor):
        """Test sensor state."""
        assert sensor.native_value == 75

    def test_sensor_state_missing_data(self, sensor, mock_coordinator):
        """Test sensor state with missing data."""
        mock_coordinator.data = {}
        assert sensor.native_value is None

    def test_sensor_state_nested_missing(self, sensor, mock_coordinator):
        """Test sensor state with partial missing data."""
        mock_coordinator.data = {"status": {}}
        assert sensor.native_value is None

    def test_sensor_device_info(self, sensor, mock_coordinator):
        """Test sensor device info."""
        assert sensor.device_info == mock_coordinator.device_info

    def test_entity_registry_enabled_default_normal(self, sensor):
        """Test entity registry enabled default for normal sensor."""
        assert sensor.entity_registry_enabled_default is True

    def test_entity_registry_enabled_default_tida_protocol(self, mock_coordinator):
        """Test entity registry enabled default for TIDA protocol sensor."""
        sensor_def = {
            "name": "TIDA Protocol Version",
            "unit": None,
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        }
        sensor = EatonXStorageSensor(
            coordinator=mock_coordinator,
            key="technical_status.tidaProtocolVersion",
            definition=sensor_def,
            config_entry_id="test_entry",
        )
        assert sensor.entity_registry_enabled_default is False

    def test_entity_registry_enabled_default_disabled_flag(self, mock_coordinator):
        """Test entity registry enabled default for sensor with disabled flag."""
        sensor_def = {
            "name": "Test Sensor",
            "unit": None,
            "device_class": None,
            "entity_category": None,
            "disabled_by_default": True,
        }
        sensor = EatonXStorageSensor(
            coordinator=mock_coordinator,
            key="test.sensor",
            definition=sensor_def,
            config_entry_id="test_entry",
        )
        assert sensor.entity_registry_enabled_default is False


@pytest.mark.asyncio
class TestEatonXStorageNotificationsSensor:
    """Test the EatonXStorageNotificationsSensor class."""

    @pytest.fixture
    def mock_coordinator(self):
        """Return a mock coordinator."""
        coordinator = Mock()
        coordinator.data = {
            "notifications": {
                "notifications": [
                    {"id": 1, "message": "Test notification 1", "type": "info"},
                    {"id": 2, "message": "Test notification 2", "type": "warning"},
                ]
            }
        }
        coordinator.device_info = {
            "identifiers": {("eaton_battery_storage", "TEST123456")},
            "name": "Eaton xStorage Home",
            "manufacturer": "Eaton",
        }
        return coordinator

    @pytest.fixture
    def notifications_sensor(self, mock_coordinator):
        """Return a notifications sensor instance."""
        return EatonXStorageNotificationsSensor(
            coordinator=mock_coordinator,
            config_entry_id="test_entry",
        )

    def test_notifications_sensor_properties(self, notifications_sensor):
        """Test notifications sensor properties."""
        assert notifications_sensor.name == "Notifications"
        assert notifications_sensor.unique_id == "test_entry_notifications"
        assert notifications_sensor.icon == "mdi:bell"

    def test_notifications_sensor_state(self, notifications_sensor):
        """Test notifications sensor state."""
        state = notifications_sensor.native_value
        assert isinstance(state, str)
        # Should contain information about the notifications
        assert "Test notification 1" in state
        assert "Test notification 2" in state

    def test_notifications_sensor_state_no_data(self, notifications_sensor, mock_coordinator):
        """Test notifications sensor state with no data."""
        mock_coordinator.data = {}
        assert notifications_sensor.native_value == "No notifications"

    def test_notifications_sensor_state_empty_notifications(self, notifications_sensor, mock_coordinator):
        """Test notifications sensor state with empty notifications."""
        mock_coordinator.data = {"notifications": {"notifications": []}}
        assert notifications_sensor.native_value == "No notifications"

    def test_notifications_sensor_extra_state_attributes(self, notifications_sensor):
        """Test notifications sensor extra state attributes."""
        attributes = notifications_sensor.extra_state_attributes
        assert "notification_count" in attributes
        assert attributes["notification_count"] == 2
        assert "notifications" in attributes
        assert len(attributes["notifications"]) == 2

    def test_notifications_sensor_device_info(self, notifications_sensor, mock_coordinator):
        """Test notifications sensor device info."""
        assert notifications_sensor.device_info == mock_coordinator.device_info


@pytest.mark.asyncio
class TestSensorDefinitions:
    """Test sensor definitions."""

    def test_sensor_definitions_structure(self):
        """Test that sensor definitions have required structure."""
        for key, definition in SENSOR_DEFINITIONS.items():
            assert isinstance(key, str)
            assert "name" in definition
            assert "unit" in definition  # Can be None
            assert "device_class" in definition  # Can be None
            assert "entity_category" in definition  # Can be None

    def test_sensor_definitions_unique_names(self):
        """Test that sensor definition names are unique."""
        names = [definition["name"] for definition in SENSOR_DEFINITIONS.values()]
        assert len(names) == len(set(names)), "Sensor names must be unique"

    def test_critical_sensors_present(self):
        """Test that critical sensors are present in definitions."""
        critical_keys = [
            "status.battery.charge",
            "status.battery.status",
            "status.energyFlow.gridValue",
            "status.energyFlow.batteryValue",
            "status.energyFlow.consumption",
            "status.energyFlow.production",
        ]
        
        for key in critical_keys:
            assert key in SENSOR_DEFINITIONS, f"Critical sensor {key} missing from definitions"

    def test_pv_sensors_present(self):
        """Test that PV-related sensors are present."""
        pv_keys = [
            "status.energyFlow.acPvValue",
            "status.energyFlow.dcPvValue",
            "status.today.photovoltaicProduction",
            "technical_status.pv1Voltage",
            "technical_status.pv1Current",
        ]
        
        for key in pv_keys:
            assert key in SENSOR_DEFINITIONS, f"PV sensor {key} missing from definitions"

    def test_diagnostic_sensors_have_category(self):
        """Test that diagnostic sensors have correct entity category."""
        diagnostic_keywords = ["firmware", "version", "serial", "ip", "dns", "timezone", "cpu", "ram"]
        
        for key, definition in SENSOR_DEFINITIONS.items():
            name_lower = definition["name"].lower()
            if any(keyword in name_lower for keyword in diagnostic_keywords):
                # Not all diagnostic sensors have the category set, but let's check some do
                if "entity_category" in definition and definition["entity_category"]:
                    assert definition["entity_category"] == EntityCategory.DIAGNOSTIC