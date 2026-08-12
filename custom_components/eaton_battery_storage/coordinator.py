"""Data update coordinator for Eaton xStorage Home battery integration.

IMPORTANT ACCURACY WARNING:
Power measurement data retrieved by this coordinator from the xStorage Home API
has poor accuracy. Energy flow values (consumption, production, grid power,
load values) are typically 10%-30% higher than actual measurements. This affects
all power-related data in the coordinator's data structure under energyFlow,
today, and last30daysEnergyFlow sections.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)

from .api import EatonAuthError, EatonBatteryAPI, EatonError, EatonResponseError
from .const import ACCOUNT_TYPE_TECHNICIAN, CONF_USER_TYPE, DOMAIN
from .settings_helpers import async_get_and_transform_settings

_LOGGER = logging.getLogger(__name__)

type EatonConfigEntry = ConfigEntry[EatonXstorageHomeCoordinator]


def _unwrap(response: dict[str, Any]) -> dict[str, Any]:
    """Return the payload of an optional API response."""
    result = response.get("result")
    return result if isinstance(result, dict) else {}


def _unwrap_required(response: dict[str, Any], name: str) -> dict[str, Any]:
    """Return the payload of an API response the integration cannot work without."""
    result = response.get("result")
    if not isinstance(result, dict) or not result:
        raise EatonResponseError(f"Device returned no {name} data: {response}")
    return result


class EatonXstorageHomeCoordinator(TimestampDataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the Eaton xStorage Home API."""

    config_entry: EatonConfigEntry
    # Populated by the number platform, which owns the local helper values.
    number_values: dict[str, float]
    number_store: Store[dict[str, float]]

    def __init__(
        self,
        hass: HomeAssistant,
        api: EatonBatteryAPI,
        config_entry: EatonConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Eaton xStorage Home",
            update_interval=timedelta(minutes=1),
            config_entry=config_entry,
        )
        self.api = api
        self._settings_lock = asyncio.Lock()
        self._unavailable_logged = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this coordinator."""
        device_data = self.data.get("device", {}) if self.data else {}
        serial = device_data.get("inverterSerialNumber")

        device_info = DeviceInfo(
            # Never key the device on an IP/hostname: a DHCP change would orphan it.
            identifiers={(DOMAIN, serial or self.config_entry.entry_id)},
            name="Eaton xStorage Home",
            manufacturer="Eaton",
            model="xStorage Home",
            configuration_url=f"https://{self.api.host}",
        )

        if serial:
            device_info["serial_number"] = serial
        if "firmwareVersion" in device_data:
            device_info["sw_version"] = device_data["firmwareVersion"]
        if "inverterModelName" in device_data:
            device_info["model"] = f"xStorage Home ({device_data['inverterModelName']})"
        if "bmsFirmwareVersion" in device_data:
            device_info["hw_version"] = device_data["bmsFirmwareVersion"]

        return device_info

    async def async_patch_settings(
        self, mutate: Callable[[dict[str, Any]], None]
    ) -> None:
        """Apply a mutation to the device settings atomically.

        The device only accepts writes of the whole settings document, so the
        read-modify-write cycle is serialized to avoid lost updates.
        """
        async with self._settings_lock:
            settings = await async_get_and_transform_settings(self.api)
            mutate(settings)
            await self.api.update_settings({"settings": settings})
        await self.async_request_refresh()

    async def _async_fetch_all(self) -> dict[str, Any]:
        """Fetch every endpoint, tolerating failures of the optional ones."""
        # Core data: if these fail the device is considered offline.
        results: dict[str, Any] = {
            "status": _unwrap_required(await self.api.get_status(), "status"),
            "device": _unwrap_required(await self.api.get_device(), "device"),
        }

        optional: dict[str, Callable[[], Coroutine[Any, Any, dict[str, Any]]]] = {
            "config_state": self.api.get_config_state,
            "settings": self.api.get_settings,
            "schedule": self.api.get_schedule,
            "notifications": self.api.get_notifications,
            "unread_notifications_count": self.api.get_unread_notifications_count,
        }
        if (
            self.config_entry.data.get(CONF_USER_TYPE, ACCOUNT_TYPE_TECHNICIAN)
            == ACCOUNT_TYPE_TECHNICIAN
        ):
            optional["technical_status"] = self.api.get_technical_status
            optional["maintenance_diagnostics"] = self.api.get_maintenance_diagnostics
        else:
            results["technical_status"] = {}
            results["maintenance_diagnostics"] = {}

        responses = await asyncio.gather(
            *(fetch() for fetch in optional.values()), return_exceptions=True
        )
        for name, response in zip(optional, responses, strict=True):
            if isinstance(response, BaseException):
                _LOGGER.debug("Failed to fetch %s: %s", name, response)
                results[name] = {}
            else:
                results[name] = _unwrap(response)

        return results

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            results = await self._async_fetch_all()
        except EatonAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EatonError as err:
            if not self._unavailable_logged:
                self._unavailable_logged = True
                _LOGGER.warning("Eaton xStorage Home is unavailable: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        if self._unavailable_logged:
            self._unavailable_logged = False
            _LOGGER.info("Eaton xStorage Home is available again")

        return results
