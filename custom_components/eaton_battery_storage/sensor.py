"""Sensor entities for Eaton xStorage Home battery integration.

IMPORTANT ACCURACY WARNING:
The built-in inverter energy monitoring has poor accuracy and typically reports
power output/consumption values approximately 10%-30% higher than actual values.
This affects all power-related data in Home Assistant including:
- Grid power values
- Load consumption values
- PV production metrics
- Self-consumption calculations
- All 30-day and daily metrics

Users should rely on external power monitoring devices for accurate energy data.
Do not rely on consumption and production metrics from the inverter for accurate
energy calculations. This affects all power-related sensors including:
- Grid power values
- Load consumption values
- PV production metrics
- Self-consumption calculations
- All 30-day and daily metrics

Sensors with accuracy issues are marked with accuracy_warning=True in SENSOR_TYPES.
30-day metrics are disabled by default due to these accuracy concerns.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ACCOUNT_TYPE_TECHNICIAN,
    BMS_FAULT_CODE_MAP,
    BMS_NO_FAULT,
    BMS_STATE_MAP,
    CONF_HAS_PV,
    CONF_USER_TYPE,
    CURRENT_MODE_ACTION_MAP,
    CURRENT_MODE_COMMAND_MAP,
    CURRENT_MODE_RECURRENCE_MAP,
    CURRENT_MODE_TYPE_MAP,
    NOTIFICATION_SUBTYPE_MAP,
    OPERATION_MODE_MAP,
    POWER_ACCURACY_WARNING,
    TECHNICIAN_ONLY_SENSORS,
    resolve_mode_command,
    sensor_unique_id,
)
from .coordinator import EatonConfigEntry, EatonXstorageHomeCoordinator
from .entity import EatonEntity

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)

CELL_VOLTAGE_DELTA_KEY = "technical_status.bmsCellVoltageDelta"
BMS_FAULT_CODE_KEY = "technical_status.bmsFaultCode"
CURRENT_MODE_COMMAND_KEY = "status.currentMode.command"

# The BMS reports cell voltages in mV; a lower reading is a sensor error.
MIN_CELL_VOLTAGE_MV = 1000
CELL_VOLTAGE_KEYS = frozenset(
    {
        "technical_status.bmsHighestCellVoltage",
        "technical_status.bmsLowestCellVoltage",
    }
)

# These sensors report 0 when the device has no reading rather than a real zero.
ZERO_IS_INVALID_KEYS = frozenset(
    {
        "technical_status.bmsMaxTemperature",
        "technical_status.bmsMinTemperature",
        "technical_status.bmsAvgTemperature",
        "technical_status.bmsTotalCharge",
        "technical_status.bmsTotalDischarge",
        "technical_status.bmsVoltage",
        "technical_status.gridFrequency",
    }
)

# Sensor keys whose raw string value has a human-readable label.
VALUE_MAPS: dict[str, dict[str, str]] = {
    "status.currentMode.command": CURRENT_MODE_COMMAND_MAP,
    "status.currentMode.parameters.action": CURRENT_MODE_ACTION_MAP,
    "status.currentMode.type": CURRENT_MODE_TYPE_MAP,
    "status.currentMode.recurrence": CURRENT_MODE_RECURRENCE_MAP,
    "status.energyFlow.operationMode": OPERATION_MODE_MAP,
    "technical_status.operationMode": OPERATION_MODE_MAP,
    "technical_status.bmsState": BMS_STATE_MAP,
    "status.energyFlow.batteryStatus": BMS_STATE_MAP,
}


def _value_at(data: dict[str, Any], key: str) -> Any:
    """Return the scalar at a dotted key path, or None if there is none."""
    value: Any = data
    for part in key.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return None if isinstance(value, dict) else value


def _format_fault_codes(value: Any) -> Any:
    """Render the BMS fault codes, which arrive as a list or null when healthy."""
    if value is None:
        return BMS_NO_FAULT
    if not isinstance(value, list):
        return value
    return (
        ", ".join(BMS_FAULT_CODE_MAP.get(code, str(code)) for code in value)[:255]
        or BMS_NO_FAULT
    )


def _cell_voltage_delta(technical_status: dict[str, Any]) -> float | None:
    """Return the spread between the highest and lowest cell voltage."""
    highest = technical_status.get("bmsHighestCellVoltage")
    lowest = technical_status.get("bmsLowestCellVoltage")
    if highest is None or lowest is None:
        _LOGGER.debug(
            "Cell voltage delta needs both readings, got %s and %s", highest, lowest
        )
        return None

    try:
        highest, lowest = float(highest), float(lowest)
    except (TypeError, ValueError):
        _LOGGER.error("Cell voltages are not numeric: %s and %s", highest, lowest)
        return None

    if min(highest, lowest) < MIN_CELL_VOLTAGE_MV:
        _LOGGER.error(
            "Cell voltage below %smV, delta not calculated: %s and %s",
            MIN_CELL_VOLTAGE_MV,
            highest,
            lowest,
        )
        return None

    return round(highest - lowest, 1)


def _is_device_time(value: Any) -> bool:
    """Return True when the value looks like the HHMM the API reports."""
    return isinstance(value, int) or (isinstance(value, str) and value.isdigit())


def _format_device_time(value: int | str) -> str | None:
    """Format an HHMM reading as HH:MM, or None when it is out of range."""
    hour, minute = divmod(int(value), 100)
    if 0 <= hour < 24 and 0 <= minute < 60:
        return f"{hour:02d}:{minute:02d}"
    return None


def _translation_key_from_key(key: str) -> str:
    """Build a stable translation key from a sensor data key."""
    return key.replace(".", "_").replace("-", "_").lower()


# Every device class Home Assistant accepts a state class for, per its own
# DEVICE_CLASS_STATE_CLASSES. Sensors carrying a device class not listed here,
# and sensors with none at all, need an explicit "state_class" in SENSOR_TYPES.
DEVICE_CLASS_STATE_CLASSES: dict[str, SensorStateClass] = {
    "apparent_power": SensorStateClass.MEASUREMENT,
    "battery": SensorStateClass.MEASUREMENT,
    "current": SensorStateClass.MEASUREMENT,
    "energy": SensorStateClass.TOTAL_INCREASING,
    "energy_storage": SensorStateClass.MEASUREMENT,
    "frequency": SensorStateClass.MEASUREMENT,
    "power": SensorStateClass.MEASUREMENT,
    "temperature": SensorStateClass.MEASUREMENT,
    "voltage": SensorStateClass.MEASUREMENT,
}

# The BMS reports its coulomb counters in ampere hours. Home Assistant has no
# device class or unit constant for charge, so these carry neither.
AMPERE_HOUR = "Ah"


SENSOR_TYPES: dict[str, dict[str, Any]] = {
    # status endpoint
    "status.currentMode.command": {
        "name": "Current Mode Command",
        "unit": None,
        "device_class": None,
        "entity_category": None,
        "icon": "mdi:gesture-tap-button",
    },
    "status.currentMode.duration": {
        "name": "Current Mode Duration",
        "unit": "h",
        "device_class": "duration",
        "entity_category": None,
        "icon": "mdi:timer-outline",
    },
    "status.currentMode.startTime": {
        "name": "Current Mode Start Time",
        "unit": None,
        "device_class": None,
        "entity_category": None,
        "icon": "mdi:clock-start",
    },
    "status.currentMode.endTime": {
        "name": "Current Mode End Time",
        "unit": None,
        "device_class": None,
        "entity_category": None,
        "icon": "mdi:clock-end",
    },
    "status.currentMode.recurrence": {
        "name": "Current Mode Recurrence",
        "unit": None,
        "device_class": None,
        "entity_category": None,
        "icon": "mdi:calendar-refresh",
    },
    "status.currentMode.type": {
        "name": "Current Mode Type",
        "unit": None,
        "device_class": None,
        "entity_category": None,
        "icon": "mdi:format-list-bulleted-type",
    },
    "status.currentMode.parameters.action": {
        "name": "Current Mode Action",
        "unit": None,
        "device_class": None,
        "entity_category": None,
        "icon": "mdi:play-outline",
    },
    "status.currentMode.parameters.power": {
        "name": "Current Mode Power",
        "unit": PERCENTAGE,
        "device_class": None,
        "entity_category": None,
        "state_class": None,
        "icon": "mdi:flash",
    },
    "status.currentMode.parameters.soc": {
        "name": "Current Mode SOC",
        "unit": PERCENTAGE,
        "device_class": "battery",
        "entity_category": None,
        "state_class": None,
    },
    "status.energyFlow.acPvRole": {
        "name": "AC PV Role",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
        "icon": "mdi:solar-power",
    },
    # WARNING: Inverter power measurements are typically 10%-30% higher than actual values - accuracy is poor
    "status.energyFlow.acPvValue": {
        "name": "AC PV Value",
        "unit": UnitOfPower.WATT,
        "device_class": "power",
        "entity_category": None,
        "pv_related": True,
        "accuracy_warning": True,
    },
    "status.energyFlow.batteryBackupLevel": {
        "name": "Battery Backup Level",
        "unit": PERCENTAGE,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart-outline",
    },
    "status.energyFlow.batteryStatus": {
        "name": "Battery Status",
        "unit": None,
        "device_class": None,
        "entity_category": None,
        "icon": "mdi:battery",
    },
    "status.energyFlow.batteryEnergyFlow": {
        "name": "Battery Power",
        "unit": UnitOfPower.WATT,
        "device_class": "power",
        "entity_category": None,
    },
    "status.energyFlow.criticalLoadRole": {
        "name": "Critical Load Role",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:alert-octagon-outline",
    },
    # WARNING: Inverter power measurements are typically 10%-30% higher than actual values - accuracy is poor
    "status.energyFlow.criticalLoadValue": {
        "name": "Critical Load Value",
        "unit": UnitOfPower.WATT,
        "device_class": "power",
        "entity_category": None,
        "accuracy_warning": True,
    },
    "status.energyFlow.dcPvRole": {
        "name": "DC PV Role",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
        "icon": "mdi:solar-power",
    },
    # WARNING: Inverter power measurements are typically 10%-30% higher than actual values - accuracy is poor
    "status.energyFlow.dcPvValue": {
        "name": "DC PV Value",
        "unit": UnitOfPower.WATT,
        "device_class": "power",
        "entity_category": None,
        "pv_related": True,
        "accuracy_warning": True,
    },
    "status.energyFlow.gridRole": {
        "name": "Grid Role",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:transmission-tower",
    },
    # WARNING: Inverter power measurements are typically 10%-30% higher than actual values - accuracy is poor
    "status.energyFlow.gridValue": {
        "name": "Grid Power",
        "unit": UnitOfPower.WATT,
        "device_class": "power",
        "entity_category": None,
        "accuracy_warning": True,
    },
    "status.energyFlow.nonCriticalLoadRole": {
        "name": "Non-Critical Load Role",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:power-socket",
    },
    # WARNING: Inverter power measurements are typically 10%-30% higher than actual values - accuracy is poor
    "status.energyFlow.nonCriticalLoadValue": {
        "name": "Non-Critical Load Value",
        "unit": UnitOfPower.WATT,
        "device_class": "power",
        "entity_category": None,
        "accuracy_warning": True,
    },
    "status.energyFlow.operationMode": {
        "name": "Operation Mode",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:cog-outline",
    },
    # WARNING: Inverter power measurements are typically 10%-30% higher than actual values - accuracy is poor
    # The API reports this as a percentage of generated energy used directly,
    # not as a power reading.
    "status.energyFlow.selfConsumption": {
        "name": "Self Consumption",
        "unit": PERCENTAGE,
        "device_class": None,
        "entity_category": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "accuracy_warning": True,
        "icon": "mdi:home-lightning-bolt",
    },
    "status.energyFlow.selfSufficiency": {
        "name": "Self Sufficiency",
        "unit": PERCENTAGE,
        "device_class": None,
        "entity_category": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:gauge",
    },
    "status.energyFlow.stateOfCharge": {
        "name": "Battery State of Charge",
        "unit": PERCENTAGE,
        "device_class": "battery",
        "entity_category": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "status.energyFlow.energySavingModeEnabled": {
        "name": "Energy Saving Mode Enabled",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:leaf",
    },
    "status.energyFlow.energySavingModeActivated": {
        "name": "Energy Saving Mode Activated",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:leaf-circle",
    },
    # WARNING: 30-day metrics disabled by default - inverter measurements are typically 10%-30% higher than actual values
    # A rolling window's absolute value is what matters, not its growth, so TOTAL
    # is wrong; MEASUREMENT is barred for the energy device class, hence none.
    "status.last30daysEnergyFlow.gridConsumption": {
        "name": "30 Days Grid Consumption",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": "energy",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "state_class": None,
        "accuracy_warning": True,
    },
    "status.last30daysEnergyFlow.photovoltaicProduction": {
        "name": "30 Days PV Production",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": "energy",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
        "disabled_by_default": True,
        "state_class": None,
        "accuracy_warning": True,
    },
    "status.last30daysEnergyFlow.selfConsumption": {
        "name": "30 Days Self Consumption",
        "unit": PERCENTAGE,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "state_class": SensorStateClass.MEASUREMENT,
        "accuracy_warning": True,
        "icon": "mdi:calendar-clock",
    },
    "status.last30daysEnergyFlow.selfSufficiency": {
        "name": "30 Days Self Sufficiency",
        "unit": PERCENTAGE,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "state_class": SensorStateClass.MEASUREMENT,
        "accuracy_warning": True,
        "icon": "mdi:calendar-gauge",
    },
    # WARNING: Today's metrics also affected by inverter accuracy issues
    "status.today.gridConsumption": {
        "name": "Today's Grid Consumption",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": "energy",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "accuracy_warning": True,
    },
    "status.today.photovoltaicProduction": {
        "name": "Today's PV Production",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": "energy",
        "entity_category": None,
        "pv_related": True,
        "accuracy_warning": True,
    },
    "status.today.selfConsumption": {
        "name": "Today's Self Consumption",
        "unit": PERCENTAGE,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "state_class": SensorStateClass.MEASUREMENT,
        "accuracy_warning": True,
        "icon": "mdi:clock-outline",
    },
    "status.today.selfSufficiency": {
        "name": "Today's Self Sufficiency",
        "unit": PERCENTAGE,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "state_class": SensorStateClass.MEASUREMENT,
        "accuracy_warning": True,
        "icon": "mdi:clock-check-outline",
    },
    # device endpoint
    "device.firmwareVersion": {
        "name": "Firmware Version",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:chip",
    },
    "device.inverterFirmwareVersion": {
        "name": "Inverter Firmware Version",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:chip",
    },
    "device.bmsFirmwareVersion": {
        "name": "BMS Firmware Version",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:chip",
    },
    "device.energySavingMode.houseConsumptionThreshold": {
        "name": "House Consumption Threshold",
        "unit": UnitOfPower.WATT,
        "device_class": "power",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
    },
    "device.inverterManufacturer": {
        "name": "Inverter Manufacturer",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:factory",
    },
    "device.inverterModelName": {
        "name": "Inverter Model Name",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:identifier",
    },
    "device.inverterVaRating": {
        "name": "Inverter VA Rating",
        "unit": "VA",
        "device_class": "apparent_power",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "state_class": None,
    },
    "device.inverterSerialNumber": {
        "name": "Inverter Serial Number",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:barcode",
    },
    "device.inverterNominalVpv": {
        "name": "Inverter Nominal VPV",
        "unit": "V",
        "device_class": "voltage",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
        "disabled_by_default": True,
    },
    "device.bmsCapacity": {
        "name": "BMS Capacity",
        "unit": "kWh",
        "device_class": "energy_storage",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
    },
    "device.bmsSerialNumber": {
        "name": "BMS Serial Number",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:barcode",
    },
    "device.bmsModel": {
        "name": "BMS Model",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:identifier",
    },
    "device.bundleVersion": {
        "name": "Bundle Version",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:package-variant",
    },
    "device.localPortalRemoteId": {
        "name": "Local Portal Remote ID",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:remote-desktop",
    },
    "device.dns": {
        "name": "DNS Server",
        "unit": None,
        "device_class": None,
        "disabled_by_default": True,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:dns",
    },
    "device.timezone.name": {
        "name": "Device Timezone",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:earth",
    },
    # technical status endpoint - requires technician account
    "technical_status.operationMode": {
        "name": "Technical Operation Mode",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:cog-outline",
    },
    "technical_status.gridVoltage": {
        "name": "Grid Voltage",
        "unit": "V",
        "device_class": "voltage",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.gridFrequency": {
        "name": "Grid Frequency",
        "unit": "Hz",
        "device_class": "frequency",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.currentToGrid": {
        "name": "Current To Grid",
        "unit": "A",
        "device_class": "current",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.inverterPower": {
        "name": "Inverter Power",
        "unit": UnitOfPower.WATT,
        "device_class": "power",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.inverterTemperature": {
        "name": "Inverter Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.busVoltage": {
        "name": "Bus Voltage",
        "unit": "V",
        "device_class": "voltage",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.gridCode": {
        "name": "Grid Code",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:code-tags",
    },
    "technical_status.dcCurrentInjectionR": {
        "name": "DC Current Injection R",
        "unit": "A",
        "device_class": "current",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
    },
    "technical_status.dcCurrentInjectionS": {
        "name": "DC Current Injection S",
        "unit": "A",
        "device_class": "current",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
    },
    "technical_status.dcCurrentInjectionT": {
        "name": "DC Current Injection T",
        "unit": "A",
        "device_class": "current",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
    },
    "technical_status.inverterModel": {
        "name": "Technical Inverter Model",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:identifier",
    },
    # Reads a constant 0 on at least the 3.6kW unit, so it is not a statistic.
    "technical_status.inverterPowerRating": {
        "name": "Technical Inverter Power Rating",
        "unit": UnitOfPower.WATT,
        "device_class": "power",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "state_class": None,
    },
    "technical_status.pv1Voltage": {
        "name": "PV1 Voltage",
        "unit": "V",
        "device_class": "voltage",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
    },
    "technical_status.pv1Current": {
        "name": "PV1 Current",
        "unit": "A",
        "device_class": "current",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
    },
    "technical_status.pv2Voltage": {
        "name": "PV2 Voltage",
        "unit": "V",
        "device_class": "voltage",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
    },
    "technical_status.pv2Current": {
        "name": "PV2 Current",
        "unit": "A",
        "device_class": "current",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "pv_related": True,
    },
    "technical_status.bmsVoltage": {
        "name": "BMS Voltage",
        "unit": "V",
        "device_class": "voltage",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.bmsCurrent": {
        "name": "BMS Current",
        "unit": "A",
        "device_class": "current",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.bmsTemperature": {
        "name": "BMS Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.bmsAvgTemperature": {
        "name": "BMS Average Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.bmsMaxTemperature": {
        "name": "BMS Max Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.bmsMinTemperature": {
        "name": "BMS Min Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    # Lifetime counters that never reset, so TOTAL rather than TOTAL_INCREASING.
    "technical_status.bmsTotalCharge": {
        "name": "BMS Total Charge",
        "unit": AMPERE_HOUR,
        "device_class": None,
        "precision": 0,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "state_class": SensorStateClass.TOTAL,
    },
    "technical_status.bmsTotalDischarge": {
        "name": "BMS Total Discharge",
        "unit": AMPERE_HOUR,
        "device_class": None,
        "precision": 0,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "state_class": SensorStateClass.TOTAL,
    },
    "technical_status.bmsStateOfCharge": {
        "name": "Technical BMS State of Charge",
        "unit": PERCENTAGE,
        "device_class": "battery",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "technical_status.bmsState": {
        "name": "BMS State",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:battery",
    },
    "technical_status.bmsFaultCode": {
        "name": "BMS Fault Code",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:alert-circle-outline",
    },
    "technical_status.bmsHighestCellVoltage": {
        "name": "BMS Highest Cell Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "precision": 0,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.bmsLowestCellVoltage": {
        "name": "BMS Lowest Cell Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "precision": 0,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.bmsCellVoltageDelta": {
        "name": "BMS Cell Voltage Delta",
        "unit": "mV",
        "device_class": "voltage",
        "precision": 0,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "technical_status.tidaProtocolVersion": {
        "name": "TIDA Protocol Version",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:protocol",
    },
    "technical_status.invBootloaderVersion": {
        "name": "Inverter Bootloader Version",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "disabled_by_default": True,
        "icon": "mdi:chip",
    },
    # maintenance diagnostics endpoint - requires technician account
    "maintenance_diagnostics.ramUsage.total": {
        "name": "System RAM Total",
        "unit": "MB",
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:memory",
    },
    "maintenance_diagnostics.ramUsage.used": {
        "name": "System RAM Used",
        "unit": "MB",
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:memory",
    },
    "maintenance_diagnostics.cpuUsage.used": {
        "name": "System CPU Usage",
        "unit": PERCENTAGE,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:cpu-64-bit",
    },
    # notification endpoints
    "unread_notifications_count.total": {
        "name": "Unread Notifications Count",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:bell-badge-outline",
    },
    "notifications.total": {
        "name": "Total Notifications Count",
        "unit": None,
        "device_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:bell-outline",
    },
}


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: EatonConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Eaton xStorage Home sensor platform."""
    coordinator = config_entry.runtime_data
    has_pv = config_entry.data.get(CONF_HAS_PV, False)
    is_technician = (
        config_entry.data.get(CONF_USER_TYPE, ACCOUNT_TYPE_TECHNICIAN)
        == ACCOUNT_TYPE_TECHNICIAN
    )

    # Create sensors based on account type and PV configuration
    entities: list[
        EatonXStorageSensor
        | EatonXStorageNotificationsSensor
        | EatonXStorageLatestNotificationSensor
        | EatonXStorageInverterInfoSensor
        | EatonXStorageBmsInfoSensor
        | EatonXStorageDeviceInfoSensor
        | EatonXStorageTechnicalInfoSensor
    ] = []
    for key, description in SENSOR_TYPES.items():
        # Skip PV-related sensors if has_pv is False
        if description.get("pv_related", False) and not has_pv:
            continue

        # Skip technician-only sensors for customer accounts
        if key in TECHNICIAN_ONLY_SENSORS and not is_technician:
            continue

        entities.append(EatonXStorageSensor(coordinator, key, description, has_pv))

    # Add the notifications array sensor
    entities.append(EatonXStorageNotificationsSensor(coordinator))
    entities.append(EatonXStorageLatestNotificationSensor(coordinator))

    # Static identity fields grouped into a few sensors instead of one each
    entities.append(EatonXStorageInverterInfoSensor(coordinator, has_pv))
    entities.append(EatonXStorageBmsInfoSensor(coordinator))
    entities.append(EatonXStorageDeviceInfoSensor(coordinator))
    if is_technician:
        entities.append(EatonXStorageTechnicalInfoSensor(coordinator))

    async_add_entities(entities)


