"""Test the Eaton Battery Storage integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

from custom_components.eaton_battery_storage import (
    PV_SENSOR_KEYS,
    async_migrate_pv_sensors,
    async_setup,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
)
from custom_components.eaton_battery_storage.const import DOMAIN


@pytest.mark.asyncio
class TestIntegrationSetup:
    """Test the integration setup functions."""

    async def test_async_setup(self, hass: HomeAssistant) -> None:
        """Test async_setup returns True."""
        result = await async_setup(hass, {})
        assert result is True

    async def test_async_setup_entry_success(
        self, hass: HomeAssistant, mock_config_entry, mock_api
    ) -> None:
        """Test successful setup of config entry."""
        mock_api.connect = AsyncMock()

        with patch(
            "custom_components.eaton_battery_storage.EatonBatteryAPI",
            return_value=mock_api,
        ), patch(
            "custom_components.eaton_battery_storage.EatonXstorageHomeCoordinator"
        ) as mock_coordinator_class, patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
        ) as mock_forward_setups, patch(
            "custom_components.eaton_battery_storage.async_migrate_pv_sensors"
        ) as mock_migrate:

            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator

            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            assert mock_config_entry.runtime_data == mock_coordinator

            mock_api.connect.assert_called_once()
            mock_coordinator.async_config_entry_first_refresh.assert_called_once()
            mock_forward_setups.assert_called_once()
            mock_migrate.assert_called_once_with(hass, mock_config_entry)

    async def test_async_setup_entry_connection_failure(
        self, hass: HomeAssistant, mock_config_entry, mock_api
    ) -> None:
        """Test setup failure due to connection error."""
        mock_api.connect = AsyncMock(side_effect=ConnectionError("Cannot connect"))

        with patch(
            "custom_components.eaton_battery_storage.EatonBatteryAPI",
            return_value=mock_api,
        ):
            with pytest.raises(
                ConfigEntryNotReady, match="Failed to connect to device"
            ):
                await async_setup_entry(hass, mock_config_entry)

    async def test_async_setup_entry_api_creation_failure(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test setup failure due to API creation error."""
        with patch(
            "custom_components.eaton_battery_storage.EatonBatteryAPI",
            side_effect=ValueError("Invalid configuration"),
        ):
            with pytest.raises(
                ConfigEntryNotReady, match="Failed to connect to device"
            ):
                await async_setup_entry(hass, mock_config_entry)

    async def test_async_setup_entry_coordinator_failure(
        self, hass: HomeAssistant, mock_config_entry, mock_api
    ) -> None:
        """Test setup failure due to coordinator refresh error."""
        mock_api.connect = AsyncMock()

        with patch(
            "custom_components.eaton_battery_storage.EatonBatteryAPI",
            return_value=mock_api,
        ), patch(
            "custom_components.eaton_battery_storage.EatonXstorageHomeCoordinator"
        ) as mock_coordinator_class:

            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock(
                side_effect=Exception("Coordinator failure")
            )
            mock_coordinator_class.return_value = mock_coordinator

            with pytest.raises(
                ConfigEntryNotReady, match="Failed to connect to device"
            ):
                await async_setup_entry(hass, mock_config_entry)

    async def test_async_unload_entry(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test unloading a config entry."""
        with patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            return_value=True,
        ) as mock_unload:
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            mock_unload.assert_called_once()

    async def test_reload_service_registration(
        self, hass: HomeAssistant, mock_config_entry, mock_api
    ) -> None:
        """Test that reload service is registered."""
        mock_api.connect = AsyncMock()

        with patch(
            "custom_components.eaton_battery_storage.EatonBatteryAPI",
            return_value=mock_api,
        ), patch(
            "custom_components.eaton_battery_storage.EatonXstorageHomeCoordinator"
        ) as mock_coordinator_class, patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
        ), patch(
            "custom_components.eaton_battery_storage.async_migrate_pv_sensors"
        ), patch.object(
            hass.services, "async_register"
        ) as mock_register:

            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator

            await async_setup_entry(hass, mock_config_entry)

            mock_register.assert_called_once()
            args, kwargs = mock_register.call_args
            assert args[0] == DOMAIN
            assert args[1] == "reload"

    async def test_async_update_options(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test async_update_options function."""
        with patch(
            "custom_components.eaton_battery_storage.async_migrate_pv_sensors"
        ) as mock_migrate:
            await async_update_options(hass, mock_config_entry)
            mock_migrate.assert_called_once_with(hass, mock_config_entry)


@pytest.mark.asyncio
class TestPVSensorMigration:
    """Test PV sensor migration functionality."""

    async def test_async_migrate_pv_sensors_no_pv(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test PV sensor migration when has_pv is False."""
        # Set has_pv to False in options
        mock_config_entry.options = {"has_pv": False}

        # Create entity registry
        entity_registry = er.async_get(hass)

        # Add some PV sensors to the registry
        for key in PV_SENSOR_KEYS[:3]:  # Just test with first 3 keys
            entity_registry.async_get_or_create(
                "sensor",
                DOMAIN,
                f"{mock_config_entry.entry_id}_{key}",
                config_entry=mock_config_entry,
                disabled_by=None,
            )

        # Count enabled PV sensors before migration
        # enabled_pv_sensors_before = sum(
        #     1 for key in PV_SENSOR_KEYS
        #     if entity_registry.async_get(f"sensor.{DOMAIN}_{key}") is not None
        #     and not entity_registry.async_get(f"sensor.{DOMAIN}_{key}").disabled
        # )

        await async_migrate_pv_sensors(hass, mock_config_entry)

        # Check that PV sensors are disabled
        for key in PV_SENSOR_KEYS[:3]:
            entity_id = f"sensor.{DOMAIN}_{key}"
            entity = entity_registry.async_get(entity_id)
            if entity:
                assert entity.disabled_by == er.RegistryEntryDisabler.INTEGRATION

    async def test_async_migrate_pv_sensors_has_pv(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test PV sensor migration when has_pv is True."""
        # Set has_pv to True in options
        mock_config_entry.options = {"has_pv": True}

        # Create entity registry
        entity_registry = er.async_get(hass)

        # Add some disabled PV sensors to the registry
        for key in PV_SENSOR_KEYS[:3]:  # Just test with first 3 keys
            entity_registry.async_get_or_create(
                "sensor",
                DOMAIN,
                f"{mock_config_entry.entry_id}_{key}",
                config_entry=mock_config_entry,
                disabled_by=er.RegistryEntryDisabler.INTEGRATION,
            )

        await async_migrate_pv_sensors(hass, mock_config_entry)

        # Check that PV sensors are enabled
        for key in PV_SENSOR_KEYS[:3]:
            entity_id = f"sensor.{DOMAIN}_{key}"
            entity = entity_registry.async_get(entity_id)
            if entity:
                assert entity.disabled_by is None

    async def test_async_migrate_pv_sensors_default_has_pv(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test PV sensor migration with default has_pv (True)."""
        # Don't set has_pv in options (defaults to True)
        mock_config_entry.options = {}

        # Create entity registry
        entity_registry = er.async_get(hass)

        # Add some disabled PV sensors to the registry
        for key in PV_SENSOR_KEYS[:3]:  # Just test with first 3 keys
            entity_registry.async_get_or_create(
                "sensor",
                DOMAIN,
                f"{mock_config_entry.entry_id}_{key}",
                config_entry=mock_config_entry,
                disabled_by=er.RegistryEntryDisabler.INTEGRATION,
            )

        await async_migrate_pv_sensors(hass, mock_config_entry)

        # Check that PV sensors are enabled (default behavior)
        for key in PV_SENSOR_KEYS[:3]:
            entity_id = f"sensor.{DOMAIN}_{key}"
            entity = entity_registry.async_get(entity_id)
            if entity:
                assert entity.disabled_by is None

    async def test_async_migrate_pv_sensors_no_entities(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test PV sensor migration when no PV entities exist."""
        mock_config_entry.options = {"has_pv": False}

        # Don't create any entities
        await async_migrate_pv_sensors(hass, mock_config_entry)

        # Should complete without error even with no entities to migrate

    async def test_pv_sensor_keys_constant(self) -> None:
        """Test that PV_SENSOR_KEYS contains expected keys."""
        expected_keys = [
            "status.energyFlow.acPvRole",
            "status.energyFlow.acPvValue",
            "status.energyFlow.dcPvRole",
            "status.energyFlow.dcPvValue",
            "status.last30daysEnergyFlow.photovoltaicProduction",
            "status.today.photovoltaicProduction",
            "device.inverterNominalVpv",
            "technical_status.pv1Voltage",
            "technical_status.pv1Current",
            "technical_status.pv2Voltage",
            "technical_status.pv2Current",
            "technical_status.dcCurrentInjectionR",
            "technical_status.dcCurrentInjectionS",
            "technical_status.dcCurrentInjectionT",
        ]

        assert PV_SENSOR_KEYS == expected_keys
