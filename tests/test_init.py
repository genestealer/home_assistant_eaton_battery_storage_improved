"""Tests for the Eaton xStorage Home integration setup and migration."""

from typing import Any

import aiohttp
import pytest
from homeassistant.config_entries import SOURCE_RECONFIGURE, ConfigEntryState
from homeassistant.const import SERVICE_RELOAD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.service import async_get_all_descriptions
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.eaton_battery_storage.api import token_store_key
from custom_components.eaton_battery_storage.const import (
    CONF_HAS_PV,
    DOMAIN,
    sensor_unique_id,
)

from .conftest import BASE_URL, HOST, JSON_HEADERS, SERIAL, USER_INPUT, mock_device

# A sensor that only exists for systems with solar panels.
PV_SENSOR_KEY = "status.energyFlow.acPvValue"
PV_INPUT = {**USER_INPUT, CONF_HAS_PV: True}


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Add the entry to hass and set it up."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def reconfigure(
    hass: HomeAssistant, entry: MockConfigEntry, data: dict[str, Any]
) -> None:
    """Change the entry's settings the way a user does, through the flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    await hass.config_entries.flow.async_configure(result["flow_id"], data)
    await hass.async_block_till_done()


@pytest.mark.usefixtures("mock_connected_device")
async def test_setup_and_unload(hass: HomeAssistant) -> None:
    """The entry sets up its platforms and unloads cleanly."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=3
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
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=3
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
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=3
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
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=3
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


@pytest.mark.usefixtures("mock_connected_device")
async def test_pv_sensors_follow_the_pv_option(hass: HomeAssistant) -> None:
    """Turning the PV option off hides the sensors it created, and back on restores them."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=PV_INPUT, minor_version=3
    )
    await setup_entry(hass, entry)
    entity_registry = er.async_get(hass)
    entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, sensor_unique_id(entry.entry_id, PV_SENSOR_KEY)
    )
    assert entity_registry.async_get(entity_id).disabled_by is None

    await reconfigure(hass, entry, USER_INPUT)

    assert (
        entity_registry.async_get(entity_id).disabled_by
        is er.RegistryEntryDisabler.INTEGRATION
    )

    await reconfigure(hass, entry, PV_INPUT)

    assert entity_registry.async_get(entity_id).disabled_by is None


@pytest.mark.usefixtures("mock_connected_device")
async def test_a_user_disabled_pv_sensor_is_left_alone(hass: HomeAssistant) -> None:
    """A deliberate user choice must survive the PV migration."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=PV_INPUT, minor_version=3
    )
    await setup_entry(hass, entry)
    entity_registry = er.async_get(hass)
    entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, sensor_unique_id(entry.entry_id, PV_SENSOR_KEY)
    )
    entity_registry.async_update_entity(
        entity_id, disabled_by=er.RegistryEntryDisabler.USER
    )

    await reconfigure(hass, entry, USER_INPUT)

    assert (
        entity_registry.async_get(entity_id).disabled_by
        is er.RegistryEntryDisabler.USER
    )


@pytest.mark.usefixtures("mock_connected_device")
async def test_removing_the_entry_deletes_the_stored_token(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """The device credentials must not outlive the config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=3
    )
    await setup_entry(hass, entry)
    store_key = token_store_key(entry.entry_id)
    assert store_key in hass_storage

    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert store_key not in hass_storage


@pytest.mark.usefixtures("mock_connected_device")
async def test_the_reload_service_repolls_the_device(hass: HomeAssistant) -> None:
    """Reloading tears the entry down and sets it back up against the device."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=3
    )
    await setup_entry(hass, entry)
    coordinator = entry.runtime_data

    await hass.services.async_call(DOMAIN, SERVICE_RELOAD, {}, blocking=True)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    # A reload replaces the coordinator, so the old one cannot still be in use.
    assert entry.runtime_data is not coordinator


@pytest.mark.usefixtures("mock_connected_device")
async def test_every_registered_service_is_described(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """A service missing from services.yaml makes Home Assistant log an error."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT, minor_version=3
    )
    await setup_entry(hass, entry)

    await async_get_all_descriptions(hass)

    assert set(hass.services.async_services_for_domain(DOMAIN)) == {SERVICE_RELOAD}
    assert "services.yaml" not in caplog.text
