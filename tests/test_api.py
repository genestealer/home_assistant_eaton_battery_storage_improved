"""Test API client for Eaton Battery Storage integration."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from homeassistant.core import HomeAssistant

from custom_components.eaton_battery_storage.api import EatonBatteryAPI


class TestEatonBatteryAPI:
    """Test the EatonBatteryAPI class."""

    @pytest.fixture
    def api_client(self, hass: HomeAssistant):
        """Create an API client instance for testing."""
        return EatonBatteryAPI(
            hass=hass,
            host="192.168.1.100",
            username="admin",
            password="password",
            inverter_sn="test_serial",
            email="test@example.com",
            app_id="com.eaton.xstoragehome",
            name="Eaton xStorage Home",
            manufacturer="Eaton",
        )

    async def test_init(self, api_client):
        """Test API client initialization."""
        assert api_client.host == "192.168.1.100"
        assert api_client.username == "admin"
        assert api_client.password == "password"
        assert api_client.inverter_sn == "test_serial"
        assert api_client.email == "test@example.com"
        assert api_client.access_token is None
        assert api_client.token_expiration is None

    async def test_connect_success(self, api_client, mock_successful_auth_response):
        """Test successful connection and authentication."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content_type = "application/json"
            mock_response.json.return_value = mock_successful_auth_response
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            with patch.object(api_client, "store_token", new_callable=AsyncMock) as mock_store:
                await api_client.connect()

                assert api_client.access_token == "mock_access_token"
                assert api_client.token_expiration is not None
                assert api_client.token_expiration > datetime.utcnow()
                mock_store.assert_called_once()

    async def test_connect_auth_failure(self, api_client, mock_failed_auth_response):
        """Test connection failure due to authentication error."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.content_type = "application/json"
            mock_response.json.return_value = mock_failed_auth_response
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ValueError, match="Invalid credentials"):
                await api_client.connect()

    async def test_connect_non_json_response(self, api_client):
        """Test connection with non-JSON response."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.content_type = "text/html"
            mock_response.text.return_value = "<html>Server Error</html>"
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ValueError, match="Authentication failed: non-JSON response"):
                await api_client.connect()

    async def test_connect_network_error(self, api_client):
        """Test connection failure due to network error."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.post.side_effect = aiohttp.ClientError("Network error")

            with pytest.raises(ConnectionError, match="Cannot connect to device"):
                await api_client.connect()

    async def test_ensure_token_valid_refresh_needed(self, api_client):
        """Test token refresh when token is expired."""
        # Set expired token
        api_client.access_token = "old_token"
        api_client.token_expiration = datetime.utcnow() - timedelta(minutes=5)

        with patch.object(api_client, "refresh_token", new_callable=AsyncMock) as mock_refresh:
            await api_client.ensure_token_valid()
            mock_refresh.assert_called_once()

    async def test_ensure_token_valid_no_refresh_needed(self, api_client):
        """Test that valid token doesn't trigger refresh."""
        # Set valid token
        api_client.access_token = "valid_token"
        api_client.token_expiration = datetime.utcnow() + timedelta(minutes=30)

        with patch.object(api_client, "refresh_token", new_callable=AsyncMock) as mock_refresh:
            await api_client.ensure_token_valid()
            mock_refresh.assert_not_called()

    async def test_make_request_success(self, api_client, mock_device_status_response):
        """Test successful API request."""
        api_client.access_token = "valid_token"
        api_client.token_expiration = datetime.utcnow() + timedelta(minutes=30)

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content_type = "application/json"
            mock_response.json.return_value = mock_device_status_response
            
            mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.return_value = mock_response

            result = await api_client.make_request("GET", "/api/device/status")

            assert result == mock_device_status_response
            mock_session.return_value.__aenter__.return_value.request.assert_called_once()

    async def test_make_request_token_refresh(self, api_client, mock_device_status_response, mock_successful_auth_response):
        """Test API request with token refresh on 401."""
        api_client.access_token = "expired_token"
        api_client.token_expiration = datetime.utcnow() + timedelta(minutes=30)

        with patch("aiohttp.ClientSession") as mock_session:
            # First request returns 401, second succeeds
            mock_401_response = AsyncMock()
            mock_401_response.status = 401
            
            mock_success_response = AsyncMock()
            mock_success_response.status = 200
            mock_success_response.content_type = "application/json"
            mock_success_response.json.return_value = mock_device_status_response
            
            mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.side_effect = [
                mock_401_response,
                mock_success_response
            ]

            with patch.object(api_client, "refresh_token", new_callable=AsyncMock) as mock_refresh:
                result = await api_client.make_request("GET", "/api/device/status")

                assert result == mock_device_status_response
                mock_refresh.assert_called_once()
                assert mock_session.return_value.__aenter__.return_value.request.call_count == 2

    async def test_make_request_non_json_response(self, api_client):
        """Test API request with non-JSON response."""
        api_client.access_token = "valid_token"
        api_client.token_expiration = datetime.utcnow() + timedelta(minutes=30)

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.content_type = "text/html"
            mock_response.text.return_value = "<html>Server Error</html>"
            
            mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.return_value = mock_response

            result = await api_client.make_request("GET", "/api/device/status")

            assert result["successful"] is False
            assert result["error"] == "<html>Server Error</html>"
            assert result["status"] == 500

    async def test_make_request_network_error(self, api_client):
        """Test API request with network error."""
        api_client.access_token = "valid_token"
        api_client.token_expiration = datetime.utcnow() + timedelta(minutes=30)

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.request.side_effect = aiohttp.ClientError("Network error")

            result = await api_client.make_request("GET", "/api/device/status")

            assert result["successful"] is False
            assert "Network error" in result["error"]

    async def test_get_device_status(self, api_client, mock_device_status_response):
        """Test get_device_status method."""
        with patch.object(api_client, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_device_status_response

            result = await api_client.get_device_status()

            assert result == mock_device_status_response
            mock_request.assert_called_once_with("GET", "/api/device/status")

    async def test_get_schedule(self, api_client):
        """Test get_schedule method."""
        expected_response = {"successful": True, "result": {"schedule": []}}
        
        with patch.object(api_client, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = expected_response

            result = await api_client.get_schedule()

            assert result == expected_response
            mock_request.assert_called_once_with("GET", "/api/schedule/")

    async def test_get_technical_status(self, api_client):
        """Test get_technical_status method."""
        expected_response = {"successful": True, "result": {"technical": {}}}
        
        with patch.object(api_client, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = expected_response

            result = await api_client.get_technical_status()

            assert result == expected_response
            mock_request.assert_called_once_with("GET", "/api/technical/status")

    async def test_get_maintenance_diagnostics(self, api_client):
        """Test get_maintenance_diagnostics method."""
        expected_response = {"successful": True, "result": {"diagnostics": {}}}
        
        with patch.object(api_client, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = expected_response

            result = await api_client.get_maintenance_diagnostics()

            assert result == expected_response
            mock_request.assert_called_once_with("GET", "/api/device/maintenance/diagnostics")

    async def test_send_command(self, api_client):
        """Test send_command method."""
        command_data = {"command": "SET_CHARGE", "value": 80}
        expected_response = {"successful": True, "result": {"status": "accepted"}}
        
        with patch.object(api_client, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = expected_response

            result = await api_client.send_command(command_data)

            assert result == expected_response
            mock_request.assert_called_once_with("POST", "/api/device/command", json=command_data)

    async def test_update_settings(self, api_client):
        """Test update_settings method."""
        settings_data = {"defaultMode": "SET_BASIC_MODE"}
        expected_response = {"successful": True, "result": {"status": "updated"}}
        
        with patch.object(api_client, "make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = expected_response

            result = await api_client.update_settings(settings_data)

            assert result == expected_response
            mock_request.assert_called_once_with("PUT", "/api/settings", json=settings_data)

    async def test_store_token(self, api_client, hass: HomeAssistant):
        """Test token storage."""
        api_client.access_token = "test_token"
        api_client.token_expiration = datetime.utcnow() + timedelta(minutes=55)

        with patch.object(api_client.store, "async_save", new_callable=AsyncMock) as mock_save:
            await api_client.store_token()
            
            mock_save.assert_called_once()
            call_args = mock_save.call_args[0][0]
            assert call_args["access_token"] == "test_token"
            assert "expiration" in call_args

    async def test_load_token(self, api_client, hass: HomeAssistant):
        """Test token loading."""
        token_data = {
            "access_token": "stored_token",
            "expiration": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }

        with patch.object(api_client.store, "async_load", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = token_data

            await api_client.load_token()

            assert api_client.access_token == "stored_token"
            assert api_client.token_expiration is not None

    async def test_load_token_no_data(self, api_client, hass: HomeAssistant):
        """Test token loading when no data exists."""
        with patch.object(api_client.store, "async_load", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = None

            await api_client.load_token()

            assert api_client.access_token is None
            assert api_client.token_expiration is None

    async def test_refresh_token(self, api_client):
        """Test token refresh."""
        with patch.object(api_client, "connect", new_callable=AsyncMock) as mock_connect:
            await api_client.refresh_token()
            mock_connect.assert_called_once()