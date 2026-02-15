"""Tests for the Eaton Battery Storage config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_battery_storage.const import (
    ACCOUNT_TYPE_CUSTOMER,
    ACCOUNT_TYPE_TECHNICIAN,
    DOMAIN,
)

from .conftest import MOCK_HOST, MOCK_INVERTER_SN, MOCK_PASSWORD, MOCK_USERNAME

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_USER_INPUT_CUSTOMER = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    "user_type": ACCOUNT_TYPE_CUSTOMER,
    "has_pv": False,
}

VALID_USER_INPUT_TECH = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    "user_type": ACCOUNT_TYPE_TECHNICIAN,
    "inverter_sn": MOCK_INVERTER_SN,
    "has_pv": False,
}


# ---------------------------------------------------------------------------
# User step tests
# ---------------------------------------------------------------------------


async def test_user_step_shows_form(hass: HomeAssistant) -> None:
    """Test that the user step shows a form when no data is provided."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_success_customer(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test successful config flow for a customer account."""
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Eaton xStorage Home"
    assert result["data"][CONF_HOST] == MOCK_HOST
    assert result["data"][CONF_USERNAME] == MOCK_USERNAME
    assert result["data"]["user_type"] == ACCOUNT_TYPE_CUSTOMER
    assert result["data"]["email"] == "anything@anything.com"


