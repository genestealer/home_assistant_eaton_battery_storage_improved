"""Test integration setup for Eaton Battery Storage."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

from custom_components.eaton_battery_storage import (
    async_migrate_pv_sensors,
    async_setup,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
)
from custom_components.eaton_battery_storage.const import DOMAIN


class TestIntegrationSetup:
    """Test integration setup functions."""

    async def test_async_setup(self, hass: HomeAssistant):
        """Test async_setup returns True."""
        result = await async_setup(hass, {})
        assert result is True

    async def test_async_setup_entry_success(self, hass: HomeAssistant, mock_config_entry, mock_api, mock_coordinator):
        """Test successful setup of config entry."""
        with patch("custom_components.eaton_battery_storage.EatonBatteryAPI") as mock_api_class, \
             patch("custom_components.eaton_battery_storage.EatonXstorageHomeCoordinator") as mock_coord_class, \
             patch("custom_components.eaton_battery_storage.async_migrate_pv_sensors", new_callable=AsyncMock) as mock_migrate:
            
            mock_api_class.return_value = mock_api
            mock_coord_class.return_value = mock_coordinator
            
            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            assert mock_config_entry.runtime_data == mock_coordinator
            mock_api.connect.assert_called_once()
            mock_coordinator.async_config_entry_first_refresh.assert_called_once()
            mock_migrate.assert_called_once_with(hass, mock_config_entry)

    async def test_async_setup_entry_connection_failure(self, hass: HomeAssistant, mock_config_entry):
        """Test setup entry failure due to connection error."""
        with patch("custom_components.eaton_battery_storage.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = ConnectionError("Cannot connect")
            mock_api_class.return_value = mock_api

            with pytest.raises(ConfigEntryNotReady, match="Cannot connect"):
                await async_setup_entry(hass, mock_config_entry)

    async def test_async_setup_entry_auth_failure(self, hass: HomeAssistant, mock_config_entry):
        """Test setup entry failure due to authentication error."""
        with patch("custom_components.eaton_battery_storage.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = ValueError("Invalid credentials")
            mock_api_class.return_value = mock_api

            with pytest.raises(ConfigEntryNotReady, match="Invalid credentials"):
                await async_setup_entry(hass, mock_config_entry)

    async def test_async_setup_entry_coordinator_failure(self, hass: HomeAssistant, mock_config_entry, mock_api):
        """Test setup entry failure due to coordinator refresh error."""
        with patch("custom_components.eaton_battery_storage.EatonBatteryAPI") as mock_api_class, \
             patch("custom_components.eaton_battery_storage.EatonXstorageHomeCoordinator") as mock_coord_class:
            
            mock_api_class.return_value = mock_api
            
            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh.side_effect = Exception("Coordinator error")
            mock_coord_class.return_value = mock_coordinator

            with pytest.raises(ConfigEntryNotReady, match="Coordinator error"):
                await async_setup_entry(hass, mock_config_entry)

    async def test_async_unload_entry(self, hass: HomeAssistant, mock_config_entry):
        """Test unloading config entry."""
        with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms", new_callable=AsyncMock) as mock_unload:
            mock_unload.return_value = True

            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            mock_unload.assert_called_once()

    async def test_async_update_options(self, hass: HomeAssistant, mock_config_entry):
        """Test updating options."""
        with patch("custom_components.eaton_battery_storage.async_migrate_pv_sensors", new_callable=AsyncMock) as mock_migrate, \
             patch("homeassistant.config_entries.ConfigEntries.async_reload", new_callable=AsyncMock) as mock_reload:

            await async_update_options(hass, mock_config_entry)

            mock_migrate.assert_called_once_with(hass, mock_config_entry)
            mock_reload.assert_called_once_with(mock_config_entry.entry_id)


class TestPVSensorMigration:
    """Test PV sensor migration functionality."""

    async def test_async_migrate_pv_sensors_enable(self, hass: HomeAssistant):
        """Test enabling PV sensors when has_pv=True."""
        # Create config entry with has_pv=True
        config_entry = ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="Test",
            data={"has_pv": True},
            entry_id="test_entry",
        )

        # Mock entity registry
        mock_registry = Mock()
        mock_entity = Mock()
        mock_registry.async_get.return_value = mock_entity
        
        with patch("homeassistant.helpers.entity_registry.async_get", return_value=mock_registry):
            await async_migrate_pv_sensors(hass, config_entry)

            # Should call update_entity for each PV sensor to enable them
            assert mock_registry.async_update_entity.call_count > 0
            
            # Check that entities are enabled (disabled_by=None)
            for call in mock_registry.async_update_entity.call_args_list:
                entity_id, disabled_by = call[0][0], call[1]["disabled_by"]
                assert "pv" in entity_id.lower() or "photovoltaic" in entity_id.lower()
                assert disabled_by is None

    async def test_async_migrate_pv_sensors_disable(self, hass: HomeAssistant):
        """Test disabling PV sensors when has_pv=False."""
        # Create config entry with has_pv=False
        config_entry = ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="Test",
            data={"has_pv": False},
            entry_id="test_entry",
        )

        # Mock entity registry
        mock_registry = Mock()
        mock_entity = Mock()
        mock_registry.async_get.return_value = mock_entity
        
        with patch("homeassistant.helpers.entity_registry.async_get", return_value=mock_registry):
            await async_migrate_pv_sensors(hass, config_entry)

            # Should call update_entity for each PV sensor to disable them
            assert mock_registry.async_update_entity.call_count > 0
            
            # Check that entities are disabled
            for call in mock_registry.async_update_entity.call_args_list:
                entity_id, disabled_by = call[0][0], call[1]["disabled_by"]
                assert "pv" in entity_id.lower() or "photovoltaic" in entity_id.lower()
                assert disabled_by == er.RegistryEntryDisabler.INTEGRATION

    async def test_async_migrate_pv_sensors_no_entities(self, hass: HomeAssistant):
        """Test PV sensor migration when no entities exist in registry."""
        # Create config entry
        config_entry = ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="Test",
            data={"has_pv": True},
            entry_id="test_entry",
        )

        # Mock entity registry with no entities found
        mock_registry = Mock()
        mock_registry.async_get.return_value = None
        
        with patch("homeassistant.helpers.entity_registry.async_get", return_value=mock_registry):
            # Should not raise any exception
            await async_migrate_pv_sensors(hass, config_entry)

            # Should not call update_entity since no entities found
            mock_registry.async_update_entity.assert_not_called()

    async def test_async_migrate_pv_sensors_default_has_pv(self, hass: HomeAssistant):
        """Test PV sensor migration with default has_pv value."""
        # Create config entry without has_pv key (should default to False)
        config_entry = ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="Test",
            data={},  # No has_pv key
            entry_id="test_entry",
        )

        # Mock entity registry
        mock_registry = Mock()
        mock_entity = Mock()
        mock_registry.async_get.return_value = mock_entity
        
        with patch("homeassistant.helpers.entity_registry.async_get", return_value=mock_registry):
            await async_migrate_pv_sensors(hass, config_entry)

            # Should call update_entity for each PV sensor to disable them (default has_pv=False)
            if mock_registry.async_update_entity.call_count > 0:
                for call in mock_registry.async_update_entity.call_args_list:
                    disabled_by = call[1]["disabled_by"]
                    assert disabled_by == er.RegistryEntryDisabler.INTEGRATION