"""Tests for the Eaton xStorage Home select platform."""

from homeassistant.components.select import (
    ATTR_OPTION,
    SERVICE_SELECT_OPTION,
)
from homeassistant.components.select import (
    DOMAIN as SELECT_DOMAIN,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest import raises
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.eaton_battery_storage.const import DOMAIN

from .conftest import BASE_URL, JSON_HEADERS, SERIAL, TECH_INPUT, mock_device

CURRENT_MODE_ENTITY_ID = "select.eaton_xstorage_home_current_operation_mode"

# What the inverter answers a command with, captured from a real device.
COMMAND_ACCEPTED = {
    "successful": True,
    "message": "Content Ready",
    "result": {
        "command": "SET_CHARGE",
        "duration": 1,
        "recurrence": "MANUAL_EVENT",
        "type": "MANUAL",
        "parameters": {"action": "ACTION_CHARGE", "power": 20, "soc": 80},
    },
}


async def setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Set up a config entry and return it."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=TECH_INPUT, minor_version=2
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def last_command(aioclient_mock: AiohttpClientMocker) -> dict:
    """Return the body of the most recent device command."""
    return next(
        data
        for method, url, data, _headers in reversed(aioclient_mock.mock_calls)
        if method.upper() == "POST" and url.path == "/api/device/command"
    )


async def test_selecting_a_mode_sends_the_configured_helpers(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """The command carries the duration, power and target SOC helper values."""
    aioclient_mock.post(
        f"{BASE_URL}/api/device/command", json=COMMAND_ACCEPTED, headers=JSON_HEADERS
    )
    mock_device(aioclient_mock)
    await setup_entry(hass)

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: CURRENT_MODE_ENTITY_ID, ATTR_OPTION: "Manual Charge"},
        blocking=True,
    )

    assert last_command(aioclient_mock) == {
        "command": "SET_CHARGE",
        "duration": 1,
        "parameters": {"action": "ACTION_CHARGE", "power": 20, "soc": 80},
    }


async def test_a_rejected_command_raises(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A device that rejects the command surfaces a translated error."""
    aioclient_mock.post(
        f"{BASE_URL}/api/device/command",
        json={"successful": False},
        headers=JSON_HEADERS,
    )
    mock_device(aioclient_mock)
    await setup_entry(hass)

    with raises(HomeAssistantError, match="Basic Mode"):
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: CURRENT_MODE_ENTITY_ID, ATTR_OPTION: "Basic Mode"},
            blocking=True,
        )
