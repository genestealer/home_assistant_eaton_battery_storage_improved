"""Switch entities for Eaton xStorage Home battery integration."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .settings_helpers import async_get_and_transform_settings

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import EatonBatteryStorageCoordinator

    type EatonBatteryStorageConfigEntry = ConfigEntry[EatonBatteryStorageCoordinator]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: EatonBatteryStorageConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Eaton xStorage Home switches from a config entry."""
    coordinator = entry.runtime_data
    entities = [
        EatonXStoragePowerSwitch(coordinator),
        EatonXStorageEnergySavingModeSwitch(coordinator),
    ]
    async_add_entities(entities)


class EatonXStoragePowerSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to control the power state of the Eaton xStorage Home device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:power"

    def __init__(self, coordinator: EatonBatteryStorageCoordinator) -> None:
        """Initialize the power switch."""
        super().__init__(coordinator)
        # Scope unique ID to the config entry for multi-device setups
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_inverter_power"
        self._attr_translation_key = "inverter_power"
        self._optimistic_state: bool | None = None

    @property
    def device_info(self) -> dict[str, str]:
        """Return device information."""
        return self.coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the device is on."""
        # If we have an optimistic state from a recent command, use that
        if self._optimistic_state is not None:
            return self._optimistic_state

        try:
            # Otherwise, check the powerState from device data
            device_data = (
                self.coordinator.data.get("device", {}) if self.coordinator.data else {}
            )
            return device_data.get("powerState", False)
        except (AttributeError, TypeError, KeyError):
            return False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    async def async_turn_on(self, **_kwargs) -> None:
        """Turn the device on."""
        try:
            # Set optimistic state immediately for responsive UI
            self._optimistic_state = True
            self.async_write_ha_state()

            # Send the command, but don't expect a response
            await self.coordinator.api.set_device_power(True)
            _LOGGER.info(
                "Sent turn ON command to Eaton xStorage Home device (no response expected)"
            )
            # Wait a bit for the device to actually change state
            await asyncio.sleep(3)

            # Always refresh the coordinator data after attempting to change power state
            await self.coordinator.async_request_refresh()

            # Clear optimistic state so we use real data
            self._optimistic_state = None

        except Exception as exc:
            _LOGGER.error("Error turning on device: %s", exc)
            # Clear optimistic state and refresh to get current state
            self._optimistic_state = None
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError("Failed to turn on device") from exc

    async def async_turn_off(self, **_kwargs) -> None:
        """Turn the device off."""
        try:
            # Set optimistic state immediately for responsive UI
            self._optimistic_state = False
            self.async_write_ha_state()

            # Send the command, but don't expect a response
            await self.coordinator.api.set_device_power(False)
            _LOGGER.info(
                "Sent turn OFF command to Eaton xStorage Home device (no response expected)"
            )
            # Wait a bit for the device to actually change state
            await asyncio.sleep(3)

            # Always refresh the coordinator data after attempting to change power state
            await self.coordinator.async_request_refresh()

            # Clear optimistic state so we use real data
            self._optimistic_state = None

        except Exception as exc:
            _LOGGER.error("Error turning off device: %s", exc)
            # Clear optimistic state and refresh to get current state
            self._optimistic_state = None
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError("Failed to turn off device") from exc

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Clear optimistic state when we get real data from coordinator
        if self._optimistic_state is not None:
            self._optimistic_state = None
        super()._handle_coordinator_update()


class EatonXStorageEnergySavingModeSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to control the Energy Saving Mode of the Eaton xStorage Home device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:leaf"

    def __init__(self, coordinator: EatonBatteryStorageCoordinator) -> None:
        """Initialize the energy saving mode switch."""
        super().__init__(coordinator)
        # Scope unique ID to the config entry for multi-device setups
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_energy_saving_mode"
        self._attr_translation_key = "energy_saving_mode"
        self._optimistic_state: bool | None = None

    @property
    def device_info(self) -> dict[str, str]:
        """Return device information."""
        return self.coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if energy saving mode is enabled."""
        # If we have an optimistic state from a recent command, use that
        if self._optimistic_state is not None:
            return self._optimistic_state

        try:
            # Get energy saving mode from settings data
            settings_data = (
                self.coordinator.data.get("settings", {})
                if self.coordinator.data
                else {}
            )
            energy_saving_mode = settings_data.get("energySavingMode", {})
            enabled_value = energy_saving_mode.get("enabled", False)

            # API returns boolean values
            return bool(enabled_value)
        except (AttributeError, TypeError, KeyError):
            return False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    async def async_turn_on(self, **_kwargs) -> None:
        """Turn energy saving mode on."""
        try:
            # Set optimistic state immediately for responsive UI
            self._optimistic_state = True
            self.async_write_ha_state()

            # First, get the current settings from the API (not cached data)
            current_settings = await async_get_and_transform_settings(
                self.coordinator.api
            )
            if current_settings is None:
                self._optimistic_state = None
                return

            # Update only the energySavingMode.enabled field
            if "energySavingMode" not in current_settings:
                current_settings["energySavingMode"] = {}
            current_settings["energySavingMode"]["enabled"] = True

            # API expects data wrapped in "settings" object
            payload = {"settings": current_settings}

            result = await self.coordinator.api.update_settings(payload)

            if result.get("successful", result.get("result") is not None):
                _LOGGER.info("Successfully enabled energy saving mode")
                await asyncio.sleep(2)
            else:
                _LOGGER.warning(
                    "API call completed but may not have succeeded: %s", result
                )
                await asyncio.sleep(1)

            # Always refresh the coordinator data
            await self.coordinator.async_request_refresh()

            # Clear optimistic state so we use real data
            self._optimistic_state = None

        except Exception as exc:
            _LOGGER.error("Error enabling energy saving mode: %s", exc)
            # Clear optimistic state and refresh to get current state
            self._optimistic_state = None
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError("Failed to enable energy saving mode") from exc

    async def async_turn_off(self, **_kwargs) -> None:
        """Turn energy saving mode off."""
        try:
            # Set optimistic state immediately for responsive UI
            self._optimistic_state = False
            self.async_write_ha_state()

            # First, get the current settings from the API (not cached data)
            current_settings = await async_get_and_transform_settings(
                self.coordinator.api
            )
            if current_settings is None:
                self._optimistic_state = None
                return

            # Update only the energySavingMode.enabled field
            if "energySavingMode" not in current_settings:
                current_settings["energySavingMode"] = {}
            current_settings["energySavingMode"]["enabled"] = False

            # API expects data wrapped in "settings" object
            payload = {"settings": current_settings}

            result = await self.coordinator.api.update_settings(payload)

            if result.get("successful", result.get("result") is not None):
                _LOGGER.info("Successfully disabled energy saving mode")
                await asyncio.sleep(2)
            else:
                _LOGGER.warning(
                    "API call completed but may not have succeeded: %s", result
                )
                await asyncio.sleep(1)

            # Always refresh the coordinator data
            await self.coordinator.async_request_refresh()

            # Clear optimistic state so we use real data
            self._optimistic_state = None

        except Exception as exc:
            _LOGGER.error("Error disabling energy saving mode: %s", exc)
            # Clear optimistic state and refresh to get current state
            self._optimistic_state = None
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError("Failed to disable energy saving mode") from exc

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Clear optimistic state when we get real data from coordinator
        if self._optimistic_state is not None:
            self._optimistic_state = None
        super()._handle_coordinator_update()
