"""Tests for the Eaton Battery Storage button platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.eaton_battery_storage.button import (
    EatonXStorageMarkNotificationsReadButton,
    EatonXStorageStopCurrentOperationButton,
)

from .conftest import MOCK_ENTRY_ID


# ---------------------------------------------------------------------------
# Mark Notifications Read button
# ---------------------------------------------------------------------------


def test_mark_notifications_unique_id(mock_coordinator: MagicMock) -> None:
    """Test unique_id is scoped to entry."""
    btn = EatonXStorageMarkNotificationsReadButton(mock_coordinator)
    assert btn.unique_id == f"{MOCK_ENTRY_ID}_mark_notifications_read"


async def test_mark_notifications_press_success(
    mock_coordinator: MagicMock,
) -> None:
    """Test pressing the button marks notifications read."""
    btn = EatonXStorageMarkNotificationsReadButton(mock_coordinator)
    await btn.async_press()

    mock_coordinator.api.mark_all_notifications_read.assert_awaited_once()
    mock_coordinator.async_request_refresh.assert_awaited_once()


async def test_mark_notifications_press_api_failure(
    mock_coordinator: MagicMock,
) -> None:
    """Test pressing when API returns unsuccessful."""
    mock_coordinator.api.mark_all_notifications_read.return_value = {
        "successful": False
    }
    btn = EatonXStorageMarkNotificationsReadButton(mock_coordinator)
    # Should not raise, just log
    await btn.async_press()


async def test_mark_notifications_press_exception(
    mock_coordinator: MagicMock,
) -> None:
    """Test pressing when API raises an exception."""
    mock_coordinator.api.mark_all_notifications_read.side_effect = Exception("Boom")
    btn = EatonXStorageMarkNotificationsReadButton(mock_coordinator)
    # Should not raise, catches exception internally
    await btn.async_press()


# ---------------------------------------------------------------------------
# Stop Current Operation button
# ---------------------------------------------------------------------------


def test_stop_operation_unique_id(mock_coordinator: MagicMock) -> None:
    """Test unique_id is scoped to entry."""
    btn = EatonXStorageStopCurrentOperationButton(mock_coordinator)
    assert btn.unique_id == f"{MOCK_ENTRY_ID}_stop_current_operation"


async def test_stop_operation_press_success(mock_coordinator: MagicMock) -> None:
    """Test pressing stop sends SET_BASIC_MODE command."""
    btn = EatonXStorageStopCurrentOperationButton(mock_coordinator)

    with patch("custom_components.eaton_battery_storage.button.asyncio.sleep"):
        await btn.async_press()

    mock_coordinator.api.send_device_command.assert_awaited_once_with(
        "SET_BASIC_MODE", 1, {}
    )
    mock_coordinator.async_request_refresh.assert_awaited()


async def test_stop_operation_press_exception(mock_coordinator: MagicMock) -> None:
    """Test pressing when API raises — should still refresh."""
    mock_coordinator.api.send_device_command.side_effect = Exception("Boom")
    btn = EatonXStorageStopCurrentOperationButton(mock_coordinator)
    # Should not raise; catches exception internally
    await btn.async_press()
    mock_coordinator.async_request_refresh.assert_awaited()
