"""System health support for Eaton xStorage Home integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
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
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return {}

    coordinator = entries[0].runtime_data
    return {
        "device_reachable": coordinator.last_update_success,
        "api_host": coordinator.api.host,
        "last_successful_update": coordinator.last_update_success_time,
    }
