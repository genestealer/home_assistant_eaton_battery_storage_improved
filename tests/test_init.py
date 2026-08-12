"""Tests for the Eaton xStorage Home integration setup and migration."""

from typing import Any

import aiohttp
import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.eaton_battery_storage.const import DOMAIN

from .conftest import BASE_URL, HOST, JSON_HEADERS, SERIAL, USER_INPUT, mock_device


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Add the entry to hass and set it up."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.usefixtures("mock_connected_device")
async def test_setup_and_unload(hass: HomeAssistant) -> None:
    """The entry sets up its platforms and unloads cleanly."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=2
    )
    await setup_entry(hass, entry)

    assert entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.usefixtures("mock_connected_device")
async def test_device_is_keyed_on_the_serial(hass: HomeAssistant) -> None:
    """The device registry entry never carries a host based identifier."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=2
    )
    await setup_entry(hass, entry)

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)

    assert len(devices) == 1
    assert devices[0].identifiers == {(DOMAIN, SERIAL)}
    assert devices[0].serial_number == SERIAL
    assert devices[0].sw_version == "1.2.3"


@pytest.mark.parametrize(
    ("signin_response", "expected_state"),
    [
        pytest.param(
            {
                "json": {"error": {"errCode": "3", "description": "Wrong credentials"}},
                "headers": JSON_HEADERS,
            },
            ConfigEntryState.SETUP_ERROR,
            id="auth_error_triggers_reauth",
        ),
        pytest.param(
            {"exc": aiohttp.ClientConnectionError()},
            ConfigEntryState.SETUP_RETRY,
            id="connection_error_retries",
        ),
    ],
)
async def test_setup_failures(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    signin_response: dict[str, Any],
    expected_state: ConfigEntryState,
) -> None:
    """Authentication and connectivity failures are reported differently."""
    aioclient_mock.post(f"{BASE_URL}/api/auth/signin", **signin_response)
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=2
    )
    await setup_entry(hass, entry)

    assert entry.state is expected_state


async def test_setup_retries_when_the_device_returns_no_status(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A device that authenticates but serves no data is treated as unavailable."""
    aioclient_mock.get(
        f"{BASE_URL}/api/device/status",
        json={"successful": False, "error": "busy"},
        headers=JSON_HEADERS,
    )
    mock_device(aioclient_mock)
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=2
    )
    await setup_entry(hass, entry)

    assert entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.usefixtures("mock_connected_device")
async def test_migrate_entry_rekeys_unique_id(hass: HomeAssistant) -> None:
    """A host-prefixed unique ID is migrated to the bare serial."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{HOST}_{SERIAL}",
        data=USER_INPUT,
        version=1,
        minor_version=1,
    )
    await setup_entry(hass, entry)

    assert entry.unique_id == SERIAL
    assert entry.minor_version == 2


@pytest.mark.usefixtures("mock_connected_device")
async def test_migrate_entry_drops_host_device_identifier(
    hass: HomeAssistant,
) -> None:
    """The legacy host identifier is removed from the existing device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{HOST}_{SERIAL}",
        data=USER_INPUT,
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, HOST), (DOMAIN, SERIAL)},
    )

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert device_registry.async_get(device.id).identifiers == {(DOMAIN, SERIAL)}
