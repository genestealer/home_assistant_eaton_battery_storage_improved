"""Unit tests for constants and basic functionality."""

from __future__ import annotations

import pytest
import sys
from unittest.mock import Mock, patch


def test_domain_constant():
    """Test that domain constant is correctly defined."""
    # Mock homeassistant imports to allow import of const
    with patch.dict(sys.modules, {
        'homeassistant': Mock(),
        'homeassistant.config_entries': Mock(),
        'homeassistant.const': Mock(),
        'homeassistant.core': Mock(),
        'homeassistant.exceptions': Mock(),
        'homeassistant.helpers': Mock(),
        'homeassistant.helpers.config_validation': Mock(),
        'homeassistant.helpers.entity_registry': Mock(),
        'homeassistant.helpers.reload': Mock(),
    }):
        from custom_components.eaton_battery_storage.const import DOMAIN
        assert DOMAIN == "eaton_battery_storage"


def test_power_accuracy_warning():
    """Test that power accuracy warning is defined."""
    with patch.dict(sys.modules, {
        'homeassistant': Mock(),
        'homeassistant.config_entries': Mock(),
        'homeassistant.const': Mock(),
        'homeassistant.core': Mock(),
        'homeassistant.exceptions': Mock(),
        'homeassistant.helpers': Mock(),
        'homeassistant.helpers.config_validation': Mock(),
        'homeassistant.helpers.entity_registry': Mock(),
        'homeassistant.helpers.reload': Mock(),
    }):
        from custom_components.eaton_battery_storage.const import POWER_ACCURACY_WARNING
        assert "WARNING" in POWER_ACCURACY_WARNING
        assert "30%" in POWER_ACCURACY_WARNING


def test_mode_mappings():
    """Test that mode mappings are correctly defined."""
    with patch.dict(sys.modules, {
        'homeassistant': Mock(),
        'homeassistant.config_entries': Mock(),
        'homeassistant.const': Mock(),
        'homeassistant.core': Mock(),
        'homeassistant.exceptions': Mock(),
        'homeassistant.helpers': Mock(),
        'homeassistant.helpers.config_validation': Mock(),
        'homeassistant.helpers.entity_registry': Mock(),
        'homeassistant.helpers.reload': Mock(),
    }):
        from custom_components.eaton_battery_storage.const import (
            CURRENT_MODE_COMMAND_MAP,
            CURRENT_MODE_ACTION_MAP,
            OPERATION_MODE_MAP,
            BMS_STATE_MAP,
        )
        
        # Test that basic commands are mapped
        assert "SET_CHARGE" in CURRENT_MODE_COMMAND_MAP
        assert "SET_DISCHARGE" in CURRENT_MODE_COMMAND_MAP
        assert "SET_BASIC_MODE" in CURRENT_MODE_COMMAND_MAP
        
        # Test that actions are mapped
        assert "ACTION_CHARGE" in CURRENT_MODE_ACTION_MAP
        assert "ACTION_DISCHARGE" in CURRENT_MODE_ACTION_MAP
        
        # Test that operation modes are mapped
        assert "CHARGING" in OPERATION_MODE_MAP
        assert "DISCHARGING" in OPERATION_MODE_MAP
        assert "IDLE" in OPERATION_MODE_MAP
        
        # Test that BMS states are mapped
        assert "BAT_CHARGING" in BMS_STATE_MAP
        assert "BAT_DISCHARGING" in BMS_STATE_MAP
        assert "BAT_IDLE" in BMS_STATE_MAP


@pytest.mark.unit
def test_manifest_validation():
    """Test that manifest.json is valid."""
    import json
    import os
    
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "../custom_components/eaton_battery_storage/manifest.json"
    )
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    # Test required fields
    assert manifest["domain"] == "eaton_battery_storage"
    assert manifest["name"] == "Eaton xStorage Home Battery"
    assert manifest["config_flow"] is True
    assert manifest["version"] == "0.2.0"
    assert manifest["iot_class"] == "local_polling"
    assert "codeowners" in manifest
    assert isinstance(manifest["codeowners"], list)
    assert len(manifest["codeowners"]) > 0


