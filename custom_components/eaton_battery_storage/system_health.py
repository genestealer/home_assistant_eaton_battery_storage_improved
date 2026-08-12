"""System health platform for Eaton xStorage Home Battery integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the system health panel."""
    entry = next(
        (
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.state is ConfigEntryState.LOADED
        ),
        None,
    )
    if entry is None:
        return {"device_reachable": False, "last_successful_update": "Never"}

    coordinator = entry.runtime_data
    return {
        "device_reachable": coordinator.last_update_success,
        "api_host": coordinator.api.host,
        "last_successful_update": str(coordinator.last_update_success_time)
        if coordinator.last_update_success_time
        else "Never",
    }
