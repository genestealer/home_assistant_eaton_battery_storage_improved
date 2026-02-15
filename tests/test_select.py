"""Tests for the Eaton Battery Storage select platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.eaton_battery_storage.select import (
    EatonXStorageCurrentOperationModeSelect,
    EatonXStorageDefaultOperationModeSelect,
)

from .conftest import (
    MOCK_ENTRY_ID,
    MOCK_SETTINGS_DATA,
    _build_api_response,
    build_coordinator_data,
)


# ---------------------------------------------------------------------------
# Default Operation Mode Select tests
# ---------------------------------------------------------------------------


def test_default_mode_options(mock_coordinator: MagicMock) -> None:
    """Test that default mode select exposes the correct options."""
    sel = EatonXStorageDefaultOperationModeSelect(mock_coordinator)
    assert "Basic Mode" in sel.options
    assert "Maximize Auto Consumption" in sel.options
    assert len(sel.options) == 5


def test_default_mode_current_option(mock_coordinator: MagicMock) -> None:
    """Test that current_option reads from settings.defaultMode."""
    sel = EatonXStorageDefaultOperationModeSelect(mock_coordinator)
    # MOCK_SETTINGS_DATA has command=SET_MAXIMIZE_AUTO_CONSUMPTION
    assert sel.current_option == "Maximize Auto Consumption"


def test_default_mode_current_option_unknown(mock_coordinator: MagicMock) -> None:
    """Test current_option returns None for unknown command."""
    data = build_coordinator_data()
    data["settings"]["defaultMode"]["command"] = "UNKNOWN_CMD"
    mock_coordinator.data = data
    sel = EatonXStorageDefaultOperationModeSelect(mock_coordinator)
    assert sel.current_option is None


def test_default_mode_unique_id(mock_coordinator: MagicMock) -> None:
    """Test unique ID is scoped to entry."""
    sel = EatonXStorageDefaultOperationModeSelect(mock_coordinator)
    assert sel.unique_id == f"{MOCK_ENTRY_ID}_default_operation_mode"


async def test_default_mode_select_option(mock_coordinator: MagicMock) -> None:
    """Test selecting a default mode calls update_settings."""
    mock_coordinator.api.get_settings.return_value = _build_api_response(
        dict(MOCK_SETTINGS_DATA)
    )
    sel = EatonXStorageDefaultOperationModeSelect(mock_coordinator)

    with patch("custom_components.eaton_battery_storage.select.asyncio.sleep"):
        await sel.async_select_option("Basic Mode")

    mock_coordinator.api.update_settings.assert_awaited_once()
    payload = mock_coordinator.api.update_settings.call_args[0][0]
    assert payload["settings"]["defaultMode"]["command"] == "SET_BASIC_MODE"


async def test_default_mode_invalid_option(mock_coordinator: MagicMock) -> None:
    """Test selecting an invalid option does nothing."""
    sel = EatonXStorageDefaultOperationModeSelect(mock_coordinator)
    await sel.async_select_option("Nonexistent Mode")
    mock_coordinator.api.update_settings.assert_not_called()


def test_default_mode_available(mock_coordinator: MagicMock) -> None:
    """Test availability check."""
    sel = EatonXStorageDefaultOperationModeSelect(mock_coordinator)
    assert sel.available is True
    mock_coordinator.data = None
    assert sel.available is False


# ---------------------------------------------------------------------------
# Current Operation Mode Select tests
# ---------------------------------------------------------------------------


def test_current_mode_options_include_manual(mock_coordinator: MagicMock) -> None:
    """Test current mode options include Manual Charge/Discharge."""
    sel = EatonXStorageCurrentOperationModeSelect(mock_coordinator)
    assert "Manual Charge" in sel.options
    assert "Manual Discharge" in sel.options
    assert len(sel.options) == 7  # 5 default + 2 manual


def test_current_mode_unique_id(mock_coordinator: MagicMock) -> None:
    """Test unique ID is scoped to entry."""
    sel = EatonXStorageCurrentOperationModeSelect(mock_coordinator)
    assert sel.unique_id == f"{MOCK_ENTRY_ID}_current_operation_mode"


async def test_current_mode_select_manual_charge(
    mock_coordinator: MagicMock,
) -> None:
    """Test selecting Manual Charge sends the correct command."""
    mock_coordinator.number_values = {
        "charge_duration": 2,
        "charge_power": 15,
        "charge_end_soc": 90,
    }
    sel = EatonXStorageCurrentOperationModeSelect(mock_coordinator)

    with patch("custom_components.eaton_battery_storage.select.asyncio.sleep"):
        await sel.async_select_option("Manual Charge")

    mock_coordinator.api.send_device_command.assert_awaited_once_with(
        "SET_CHARGE",
        2,
        {"action": "ACTION_CHARGE", "power": 15, "soc": 90},
    )


async def test_current_mode_select_basic_mode(mock_coordinator: MagicMock) -> None:
    """Test selecting Basic Mode uses run_duration."""
    mock_coordinator.number_values = {"run_duration": 4}
    sel = EatonXStorageCurrentOperationModeSelect(mock_coordinator)

    with patch("custom_components.eaton_battery_storage.select.asyncio.sleep"):
        await sel.async_select_option("Basic Mode")

    mock_coordinator.api.send_device_command.assert_awaited_once_with(
        "SET_BASIC_MODE", 4, {}
    )


async def test_current_mode_invalid_option(mock_coordinator: MagicMock) -> None:
    """Test selecting an invalid option does nothing."""
    sel = EatonXStorageCurrentOperationModeSelect(mock_coordinator)
    await sel.async_select_option("Nonexistent")
    mock_coordinator.api.send_device_command.assert_not_called()
