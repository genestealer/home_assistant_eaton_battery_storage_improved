"""Test config flow for Eaton Battery Storage integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientError

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.eaton_battery_storage.config_flow import (
    EatonXStorageConfigFlow,
    EatonXStorageOptionsFlow,
)
from custom_components.eaton_battery_storage.const import DOMAIN


class TestEatonXStorageConfigFlow:
    """Test the config flow."""

    async def test_user_form_shown(self, hass: HomeAssistant):
        """Test that the user form is shown on first step."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    async def test_user_form_valid_input(self, hass: HomeAssistant, mock_api):
        """Test successful config flow with valid input."""
        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api_class.return_value = mock_api
            
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.100",
                    "username": "admin",
                    "password": "password",
                    "inverter_sn": "test_serial",
                    "has_pv": True,
                },
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["title"] == "Eaton xStorage Home (192.168.1.100)"
            assert result["data"] == {
                "host": "192.168.1.100",
                "username": "admin",
                "password": "password",
                "inverter_sn": "test_serial",
                "email": "anything@anything.com",
                "has_pv": True,
            }

    async def test_user_form_cannot_connect(self, hass: HomeAssistant):
        """Test config flow when connection fails."""
        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = ConnectionError("Cannot connect to device")
            mock_api_class.return_value = mock_api

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.100",
                    "username": "admin",
                    "password": "password",
                    "inverter_sn": "test_serial",
                    "has_pv": True,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

    async def test_user_form_invalid_auth(self, hass: HomeAssistant):
        """Test config flow when authentication fails."""
        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = ValueError("Invalid credentials")
            mock_api_class.return_value = mock_api

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.100",
                    "username": "admin",
                    "password": "wrong_password",
                    "inverter_sn": "test_serial",
                    "has_pv": True,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "invalid_auth"}

    async def test_user_form_unknown_error(self, hass: HomeAssistant):
        """Test config flow when an unknown error occurs."""
        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = Exception("Unexpected error")
            mock_api_class.return_value = mock_api

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.100",
                    "username": "admin",
                    "password": "password",
                    "inverter_sn": "test_serial",
                    "has_pv": True,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "unknown"}

    async def test_already_configured(self, hass: HomeAssistant, mock_config_entry):
        """Test that configuring an already configured host shows error."""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "192.168.1.100",
                "username": "admin",
                "password": "password",
                "inverter_sn": "test_serial",
                "has_pv": True,
            },
        )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"


class TestEatonXStorageOptionsFlow:
    """Test the options flow."""

    async def test_options_form_shown(self, hass: HomeAssistant, mock_config_entry):
        """Test that the options form is shown."""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_form_valid_input(self, hass: HomeAssistant, mock_config_entry, mock_api):
        """Test successful options flow with valid input."""
        mock_config_entry.add_to_hass(hass)

        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api_class.return_value = mock_api
            
            result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.101",
                    "username": "new_admin",
                    "password": "new_password",
                    "inverter_sn": "new_serial",
                    "has_pv": False,
                },
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["data"] == {
                "host": "192.168.1.101",
                "username": "new_admin",
                "password": "new_password",
                "inverter_sn": "new_serial",
                "email": "anything@anything.com",
                "has_pv": False,
            }

    async def test_options_form_connection_error(self, hass: HomeAssistant, mock_config_entry):
        """Test options flow when connection fails."""
        mock_config_entry.add_to_hass(hass)

        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = ConnectionError("Cannot connect to device")
            mock_api_class.return_value = mock_api

            result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.101",
                    "username": "admin",
                    "password": "password",
                    "inverter_sn": "test_serial",
                    "has_pv": True,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

    async def test_options_form_auth_error(self, hass: HomeAssistant, mock_config_entry):
        """Test options flow when authentication fails."""
        mock_config_entry.add_to_hass(hass)

        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = ValueError("Invalid credentials")
            mock_api_class.return_value = mock_api

            result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.100",
                    "username": "admin",
                    "password": "wrong_password",
                    "inverter_sn": "test_serial",
                    "has_pv": True,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "invalid_auth"}

    async def test_test_connection_method(self, hass: HomeAssistant, mock_config_entry):
        """Test the _test_connection method directly."""
        options_flow = EatonXStorageOptionsFlow(mock_config_entry)
        options_flow.hass = hass

        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.return_value = None
            mock_api_class.return_value = mock_api

            # Should not raise any exception
            await options_flow._test_connection(
                "192.168.1.100", "admin", "password", "test_serial", "test@example.com"
            )

            mock_api.connect.assert_called_once()

    async def test_test_connection_method_errors(self, hass: HomeAssistant, mock_config_entry):
        """Test the _test_connection method with various errors."""
        options_flow = EatonXStorageOptionsFlow(mock_config_entry)
        options_flow.hass = hass

        # Test ValueError (auth error)
        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = ValueError("Invalid credentials")
            mock_api_class.return_value = mock_api

            with pytest.raises(ValueError, match="Invalid credentials"):
                await options_flow._test_connection(
                    "192.168.1.100", "admin", "wrong_password", "test_serial", "test@example.com"
                )

        # Test ConnectionError
        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = ConnectionError("Cannot connect to device")
            mock_api_class.return_value = mock_api

            with pytest.raises(ConnectionError, match="Cannot connect to device"):
                await options_flow._test_connection(
                    "192.168.1.100", "admin", "password", "test_serial", "test@example.com"
                )

        # Test general Exception
        with patch("custom_components.eaton_battery_storage.config_flow.EatonBatteryAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.connect.side_effect = Exception("Unexpected error")
            mock_api_class.return_value = mock_api

            with pytest.raises(Exception, match="Unexpected error"):
                await options_flow._test_connection(
                    "192.168.1.100", "admin", "password", "test_serial", "test@example.com"
                )