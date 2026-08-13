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
    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if not entries:
        return {"device_reachable": False, "last_successful_update": "Never"}

    info: dict[str, Any] = {}
    for index, entry in enumerate(entries, start=1):
        coordinator = entry.runtime_data
        # A single inverter keeps the plain keys the panel has always shown.
        suffix = "" if len(entries) == 1 else f"_{index}"
        info[f"device_reachable{suffix}"] = coordinator.last_update_success
        info[f"api_host{suffix}"] = coordinator.api.host
        info[f"last_successful_update{suffix}"] = (
            str(coordinator.last_update_success_time)
            if coordinator.last_update_success_time
            else "Never"
        )
    return info
