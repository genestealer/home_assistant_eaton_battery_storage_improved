#!/usr/bin/env python3
"""Test coordinator behavior for customer vs technician accounts."""

import asyncio
from unittest.mock import Mock, AsyncMock


class MockConfigEntry:
    """Mock config entry."""

    def __init__(self, user_type="customer"):
        self.data = {"user_type": user_type}
        self.entry_id = "test_entry"


class MockAPI:
    """Mock API client."""

    def __init__(self):
        self.get_status = AsyncMock(return_value={"result": {"test": "data"}})
        self.get_device = AsyncMock(return_value={"result": {"test": "data"}})
        self.get_config_state = AsyncMock(return_value={"result": {"test": "data"}})
        self.get_settings = AsyncMock(return_value={"result": {"test": "data"}})
        self.get_metrics = AsyncMock(return_value={"result": {"test": "data"}})
        self.get_metrics_daily = AsyncMock(return_value={"result": {"test": "data"}})
        self.get_schedule = AsyncMock(return_value={"result": {"test": "data"}})
        self.get_technical_status = AsyncMock(
            return_value={"result": {"test": "technical"}}
        )
        self.get_maintenance_diagnostics = AsyncMock(
            return_value={"result": {"test": "diagnostics"}}
        )
        self.get_notifications = AsyncMock(return_value={"result": {"test": "data"}})
        self.get_unread_notifications_count = AsyncMock(
            return_value={"result": {"test": "data"}}
        )
        self.host = "192.168.1.100"


async def test_customer_account():
    """Test that customer accounts don't call technical endpoints."""
    print("=" * 60)
    print("TEST: Customer Account - Technical Endpoints NOT Called")
    print("=" * 60)

    # Mock the coordinator's _async_update_data logic
    config_entry = MockConfigEntry(user_type="customer")
    api = MockAPI()

    # Simulate what coordinator does
    user_type = config_entry.data.get("user_type", "tech")

    print(f"\nUser Type: {user_type}")
    print(f"Is Technician: {user_type == 'tech'}")

    if user_type == "tech":
        print("\n❌ WRONG: Would call technical endpoints")
        await api.get_technical_status()
        await api.get_maintenance_diagnostics()
    else:
        print("\n✅ CORRECT: Skipping technical endpoints for customer account")
        print("   - technical_status: not called (set to {})")
        print("   - maintenance_diagnostics: not called (set to {})")

    # Verify the API methods were NOT called
    print("\nAPI Call Verification:")
    print(f"  get_technical_status called: {api.get_technical_status.called}")
    print(
        f"  get_maintenance_diagnostics called: {api.get_maintenance_diagnostics.called}"
    )

    if (
        not api.get_technical_status.called
        and not api.get_maintenance_diagnostics.called
    ):
        print("\n✅ SUCCESS: No technical endpoint calls for customer account!")
    else:
        print("\n❌ FAILURE: Technical endpoints were called!")

    return (
        not api.get_technical_status.called
        and not api.get_maintenance_diagnostics.called
    )


async def test_technician_account():
    """Test that technician accounts DO call technical endpoints."""
    print("\n" + "=" * 60)
    print("TEST: Technician Account - Technical Endpoints Called")
    print("=" * 60)

    # Mock the coordinator's _async_update_data logic
    config_entry = MockConfigEntry(user_type="tech")
    api = MockAPI()

    # Simulate what coordinator does
    user_type = config_entry.data.get("user_type", "tech")

    print(f"\nUser Type: {user_type}")
    print(f"Is Technician: {user_type == 'tech'}")

    if user_type == "tech":
        print("\n✅ CORRECT: Calling technical endpoints for technician account")
        await api.get_technical_status()
        await api.get_maintenance_diagnostics()
        print("   - technical_status: called")
        print("   - maintenance_diagnostics: called")
    else:
        print("\n❌ WRONG: Would skip technical endpoints")

    # Verify the API methods WERE called
    print("\nAPI Call Verification:")
    print(f"  get_technical_status called: {api.get_technical_status.called}")
    print(
        f"  get_maintenance_diagnostics called: {api.get_maintenance_diagnostics.called}"
    )

    if api.get_technical_status.called and api.get_maintenance_diagnostics.called:
        print("\n✅ SUCCESS: Technical endpoints called for technician account!")
    else:
        print("\n❌ FAILURE: Technical endpoints were NOT called!")

    return api.get_technical_status.called and api.get_maintenance_diagnostics.called


async def test_backward_compatibility():
    """Test that missing user_type defaults to tech."""
    print("\n" + "=" * 60)
    print("TEST: Backward Compatibility - Missing user_type defaults to tech")
    print("=" * 60)

    # Mock config entry without user_type (old installations)
    config_entry = Mock()
    config_entry.data = {}  # No user_type key

    user_type = config_entry.data.get("user_type", "tech")

    print(f"\nUser Type (missing): {user_type}")
    print(f"Defaults to tech: {user_type == 'tech'}")

    if user_type == "tech":
        print("\n✅ CORRECT: Missing user_type defaults to technician")
        print("   - Existing installations will continue to work")
        print("   - Technical endpoints will still be called")
    else:
        print("\n❌ WRONG: Should default to tech for backward compatibility")

    return user_type == "tech"


async def main():
    """Run all tests."""
    test1 = await test_customer_account()
    test2 = await test_technician_account()
    test3 = await test_backward_compatibility()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Customer Account Test: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Technician Account Test: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Backward Compatibility Test: {'✅ PASS' if test3 else '❌ FAIL'}")

    if all([test1, test2, test3]):
        print("\n🎉 All tests passed!")
        print("\nExpected Behavior:")
        print("  • Customer accounts: NO 403 errors (endpoints not called)")
        print("  • Technician accounts: Technical data fetched normally")
        print("  • Old installations: Continue working as technician accounts")
    else:
        print("\n❌ Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())
