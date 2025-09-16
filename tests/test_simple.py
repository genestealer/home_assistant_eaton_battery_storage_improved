"""Simple test to validate the test setup."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, AsyncMock


def test_simple_validation():
    """Simple test to validate that pytest is working."""
    assert True


def test_mock_creation():
    """Test that we can create mocks properly."""
    mock = Mock()
    mock.test_method.return_value = "test_value"
    
    assert mock.test_method() == "test_value"


@pytest.mark.asyncio
async def test_async_mock():
    """Test that async mocks work."""
    async_mock = AsyncMock()
    async_mock.async_method.return_value = "async_result"
    
    result = await async_mock.async_method()
    assert result == "async_result"


def test_imports():
    """Test that we can import our custom components."""
    from custom_components.eaton_battery_storage.const import DOMAIN
    assert DOMAIN == "eaton_battery_storage"


def test_config_flow_class_import():
    """Test that we can import config flow classes."""
    from custom_components.eaton_battery_storage.config_flow import EatonXStorageConfigFlow
    assert EatonXStorageConfigFlow.domain == "eaton_battery_storage"


def test_api_class_import():
    """Test that we can import API class."""
    from custom_components.eaton_battery_storage.api import EatonBatteryAPI
    assert hasattr(EatonBatteryAPI, "connect")