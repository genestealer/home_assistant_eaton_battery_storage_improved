"""Number platform for Eaton Battery Storage integration.

This module provides number entities for controlling various settings of the Eaton
Battery Storage system, including:
- Charge and discharge power settings (both percentage and wattage)
- House consumption threshold for energy saving mode
- Battery backup level configuration
"""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store

from .api import EatonError
from .const import DEFAULT_INVERTER_POWER_RATING, DOMAIN
from .coordinator import EatonConfigEntry, EatonXstorageHomeCoordinator
from .entity import EatonEntity
from .number_constants import (
    CHARGE_POWER_WATT,
    DISCHARGE_POWER_WATT,
    NUMBER_ENTITIES,
    NumberEntityDefinition,
)

PARALLEL_UPDATES = 1

_LOGGER = logging.getLogger(__name__)

# The watt entities mirror the 5-100 % range of their paired percentage entity.
WATT_KEYS = (CHARGE_POWER_WATT, DISCHARGE_POWER_WATT)
MIN_POWER_PERCENT = 5


def _full_scale_power(coordinator: EatonXstorageHomeCoordinator) -> int:
    """Return the inverter power rating used to convert percentages to watts.

    The range spans 3.6 kW to 6 kW, so the rating has to come from the device.
    inverterPowerRating needs a technician account; inverterVaRating is the
    closest equivalent a customer account can read.
    """
    data = coordinator.data or {}
    for rating in (
        data.get("technical_status", {}).get("inverterPowerRating"),
        data.get("device", {}).get("inverterVaRating"),
    ):
        if isinstance(rating, (int, float)) and rating > 0:
            return int(rating)
    return DEFAULT_INVERTER_POWER_RATING


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EatonConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Eaton Battery Storage number platform."""
    coordinator = entry.runtime_data
    full_scale = _full_scale_power(coordinator)

    # Setup storage for local number values (for percentage/watt conversions)
    store: Store[dict[str, float]] = Store(hass, 1, f"{DOMAIN}_number_values.json")
    stored = await store.async_load() or {}

    # Store data directly on the coordinator for access by entities
    if not hasattr(coordinator, "number_values"):
        coordinator.number_values = stored
        # Set defaults for missing values
        for desc in NUMBER_ENTITIES:
            key = desc["key"]
            if key not in coordinator.number_values:
                default = desc.get("default")
                if default is not None:
                    coordinator.number_values[key] = default
        # Set linked watt values if percent defaults are set
        if "charge_power" in coordinator.number_values:
            coordinator.number_values["charge_power_watt"] = round(
                (coordinator.number_values["charge_power"] / 100) * full_scale
            )
        if "discharge_power" in coordinator.number_values:
            coordinator.number_values["discharge_power_watt"] = round(
                (coordinator.number_values["discharge_power"] / 100) * full_scale
            )
        # Save defaults if storage was empty
        if not stored:
            await store.async_save(coordinator.number_values)
    if not hasattr(coordinator, "number_store"):
        coordinator.number_store = store

    entities: list[NumberEntity] = []

    # Add configurable number entities from constants
    entities.extend(
        EatonBatteryNumberEntity(coordinator, desc) for desc in NUMBER_ENTITIES
    )

    # Add API-controlled settings entities
    entities.extend(
        [
            EatonXStorageHouseConsumptionThresholdNumber(coordinator),
            EatonXStorageBatteryBackupLevelNumber(coordinator),
        ]
    )

    _LOGGER.debug("Adding %d number entities", len(entities))
    async_add_entities(entities)


class EatonBatteryNumberEntity(EatonEntity, NumberEntity):
    """Number entity for Eaton Battery Storage configurable values."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: EatonXstorageHomeCoordinator,
        description: NumberEntityDefinition,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._key = description["key"]
        # Scope unique ID to config entry to support multiple devices
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{description['key']}"
        )
        self._attr_translation_key = description["translation_key"]
        self._attr_native_min_value = float(description["min"])
        self._attr_native_max_value = float(description["max"])
        self._attr_native_step = float(description["step"])
        self._attr_native_unit_of_measurement = description["unit"]
        self._attr_device_class = NumberDeviceClass(description["device_class"])

        if self._key in WATT_KEYS:
            full_scale = _full_scale_power(coordinator)
            self._attr_native_min_value = float(
                round(full_scale * MIN_POWER_PERCENT / 100)
            )
            self._attr_native_max_value = float(full_scale)

    async def async_added_to_hass(self) -> None:
        """Register for dispatcher updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_number_update", self._handle_external_update
            )
        )

    def _handle_external_update(self) -> None:
        """Handle external updates via dispatcher."""
        self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, int] | None:
        """Return extra state attributes showing linked values."""
        native_val = self.native_value
        if native_val is None:
            return None

        full_scale = _full_scale_power(self.coordinator)
        if self._key in ("charge_power", "discharge_power"):
            return {"wattage": round((native_val / 100) * full_scale)}
        if self._key in ("charge_power_watt", "discharge_power_watt"):
            return {"percent": round((native_val / full_scale) * 100)}
        return None

    @property
    def native_value(self) -> float | None:
        """Return the current value from storage."""
        return getattr(self.coordinator, "number_values", {}).get(self._key)

    async def async_set_native_value(self, value: float) -> None:
        """Set the number value and update linked entities."""
        # Ensure number_values exists on coordinator
        if not hasattr(self.coordinator, "number_values"):
            self.coordinator.number_values = {}
        if not hasattr(self.coordinator, "number_store"):
            store: Store[dict[str, float]] = Store(
                self.hass, 1, f"{DOMAIN}_number_values.json"
            )
            self.coordinator.number_store = store

        # Store the value
        self.coordinator.number_values[self._key] = value

        # Calculate and store linked values
        linked_key = self._calculate_linked_value(value)

        # Save to persistent storage
        await self.coordinator.number_store.async_save(self.coordinator.number_values)

        # Update this entity
        self.async_write_ha_state()

        # Notify other entities via dispatcher
        if linked_key:
            async_dispatcher_send(self.hass, f"{DOMAIN}_number_update")

    def _calculate_linked_value(self, value: float) -> str | None:
        """Calculate and store linked value, return linked key if any."""
        full_scale = _full_scale_power(self.coordinator)
        if self._key == "charge_power":
            self.coordinator.number_values["charge_power_watt"] = round(
                (value / 100) * full_scale
            )
            return "charge_power_watt"
        if self._key == "charge_power_watt":
            self.coordinator.number_values["charge_power"] = round(
                (value / full_scale) * 100
            )
            return "charge_power"
        if self._key == "discharge_power":
            self.coordinator.number_values["discharge_power_watt"] = round(
                (value / 100) * full_scale
            )
            return "discharge_power_watt"
        if self._key == "discharge_power_watt":
            self.coordinator.number_values["discharge_power"] = round(
                (value / full_scale) * 100
            )
            return "discharge_power"
        return None


class EatonXStorageHouseConsumptionThresholdNumber(EatonEntity, NumberEntity):
    """Number entity to control the House Consumption Threshold.

    Used for Energy Saving Mode.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:home-lightning-bolt"
    _attr_native_unit_of_measurement = "W"
    _attr_native_min_value = 300
    _attr_native_max_value = 1000
    _attr_native_step = 25
    _attr_mode = NumberMode.BOX
    _attr_translation_key = "house_consumption_threshold"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the house consumption threshold number entity."""
        super().__init__(coordinator)
        # Scope unique ID to config entry for multi-device setups
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_set_house_consumption_threshold"
        )
        self._optimistic_value: int | None = None

    @property
    def native_value(self) -> int | None:
        """Return the current house consumption threshold value."""
        if self._optimistic_value is not None:
            return self._optimistic_value

        data = self.coordinator.data or {}
        # Prefer device endpoint data (mirrors active runtime state)
        device_esm = data.get("device", {}).get("energySavingMode", {})
        if "houseConsumptionThreshold" in device_esm:
            return device_esm["houseConsumptionThreshold"]

        settings_esm = data.get("settings", {}).get("energySavingMode", {})
        return settings_esm.get("houseConsumptionThreshold", 300)

    async def async_set_native_value(self, value: float) -> None:
        """Set the house consumption threshold value."""
        self._optimistic_value = int(value)
        self.async_write_ha_state()

        def mutate(settings: dict) -> None:
            settings.setdefault("energySavingMode", {})["houseConsumptionThreshold"] = (
                int(value)
            )

        try:
            await self.coordinator.async_patch_settings(mutate)
        except EatonError as err:
            self._optimistic_value = None
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_house_consumption_threshold_failed",
                translation_placeholders={"value": str(int(value))},
            ) from err

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._optimistic_value = None
        super()._handle_coordinator_update()


class EatonXStorageBatteryBackupLevelNumber(EatonEntity, NumberEntity):
    """Number entity to control the Battery Backup Level (bmsBackupLevel)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:battery-lock"
    _attr_native_unit_of_measurement = "%"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_translation_key = "battery_backup_level"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the battery backup level number entity."""
        super().__init__(coordinator)
        # Scope unique ID to config entry for multi-device setups
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_set_battery_backup_level"
        )
        self._optimistic_value: int | None = None

    @property
    def native_value(self) -> int | None:
        """Return the current battery backup level value."""
        if self._optimistic_value is not None:
            return self._optimistic_value

        data = self.coordinator.data or {}
        settings_data = data.get("settings", {})
        if "bmsBackupLevel" in settings_data:
            return settings_data["bmsBackupLevel"]

        energy_flow = data.get("status", {}).get("energyFlow", {})
        return energy_flow.get("batteryBackupLevel", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the battery backup level value."""
        self._optimistic_value = int(value)
        self.async_write_ha_state()

        def mutate(settings: dict) -> None:
            settings["bmsBackupLevel"] = int(value)

        try:
            await self.coordinator.async_patch_settings(mutate)
        except EatonError as err:
            self._optimistic_value = None
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_battery_backup_level_failed",
                translation_placeholders={"value": str(int(value))},
            ) from err

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._optimistic_value = None
        super()._handle_coordinator_update()
