# Changelog

All notable changes to this integration are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2026-08-11

### Added

- `sensor.eaton_xstorage_home_latest_notification`: readable description of the most recent
  notification (e.g. "The battery voltage is too high."), with `raw_sub_type`, `remedy`,
  `alert_id`, `level`, `type`, `status`, `created_at`, and `updated_at` attributes. Covers all
  51 documented notification `sub_type` values.
- `binary_sensor.eaton_xstorage_home_bms_fault`: `problem` device class, on when
  `technical_status.bmsFaultCode` reports a fault. Technician account only.
- `binary_sensor.eaton_xstorage_home_energy_saving_mode_activated`: mirrors
  `status.energyFlow.energySavingModeActivated`.
- Grouped diagnostic sensors consolidating static identity fields into attributes instead of
  one sensor each:
  - `sensor.eaton_xstorage_home_inverter_info` (state = inverter firmware version;
    attributes: `va_rating`, `nominal_vpv` on PV installs)
  - `sensor.eaton_xstorage_home_bms_info` (state = BMS model; attributes: `serial_number`,
    `capacity_kwh`)
  - `sensor.eaton_xstorage_home_device_info` (state = bundle version; attributes:
    `local_portal_remote_id`, `timezone`)
  - `sensor.eaton_xstorage_home_technical_info` (state = grid code; attributes:
    `inverter_power_rating`, `bootloader_version`, `system_ram_total_mb`). Technician account
    only.
- `BMS_FAULT_CODE_MAP` and `NOTIFICATION_SUBTYPE_MAP` in `const.py`, sourced from the
  [xStorage Home API documentation](https://github.com/genestealer/eaton-xstorage-home-api-doc).

### Changed

- `sensor.eaton_xstorage_home_bms_fault_code`: now renders readable fault text (e.g.
  "Over-voltage") instead of a stringified Python list, and reads "No fault" instead of
  `unknown` when the API reports no fault (`bmsFaultCode: null`). Raw codes are preserved in
  the `fault_codes` attribute.
- `sensor.eaton_xstorage_home_current_mode_start_time` / `_end_time`: switched from 12-hour
  `"11:54 am"` to 24-hour `"11:54"` formatting.
- `sensor.eaton_xstorage_home_current_mode_duration`: now reports a `duration` device class
  with unit `h`, matching the existing charge/discharge/run duration numbers.
- `sensor.eaton_xstorage_home_notifications`: state now reflects the true total notification
  count instead of the current page size.
- The following sensors are now diagnostic and disabled by default on new installs, since
  they duplicate another entity or the device registry, or rarely change:
  `status.energyFlow.operationMode`, `technical_status.operationMode`,
  `device.energySavingMode.houseConsumptionThreshold`, `technical_status.bmsStateOfCharge`,
  `technical_status.inverterModel`, `status.energyFlow.energySavingModeEnabled`,
  `status.energyFlow.energySavingModeActivated`, `device.firmwareVersion`,
  `device.bmsFirmwareVersion`, `device.inverterSerialNumber`, `device.inverterManufacturer`,
  `device.inverterModelName`, `device.inverterFirmwareVersion`, `device.inverterVaRating`,
  `device.inverterNominalVpv`, `device.bmsCapacity`, `device.bmsSerialNumber`,
  `device.bmsModel`, `device.bundleVersion`, `device.localPortalRemoteId`,
  `device.timezone.name`, `technical_status.gridCode`, `technical_status.inverterPowerRating`,
  `technical_status.invBootloaderVersion`. Existing installs are unaffected; only entities
  registered for the first time are hidden.
  `binary_sensor.eaton_xstorage_home_inverter_power_state` is likewise now disabled by
  default (duplicates `switch.eaton_xstorage_home_inverter_power`).
- Active-fault detection (`binary_sensor.eaton_xstorage_home_bms_fault`) requires a
  technician account; it is not created for customer accounts.

### Removed

- `GET /api/metrics` and `GET /api/metrics/daily` polling. These calls omitted the required
  `from`/`to` parameters and returned `400 Bad Request` on every poll cycle; no entity
  consumed the data.

## [0.2.2] and earlier

See git history prior to this file's creation.
