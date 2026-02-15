"""Shared helper functions for Eaton xStorage Home integration."""

from __future__ import annotations

from typing import Any


def transform_settings_for_put(settings: dict[str, Any]) -> dict[str, Any]:
    """Transform GET API settings response to PUT API format.

    The GET API returns composite objects for country, city, and timezone,
    but the PUT API expects primitive string values (geonameId or id).
    This function converts them in-place and returns the modified dict.
    """
    if "country" in settings and isinstance(settings["country"], dict):
        settings["country"] = settings["country"].get("geonameId", "")

    if "city" in settings and isinstance(settings["city"], dict):
        settings["city"] = settings["city"].get("geonameId", "")

    if "timezone" in settings and isinstance(settings["timezone"], dict):
        settings["timezone"] = settings["timezone"].get("id", "")

    return settings
