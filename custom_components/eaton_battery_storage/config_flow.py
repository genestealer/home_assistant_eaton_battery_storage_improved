"""Config flow for Eaton xStorage Home integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector as sel

from .api import EatonBatteryAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_INVERTER_SN = "inverter_sn"
CONF_HAS_PV = "has_pv"
CONF_USER_TYPE = "user_type"


async def _async_test_connection(
    hass: HomeAssistant,
    host: str,
    username: str,
    password: str,
    inverter_sn: str,
    email: str,
    user_type: str = "tech",
) -> str | None:
    """Test connection to the device and return inverter serial if available.

    Shared helper used by ConfigFlow, OptionsFlow, and ReauthFlow.
    """
    api = EatonBatteryAPI(
        hass=hass,
        host=host,
        username=username,
        password=password,
        inverter_sn=inverter_sn,
        email=email,
        app_id="com.eaton.xstoragehome",
        name="Eaton xStorage Home",
        manufacturer="Eaton",
        user_type=user_type,
    )

    try:
        await api.connect()
        # Try to fetch the device serial to allow per-device unique_id
        serial = None
        try:
            device_resp = await api.get_device()
            device_data = (
                device_resp.get("result", {})
                if isinstance(device_resp, dict)
                else device_resp
            )
            serial = (
                device_data.get("inverterSerialNumber")
                if isinstance(device_data, dict)
                else None
            )
        except Exception as exc:  # best-effort; serial not strictly required
            _LOGGER.debug("Failed to retrieve device serial number: %s", exc)
        return serial
    except ValueError as err:
        _LOGGER.warning("Authentication failed: %s", err)
        raise ValueError("Invalid credentials") from err
    except (ConnectionError, OSError) as err:
        _LOGGER.error("Connection failed: %s", err)
        raise ConnectionError("Cannot connect to device") from err
    except Exception as err:
        error_msg = str(err)
        if "Cannot connect to host" in error_msg or "Connect call failed" in error_msg:
            _LOGGER.error("Connection failed: %s", err)
            raise ConnectionError("Cannot connect to device") from err
        _LOGGER.error("Unexpected error during connection: %s", err)
        raise ConnectionError("Cannot connect to device") from err


def _classify_auth_error(err: ValueError) -> str:
    """Map a ValueError from connection test to a translation error key."""
    error_message = str(err)
    if "Error during authentication: 10" in error_message:
        return "auth_error_locked"
    if "wrong credentials" in error_message.lower():
        return "err_wrong_credentials"
    if "invalid inverter" in error_message.lower():
        return "err_invalid_inverter_sn"
    if "non-JSON response" in error_message:
        return "auth_non_json_response"
    if "unexpected response" in error_message:
        return "auth_unexpected_response"
    return "invalid_auth"


def _build_user_schema(
    user_type: str = "customer",
    defaults: dict[str, Any] | None = None,
) -> vol.Schema:
    """Build the data schema for user/options/reauth forms."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_HOST, default=defaults.get(CONF_HOST, "")
            ): sel.TextSelector(),
            vol.Required(CONF_USER_TYPE, default=user_type): sel.SelectSelector(
                sel.SelectSelectorConfig(
                    options=[
                        sel.SelectOptionDict(value="customer", label="Customer"),
                        sel.SelectOptionDict(value="tech", label="Technician"),
                    ],
                    mode=sel.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")
            ): sel.TextSelector(),
            vol.Required(
                CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")
            ): sel.TextSelector(
                sel.TextSelectorConfig(type=sel.TextSelectorType.PASSWORD)
            ),
            vol.Optional(
                CONF_INVERTER_SN, default=defaults.get(CONF_INVERTER_SN, "")
            ): sel.TextSelector(),
            vol.Optional(
                CONF_HAS_PV, default=defaults.get(CONF_HAS_PV, False)
            ): sel.BooleanSelector(),
        }
    )


class EatonXStorageConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eaton xStorage Home."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> EatonXStorageOptionsFlow:
        """Create the options flow."""
        return EatonXStorageOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step (single-step flow with conditional validation)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            user_type = user_input[CONF_USER_TYPE]
            inverter_sn = user_input.get(CONF_INVERTER_SN, "")
            email = "anything@anything.com"  # Hardcoded per API requirements

            # Conditional validation: inverter_sn required only for technician accounts
            if user_type == "tech" and not inverter_sn:
                errors[CONF_INVERTER_SN] = "required_inverter_sn"
            else:
                try:
                    # Test connection and retrieve inverter serial if available
                    device_serial = await _async_test_connection(
                        self.hass,
                        host, username, password, inverter_sn, email, user_type,
                    )
                except ConnectionError:
                    errors["base"] = "cannot_connect"
                except ValueError as err:
                    errors["base"] = _classify_auth_error(err)
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected error during connection test")
                    errors["base"] = "unknown"
                else:
                    # Determine a per-device unique_id using inverter serial if present
                    unique_suffix = device_serial or inverter_sn or username
                    unique_id = f"{host}_{unique_suffix}" if unique_suffix else host
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    entry_data = dict(user_input)
                    entry_data["email"] = email
                    return self.async_create_entry(
                        title="Eaton xStorage Home", data=entry_data
                    )

        # Determine user_type for form defaults (prefer previously selected value)
        user_type = (
            user_input.get(CONF_USER_TYPE, "customer") if user_input else "customer"
        )

        schema = _build_user_schema(user_type=user_type)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth when credentials expire."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation step."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            host = user_input[CONF_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            user_type = user_input[CONF_USER_TYPE]
            inverter_sn = user_input.get(CONF_INVERTER_SN, "")
            email = "anything@anything.com"

            if user_type == "tech" and not inverter_sn:
                errors[CONF_INVERTER_SN] = "required_inverter_sn"
            else:
                try:
                    await _async_test_connection(
                        self.hass,
                        host, username, password, inverter_sn, email, user_type,
                    )
                except ConnectionError:
                    errors["base"] = "cannot_connect"
                except ValueError as err:
                    errors["base"] = _classify_auth_error(err)
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected error during reauth")
                    errors["base"] = "unknown"
                else:
                    entry_data = dict(user_input)
                    entry_data["email"] = email
                    return self.async_update_reload_and_abort(
                        reauth_entry, data=entry_data
                    )

        current_data = reauth_entry.data
        user_type = (
            user_input.get(CONF_USER_TYPE, current_data.get(CONF_USER_TYPE, "customer"))
            if user_input
            else current_data.get(CONF_USER_TYPE, "customer")
        )

        schema = _build_user_schema(user_type=user_type, defaults=dict(current_data))

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=schema, errors=errors
        )


class EatonXStorageOptionsFlow(OptionsFlow):
    """Handle options flow for Eaton xStorage Home."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow.

        NOTE: Home Assistant now exposes the active ConfigEntry on
        `self.config_entry` in OptionsFlow. We accept the `config_entry`
        argument for backwards compatibility with older HA versions, but we
        do not assign it to an attribute to avoid the deprecation warning
        about setting `config_entry` explicitly.
        """
        super().__init__()

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_type = user_input[CONF_USER_TYPE]
            inverter_sn = user_input.get(CONF_INVERTER_SN, "")

            # Conditional validation for technician inverter serial number
            if user_type == "tech" and not inverter_sn:
                errors[CONF_INVERTER_SN] = "required_inverter_sn"
            else:
                try:
                    await _async_test_connection(
                        self.hass,
                        user_input[CONF_HOST],
                        user_input[CONF_USERNAME],
                        user_input[CONF_PASSWORD],
                        inverter_sn,
                        "anything@anything.com",
                        user_type,
                    )
                except ConnectionError:
                    errors["base"] = "cannot_connect"
                except ValueError as err:
                    errors["base"] = _classify_auth_error(err)
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected error during connection test")
                    errors["base"] = "unknown"
                else:
                    entry_data = dict(user_input)
                    entry_data["email"] = "anything@anything.com"
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=entry_data
                    )
                    return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data
        user_type = (
            user_input.get(CONF_USER_TYPE, current_data.get(CONF_USER_TYPE, "customer"))
            if user_input
            else current_data.get(CONF_USER_TYPE, "customer")
        )

        schema = _build_user_schema(
            user_type=user_type, defaults=dict(current_data)
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
