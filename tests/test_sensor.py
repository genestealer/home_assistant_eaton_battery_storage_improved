"""Tests for the value handling of the Eaton xStorage Home sensor platform."""

from typing import Any

import pytest
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.eaton_battery_storage.const import DOMAIN, sensor_unique_id

from .conftest import SERIAL, STATUS_RESULT, TECH_INPUT, mock_device


async def setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Set up a technician config entry and return it."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data=TECH_INPUT, minor_version=2
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def sensor_state(hass: HomeAssistant, entry: MockConfigEntry, key: str) -> str:
    """Return the state of the sensor for a coordinator data key."""
    entity_id = er.async_get(hass).async_get_entity_id(
        SENSOR_DOMAIN, DOMAIN, sensor_unique_id(entry.entry_id, key)
    )
    return hass.states.get(entity_id).state


async def test_state_of_charge_is_recorded_as_a_measurement(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """The state of charge needs a state class to reach long term statistics."""
    mock_device(
        aioclient_mock,
        status={**STATUS_RESULT, "energyFlow": {"stateOfCharge": 62}},
    )
    entry = await setup_entry(hass)

    entity_id = er.async_get(hass).async_get_entity_id(
        SENSOR_DOMAIN,
        DOMAIN,
        sensor_unique_id(entry.entry_id, "status.energyFlow.stateOfCharge"),
    )
    state = hass.states.get(entity_id)

    assert state.state == "62"
    assert state.attributes["state_class"] is SensorStateClass.MEASUREMENT


@pytest.mark.parametrize(
    ("technical_status", "key", "expected"),
    [
        pytest.param(
            {"bmsHighestCellVoltage": 3500, "bmsLowestCellVoltage": 3400},
            "technical_status.bmsCellVoltageDelta",
            "100.0",
            id="cell_voltage_delta",
        ),
        pytest.param(
            {"bmsLowestCellVoltage": 3400},
            "technical_status.bmsCellVoltageDelta",
            STATE_UNKNOWN,
            id="cell_voltage_delta_without_highest",
        ),
        pytest.param(
            {"bmsHighestCellVoltage": 900, "bmsLowestCellVoltage": 3400},
            "technical_status.bmsCellVoltageDelta",
            STATE_UNKNOWN,
            id="cell_voltage_delta_with_implausible_highest",
        ),
        pytest.param(
            {"bmsHighestCellVoltage": 3500, "bmsLowestCellVoltage": 900},
            "technical_status.bmsCellVoltageDelta",
            STATE_UNKNOWN,
            id="cell_voltage_delta_with_implausible_lowest",
        ),
        pytest.param(
            {"bmsHighestCellVoltage": "n/a", "bmsLowestCellVoltage": 3400},
            "technical_status.bmsCellVoltageDelta",
            STATE_UNKNOWN,
            id="cell_voltage_delta_with_non_numeric_reading",
        ),
        pytest.param(
            {"bmsHighestCellVoltage": 3500},
            "technical_status.bmsHighestCellVoltage",
            "3500",
            id="cell_voltage",
        ),
        pytest.param(
            {"bmsHighestCellVoltage": 900},
            "technical_status.bmsHighestCellVoltage",
            STATE_UNKNOWN,
            id="implausible_cell_voltage_is_dropped",
        ),
        pytest.param(
            {"bmsFaultCode": ["OVER_VOLTAGE", "GENERAL"]},
            "technical_status.bmsFaultCode",
            "Over-voltage, General BMS fault",
            id="fault_codes_are_translated",
        ),
        pytest.param(
            {"bmsFaultCode": ["NOT_A_KNOWN_CODE"]},
            "technical_status.bmsFaultCode",
            "NOT_A_KNOWN_CODE",
            id="unknown_fault_code_is_passed_through",
        ),
        pytest.param(
            {"bmsFaultCode": None},
            "technical_status.bmsFaultCode",
            "No fault",
            id="null_fault_code_reads_as_no_fault",
        ),
        pytest.param(
            {"bmsFaultCode": []},
            "technical_status.bmsFaultCode",
            "No fault",
            id="empty_fault_code_list_reads_as_no_fault",
        ),
        pytest.param(
            {"bmsFaultCode": "OVER_VOLTAGE"},
            "technical_status.bmsFaultCode",
            "OVER_VOLTAGE",
            id="scalar_fault_code_is_passed_through",
        ),
        pytest.param(
            {"bmsState": "BAT_CHARGING"},
            "technical_status.bmsState",
            "Charging",
            id="bms_state_is_translated",
        ),
        pytest.param(
            {"bmsState": "BAT_SOMETHING_NEW"},
            "technical_status.bmsState",
            "BAT_SOMETHING_NEW",
            id="unknown_bms_state_is_passed_through",
        ),
        pytest.param(
            {"bmsMaxTemperature": 25.44},
            "technical_status.bmsMaxTemperature",
            "25.4",
            id="temperature_is_rounded",
        ),
        pytest.param(
            {"bmsMaxTemperature": 0},
            "technical_status.bmsMaxTemperature",
            STATE_UNKNOWN,
            id="zero_temperature_is_dropped",
        ),
        pytest.param(
            {"gridFrequency": 0},
            "technical_status.gridFrequency",
            STATE_UNKNOWN,
            id="zero_grid_frequency_is_dropped",
        ),
        pytest.param(
            {},
            "technical_status.bmsState",
            STATE_UNKNOWN,
            id="missing_key_reads_as_unknown",
        ),
    ],
)
async def test_technical_status_values(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    technical_status: dict[str, Any],
    key: str,
    expected: str,
) -> None:
    """Technical status values are filtered and translated for display."""
    mock_device(aioclient_mock, technical_status=technical_status)
    entry = await setup_entry(hass)

    assert sensor_state(hass, entry, key) == expected


@pytest.mark.parametrize(
    ("status", "key", "expected"),
    [
        pytest.param(
            {"currentMode": {"command": "SET_CHARGE"}},
            "status.currentMode.command",
            "Charge",
            id="mode_command_is_translated",
        ),
        pytest.param(
            {
                "currentMode": {
                    "command": "SET_CHARGE",
                    "parameters": {"action": "ACTION_DISCHARGE"},
                }
            },
            "status.currentMode.command",
            "Discharge",
            id="discharge_action_wins_over_the_echoed_command",
        ),
        pytest.param(
            {"currentMode": {"command": "SET_DISCHARGE"}},
            "status.currentMode.command",
            "Discharge",
            id="discharge_without_an_action_is_translated",
        ),
        pytest.param(
            {"currentMode": {"type": "SCHEDULE"}},
            "status.currentMode.type",
            "Scheduled",
            id="mode_type_is_translated",
        ),
        pytest.param(
            {"energyFlow": {"batteryStatus": "BAT_DISCHARGING"}},
            "status.energyFlow.batteryStatus",
            "Discharging",
            id="battery_status_is_translated",
        ),
        pytest.param(
            {"currentMode": {"startTime": 1154}},
            "status.currentMode.startTime",
            "11:54",
            id="numeric_time_is_formatted",
        ),
        pytest.param(
            {"currentMode": {"startTime": "0905"}},
            "status.currentMode.startTime",
            "09:05",
            id="string_time_is_formatted",
        ),
        pytest.param(
            {"currentMode": {"startTime": 9999}},
            "status.currentMode.startTime",
            "9999",
            id="out_of_range_time_is_passed_through",
        ),
    ],
)
async def test_status_values(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    status: dict[str, Any],
    key: str,
    expected: str,
) -> None:
    """Status values are formatted for display."""
    mock_device(aioclient_mock, status={**STATUS_RESULT, **status})
    entry = await setup_entry(hass)

    assert sensor_state(hass, entry, key) == expected


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        pytest.param(
            "maintenance_diagnostics.ramUsage.used", "1.0", id="ram_bytes_to_megabytes"
        ),
        pytest.param(
            "maintenance_diagnostics.cpuUsage.used", "12.35", id="cpu_usage_is_rounded"
        ),
    ],
)
async def test_maintenance_diagnostics_values(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    key: str,
    expected: str,
) -> None:
    """Maintenance values are converted to the units the sensors declare."""
    mock_device(
        aioclient_mock,
        maintenance_diagnostics={
            "ramUsage": {"used": 1048576},
            "cpuUsage": {"used": 12.3456},
        },
    )
    entry = await setup_entry(hass)

    assert sensor_state(hass, entry, key) == expected
