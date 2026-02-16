"""Shared helpers for transforming Eaton xStorage Home settings."""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


def transform_settings_for_put(settings: dict[str, Any]) -> dict[str, Any]:
    """Transform GET API settings response to match PUT API expectations.

    The GET API returns composite objects for country, city, and timezone,
    but the PUT API expects string/primitive values.
    """
    if "country" in settings and isinstance(settings["country"], dict):
        settings["country"] = settings["country"].get("geonameId", "")

    if "city" in settings and isinstance(settings["city"], dict):
        settings["city"] = settings["city"].get("geonameId", "")

    if "timezone" in settings and isinstance(settings["timezone"], dict):
        settings["timezone"] = settings["timezone"].get("id", "")

    return settings


async def async_get_and_transform_settings(api: Any) -> dict[str, Any] | None:
    """Fetch current settings from API and transform for PUT.

    Returns the transformed settings dict, or None if fetch failed.
    """
    current_settings_response = await api.get_settings()
    if not current_settings_response or not current_settings_response.get("result"):
        _LOGGER.error("Failed to get current settings from API")
        return None

    current_settings = current_settings_response.get("result", {})
    return transform_settings_for_put(current_settings)