class EatonXStorageNotificationsSensor(EatonEntity, SensorEntity):
    """Sensor for displaying notifications array."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "notifications"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the notifications sensor."""
        super().__init__(coordinator)
        # Scope unique ID to config entry for multi-device support
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_notifications"

    @property
    def native_value(self) -> int:
        """Return the total number of notifications as the state."""
        try:
            notifications_data = self.coordinator.data.get("notifications", {})
            return notifications_data.get("total", 0)
        except (KeyError, TypeError, AttributeError) as err:
            _LOGGER.error("Error retrieving notifications state: %s", err)
            return 0

    @property
    def extra_state_attributes(self):
        """Return notifications as attributes."""
        try:
            notifications_data = self.coordinator.data.get("notifications", {})
            results = notifications_data.get("results", [])

            # Format notifications for better readability
            formatted_notifications = []
            for notification in results:
                formatted_notifications.append(
                    {
                        "alert_id": notification.get("alertId"),
                        "level": notification.get("level"),
                        "type": notification.get("type"),
                        "sub_type": notification.get("subType"),
                        "status": notification.get("status"),
                        "created_at": notification.get("createdAt"),
                        "updated_at": notification.get("updatedAt"),
                    }
                )

            return {
                "notifications": formatted_notifications,
                "total": notifications_data.get("total", 0),
                "start": notifications_data.get("start", 0),
                "size": notifications_data.get("size", 0),
            }
        except (KeyError, TypeError, AttributeError) as e:
            _LOGGER.error("Error retrieving notifications attributes: %s", e)
            return {}


