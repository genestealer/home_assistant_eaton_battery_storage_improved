"""Test the Eaton Battery Storage API client - simplified version."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.eaton_battery_storage.api import EatonBatteryAPI


@pytest.mark.asyncio
class TestEatonBatteryAPIBasic:
    """Test the EatonBatteryAPI class basic functionality."""

    def test_api_initialization(self):
        """Test API initialization without storage dependency."""
        with patch("homeassistant.helpers.storage.Store"):
            api = EatonBatteryAPI(
                hass=Mock(),
                host="192.168.1.100",
                username="test_user",
                password="test_password",
                inverter_sn="TEST123456",
                email="test@example.com",
                app_id="com.eaton.xstoragehome",
                name="Eaton xStorage Home",
                manufacturer="Eaton",
            )

            assert api.host == "192.168.1.100"
            assert api.username == "test_user"
            assert api.password == "test_password"
            assert api.inverter_sn == "TEST123456"
            assert api.email == "test@example.com"
            assert api.app_id == "com.eaton.xstoragehome"
            assert api.name == "Eaton xStorage Home"
            assert api.manufacturer == "Eaton"
            assert api.access_token is None
            assert api.refresh_token is None

    async def test_api_connect_success(self):
        """Test successful API connection."""
        mock_response_data = {
            "successful": True,
            "result": {
                "token": "test_access_token",
                "refreshToken": "test_refresh_token",
                "expiresIn": 3600,
            },
        }

        with patch("homeassistant.helpers.storage.Store"), patch(
            "aiohttp.ClientSession"
        ) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = (
                mock_response
            )

            api = EatonBatteryAPI(
                hass=Mock(),
                host="192.168.1.100",
                username="test_user",
                password="test_password",
                inverter_sn="TEST123456",
                email="test@example.com",
                app_id="com.eaton.xstoragehome",
                name="Eaton xStorage Home",
                manufacturer="Eaton",
            )

            await api.connect()

            assert api.access_token == "test_access_token"
            assert api.refresh_token == "test_refresh_token"

    async def test_api_connect_auth_failure(self):
        """Test API connection with authentication failure."""
        mock_response_data = {
            "successful": False,
            "error": "Authentication failed",
        }

        with patch("homeassistant.helpers.storage.Store"), patch(
            "aiohttp.ClientSession"
        ) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = (
                mock_response
            )

            api = EatonBatteryAPI(
                hass=Mock(),
                host="192.168.1.100",
                username="test_user",
                password="wrong_password",
                inverter_sn="TEST123456",
                email="test@example.com",
                app_id="com.eaton.xstoragehome",
                name="Eaton xStorage Home",
                manufacturer="Eaton",
            )

            with pytest.raises(ValueError, match="Authentication failed"):
                await api.connect()

    async def test_api_connect_wrong_credentials(self):
        """Test API connection with wrong credentials."""
        mock_response_data = {
            "successful": False,
            "error": "wrong credentials",
        }

        with patch("homeassistant.helpers.storage.Store"), patch(
            "aiohttp.ClientSession"
        ) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = (
                mock_response
            )

            api = EatonBatteryAPI(
                hass=Mock(),
                host="192.168.1.100",
                username="test_user",
                password="wrong_password",
                inverter_sn="TEST123456",
                email="test@example.com",
                app_id="com.eaton.xstoragehome",
                name="Eaton xStorage Home",
                manufacturer="Eaton",
            )

            with pytest.raises(
                ValueError, match="Authentication failed with wrong credentials"
            ):
                await api.connect()

    async def test_api_connect_invalid_inverter(self):
        """Test API connection with invalid inverter SN."""
        mock_response_data = {
            "successful": False,
            "error": "Invalid inverter serial number",
        }

        with patch("homeassistant.helpers.storage.Store"), patch(
            "aiohttp.ClientSession"
        ) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = (
                mock_response
            )

            api = EatonBatteryAPI(
                hass=Mock(),
                host="192.168.1.100",
                username="test_user",
                password="test_password",
                inverter_sn="INVALID123",
                email="test@example.com",
                app_id="com.eaton.xstoragehome",
                name="Eaton xStorage Home",
                manufacturer="Eaton",
            )

            with pytest.raises(
                ValueError, match="Authentication failed with invalid inverter"
            ):
                await api.connect()

    async def test_api_connect_non_json_response(self):
        """Test API connection with non-JSON response."""
        with patch("homeassistant.helpers.storage.Store"), patch(
            "aiohttp.ClientSession"
        ) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content_type = "text/html"
            mock_response.text = AsyncMock(return_value="<html>Error</html>")

            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = (
                mock_response
            )

            api = EatonBatteryAPI(
                hass=Mock(),
                host="192.168.1.100",
                username="test_user",
                password="test_password",
                inverter_sn="TEST123456",
                email="test@example.com",
                app_id="com.eaton.xstoragehome",
                name="Eaton xStorage Home",
                manufacturer="Eaton",
            )

            with pytest.raises(
                ValueError, match="Authentication failed: non-JSON response"
            ):
                await api.connect()


@pytest.mark.asyncio
class TestEatonBatteryAPIEndpoints:
    """Test API endpoint methods."""

    @pytest.fixture
    def api_instance(self):
        """Return an API instance for testing."""
        with patch("homeassistant.helpers.storage.Store"):
            api = EatonBatteryAPI(
                hass=Mock(),
                host="192.168.1.100",
                username="test_user",
                password="test_password",
                inverter_sn="TEST123456",
                email="test@example.com",
                app_id="com.eaton.xstoragehome",
                name="Eaton xStorage Home",
                manufacturer="Eaton",
            )
            return api

    async def test_get_status_endpoint(self, api_instance):
        """Test get_status method calls correct endpoint."""
        with patch.object(
            api_instance, "make_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"status": "ok"}}

            result = await api_instance.get_status()

            mock_request.assert_called_once_with("GET", "/api/device/status")
            assert result == {"successful": True, "result": {"status": "ok"}}

    async def test_get_device_endpoint(self, api_instance):
        """Test get_device method calls correct endpoint."""
        with patch.object(
            api_instance, "make_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {
                "successful": True,
                "result": {"device": "info"},
            }

            result = await api_instance.get_device()

            mock_request.assert_called_once_with("GET", "/api/device")
            assert result == {"successful": True, "result": {"device": "info"}}

    async def test_get_settings_endpoint(self, api_instance):
        """Test get_settings method calls correct endpoint."""
        with patch.object(
            api_instance, "make_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {
                "successful": True,
                "result": {"settings": "data"},
            }

            result = await api_instance.get_settings()

            mock_request.assert_called_once_with("GET", "/api/settings")
            assert result == {"successful": True, "result": {"settings": "data"}}

    async def test_update_settings_endpoint(self, api_instance):
        """Test update_settings method calls correct endpoint."""
        settings_data = {"setting1": "value1", "setting2": "value2"}

        with patch.object(
            api_instance, "make_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"successful": True}

            result = await api_instance.update_settings(settings_data)

            mock_request.assert_called_once_with(
                "PUT", "/api/settings", json=settings_data
            )
            assert result == {"successful": True}

    async def test_get_technical_status_endpoint(self, api_instance):
        """Test get_technical_status method calls correct endpoint."""
        with patch.object(
            api_instance, "make_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {
                "successful": True,
                "result": {"technical": "status"},
            }

            result = await api_instance.get_technical_status()

            mock_request.assert_called_once_with("GET", "/api/technicalstatus")
            assert result == {"successful": True, "result": {"technical": "status"}}

    async def test_get_notifications_endpoint(self, api_instance):
        """Test get_notifications method calls correct endpoint."""
        with patch.object(
            api_instance, "make_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {
                "successful": True,
                "result": {"notifications": "data"},
            }

            result = await api_instance.get_notifications()

            mock_request.assert_called_once_with("GET", "/api/notifications")
            assert result == {"successful": True, "result": {"notifications": "data"}}