@pytest.mark.unit
def test_platforms_definition():
    """Test that platforms are correctly defined."""
    with patch.dict(sys.modules, {
        'homeassistant': Mock(),
        'homeassistant.config_entries': Mock(),
        'homeassistant.const': Mock(Platform=Mock(
            SENSOR="sensor",
            BINARY_SENSOR="binary_sensor",
            NUMBER="number", 
            BUTTON="button",
            SWITCH="switch",
            SELECT="select",
            EVENT="event"
        )),
        'homeassistant.core': Mock(),
        'homeassistant.exceptions': Mock(),
        'homeassistant.helpers': Mock(),
        'homeassistant.helpers.config_validation': Mock(),
        'homeassistant.helpers.entity_registry': Mock(),
        'homeassistant.helpers.reload': Mock(),
    }):
        # This would test the platforms if we could import them
        # For now, just verify that the expected platforms exist as files
        import os
        component_dir = os.path.join(
            os.path.dirname(__file__),
            "../custom_components/eaton_battery_storage"
        )
        
        expected_platforms = [
            "sensor.py",
            "binary_sensor.py", 
            "number.py",
            "button.py",
            "switch.py",
            "select.py",
            "event.py"
        ]
        
        for platform in expected_platforms:
            platform_path = os.path.join(component_dir, platform)
            assert os.path.exists(platform_path), f"Platform {platform} should exist"


@pytest.mark.unit
def test_api_class_structure():
    """Test that API class has expected structure (without importing HA dependencies)."""
    # We can test basic imports and class structure
    with patch.dict(sys.modules, {
        'homeassistant': Mock(),
        'homeassistant.core': Mock(),
        'homeassistant.helpers': Mock(),
        'homeassistant.helpers.storage': Mock(),
    }):
        from custom_components.eaton_battery_storage.api import EatonBatteryAPI
        
        # Test that the class has expected methods
        assert hasattr(EatonBatteryAPI, "connect")
        assert hasattr(EatonBatteryAPI, "make_request")
        assert hasattr(EatonBatteryAPI, "get_device_status")
        assert hasattr(EatonBatteryAPI, "get_schedule")
        assert hasattr(EatonBatteryAPI, "send_command")
        assert hasattr(EatonBatteryAPI, "update_settings")


@pytest.mark.unit 
def test_config_flow_class_structure():
    """Test that config flow class has expected structure."""
    with patch.dict(sys.modules, {
        'homeassistant': Mock(),
        'homeassistant.config_entries': Mock(
            ConfigFlow=Mock,
            OptionsFlow=Mock,
            ConfigEntry=Mock,
        ),
        'homeassistant.const': Mock(),
        'homeassistant.core': Mock(),
        'homeassistant.data_entry_flow': Mock(),
        'homeassistant.helpers': Mock(),
        'homeassistant.helpers.selector': Mock(),
        'voluptuous': Mock(),
    }):
        from custom_components.eaton_battery_storage.config_flow import (
            EatonXStorageConfigFlow,
            EatonXStorageOptionsFlow,
        )
        
        # Test that the classes have expected attributes
        assert hasattr(EatonXStorageConfigFlow, "domain")
        assert EatonXStorageConfigFlow.domain == "eaton_battery_storage"
        assert hasattr(EatonXStorageConfigFlow, "VERSION")
        assert hasattr(EatonXStorageConfigFlow, "MINOR_VERSION")
        
        # Test that expected methods exist
        assert hasattr(EatonXStorageConfigFlow, "async_step_user")
        assert hasattr(EatonXStorageConfigFlow, "_test_connection")
        assert hasattr(EatonXStorageOptionsFlow, "_test_connection")