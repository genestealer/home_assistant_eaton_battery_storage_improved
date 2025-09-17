"""Test the Eaton Battery Storage API client."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from custom_components.eaton_battery_storage.api import EatonBatteryAPI


@pytest.mark.asyncio
class TestEatonBatteryAPI:
    """Test the EatonBatteryAPI class."""

    @pytest.fixture
    def mock_hass(self):
        """Return a mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.data = {}
        return hass

    @pytest.fixture
    def api_instance(self, mock_hass, mock_storage):
        """Return an API instance for testing."""
        return EatonBatteryAPI(
            hass=mock_hass,
            host="192.168.1.100",
            username="test_user",
            password="test_password",
            inverter_sn="TEST123456",
            email="test@example.com",
            app_id="com.eaton.xstoragehome",
            name="Eaton xStorage Home",
            manufacturer="Eaton",
        )

    async def test_init(self, api_instance):
        """Test API initialization."""
        assert api_instance.host == "192.168.1.100"
        assert api_instance.username == "test_user"
        assert api_instance.password == "test_password"
        assert api_instance.inverter_sn == "TEST123456"
        assert api_instance.email == "test@example.com"
        assert api_instance.app_id == "com.eaton.xstoragehome"
        assert api_instance.name == "Eaton xStorage Home"
        assert api_instance.manufacturer == "Eaton"
        assert api_instance.access_token is None
        assert api_instance.refresh_token is None

    async def test_connect_success(self, api_instance):
        """Test successful connection."""
        mock_response_data = {
            "successful": True,
            "result": {
                "token": "test_access_token",
                "refreshToken": "test_refresh_token",
                "expiresIn": 3600,
            },
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            await api_instance.connect()

            assert api_instance.access_token == "test_access_token"
            assert api_instance.refresh_token == "test_refresh_token"

    async def test_connect_auth_failure(self, api_instance):
        """Test connection with authentication failure."""
        mock_response_data = {
            "successful": False,
            "error": "Authentication failed",
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ValueError, match="Authentication failed"):
                await api_instance.connect()

    async def test_connect_non_json_response(self, api_instance):
        """Test connection with non-JSON response."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content_type = "text/html"
            mock_response.text = AsyncMock(return_value="<html>Error</html>")
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ValueError, match="Authentication failed: non-JSON response"):
                await api_instance.connect()

    async def test_connect_wrong_credentials(self, api_instance):
        """Test connection with wrong credentials."""
        mock_response_data = {
            "successful": False,
            "error": "wrong credentials",
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ValueError, match="Authentication failed with wrong credentials"):
                await api_instance.connect()

    async def test_connect_invalid_inverter(self, api_instance):
        """Test connection with invalid inverter SN."""
        mock_response_data = {
            "successful": False,
            "error": "Invalid inverter serial number",
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ValueError, match="Authentication failed with invalid inverter"):
                await api_instance.connect()

    async def test_store_token(self, api_instance, mock_storage):
        """Test token storage."""
        api_instance.access_token = "test_token"
        api_instance.refresh_token = "test_refresh"
        api_instance.token_expires_at = 1234567890

        await api_instance.store_token()

        mock_storage.async_save.assert_called_once_with({
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": 1234567890,
        })

    async def test_load_token(self, api_instance, mock_storage):
        """Test token loading."""
        stored_data = {
            "access_token": "stored_token",
            "refresh_token": "stored_refresh",
            "expires_at": 1234567890,
        }
        mock_storage.async_load.return_value = stored_data

        await api_instance.load_token()

        assert api_instance.access_token == "stored_token"
        assert api_instance.refresh_token == "stored_refresh"
        assert api_instance.token_expires_at == 1234567890

    async def test_load_token_no_data(self, api_instance, mock_storage):
        """Test token loading with no stored data."""
        mock_storage.async_load.return_value = None

        await api_instance.load_token()

        assert api_instance.access_token is None
        assert api_instance.refresh_token is None
        assert api_instance.token_expires_at is None

    async def test_refresh_token_success(self, api_instance):
        """Test successful token refresh."""
        api_instance.refresh_token = "existing_refresh_token"
        
        mock_response_data = {
            "successful": True,
            "result": {
                "token": "new_access_token",
                "refreshToken": "new_refresh_token",
                "expiresIn": 3600,
            },
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            await api_instance.refresh_token()

            assert api_instance.access_token == "new_access_token"
            assert api_instance.refresh_token == "new_refresh_token"

    async def test_refresh_token_failure(self, api_instance):
        """Test token refresh failure."""
        api_instance.refresh_token = "invalid_refresh_token"

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value={"successful": False})
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ValueError, match="Token refresh failed"):
                await api_instance.refresh_token()

    async def test_make_request_success(self, api_instance):
        """Test successful API request."""
        api_instance.access_token = "valid_token"
        api_instance.token_expires_at = 9999999999  # Far future
        
        mock_response_data = {"successful": True, "result": {"data": "test"}}

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.return_value = mock_response

            result = await api_instance.make_request("GET", "/api/test")

            assert result == mock_response_data

    async def test_make_request_token_refresh(self, api_instance):
        """Test API request with token refresh."""
        api_instance.access_token = "expired_token"
        api_instance.refresh_token = "valid_refresh"
        api_instance.token_expires_at = 9999999999  # Far future
        
        # First call returns 401, second call succeeds
        mock_response_401 = AsyncMock()
        mock_response_401.status = 401
        
        mock_response_200 = AsyncMock()
        mock_response_200.status = 200
        mock_response_200.content_type = "application/json"
        mock_response_200.json = AsyncMock(return_value={"successful": True})

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.side_effect = [
                mock_response_401,
                mock_response_200,
            ]
            
            with patch.object(api_instance, "refresh_token", new_callable=AsyncMock) as mock_refresh:
                mock_refresh.return_value = None
                api_instance.access_token = "new_token"  # Simulate refresh

                result = await api_instance.make_request("GET", "/api/test")

                assert result == {"successful": True}
                mock_refresh.assert_called_once()

    async def test_make_request_network_error(self, api_instance):
        """Test API request with network error."""
        api_instance.access_token = "valid_token"
        api_instance.token_expires_at = 9999999999  # Far future

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.request.side_effect = aiohttp.ClientError("Network error")

            result = await api_instance.make_request("GET", "/api/test")

            assert result["successful"] is False
            assert "Network error" in result["error"]

    async def test_get_status(self, api_instance):
        """Test get_status method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"status": "ok"}}

            result = await api_instance.get_status()

            mock_request.assert_called_once_with("GET", "/api/device/status")
            assert result == {"successful": True, "result": {"status": "ok"}}

    async def test_get_device(self, api_instance):
        """Test get_device method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"device": "info"}}

            result = await api_instance.get_device()

            mock_request.assert_called_once_with("GET", "/api/device")
            assert result == {"successful": True, "result": {"device": "info"}}

    async def test_get_config_state(self, api_instance):
        """Test get_config_state method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"config": "state"}}

            result = await api_instance.get_config_state()

            mock_request.assert_called_once_with("GET", "/api/config/state")
            assert result == {"successful": True, "result": {"config": "state"}}

    async def test_get_settings(self, api_instance):
        """Test get_settings method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"settings": "data"}}

            result = await api_instance.get_settings()

            mock_request.assert_called_once_with("GET", "/api/settings")
            assert result == {"successful": True, "result": {"settings": "data"}}

    async def test_update_settings(self, api_instance):
        """Test update_settings method."""
        settings_data = {"setting1": "value1", "setting2": "value2"}
        
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True}

            result = await api_instance.update_settings(settings_data)

            mock_request.assert_called_once_with("PUT", "/api/settings", json=settings_data)
            assert result == {"successful": True}

    async def test_get_metrics(self, api_instance):
        """Test get_metrics method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"metrics": "data"}}

            result = await api_instance.get_metrics()

            mock_request.assert_called_once_with("GET", "/api/metrics")
            assert result == {"successful": True, "result": {"metrics": "data"}}

    async def test_get_metrics_daily(self, api_instance):
        """Test get_metrics_daily method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"daily": "metrics"}}

            result = await api_instance.get_metrics_daily()

            mock_request.assert_called_once_with("GET", "/api/metrics/daily")
            assert result == {"successful": True, "result": {"daily": "metrics"}}

    async def test_get_schedule(self, api_instance):
        """Test get_schedule method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"schedule": "data"}}

            result = await api_instance.get_schedule()

            mock_request.assert_called_once_with("GET", "/api/schedule")
            assert result == {"successful": True, "result": {"schedule": "data"}}

    async def test_get_technical_status(self, api_instance):
        """Test get_technical_status method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"technical": "status"}}

            result = await api_instance.get_technical_status()

            mock_request.assert_called_once_with("GET", "/api/technicalstatus")
            assert result == {"successful": True, "result": {"technical": "status"}}

    async def test_get_maintenance_diagnostics(self, api_instance):
        """Test get_maintenance_diagnostics method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"diagnostics": "data"}}

            result = await api_instance.get_maintenance_diagnostics()

            mock_request.assert_called_once_with("GET", "/api/maintenance/diagnostics")
            assert result == {"successful": True, "result": {"diagnostics": "data"}}

    async def test_get_notifications(self, api_instance):
        """Test get_notifications method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"notifications": "data"}}

            result = await api_instance.get_notifications()

            mock_request.assert_called_once_with("GET", "/api/notifications")
            assert result == {"successful": True, "result": {"notifications": "data"}}

    async def test_get_unread_notifications_count(self, api_instance):
        """Test get_unread_notifications_count method."""
        with patch.object(api_instance, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"successful": True, "result": {"total": 5}}

            result = await api_instance.get_unread_notifications_count()

            mock_request.assert_called_once_with("GET", "/api/notifications/unread")
            assert result == {"successful": True, "result": {"total": 5}}