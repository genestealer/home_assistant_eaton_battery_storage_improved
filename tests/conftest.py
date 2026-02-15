"""Fixtures for Eaton Battery Storage integration tests.

Follows Home Assistant testing guidelines:
https://developers.home-assistant.io/docs/development_testing/

Uses pytest-homeassistant-custom-component which provides the ``hass`` fixture
and re-exports ``MockConfigEntry`` from HA core's test helpers.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_battery_storage.const import DOMAIN

# ---------------------------------------------------------------------------
# Reusable test data
# ---------------------------------------------------------------------------

MOCK_HOST = "192.168.1.100"
MOCK_USERNAME = "admin"
MOCK_PASSWORD = "password123"
MOCK_INVERTER_SN = "INV123456"
MOCK_EMAIL = "anything@anything.com"
MOCK_ENTRY_ID = "test_entry_id_001"

MOCK_CONFIG_DATA_TECH: dict[str, Any] = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    "inverter_sn": MOCK_INVERTER_SN,
    "email": MOCK_EMAIL,
    "user_type": "tech",
    "has_pv": False,
}

MOCK_CONFIG_DATA_CUSTOMER: dict[str, Any] = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    "inverter_sn": "",
    "email": MOCK_EMAIL,
    "user_type": "customer",
    "has_pv": False,
}


def _build_api_response(result: dict[str, Any] | list | None = None) -> dict[str, Any]:
    """Build a standard successful API response envelope."""
    return {"successful": True, "result": result or {}}


# ---------------------------------------------------------------------------
# Mock coordinator data — representative subset of real device responses
# ---------------------------------------------------------------------------

MOCK_DEVICE_DATA: dict[str, Any] = {
    "powerState": True,
    "inverterSerialNumber": MOCK_INVERTER_SN,
    "inverterModelName": "XSHOME-10.0-EN",
    "firmwareVersion": "3.2.1",
    "bmsFirmwareVersion": "1.0.4",
}

MOCK_STATUS_DATA: dict[str, Any] = {
    "energyFlow": {
        "batteryStatus": "BAT_CHARGING",
        "stateOfCharge": 72,
        "gridValue": 150,
        "gridRole": "IMPORT",
        "loadValue": 500,
        "dcPvValue": 0,
        "dcPvRole": "IDLE",
        "acPvValue": 0,
        "acPvRole": "IDLE",
    },
    "today": {
        "selfConsumption": 12.5,
        "gridConsumption": 3.2,
        "photovoltaicProduction": 0,
    },
    "last30daysEnergyFlow": {
        "selfConsumption": 250.0,
        "gridConsumption": 80.0,
        "photovoltaicProduction": 0,
    },
}

MOCK_SETTINGS_DATA: dict[str, Any] = {
    "defaultMode": {
        "command": "SET_MAXIMIZE_AUTO_CONSUMPTION",
        "parameters": {},
    },
    "energySavingMode": {
        "enabled": False,
        "houseConsumptionThreshold": 500,
    },
    "bmsBackupLevel": 10,
    "country": {"geonameId": "2635167", "name": "United Kingdom"},
    "city": {"geonameId": "2643743", "name": "London"},
    "timezone": {"id": "Europe/London", "name": "GMT"},
}

MOCK_CONFIG_STATE_DATA: dict[str, Any] = {
    "currentMode": {
        "command": "SET_MAXIMIZE_AUTO_CONSUMPTION",
        "action": "ACTION_CHARGE",
        "type": "SCHEDULE",
        "recurrence": "DAILY",
        "parameters": {},
    },
}

MOCK_METRICS_DATA: dict[str, Any] = {}
MOCK_METRICS_DAILY_DATA: dict[str, Any] = {}
MOCK_SCHEDULE_DATA: dict[str, Any] = {}

MOCK_TECHNICAL_STATUS_DATA: dict[str, Any] = {
    "operationMode": "MAXIMIZE_AUTO_CONSUMPTION",
    "gridVoltage": 240.5,
    "gridFrequency": 50.01,
    "inverterPower": 1500,
    "inverterTemperature": 35.2,
    "bmsVoltage": 52.1,
    "bmsCurrent": 12.3,
    "bmsTemperature": 28.0,
    "bmsStateOfCharge": 72,
    "bmsState": "BAT_CHARGING",
}

MOCK_MAINTENANCE_DIAGNOSTICS_DATA: dict[str, Any] = {
    "ramUsage": {"total": 1024, "used": 512},
    "cpuUsage": {"used": 45},
}

MOCK_NOTIFICATIONS_DATA: dict[str, Any] = {
    "results": [
        {
            "alertId": "alert_001",
            "title": "Battery Low",
            "message": "Battery below 20%",
            "status": "unread",
        },
    ],
}

MOCK_UNREAD_NOTIFICATIONS_DATA: dict[str, Any] = {"total": 1}


def build_coordinator_data(
    *,
    device: dict[str, Any] | None = None,
    status: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
    config_state: dict[str, Any] | None = None,
    technical_status: dict[str, Any] | None = None,
    maintenance_diagnostics: dict[str, Any] | None = None,
    notifications: dict[str, Any] | None = None,
    unread_notifications_count: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete coordinator data dict with sensible defaults."""
    return {
        "device": device if device is not None else MOCK_DEVICE_DATA,
        "status": status if status is not None else MOCK_STATUS_DATA,
        "settings": settings if settings is not None else MOCK_SETTINGS_DATA,
        "config_state": config_state if config_state is not None else MOCK_CONFIG_STATE_DATA,
        "metrics": MOCK_METRICS_DATA,
        "metrics_daily": MOCK_METRICS_DAILY_DATA,
        "schedule": MOCK_SCHEDULE_DATA,
        "technical_status": (
            technical_status if technical_status is not None else MOCK_TECHNICAL_STATUS_DATA
        ),
        "maintenance_diagnostics": (
            maintenance_diagnostics
            if maintenance_diagnostics is not None
            else MOCK_MAINTENANCE_DIAGNOSTICS_DATA
        ),
        "notifications": notifications if notifications is not None else MOCK_NOTIFICATIONS_DATA,
        "unread_notifications_count": (
            unread_notifications_count
            if unread_notifications_count is not None
            else MOCK_UNREAD_NOTIFICATIONS_DATA
        ),
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_api() -> AsyncMock:
    """Return a fully-mocked EatonBatteryAPI instance."""
    api = AsyncMock()
    api.host = MOCK_HOST
    api.username = MOCK_USERNAME
    api.password = MOCK_PASSWORD
    api.inverter_sn = MOCK_INVERTER_SN
    api.email = MOCK_EMAIL
    api.user_type = "tech"
    api.access_token = "mock_token"
    api.name = "Eaton xStorage Home"
    api.manufacturer = "Eaton"

    # Default return values for API calls
    api.connect = AsyncMock(return_value=None)
    api.get_status = AsyncMock(return_value=_build_api_response(MOCK_STATUS_DATA))
    api.get_device = AsyncMock(return_value=_build_api_response(MOCK_DEVICE_DATA))
    api.get_config_state = AsyncMock(return_value=_build_api_response(MOCK_CONFIG_STATE_DATA))
    api.get_settings = AsyncMock(return_value=_build_api_response(MOCK_SETTINGS_DATA))
    api.get_metrics = AsyncMock(return_value=_build_api_response(MOCK_METRICS_DATA))
    api.get_metrics_daily = AsyncMock(return_value=_build_api_response(MOCK_METRICS_DAILY_DATA))
    api.get_schedule = AsyncMock(return_value=_build_api_response(MOCK_SCHEDULE_DATA))
    api.get_technical_status = AsyncMock(
        return_value=_build_api_response(MOCK_TECHNICAL_STATUS_DATA)
    )
    api.get_maintenance_diagnostics = AsyncMock(
        return_value=_build_api_response(MOCK_MAINTENANCE_DIAGNOSTICS_DATA)
    )
    api.get_notifications = AsyncMock(
        return_value=_build_api_response(MOCK_NOTIFICATIONS_DATA)
    )
    api.get_unread_notifications_count = AsyncMock(
        return_value=_build_api_response(MOCK_UNREAD_NOTIFICATIONS_DATA)
    )
    api.mark_all_notifications_read = AsyncMock(return_value={"successful": True})
    api.set_device_power = AsyncMock(return_value={"successful": True})
    api.send_device_command = AsyncMock(return_value={"successful": True})
    api.update_settings = AsyncMock(return_value={"successful": True})
    api.store_token = AsyncMock(return_value=None)
    api.load_token = AsyncMock(return_value=None)

    return api


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a MockConfigEntry and add it to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=dict(MOCK_CONFIG_DATA_TECH),
        options={},
        unique_id=f"{MOCK_HOST}_{MOCK_INVERTER_SN}",
        title="Eaton xStorage Home",
        entry_id=MOCK_ENTRY_ID,
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_coordinator(
    hass: HomeAssistant, mock_api: AsyncMock, mock_config_entry: MagicMock
) -> MagicMock:
    """Return a mock coordinator with data pre-loaded."""
    coordinator = MagicMock()
    coordinator.hass = hass
    coordinator.api = mock_api
    coordinator.config_entry = mock_config_entry
    coordinator.data = build_coordinator_data()
    coordinator.last_update_success = True
    coordinator.last_update_success_time = None
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_add_listener = MagicMock(return_value=MagicMock())

    # Build device info matching what the real coordinator returns
    coordinator.device_info = {
        "identifiers": {(DOMAIN, MOCK_HOST)},
        "name": "Eaton xStorage Home",
        "manufacturer": "Eaton",
        "model": f"xStorage Home ({MOCK_DEVICE_DATA['inverterModelName']})",
        "sw_version": MOCK_DEVICE_DATA["firmwareVersion"],
        "hw_version": MOCK_DEVICE_DATA["bmsFirmwareVersion"],
        "serial_number": MOCK_INVERTER_SN,
        "configuration_url": f"https://{MOCK_HOST}",
    }

    return coordinator


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,  # noqa: ARG001 — provided by pytest-homeassistant-custom-component
) -> None:
    """Enable loading of custom_components in every test.

    Required since pytest-homeassistant-custom-component >= 2021.6.0b0.
    """


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Prevent actual setup during config flow tests."""
    with patch(
        "custom_components.eaton_battery_storage.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock
