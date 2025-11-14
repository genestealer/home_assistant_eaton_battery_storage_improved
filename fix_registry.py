#!/usr/bin/env python3
"""Fix corrupted device and entity registry entries.

This script fixes the 'device' entry_type issue in the device registry
without losing all your entity customizations and area assignments.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def fix_device_registry(registry_path: Path) -> bool:
    """Fix corrupted device registry entries."""
    if not registry_path.exists():
        print(f"Registry file not found: {registry_path}")
        return False

    # Backup the file first
    backup_path = registry_path.with_suffix(
        f".json.fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    print(f"Creating backup: {backup_path}")
    backup_path.write_text(registry_path.read_text())

    # Load and fix the registry
    try:
        data = json.loads(registry_path.read_text())
        fixed = False

        if "data" in data and "devices" in data["data"]:
            for device in data["data"]["devices"]:
                # Fix invalid 'device' entry_type (should be 'service' or None)
                if device.get("entry_type") == "device":
                    print(
                        f"Fixing device: {device.get('name', 'Unknown')} (id: {device.get('id', 'Unknown')}) - removing invalid entry_type='device'"
                    )
                    device["entry_type"] = None
                    fixed = True

        if fixed:
            # Write the fixed registry
            registry_path.write_text(json.dumps(data, indent=2))
            print(f"✓ Fixed and saved to: {registry_path}")
            return True
        else:
            print("No issues found in device registry")
            return True

    except Exception as e:
        print(f"Error fixing registry: {e}")
        print(f"You can restore from backup: {backup_path}")
        return False


def main():
    """Main entry point."""
    # Default path to Home Assistant config
    config_path = Path("/workspaces/core/config/.storage")

    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])

    device_registry = config_path / "core.device_registry"

    print("=" * 60)
    print("Home Assistant Registry Fixer")
    print("=" * 60)
    print()

    if not device_registry.exists():
        print("⚠ Device registry not found. It will be created on next HA startup.")
        return 0

    success = fix_device_registry(device_registry)

    print()
    print("=" * 60)
    if success:
        print("✓ Registry fix completed successfully!")
        print("  You can now restart Home Assistant.")
    else:
        print("✗ Registry fix failed.")
        print("  Check the error messages above.")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
