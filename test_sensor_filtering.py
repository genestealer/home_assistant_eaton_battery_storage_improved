#!/usr/bin/env python3
"""Test to verify sensor filtering by account type."""

import sys

# Add the custom_components directory to path
sys.path.insert(0, "/workspaces/eaton_battery_storage_hacs/custom_components")

# Now import from the package
from eaton_battery_storage.const import TECHNICIAN_ONLY_SENSORS
from eaton_battery_storage.sensor import SENSOR_TYPES


def test_sensor_filtering():
    """Test which sensors would be created for each account type."""

    print("=" * 80)
    print("SENSOR FILTERING TEST")
    print("=" * 80)

    print(f"\nTotal sensors defined: {len(SENSOR_TYPES)}")
    print(f"Technician-only sensors: {len(TECHNICIAN_ONLY_SENSORS)}")

    # Calculate which sensors would be created for customer
    customer_sensors = []
    tech_only_found = []

    for key in SENSOR_TYPES.keys():
        if key in TECHNICIAN_ONLY_SENSORS:
            tech_only_found.append(key)
        else:
            customer_sensors.append(key)

    print(f"\n✓ Customer account sensors: {len(customer_sensors)}")
    print(f"✓ Technician-only sensors found in SENSOR_TYPES: {len(tech_only_found)}")

    # Check for technical_status or maintenance_diagnostics sensors not in the filter list
    missing_from_filter = []
    for key in SENSOR_TYPES.keys():
        if (
            key.startswith("technical_status.")
            or key.startswith("maintenance_diagnostics.")
        ) and key not in TECHNICIAN_ONLY_SENSORS:
            missing_from_filter.append(key)

    if missing_from_filter:
        print(
            f"\n⚠️  WARNING: {len(missing_from_filter)} technical sensors NOT in filter list:"
        )
        for key in missing_from_filter:
            print(f"  - {key}")
    else:
        print("\n✅ All technical/maintenance sensors are in the filter list")

    print("\n" + "=" * 80)
    print("CUSTOMER ACCOUNT SENSORS (Always Available)")
    print("=" * 80)
    for key in sorted(customer_sensors):
        desc = SENSOR_TYPES[key]
        name = desc.get("name", "Unknown")
        print(f"  • {name:<50} ({key})")

    print("\n" + "=" * 80)
    print("TECHNICIAN ACCOUNT ONLY SENSORS")
    print("=" * 80)
    for key in sorted(tech_only_found):
        desc = SENSOR_TYPES[key]
        name = desc.get("name", "Unknown")
        print(f"  • {name:<50} ({key})")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ Customer accounts will have: {len(customer_sensors)} sensors")
    print(f"✓ Technician accounts will have: {len(SENSOR_TYPES)} sensors")
    print(f"✓ Additional sensors for technician: {len(tech_only_found)}")

    if missing_from_filter:
        print(
            f"\n❌ ISSUE: {len(missing_from_filter)} technical sensors would still be created for customer accounts!"
        )
        return False
    else:
        print("\n✅ All technical sensors are properly filtered!")
        return True


if __name__ == "__main__":
    success = test_sensor_filtering()
    sys.exit(0 if success else 1)
