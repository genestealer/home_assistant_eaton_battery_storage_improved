"""Test the Eaton Battery Storage config flow - simplified version."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.eaton_battery_storage.config_flow import (
    CONF_INVERTER_SN,
    EatonXStorageConfigFlow,
)
from custom_components.eaton_battery_storage.const import DOMAIN


@pytest.mark.asyncio
class TestConfigFlowSimple:
    """Test the config flow with simplified mocking."""

    async def test_test_connection_success(self) -> None:
        """Test successful connection test."""
        config_flow = EatonXStorageConfigFlow()
        config_flow.hass = Mock()

        with patch(
            "custom_components.eaton_battery_storage.api.EatonBatteryAPI"
        ) as mock_api:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_api.return_value = mock_instance

            # Should not raise an exception
            await config_flow._test_connection(
                "192.168.1.100", "test_user", "test_pass", "TEST123", "test@test.com"
            )

            mock_api.assert_called_once()
            mock_instance.connect.assert_called_once()

    async def test_test_connection_value_error(self) -> None:
        """Test connection with ValueError."""
        config_flow = EatonXStorageConfigFlow()
        config_flow.hass = Mock()

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

    async def test_test_connection_connection_error(self) -> None:
        """Test connection with ConnectionError."""
        config_flow = EatonXStorageConfigFlow()
        config_flow.hass = Mock()

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

    async def test_test_connection_generic_error(self) -> None:
        """Test connection with generic exception."""
        config_flow = EatonXStorageConfigFlow()
        config_flow.hass = Mock()

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


@pytest.mark.asyncio
class TestConfigFlowProperties:
    """Test config flow properties and constants."""

    def test_domain_constant(self) -> None:
        """Test that domain constant is correctly defined."""
        config_flow = EatonXStorageConfigFlow()
        assert hasattr(config_flow, "domain")
        # The domain should be set via the decorator
        assert DOMAIN == "eaton_battery_storage"

    def test_conf_inverter_sn_constant(self) -> None:
        """Test that inverter SN constant is correctly defined."""
        assert CONF_INVERTER_SN == "inverter_sn"
        assert isinstance(CONF_INVERTER_SN, str)

    async def test_config_flow_initialization(self) -> None:
        """Test config flow can be initialized."""
        config_flow = EatonXStorageConfigFlow()
        assert config_flow is not None

    async def test_api_initialization_parameters(self) -> None:
        """Test that API is initialized with correct parameters."""
        config_flow = EatonXStorageConfigFlow()
        config_flow.hass = Mock()

        with patch(
            "custom_components.eaton_battery_storage.api.EatonBatteryAPI"
        ) as mock_api:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_api.return_value = mock_instance

            await config_flow._test_connection(
                "192.168.1.100", "test_user", "test_pass", "TEST123", "test@test.com"
            )

            # Verify API was called with correct parameters
            mock_api.assert_called_once_with(
                hass=config_flow.hass,
                host="192.168.1.100",
                username="test_user",
                password="test_pass",
                inverter_sn="TEST123",
                email="test@test.com",
                app_id="com.eaton.xstoragehome",
                name="Eaton xStorage Home",
                manufacturer="Eaton",
            )