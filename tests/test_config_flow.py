"""Test the Eaton Battery Storage config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.eaton_battery_storage.config_flow import (
    CONF_INVERTER_SN,
    EatonXStorageConfigFlow,
)
from custom_components.eaton_battery_storage.const import DOMAIN


@pytest.mark.asyncio
class TestConfigFlow:
    """Test the config flow."""

    async def test_form(self, hass: HomeAssistant) -> None:
        """Test we get the form."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] is None

    async def test_form_invalid_auth(self, hass: HomeAssistant) -> None:
        """Test we handle invalid auth."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.eaton_battery_storage.config_flow.EatonXStorageConfigFlow._test_connection",
            side_effect=ValueError("Invalid credentials"),
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_USERNAME: "test_user",
                    CONF_PASSWORD: "wrong_password",
                    CONF_INVERTER_SN: "TEST123456",
                },
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "invalid_auth"}

    async def test_form_cannot_connect(self, hass: HomeAssistant) -> None:
        """Test we handle cannot connect error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.eaton_battery_storage.config_flow.EatonXStorageConfigFlow._test_connection",
            side_effect=ConnectionError("Cannot connect to device"),
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_USERNAME: "test_user",
                    CONF_PASSWORD: "test_password",
                    CONF_INVERTER_SN: "TEST123456",
                },
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}

    async def test_form_success(self, hass: HomeAssistant) -> None:
        """Test successful config flow."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.eaton_battery_storage.config_flow.EatonXStorageConfigFlow._test_connection",
            return_value=None,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_USERNAME: "test_user",
                    CONF_PASSWORD: "test_password",
                    CONF_INVERTER_SN: "TEST123456",
                },
            )

        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["title"] == "192.168.1.100"
        assert result2["data"] == {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
            CONF_INVERTER_SN: "TEST123456",
            "email": "anything@anything.com",
        }

    async def test_form_already_configured(self, hass: HomeAssistant) -> None:
        """Test we abort if already configured."""
        # Create a config entry
        entry = config_entries.ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="Eaton xStorage Home",
            data={
                CONF_HOST: "192.168.1.100",
                CONF_USERNAME: "test_user",
                CONF_PASSWORD: "test_password",
                CONF_INVERTER_SN: "TEST123456",
                "email": "anything@anything.com",
            },
            options={},
            entry_id="test_entry_id",
            unique_id="192.168.1.100_TEST123456",
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.eaton_battery_storage.config_flow.EatonXStorageConfigFlow._test_connection",
            return_value=None,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_USERNAME: "test_user",
                    CONF_PASSWORD: "test_password",
                    CONF_INVERTER_SN: "TEST123456",
                },
            )

        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "already_configured"

    async def test_error_auth_10(self, hass: HomeAssistant) -> None:
        """Test handling of auth error 10."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.eaton_battery_storage.config_flow.EatonXStorageConfigFlow._test_connection",
            side_effect=ValueError("Error during authentication: 10"),
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_USERNAME: "test_user",
                    CONF_PASSWORD: "test_password",
                    CONF_INVERTER_SN: "TEST123456",
                },
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "Error during authentication: 10"}

    async def test_error_wrong_credentials(self, hass: HomeAssistant) -> None:
        """Test handling of wrong credentials error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.eaton_battery_storage.config_flow.EatonXStorageConfigFlow._test_connection",
            side_effect=ValueError("wrong credentials detected"),
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_USERNAME: "test_user",
                    CONF_PASSWORD: "test_password",
                    CONF_INVERTER_SN: "TEST123456",
                },
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "err_wrong_credentials"}

    async def test_error_invalid_inverter(self, hass: HomeAssistant) -> None:
        """Test handling of invalid inverter error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.eaton_battery_storage.config_flow.EatonXStorageConfigFlow._test_connection",
            side_effect=ValueError("invalid inverter serial number"),
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_USERNAME: "test_user",
                    CONF_PASSWORD: "test_password",
                    CONF_INVERTER_SN: "INVALID123",
                },
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "err_invalid_inverter_sn"}