async def test_user_step_success_technician(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test successful config flow for a technician account with serial."""
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        return_value=MOCK_INVERTER_SN,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_TECH,
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["inverter_sn"] == MOCK_INVERTER_SN


async def test_user_step_technician_missing_inverter_sn(
    hass: HomeAssistant,
) -> None:
    """Test that a tech account without inverter_sn shows an error."""
    input_data = {
        CONF_HOST: MOCK_HOST,
        CONF_USERNAME: MOCK_USERNAME,
        CONF_PASSWORD: MOCK_PASSWORD,
        "user_type": ACCOUNT_TYPE_TECHNICIAN,
        "inverter_sn": "",
        "has_pv": False,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=input_data,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["inverter_sn"] == "required_inverter_sn"


async def test_user_step_cannot_connect(
    hass: HomeAssistant,
) -> None:
    """Test error handling when the device is unreachable."""
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        side_effect=ConnectionError("Cannot connect to device"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_user_step_invalid_auth(
    hass: HomeAssistant,
) -> None:
    """Test error handling when credentials are wrong."""
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        side_effect=ValueError("Invalid credentials"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


async def test_user_step_auth_error_locked(
    hass: HomeAssistant,
) -> None:
    """Test error handling when the account is locked."""
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        side_effect=ValueError("Error during authentication: 10"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "auth_error_locked"


async def test_user_step_wrong_credentials(
    hass: HomeAssistant,
) -> None:
    """Test error handling for wrong credentials message."""
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        side_effect=ValueError("Wrong credentials"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "err_wrong_credentials"


async def test_user_step_unknown_error(
    hass: HomeAssistant,
) -> None:
    """Test error handling for unexpected exceptions."""
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        side_effect=RuntimeError("Boom"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "unknown"


async def test_user_step_already_configured(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test that duplicate entries are aborted."""
    # First entry
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Second entry - same host+username → should abort
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# _map_auth_error tests
# ---------------------------------------------------------------------------


def test_map_auth_error_locked() -> None:
    """Test mapping of locked error."""
    from custom_components.eaton_battery_storage.config_flow import _map_auth_error

    assert _map_auth_error(ValueError("Error during authentication: 10")) == "auth_error_locked"


def test_map_auth_error_wrong_creds() -> None:
    """Test mapping of wrong credentials error."""
    from custom_components.eaton_battery_storage.config_flow import _map_auth_error

    assert _map_auth_error(ValueError("wrong credentials")) == "err_wrong_credentials"


def test_map_auth_error_invalid_inverter() -> None:
    """Test mapping of invalid inverter serial error."""
    from custom_components.eaton_battery_storage.config_flow import _map_auth_error

    assert _map_auth_error(ValueError("invalid inverter serial")) == "err_invalid_inverter_sn"


def test_map_auth_error_non_json() -> None:
    """Test mapping of non-JSON response error."""
    from custom_components.eaton_battery_storage.config_flow import _map_auth_error

    assert _map_auth_error(ValueError("non-JSON response")) == "auth_non_json_response"


def test_map_auth_error_unexpected_response() -> None:
    """Test mapping of unexpected response error."""
    from custom_components.eaton_battery_storage.config_flow import _map_auth_error

    assert _map_auth_error(ValueError("unexpected response")) == "auth_unexpected_response"


def test_map_auth_error_fallback() -> None:
    """Test the fallback mapping for unrecognized errors."""
    from custom_components.eaton_battery_storage.config_flow import _map_auth_error

    assert _map_auth_error(ValueError("something else")) == "invalid_auth"


# ---------------------------------------------------------------------------
# Reauth flow tests
# ---------------------------------------------------------------------------


async def test_reauth_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test that reauth updates existing entry credentials."""
    # Create an existing entry first
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Eaton xStorage Home",
        data={
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: "old_user",
            CONF_PASSWORD: "old_pass",
            "user_type": ACCOUNT_TYPE_CUSTOMER,
            "inverter_sn": "",
            "email": "anything@anything.com",
        },
    )
    entry.add_to_hass(hass)

    # Start reauth
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Submit new credentials
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "new_user",
                CONF_PASSWORD: "new_pass",
            },
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    # Verify data was updated
    assert entry.data[CONF_USERNAME] == "new_user"


async def test_reauth_flow_connection_error(
    hass: HomeAssistant,
) -> None:
    """Test reauth handles connection errors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Eaton xStorage Home",
        data={
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: "old_user",
            CONF_PASSWORD: "old_pass",
            "user_type": ACCOUNT_TYPE_CUSTOMER,
            "inverter_sn": "",
            "email": "anything@anything.com",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        side_effect=ConnectionError("Cannot connect to device"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "new_user",
                CONF_PASSWORD: "new_pass",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "cannot_connect"


# ---------------------------------------------------------------------------
# Options flow tests
# ---------------------------------------------------------------------------


async def test_options_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test successful options flow updates entry data."""
    # Create a config entry
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]

    # Start options flow
    result2 = await hass.config_entries.options.async_init(entry.entry_id)
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "init"

    # Submit new options
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        return_value=None,
    ):
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"],
            user_input={
                CONF_HOST: MOCK_HOST,
                CONF_USERNAME: "updated_user",
                CONF_PASSWORD: "updated_pass",
                "user_type": ACCOUNT_TYPE_CUSTOMER,
                "has_pv": True,
            },
        )

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    # Check that the config entry data was updated
    assert entry.data[CONF_USERNAME] == "updated_user"
    assert entry.data["has_pv"] is True


async def test_options_flow_connection_error(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test options flow handles connection error gracefully."""
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )
    entry = result["result"]

    result2 = await hass.config_entries.options.async_init(entry.entry_id)

    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        side_effect=ConnectionError("Cannot connect to device"),
    ):
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"],
            user_input={
                CONF_HOST: MOCK_HOST,
                CONF_USERNAME: "updated_user",
                CONF_PASSWORD: "updated_pass",
                "user_type": ACCOUNT_TYPE_CUSTOMER,
                "has_pv": False,
            },
        )

    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"]["base"] == "cannot_connect"


async def test_options_flow_technician_missing_sn(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test options flow requires inverter_sn for technician."""
    with patch(
        "custom_components.eaton_battery_storage.config_flow._async_test_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_USER_INPUT_CUSTOMER,
        )
    entry = result["result"]

    result2 = await hass.config_entries.options.async_init(entry.entry_id)

    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
            "user_type": ACCOUNT_TYPE_TECHNICIAN,
            "inverter_sn": "",
            "has_pv": False,
        },
    )

    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"]["inverter_sn"] == "required_inverter_sn"
