"""Constants for Eaton Battery Storage integration."""

from __future__ import annotations

# Account type constants
ACCOUNT_TYPE_CUSTOMER = "customer"
ACCOUNT_TYPE_TECHNICIAN = "tech"

# BMS State mapping for human-readable display
BMS_STATE_MAP: dict[str, str] = {
    "BAT_CHARGING": "Charging",
    "BAT_DISCHARGING": "Discharging",
    "BAT_IDLE": "Idle",
}

# bmsFaultCode from /api/technical/status is null when healthy, else an array of these
BMS_FAULT_CODE_MAP: dict[str, str] = {
    "GENERAL": "General BMS fault",
    "UNDER_TEMPERATURE": "Under-temperature",
    "OVER_TEMPERATURE": "Over-temperature",
    "OVER_VOLTAGE": "Over-voltage",
    "UNDER_VOLTAGE": "Under-voltage",
    "CHARGE_OVER_CURRENT": "Charge over-current",
    "DISCHARGE_OVER_CURRENT": "Discharge over-current",
    "CURRENT_MISMATCH": "Charger current mismatch",
}

# State of the BMS fault code sensor when the API reports no fault
BMS_NO_FAULT = "No fault"

# Notification subType text from the eaton-xstorage-home-api-doc repo.
# The BATTERY_VOLTAGE_* and BUS_*_FAIL descriptions are deliberately reworded here:
# Eaton's translation bundle reuses one string per opposing pair, which would make
# the sensor state unable to distinguish over- from under-voltage.
NOTIFICATION_SUBTYPE_MAP: dict[str, dict[str, str]] = {
    # Battery faults
    "BATTERY_VOLTAGE_HIGH": {
        "description": "The battery voltage is too high.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "BATTERY_VOLTAGE_LOW": {
        "description": "The battery voltage is too low.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "BATTERY_OVER_TEMP": {
        "description": "Battery temperature is too high.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "BATTERY_UNDER_TEMP": {
        "description": "Battery temperature is too low.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "BMS_FAULT": {
        "description": "General BMS fault detected.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "BMS_DEEP_UV": {
        "description": "Battery deep under-voltage.",
        "remedy": "Contact service representative.",
    },
    "BMS_VOLT_SENSOR_FAIL": {
        "description": "Battery voltage sensor failure.",
        "remedy": "Restart battery; contact service if fault persists.",
    },
    "BMS_TEMP_SENSOR_FAIL": {
        "description": "Battery temperature sensor failure.",
        "remedy": "Restart battery; contact service if fault persists.",
    },
    "BMS_CONTACTOR_DISCONNECTED": {
        "description": "The battery contactor appears disconnected.",
        "remedy": "Restart battery; contact service if fault persists.",
    },
    "BMS_CONTACTOR_WELDED": {
        "description": "The battery contactor appears welded.",
        "remedy": "Restart battery; contact service if fault persists.",
    },
    "BMS_FUSE_BLOWN": {
        "description": "The battery fuse has ruptured.",
        "remedy": "Restart battery; contact service if fault persists.",
    },
    "BMS_WRONG_PRODUCT_TYPE": {
        "description": "The battery product ID is incorrect.",
        "remedy": "Contact service representative.",
    },
    "BMS_EXT_COMMS_FAIL": {
        "description": "The battery cannot communicate with the inverter.",
        "remedy": "Restart system; contact service if fault persists.",
    },
    "BMS_INT_COMMS_FAIL": {
        "description": "The battery has an internal communication failure.",
        "remedy": "Restart battery; contact service if fault persists.",
    },
    "NO_BATTERY": {
        "description": "Battery communication or connection is lost.",
        "remedy": "Restart inverter if connection persists.",
    },
    # Inverter faults
    "DEVICE_FAULT": {
        "description": "Inverter device abnormal or output short circuit.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "INVERTER_CURR_FAIL": {
        "description": "Inverter current is over the tolerable value.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "RELAY_FAIL": {
        "description": "The relay inside the inverter is malfunctioning.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "OVER_LOAD": {
        "description": "Please decrease critical load connection.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "OVER_POWER": {
        "description": "The power on grid terminal or inverter terminal is exceeded.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "TEMPERATURE_FAIL": {
        "description": "The ambient temperature of the inverter is too high.",
        "remedy": "Contact service if error shows below 40C ambient.",
    },
    "FAN_LOCK": {
        "description": "The fan is locked.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "BUS_FAIL": {
        "description": "The internal bus voltage is abnormal.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "BUS_HIGH_FAIL": {
        "description": "The internal bus voltage is too high.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "BUS_LOW_FAIL": {
        "description": "The internal bus voltage is too low.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "BUS_START_FAIL": {
        "description": "Time limit of DC bus soft start exceeded.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "RCMU_DEVICE_FAIL": {
        "description": "Internal module is found abnormal.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "RCMU_CURR_FAIL": {
        "description": "Leakage current at AC output is too high.",
        "remedy": "Contact supplier for service if unresolvable.",
    },
    "DC_SENSOR_FAULT": {
        "description": "The DC output sensor is abnormal.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "REF_VOLTAGE_FAULT": {
        "description": "The reference voltage of the microprocessor is abnormal.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "EEPROM_FAIL": {
        "description": "Memory error was detected.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "MASTER_SLAVE_FAIL": {
        "description": "A communication problem was detected within the inverter.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "M_S_VERSION_FAIL": {
        "description": "Master and slave firmware versions mismatch.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "OFFSET_IAC_FAIL": {
        "description": "High DC component detected in the AC output current.",
        "remedy": "Disconnect AC grid, wait 1 minute, restart inverter.",
    },
    "EMERGENCY_OFF": {
        "description": "Emergency power off is set.",
        "remedy": "Contact service if EPO persists.",
    },
    "FILESYSTEM_FAULT": {
        "description": "The device filesystem is failing.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    # Grid / AC faults
    "NO_UTILITY": {
        "description": "AC grid is not available.",
        "remedy": "Check AC breaker; contact service if grid present but fault persists.",
    },
    "GRID_VAC_FAIL": {
        "description": "AC grid over- or under-voltage.",
        "remedy": "Contact installer; check AC grid is normal.",
    },
    "GRID_FAC_FAIL": {
        "description": "AC grid over- or under-frequency.",
        "remedy": "Contact installer; check AC grid is normal.",
    },
    "ENS_GFCI_FAIL": {
        "description": "Master/slave mismatch for GFCI current detection.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "ENS_FAC_FAIL": {
        "description": "Master/slave mismatch for grid frequency detection.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "ENS_VAC_FAIL": {
        "description": "Master/slave mismatch for grid voltage detection.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "ENS_IAC_FAIL": {
        "description": "Master/slave mismatch for grid current detection.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    "TEST_FAIL": {
        "description": "Only for Italy grid code requirement.",
        "remedy": "Restart inverter; contact service if unresolvable.",
    },
    # PV / DC faults
    "PV_OVER_POWER": {
        "description": "The DC power fed from PV arrays is too high.",
        "remedy": "Verify PV array meets manual specification.",
    },
    "VPV_MAX_FAIL": {
        "description": "The DC voltage fed from PV arrays is too high.",
        "remedy": "Verify PV string meets unit specification.",
    },
    "ZPV_PE_FAIL": {
        "description": "Poor PV DC insulation to ground; leakage current possible.",
        "remedy": "Contact installer; check PV(+)/PV(-) to ground impedance per manual.",
    },
    # Firmware / software faults
    "BMS_FW_UPDATE_FAIL": {
        "description": "The device failed to update its BMS firmware version.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "INVERTER_FW_UPDATE_FAIL": {
        "description": "The device failed to update its inverter firmware version.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    "APP_UPDATE_FAIL": {
        "description": "The device failed to update its software version.",
        "remedy": "Restart inverter; contact service if fault persists.",
    },
    # Other
    "UNKNOWN_FAULT": {
        "description": "An unknown error has been detected.",
        "remedy": "Contact service if error persists.",
    },
}

# Current Mode Action mapping for human-readable display
CURRENT_MODE_ACTION_MAP: dict[str, str] = {
    "ACTION_CHARGE": "Charge",
    "ACTION_DISCHARGE": "Discharge",
}

# Current Mode Command mapping for human-readable display
CURRENT_MODE_COMMAND_MAP: dict[str, str] = {
    "SET_BASIC_MODE": "Basic Mode",
    "SET_CHARGE": "Charge",
    "SET_DISCHARGE": "Discharge",
    "SET_FREQUENCY_REGULATION": "Frequency Regulation",
    "SET_MAXIMIZE_AUTO_CONSUMPTION": "Maximize Auto Consumption",
    "SET_PEAK_SHAVING": "Peak Shaving",
    "SET_VARIABLE_GRID_INJECTION": "Variable Grid Injection",
}

# Current Mode Recurrence mapping for human-readable display
CURRENT_MODE_RECURRENCE_MAP: dict[str, str] = {
    "DAILY": "Daily",
    "MANUAL_EVENT": "Manual Event",
    "WEEKLY": "Weekly",
}

# Current Mode Type mapping for human-readable display
CURRENT_MODE_TYPE_MAP: dict[str, str] = {"MANUAL": "Manual", "SCHEDULE": "Scheduled"}

# Integration domain
DOMAIN = "eaton_battery_storage"

# Operation Mode mapping for human-readable display
OPERATION_MODE_MAP: dict[str, str] = {
    "BAT_CHARGING": "Charging",
    "BAT_DISCHARGING": "Discharging",
    "BAT_IDLE": "Idle",
    "CHARGING": "Charging",
    "DISCHARGING": "Discharging",
    "FAULT": "Fault",
    "IDLE": "Idle",
    "MAXIMIZE_AUTO_CONSUMPTION": "Maximize Auto Consumption",
    "OFF": "Off",
    "STANDBY": "Standby",
    "UNKNOWN": "Unknown",
}

# Accuracy warning message for power measurements
POWER_ACCURACY_WARNING = (
    "WARNING: Inverter power measurements are typically 10%-30% higher than actual values. "
    "Do not rely on this data for accurate energy calculations."
)

# List of sensor keys that require technician account access
TECHNICIAN_ONLY_SENSORS = [
    "technical_status.operationMode",
    "technical_status.gridVoltage",
    "technical_status.gridFrequency",
    "technical_status.currentToGrid",
    "technical_status.inverterPower",
    "technical_status.inverterTemperature",
    "technical_status.busVoltage",
    "technical_status.gridCode",
    "technical_status.dcCurrentInjectionR",
    "technical_status.dcCurrentInjectionS",
    "technical_status.dcCurrentInjectionT",
    "technical_status.inverterModel",
    "technical_status.inverterPowerRating",
    "technical_status.pv1Voltage",
    "technical_status.pv1Current",
    "technical_status.pv2Voltage",
    "technical_status.pv2Current",
    "technical_status.bmsVoltage",
    "technical_status.bmsCurrent",
    "technical_status.bmsTemperature",
    "technical_status.bmsAvgTemperature",
    "technical_status.bmsMaxTemperature",
    "technical_status.bmsMinTemperature",
    "technical_status.bmsTotalCharge",
    "technical_status.bmsTotalDischarge",
    "technical_status.bmsStateOfCharge",
    "technical_status.bmsState",
    "technical_status.bmsFaultCode",
    "technical_status.bmsHighestCellVoltage",
    "technical_status.bmsLowestCellVoltage",
    "technical_status.bmsCellVoltageDelta",  # Calculated from highest/lowest
    "technical_status.tidaProtocolVersion",
    "technical_status.invBootloaderVersion",
    # Maintenance diagnostics sensors (also require technician account)
    "maintenance_diagnostics.ramUsage.total",
    "maintenance_diagnostics.ramUsage.used",
    "maintenance_diagnostics.cpuUsage.used",
]
