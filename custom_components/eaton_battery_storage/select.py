"""Select entities for Eaton battery storage system operation modes."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import EatonError
from .const import DOMAIN
from .coordinator import EatonConfigEntry, EatonXstorageHomeCoordinator
from .entity import EatonEntity

PARALLEL_UPDATES = 1

_LOGGER = logging.getLogger(__name__)

# Supported default modes and their command codes
DEFAULT_MODE_OPTIONS: list[tuple[str, str]] = [
    ("Basic Mode", "SET_BASIC_MODE"),
    ("Maximize Auto Consumption", "SET_MAXIMIZE_AUTO_CONSUMPTION"),
    ("Variable Grid Injection", "SET_VARIABLE_GRID_INJECTION"),
    ("Frequency Regulation", "SET_FREQUENCY_REGULATION"),
    ("Peak Shaving", "SET_PEAK_SHAVING"),
]

# Fallback state of charge used by frequency regulation when the device does
# not report a backup level.
DEFAULT_OPTIMAL_SOC = 28
DEFAULT_HOUSE_PEAK_CONSUMPTION = 1000


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: EatonConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            EatonXStorageDefaultOperationModeSelect(coordinator),
            EatonXStorageCurrentOperationModeSelect(coordinator),
        ]
    )


class EatonXStorageBaseSelect(EatonEntity, SelectEntity):
    """Common behavior for the operation mode selects."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._option_to_cmd: dict[str, str] = {}
        self._cmd_to_label: dict[str, str] = {}


class EatonXStorageDefaultOperationModeSelect(EatonXStorageBaseSelect):
    """Select entity to configure Default Operation Mode in settings.defaultMode."""

    _attr_icon = "mdi:transmission-tower"
    _attr_translation_key = "default_operation_mode"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_default_operation_mode"
        )
        self._option_to_cmd = dict(DEFAULT_MODE_OPTIONS)
        self._cmd_to_label = {cmd: label for label, cmd in DEFAULT_MODE_OPTIONS}
        self._attr_options = list(self._option_to_cmd)

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        settings = (self.coordinator.data or {}).get("settings", {})
        default_mode = settings.get("defaultMode", {})
        return self._cmd_to_label.get(default_mode.get("command"))

    def _build_parameters(self, command: str, settings: dict) -> dict[str, int]:
        """Build the parameters the device expects for the selected command."""
        if command == "SET_PEAK_SHAVING":
            threshold = settings.get("energySavingMode", {}).get(
                "houseConsumptionThreshold"
            )
            if isinstance(threshold, (int, float)):
                return {"maxHousePeakConsumption": int(threshold)}
            return {}
        if command == "SET_VARIABLE_GRID_INJECTION":
            return {"maximumPower": 0}
        if command == "SET_FREQUENCY_REGULATION":
            optimal_soc = settings.get("bmsBackupLevel")
            if not isinstance(optimal_soc, (int, float)):
                energy_flow = (
                    (self.coordinator.data or {})
                    .get("status", {})
                    .get("energyFlow", {})
                )
                optimal_soc = energy_flow.get("batteryBackupLevel", DEFAULT_OPTIMAL_SOC)
            return {"powerAllocation": 0, "optimalSoc": int(optimal_soc)}
        return {}

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        command = self._option_to_cmd[option]

        def mutate(settings: dict) -> None:
            settings["defaultMode"] = {
                "command": command,
                "parameters": self._build_parameters(command, settings),
            }

        try:
            await self.coordinator.async_patch_settings(mutate)
        except EatonError as err:
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_default_operation_mode_failed",
                translation_placeholders={"mode": option},
            ) from err


class EatonXStorageCurrentOperationModeSelect(EatonXStorageBaseSelect):
    """Select entity to send immediate operation mode commands.

    Commands sent via /api/device/command.
    """

    _attr_icon = "mdi:battery-clock"
    _attr_translation_key = "current_operation_mode"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_current_operation_mode"
        )
        self._option_to_cmd = dict(DEFAULT_MODE_OPTIONS) | {
            "Manual Charge": "SET_CHARGE",
            "Manual Discharge": "SET_DISCHARGE",
        }
        self._cmd_to_label = {cmd: label for label, cmd in self._option_to_cmd.items()}
        self._attr_options = list(self._option_to_cmd)

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        status = (self.coordinator.data or {}).get("status", {})
        current_mode = status.get("currentMode", {})
        return self._cmd_to_label.get(current_mode.get("command"))

    def _command_duration(self, command: str, helper_values: dict) -> int:
        """Return the run duration in hours configured for this command."""
        if command == "SET_CHARGE":
            return int(helper_values.get("charge_duration", 1))
        if command == "SET_DISCHARGE":
            return int(helper_values.get("discharge_duration", 1))
        # All intelligent modes use the shared run_duration
        return int(helper_values.get("run_duration", 2))

    def _command_parameters(self, command: str, helper_values: dict) -> dict[str, Any]:
        """Build the parameters the device expects for the selected command."""
        settings = (self.coordinator.data or {}).get("settings", {})

        if command == "SET_CHARGE":
            return {
                "action": "ACTION_CHARGE",
                "power": int(helper_values.get("charge_power", 15)),
                "soc": int(helper_values.get("charge_end_soc", 90)),
            }
        if command == "SET_DISCHARGE":
            return {
                "action": "ACTION_DISCHARGE",
                "power": int(helper_values.get("discharge_power", 15)),
                "soc": int(helper_values.get("discharge_end_soc", 10)),
            }
        if command == "SET_PEAK_SHAVING":
            threshold = settings.get("energySavingMode", {}).get(
                "houseConsumptionThreshold", DEFAULT_HOUSE_PEAK_CONSUMPTION
            )
            return {"maxHousePeakConsumption": int(threshold)}
        if command == "SET_VARIABLE_GRID_INJECTION":
            return {"maximumPower": 0}
        if command == "SET_FREQUENCY_REGULATION":
            optimal_soc = settings.get("bmsBackupLevel", DEFAULT_OPTIMAL_SOC)
            return {"powerAllocation": 0, "optimalSoc": int(optimal_soc)}
        return {}

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        command = self._option_to_cmd[option]
        helper_values = getattr(self.coordinator, "number_values", {})
        duration = self._command_duration(command, helper_values)

        try:
            await self.coordinator.api.send_device_command(
                command, duration, self._command_parameters(command, helper_values)
            )
        except EatonError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_operation_mode_failed",
                translation_placeholders={"mode": option},
            ) from err
        finally:
            await self.coordinator.async_request_refresh()

        _LOGGER.debug("Current operation mode set to %s for %d hours", option, duration)