class EatonXStorageLatestNotificationSensor(EatonEntity, SensorEntity):
    """Sensor exposing the most recent notification's type as its state."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "latest_notification"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the latest notification sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_latest_notification"
        )

    def _latest_notification(self) -> dict[str, Any] | None:
        """Return the most recent notification, if any."""
        notifications_data = self.coordinator.data.get("notifications", {})
        results = notifications_data.get("results", [])
        return results[0] if results else None

    @property
    def native_value(self) -> str | None:
        """Return the most recent notification's description as the state."""
        try:
            notification = self._latest_notification()
            if not notification:
                return None
            sub_type = notification.get("subType") or notification.get("type")
            if not sub_type:
                return None
            mapped = NOTIFICATION_SUBTYPE_MAP.get(sub_type)
            return mapped["description"] if mapped else sub_type
        except (KeyError, TypeError, AttributeError) as err:
            _LOGGER.error("Error retrieving latest notification state: %s", err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the remaining notification details as attributes."""
        try:
            notification = self._latest_notification()
            if not notification:
                return None
            sub_type = notification.get("subType")
            mapped = NOTIFICATION_SUBTYPE_MAP.get(sub_type or "", {})
            return {
                "raw_sub_type": sub_type,
                "remedy": mapped.get("remedy"),
                "alert_id": notification.get("alertId"),
                "level": notification.get("level"),
                "type": notification.get("type"),
                "status": notification.get("status"),
                "created_at": notification.get("createdAt"),
                "updated_at": notification.get("updatedAt"),
            }
        except (KeyError, TypeError, AttributeError) as err:
            _LOGGER.error("Error retrieving latest notification attributes: %s", err)
            return None


class EatonXStorageInverterInfoSensor(EatonEntity, SensorEntity):
    """Sensor grouping static inverter identity fields as attributes."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "inverter_info"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator, has_pv: bool) -> None:
        """Initialize the inverter info sensor."""
        super().__init__(coordinator)
        self._has_pv = has_pv
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_inverter_info"

    @property
    def native_value(self) -> str | None:
        """Return the inverter firmware version as the state."""
        device = (self.coordinator.data or {}).get("device", {})
        return device.get("inverterFirmwareVersion")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the remaining static inverter fields as attributes."""
        device = (self.coordinator.data or {}).get("device", {})
        attributes = {"va_rating": device.get("inverterVaRating")}
        if self._has_pv:
            attributes["nominal_vpv"] = device.get("inverterNominalVpv")
        return attributes


class EatonXStorageBmsInfoSensor(EatonEntity, SensorEntity):
    """Sensor grouping static BMS identity fields as attributes."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "bms_info"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the BMS info sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_bms_info"

    @property
    def native_value(self) -> str | None:
        """Return the BMS model as the state."""
        device = (self.coordinator.data or {}).get("device", {})
        return device.get("bmsModel")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the remaining static BMS fields as attributes."""
        device = (self.coordinator.data or {}).get("device", {})
        return {
            "serial_number": device.get("bmsSerialNumber"),
            "capacity_kwh": device.get("bmsCapacity"),
        }


class EatonXStorageDeviceInfoSensor(EatonEntity, SensorEntity):
    """Sensor grouping static device/network identity fields as attributes."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "device_info"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the device info sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_device_info"

    @property
    def native_value(self) -> str | None:
        """Return the bundle version as the state."""
        device = (self.coordinator.data or {}).get("device", {})
        return device.get("bundleVersion")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the remaining static device fields as attributes."""
        device = (self.coordinator.data or {}).get("device", {})
        return {
            "local_portal_remote_id": device.get("localPortalRemoteId"),
            "timezone": (device.get("timezone") or {}).get("name"),
        }


class EatonXStorageTechnicalInfoSensor(EatonEntity, SensorEntity):
    """Sensor grouping static technician-only identity fields as attributes."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "technical_info"

    def __init__(self, coordinator: EatonXstorageHomeCoordinator) -> None:
        """Initialize the technical info sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_technical_info"

    @property
    def native_value(self) -> str | None:
        """Return the grid code as the state."""
        technical_status = (self.coordinator.data or {}).get("technical_status", {})
        return technical_status.get("gridCode")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the remaining static technical fields as attributes."""
        technical_status = (self.coordinator.data or {}).get("technical_status", {})
        maintenance_diagnostics = (self.coordinator.data or {}).get(
            "maintenance_diagnostics", {}
        )
        ram_total = maintenance_diagnostics.get("ramUsage", {}).get("total")
        return {
            "inverter_power_rating": technical_status.get("inverterPowerRating"),
            "bootloader_version": technical_status.get("invBootloaderVersion"),
            "system_ram_total_mb": (
                round(ram_total / 1024 / 1024, 2) if ram_total is not None else None
            ),
        }


class EatonXStorageSensor(EatonEntity, SensorEntity):
    """Eaton xStorage Home sensor entity."""

    def __init__(
        self,
        coordinator: EatonXstorageHomeCoordinator,
        key: str,
        description: dict[str, Any],
        _has_pv: bool,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        # Be robust to missing fields in description
        self._attr_translation_key = _translation_key_from_key(self._key)
        self._attr_native_unit_of_measurement = description.get("unit")
        self._attr_device_class = description.get("device_class")
        self._attr_entity_category = description.get("entity_category")
        self._attr_entity_registry_enabled_default = not description.get(
            "disabled_by_default", False
        )
        self._accuracy_warning = description.get("accuracy_warning", False)
        self._precision = description.get("precision")
        # Ensure per-entry unique IDs to avoid collisions across multiple devices
        self._attr_unique_id = sensor_unique_id(coordinator.config_entry.entry_id, key)

        # Apply icon from description if provided
        if description.get("icon"):
            self._attr_icon = description["icon"]

        # An explicit state_class wins, including an explicit None for setpoints
        # and static ratings that would otherwise be recorded as statistics.
        if "state_class" in description:
            self._attr_state_class = description["state_class"]
        elif (device_class := description["device_class"]) is not None:
            self._attr_state_class = DEVICE_CLASS_STATE_CLASSES.get(device_class)

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current value of the sensor."""
        data = self.coordinator.data or {}

        if self._key == CELL_VOLTAGE_DELTA_KEY:
            return _cell_voltage_delta(data.get("technical_status", {}))

        if self._key == CURRENT_MODE_COMMAND_KEY:
            value = resolve_mode_command(data.get("status", {}).get("currentMode", {}))
        else:
            value = _value_at(data, self._key)

        if self._key == BMS_FAULT_CODE_KEY:
            return _format_fault_codes(value)

        if value is None:
            return None

        if (
            self._key in CELL_VOLTAGE_KEYS
            and isinstance(value, (int, float))
            and value < MIN_CELL_VOLTAGE_MV
        ):
            _LOGGER.error(
                "Cell voltage %s below %smV, treating as a read error: %smV",
                self._key,
                MIN_CELL_VOLTAGE_MV,
                value,
            )
            return None

        if (
            self._key in ZERO_IS_INVALID_KEYS
            and isinstance(value, (int, float))
            and value == 0
        ):
            _LOGGER.debug("Sensor %s returned invalid value 0 - ignoring", self._key)
            return None

        if (labels := VALUE_MAPS.get(self._key)) is not None and isinstance(value, str):
            return labels.get(value, value)

        if self._attr_device_class == "temperature" and isinstance(value, (int, float)):
            return round(value, 1)

        if self._key.endswith(("startTime", "endTime")) and _is_device_time(value):
            return _format_device_time(value) or value

        if "ramUsage" in self._key and isinstance(value, (int, float)):
            return round(value / 1024 / 1024, 2)

        if "cpuUsage.used" in self._key and isinstance(value, (int, float)):
            return round(value, 2)

        return value

    @property
    def suggested_display_precision(self) -> int | None:
        """Return the suggested number of decimal places for display."""
        # Use sensor-specific precision if defined
        if self._precision is not None:
            return self._precision

        # Temperature sensors: 1 decimal place
        if (
            self._attr_device_class == "temperature"
            or self._attr_device_class == "voltage"
        ):
            return 1
        # Current sensors: 2 decimal places
        if (
            self._attr_device_class == "current"
            or self._attr_device_class == "frequency"
        ):
            return 2
        # Power sensors: 0 decimal places (whole watts)
        if self._attr_device_class == "power":
            return 0
        # Energy sensors: 1 decimal place
        if (
            self._attr_device_class == "energy"
            or self._attr_device_class == "energy_storage"
        ):
            return 1
        # Apparent power (VA): 0 decimal places
        if (
            self._attr_device_class == "apparent_power"
            or self._attr_native_unit_of_measurement == PERCENTAGE
            or "ramUsage" in self._key
        ):
            return 0
        # CPU usage: 1 decimal place
        if "cpuUsage" in self._key:
            return 1
        # Default: no specific precision
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes for entities with accuracy warnings."""
        if self._key == "technical_status.bmsFaultCode":
            technical_status = (self.coordinator.data or {}).get("technical_status", {})
            codes = technical_status.get("bmsFaultCode")
            return {"fault_codes": codes if isinstance(codes, list) else []}
        if self._accuracy_warning:
            return {
                "accuracy_warning": POWER_ACCURACY_WARNING,
                "measurement_note": "Values typically 10%-30% higher than actual",
            }
        return None