@pytest.mark.asyncio
class TestOptionsFlow:
    """Test the options flow."""

    async def test_options_flow(self, hass: HomeAssistant, mock_config_entry) -> None:
        """Test config flow options."""
        mock_config_entry.add_to_hass(hass)

        with patch(
            "custom_components.eaton_battery_storage.async_setup_entry",
            return_value=True,
        ):
            await hass.config_entries.async_setup(mock_config_entry.entry_id)

        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

        with patch(
            "custom_components.eaton_battery_storage.config_flow.EatonXStorageOptionsFlow._test_connection",
            return_value=None,
        ):
            result2 = await hass.config_entries.options.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "192.168.1.101",
                    CONF_USERNAME: "updated_user",
                    CONF_PASSWORD: "updated_password",
                    CONF_INVERTER_SN: "UPDATED123",
                    "has_pv": True,
                },
            )

        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["data"] == {
            CONF_HOST: "192.168.1.101",
            CONF_USERNAME: "updated_user",
            CONF_PASSWORD: "updated_password",
            CONF_INVERTER_SN: "UPDATED123",
            "email": "anything@anything.com",
            "has_pv": True,
        }

    async def test_options_flow_cannot_connect(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test options flow with connection error."""
        mock_config_entry.add_to_hass(hass)

        with patch(
            "custom_components.eaton_battery_storage.async_setup_entry",
            return_value=True,
        ):
            await hass.config_entries.async_setup(mock_config_entry.entry_id)

        result = await hass.config_entries.options.async_init(
            mock_config_entry.entry_id
        )

        with patch(
            "custom_components.eaton_battery_storage.config_flow.EatonXStorageOptionsFlow._test_connection",
            side_effect=ConnectionError("Cannot connect to device"),
        ):
            result2 = await hass.config_entries.options.async_configure(
                result["flow_id"],
                user_input={
                    CONF_HOST: "192.168.1.101",
                    CONF_USERNAME: "updated_user",
                    CONF_PASSWORD: "updated_password",
                    CONF_INVERTER_SN: "UPDATED123",
                    "has_pv": True,
                },
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
class TestConnectionTest:
    """Test the connection test method."""

    async def test_connection_success(self, hass: HomeAssistant) -> None:
        """Test successful connection."""
        config_flow = EatonXStorageConfigFlow()
        config_flow.hass = hass

        with patch(
            "custom_components.eaton_battery_storage.api.EatonBatteryAPI"
        ) as mock_api:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_api.return_value = mock_instance

            await config_flow._test_connection(
                "192.168.1.100", "test_user", "test_pass", "TEST123", "test@test.com"
            )

            mock_api.assert_called_once()
            mock_instance.connect.assert_called_once()

    async def test_connection_value_error(self, hass: HomeAssistant) -> None:
        """Test connection with ValueError."""
        config_flow = EatonXStorageConfigFlow()
        config_flow.hass = hass

        with patch(
            "custom_components.eaton_battery_storage.api.EatonBatteryAPI"
        ) as mock_api:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock(side_effect=ValueError("Auth failed"))
            mock_api.return_value = mock_instance

            with pytest.raises(ValueError, match="Invalid credentials"):
                await config_flow._test_connection(
                    "192.168.1.100",
                    "test_user",
                    "test_pass",
                    "TEST123",
                    "test@test.com",
                )

    async def test_connection_connection_error(self, hass: HomeAssistant) -> None:
        """Test connection with ConnectionError."""
        config_flow = EatonXStorageConfigFlow()
        config_flow.hass = hass

        with patch(
            "custom_components.eaton_battery_storage.api.EatonBatteryAPI"
        ) as mock_api:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock(side_effect=ConnectionError("No connect"))
            mock_api.return_value = mock_instance

            with pytest.raises(ConnectionError, match="Cannot connect to device"):
                await config_flow._test_connection(
                    "192.168.1.100",
                    "test_user",
                    "test_pass",
                    "TEST123",
                    "test@test.com",
                )

    async def test_connection_generic_error(self, hass: HomeAssistant) -> None:
        """Test connection with generic exception."""
        config_flow = EatonXStorageConfigFlow()
        config_flow.hass = hass

        with patch(
            "custom_components.eaton_battery_storage.api.EatonBatteryAPI"
        ) as mock_api:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock(side_effect=Exception("Generic error"))
            mock_api.return_value = mock_instance

            with pytest.raises(ConnectionError, match="Cannot connect to device"):
                await config_flow._test_connection(
                    "192.168.1.100",
                    "test_user",
                    "test_pass",
                    "TEST123",
                    "test@test.com",
                )