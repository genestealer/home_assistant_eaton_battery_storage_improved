"""Test the Eaton Battery Storage constants."""

from __future__ import annotations

from custom_components.eaton_battery_storage.const import (
    BMS_STATE_MAP,
    CURRENT_MODE_ACTION_MAP,
    CURRENT_MODE_COMMAND_MAP,
    CURRENT_MODE_RECURRENCE_MAP,
    CURRENT_MODE_TYPE_MAP,
    DOMAIN,
    OPERATION_MODE_MAP,
    POWER_ACCURACY_WARNING,
)


class TestConstants:
    """Test integration constants."""

    def test_domain(self):
        """Test domain constant."""
        assert DOMAIN == "eaton_battery_storage"
        assert isinstance(DOMAIN, str)

    def test_power_accuracy_warning(self):
        """Test power accuracy warning message."""
        assert isinstance(POWER_ACCURACY_WARNING, str)
        assert len(POWER_ACCURACY_WARNING) > 0
        assert "30%" in POWER_ACCURACY_WARNING
        assert "WARNING" in POWER_ACCURACY_WARNING

    def test_current_mode_command_map(self):
        """Test current mode command mappings."""
        assert isinstance(CURRENT_MODE_COMMAND_MAP, dict)

        expected_commands = [
            "SET_CHARGE",
            "SET_BASIC_MODE",
            "SET_DISCHARGE",
            "SET_MAXIMIZE_AUTO_CONSUMPTION",
            "SET_VARIABLE_GRID_INJECTION",
            "SET_FREQUENCY_REGULATION",
            "SET_PEAK_SHAVING",
        ]

        for command in expected_commands:
            assert command in CURRENT_MODE_COMMAND_MAP
            assert isinstance(CURRENT_MODE_COMMAND_MAP[command], str)
            assert len(CURRENT_MODE_COMMAND_MAP[command]) > 0

    def test_current_mode_action_map(self):
        """Test current mode action mappings."""
        assert isinstance(CURRENT_MODE_ACTION_MAP, dict)

        expected_actions = ["ACTION_CHARGE", "ACTION_DISCHARGE"]

        for action in expected_actions:
            assert action in CURRENT_MODE_ACTION_MAP
            assert isinstance(CURRENT_MODE_ACTION_MAP[action], str)
            assert len(CURRENT_MODE_ACTION_MAP[action]) > 0

    def test_current_mode_type_map(self):
        """Test current mode type mappings."""
        assert isinstance(CURRENT_MODE_TYPE_MAP, dict)

        expected_types = ["MANUAL", "SCHEDULE"]

        for mode_type in expected_types:
            assert mode_type in CURRENT_MODE_TYPE_MAP
            assert isinstance(CURRENT_MODE_TYPE_MAP[mode_type], str)
            assert len(CURRENT_MODE_TYPE_MAP[mode_type]) > 0

    def test_current_mode_recurrence_map(self):
        """Test current mode recurrence mappings."""
        assert isinstance(CURRENT_MODE_RECURRENCE_MAP, dict)

        expected_recurrences = ["MANUAL_EVENT", "DAILY", "WEEKLY"]

        for recurrence in expected_recurrences:
            assert recurrence in CURRENT_MODE_RECURRENCE_MAP
            assert isinstance(CURRENT_MODE_RECURRENCE_MAP[recurrence], str)
            assert len(CURRENT_MODE_RECURRENCE_MAP[recurrence]) > 0

    def test_operation_mode_map(self):
        """Test operation mode mappings."""
        assert isinstance(OPERATION_MODE_MAP, dict)

        expected_modes = [
            "CHARGING",
            "DISCHARGING",
            "IDLE",
            "STANDBY",
            "MAXIMIZE_AUTO_CONSUMPTION",
            "BAT_CHARGING",
            "BAT_DISCHARGING",
            "BAT_IDLE",
            "UNKNOWN",
            "OFF",
            "FAULT",
        ]

        for mode in expected_modes:
            assert mode in OPERATION_MODE_MAP
            assert isinstance(OPERATION_MODE_MAP[mode], str)
            assert len(OPERATION_MODE_MAP[mode]) > 0

    def test_bms_state_map(self):
        """Test BMS state mappings."""
        assert isinstance(BMS_STATE_MAP, dict)

        expected_states = ["BAT_CHARGING", "BAT_DISCHARGING", "BAT_IDLE"]

        for state in expected_states:
            assert state in BMS_STATE_MAP
            assert isinstance(BMS_STATE_MAP[state], str)
            assert len(BMS_STATE_MAP[state]) > 0

    def test_mappings_no_empty_values(self):
        """Test that mappings don't have empty string values."""
        all_maps = [
            CURRENT_MODE_COMMAND_MAP,
            CURRENT_MODE_ACTION_MAP,
            CURRENT_MODE_TYPE_MAP,
            CURRENT_MODE_RECURRENCE_MAP,
            OPERATION_MODE_MAP,
            BMS_STATE_MAP,
        ]

        for mapping in all_maps:
            for key, value in mapping.items():
                assert value.strip() != "", f"Empty value for key '{key}'"

    def test_mappings_consistent_formatting(self):
        """Test that human-readable values follow consistent formatting."""
        all_maps = [
            CURRENT_MODE_COMMAND_MAP,
            CURRENT_MODE_ACTION_MAP,
            CURRENT_MODE_TYPE_MAP,
            CURRENT_MODE_RECURRENCE_MAP,
            OPERATION_MODE_MAP,
            BMS_STATE_MAP,
        ]

        for mapping in all_maps:
            for key, value in mapping.items():
                # Values should be title case or proper nouns
                assert value[
                    0
                ].isupper(), (
                    f"Value '{value}' for key '{key}' should start with uppercase"
                )
                # Should not end with punctuation
                assert not value.endswith(
                    "."
                ), f"Value '{value}' for key '{key}' should not end with period"

    def test_operation_mode_map_aliases(self):
        """Test that operation mode map includes battery state aliases."""
        # Test that battery-specific states map to the same values as general states
        assert OPERATION_MODE_MAP["CHARGING"] == OPERATION_MODE_MAP["BAT_CHARGING"]
        assert (
            OPERATION_MODE_MAP["DISCHARGING"] == OPERATION_MODE_MAP["BAT_DISCHARGING"]
        )
        assert OPERATION_MODE_MAP["IDLE"] == OPERATION_MODE_MAP["BAT_IDLE"]

    def test_bms_state_consistency(self):
        """Test that BMS state map is consistent with operation mode map."""
        for bms_key, bms_value in BMS_STATE_MAP.items():
            assert bms_key in OPERATION_MODE_MAP
            assert OPERATION_MODE_MAP[bms_key] == bms_value
