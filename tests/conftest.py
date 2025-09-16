"""Simple conftest for basic testing without Home Assistant dependencies."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def mock_api():
    """Mock EatonBatteryAPI fixture."""
    api_instance = AsyncMock()
    api_instance.host = "192.168.1.100"
    api_instance.username = "admin"
    api_instance.password = "password"
    api_instance.inverter_sn = "test_serial"
    api_instance.email = "test@example.com"
    api_instance.access_token = None
    api_instance.token_expiration = None
    
    # Mock common API responses
    api_instance.connect.return_value = None
    api_instance.get_device_status.return_value = {
        "successful": True,
        "result": {
            "status": {
                "operationMode": "IDLE",
                "batteryLevel": 85,
                "energyFlow": {
                    "consumptionValue": 1200,
                    "productionValue": 800,
                    "gridValue": 400,
                    "batteryValue": 0,
                },
            },
        },
    }
    return api_instance


@pytest.fixture
def mock_successful_auth_response():
    """Mock successful authentication response."""
    return {
        "successful": True,
        "result": {
            "token": "mock_access_token",
        }
    }


@pytest.fixture
def mock_failed_auth_response():
    """Mock failed authentication response."""
    return {
        "successful": False,
        "error": {
            "description": "Invalid credentials",
            "errCode": "AUTH_FAILED"
        }
    }


@pytest.fixture
def mock_device_status_response():
    """Mock device status response."""
    return {
        "successful": True,
        "result": {
            "status": {
                "operationMode": "IDLE",
                "batteryLevel": 85,
                "energyFlow": {
                    "consumptionValue": 1200,
                    "productionValue": 800,
                    "gridValue": 400,
                    "batteryValue": 0,
                    "acPvValue": 500,
                    "dcPvValue": 300,
                },
                "today": {
                    "gridConsumption": 15.5,
                    "gridInjection": 8.2,
                    "photovoltaicProduction": 12.8,
                },
            },
            "device": {
                "serialNumber": "test_serial",
                "modelName": "xStorage Home",
                "softwareVersion": "1.0.0",
            },
        }
    }