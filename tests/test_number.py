"""Tests for the Eaton xStorage Home number platform."""

from typing import Any

import pytest
from homeassistant.components.number import (
    ATTR_VALUE,
    SERVICE_SET_VALUE,
)
from homeassistant.components.number import (
    DOMAIN as NUMBER_DOMAIN,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.eaton_battery_storage.const import DOMAIN

from .conftest import DEVICE_RESULT, SERIAL, TECH_INPUT, USER_INPUT, mock_device

CHARGE_POWER_KEY = "charge_power"
CHARGE_POWER_WATT_KEY = "charge_power_watt"


async def setup_entry(hass: HomeAssistant, data: dict[str, Any]) -> MockConfigEntry:
    """Set up a config entry and return it."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=data, minor_version=2)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def entity_id_for(hass: HomeAssistant, entry: MockConfigEntry, key: str) -> str:
    """Return the entity ID of a number entity by its unique ID suffix."""
    return er.async_get(hass).async_get_entity_id(
        NUMBER_DOMAIN, DOMAIN, f"{entry.entry_id}_{key}"
    )


@pytest.mark.parametrize(
    ("data", "device", "technical_status", "expected_max"),
    [
        pytest.param(
            TECH_INPUT,
            DEVICE_RESULT,
            {"inverterPowerRating": 6000},
            6000,
            id="technician_reads_inverter_power_rating",
        ),
        pytest.param(
            USER_INPUT,
            {**DEVICE_RESULT, "inverterVaRating": 4600},
            {},
            4600,
            id="customer_falls_back_to_va_rating",
        ),
        pytest.param(
            TECH_INPUT,
            {**DEVICE_RESULT, "inverterVaRating": 3600},
            {"inverterPowerRating": 0},
            3600,
            id="rating_reported_as_zero_falls_back_to_va_rating",
        ),
        pytest.param(
            USER_INPUT,
            DEVICE_RESULT,
            {},
            3600,
            id="unknown_rating_falls_back_to_smallest_model",
        ),
    ],
)
async def test_watt_range_follows_inverter_rating(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    data: dict[str, Any],
    device: dict[str, Any],
    technical_status: dict[str, Any],
    expected_max: int,
) -> None:
    """The watt entities span 5-100 % of the rating the device reports."""
    mock_device(aioclient_mock, device=device, technical_status=technical_status)

    entry = await setup_entry(hass, data)
    state = hass.states.get(entity_id_for(hass, entry, CHARGE_POWER_WATT_KEY))

    assert state.attributes["max"] == expected_max
    assert state.attributes["min"] == expected_max * 0.05


async def test_percentage_conversion_uses_inverter_rating(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Setting a percentage stores the matching wattage for the actual model."""
    mock_device(aioclient_mock, technical_status={"inverterPowerRating": 6000})

    entry = await setup_entry(hass, TECH_INPUT)

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id_for(hass, entry, CHARGE_POWER_KEY),
            ATTR_VALUE: 50,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    watt_state = hass.states.get(entity_id_for(hass, entry, CHARGE_POWER_WATT_KEY))

    assert watt_state.state == "3000"
