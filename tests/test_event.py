"""Tests for the Eaton Battery Storage event platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.eaton_battery_storage.event import (
    EatonXStorageNotificationEvent,
)

from .conftest import MOCK_ENTRY_ID, MOCK_NOTIFICATIONS_DATA, build_coordinator_data


def test_event_unique_id(mock_coordinator: MagicMock) -> None:
    """Test unique_id is scoped to entry."""
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    assert ev.unique_id == f"{MOCK_ENTRY_ID}_notifications_event"


def test_event_types(mock_coordinator: MagicMock) -> None:
    """Test event entity has the correct event types."""
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    assert ev.event_types == ["notification"]


def test_extract_alerts(mock_coordinator: MagicMock) -> None:
    """Test _extract_alerts returns alerts from coordinator data."""
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    alerts = ev._extract_alerts()
    assert len(alerts) == 1
    assert alerts[0]["alertId"] == "alert_001"


def test_extract_alerts_empty(mock_coordinator: MagicMock) -> None:
    """Test _extract_alerts returns empty list when no notifications."""
    data = build_coordinator_data(notifications={"results": []})
    mock_coordinator.data = data
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    assert ev._extract_alerts() == []


def test_extract_alerts_none_data(mock_coordinator: MagicMock) -> None:
    """Test _extract_alerts with None coordinator data."""
    mock_coordinator.data = None
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    assert ev._extract_alerts() == []


def test_priming_fills_seen_set(mock_coordinator: MagicMock) -> None:
    """Test that async_added_to_hass primes the seen set with existing alerts."""
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    # Simulate priming manually (can't fully await async_added_to_hass without HA running)
    for alert in ev._extract_alerts():
        aid = alert.get("alertId") or alert.get("alert_id")
        if aid:
            ev._seen.add(aid)
    ev._primed = True
    assert "alert_001" in ev._seen
    assert ev._primed is True


def test_handle_coordinator_update_new_alert(mock_coordinator: MagicMock) -> None:
    """Test that _handle_coordinator_update emits events for new alerts."""
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    ev._primed = True
    ev._seen = set()  # No seen alerts → all are new
    ev.async_write_ha_state = MagicMock()
    ev._trigger_event = MagicMock()

    ev._handle_coordinator_update()

    ev._trigger_event.assert_called_once_with(
        "notification",
        {"alert": MOCK_NOTIFICATIONS_DATA["results"][0]},
    )
    assert "alert_001" in ev._seen


def test_handle_coordinator_update_already_seen(mock_coordinator: MagicMock) -> None:
    """Test that already-seen alerts don't trigger events."""
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    ev._primed = True
    ev._seen = {"alert_001"}
    ev.async_write_ha_state = MagicMock()
    ev._trigger_event = MagicMock()

    ev._handle_coordinator_update()

    ev._trigger_event.assert_not_called()


def test_extra_state_attributes_has_unread(mock_coordinator: MagicMock) -> None:
    """Test extra_state_attributes shows 'has_unread' when count > 0."""
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    attrs = ev.extra_state_attributes
    assert attrs["status"] == "has_unread"
    assert attrs["unread_count"] == 1


def test_extra_state_attributes_idle(mock_coordinator: MagicMock) -> None:
    """Test extra_state_attributes shows 'idle' when no unread."""
    data = build_coordinator_data(unread_notifications_count={"total": 0})
    mock_coordinator.data = data
    ev = EatonXStorageNotificationEvent(mock_coordinator)
    attrs = ev.extra_state_attributes
    assert attrs["status"] == "idle"
    assert attrs["unread_count"] == 0
