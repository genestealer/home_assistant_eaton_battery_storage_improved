# Changelog

All notable changes to this integration are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Implements the findings of [the 2026-08-01 code review](docs/code-review-2026-08-01.md).

### Added

- **Verify SSL certificate** option in the config, reauth and options flows. It defaults to
  off, matching the previous hardcoded behaviour, because the inverter ships a self-signed
  certificate. Turning it on makes Home Assistant validate the certificate for every request,
  including the credential exchange.
- Host validation in the config flow: values containing a scheme, path or whitespace are now
  rejected instead of being used to build a storage filename.
- Reauthentication is now actually reachable — the coordinator raises `ConfigEntryAuthFailed`
  when the device rejects the credentials, so Home Assistant prompts for new ones instead of
  leaving every entity unavailable.
- Test scaffolding: `requirements_test.txt`, ruff/mypy/pytest configuration in
  `pyproject.toml`, a `tests/` suite and a CI job that runs ruff, mypy and pytest on every
  pull request. The device is mocked at the HTTP boundary, so the tests exercise the real
  API client, coordinator and entity platforms rather than stand-ins for them.
- `entity.py` with a shared `EatonEntity` base class, replacing the twelve copies of
  `device_info` and `has_entity_name` spread across the platforms.
- Syrupy snapshot coverage of every entity on all seven platforms, so an accidental change
  to a unit, device class, entity category or state shows up as a snapshot diff.

### Changed

- **Device identity is now keyed on the inverter serial number.** The host-based identifier
  is removed from existing devices on upgrade, and the config entry unique ID is migrated
  from `{host}_{serial}` to the bare serial. A device that changes IP address now updates its
  host instead of appearing as a duplicate.
- Settings writes (energy saving mode, backup level, house consumption threshold, default
  operation mode) go through a single lock-protected read-modify-write helper, so two
  automations firing at the same time can no longer overwrite each other's changes.
- The coordinator fetches the optional endpoints concurrently instead of serially, and logs
  loss of connectivity once rather than on every failed refresh.
- Command entities no longer sleep 1–3 seconds inside the service call; they schedule a
  debounced refresh instead.
- The API layer signals failures with a dedicated exception hierarchy
  (`EatonAuthError`, `EatonConnectionError`, `EatonResponseError`, `EatonCommandError`)
  instead of a mix of `ValueError`, `ConnectionError` and error dictionaries. The config flow
  classifies authentication failures on the device error code rather than on English text.
- Select entities now raise a translated error when a command fails, instead of logging and
  reporting success.
- The sensor value handling no longer wraps ~180 lines in a single `try`/`except`. The
  lookups, fault-code rendering, cell-voltage delta and HHMM time formatting are separate
  helpers with targeted guards, so a genuine bug surfaces instead of being swallowed as
  "Error retrieving state". Two debug logs that fired on every state read were removed;
  the same data is available in the diagnostics download.
- The access token is stored under `{domain}.{entry_id}_token`, is read back on restart
  instead of being written and never used, and is deleted when the entry is removed.
- The `reload` service is registered once in `async_setup` instead of per config entry, and
  now requires an administrator, matching Home Assistant's own reload helper. Automations
  run as a non-admin user can no longer call it.
- `PARALLEL_UPDATES` is declared on every platform: `0` for the read-only ones, `1` for the
  command platforms.
- Password fields are no longer prefilled in the reauth and options forms.
- Saving the options form writes the entry once and reloads once, instead of twice.
- `quality_scale.yaml` now lists every rule through Platinum with an accurate status. The
  `"quality_scale": "bronze"` claim was removed from `manifest.json` until the remaining
  Bronze rules (brands, removal instructions) are met, since it was self-asserted and
  unverifiable for a custom component.

### Fixed

- System health no longer crashes when the first config entry is disabled or retrying setup.
- The PV sensor migration no longer re-enables sensors that the user disabled deliberately.
- Cell voltage sensors declare their display precision explicitly instead of relying on
  substring matching against the sensor key.
- The notification event entity no longer grows its "seen alerts" set without bound.
- The percentage/watt conversion for charge and discharge power now uses the inverter's
  reported power rating (`technical_status.inverterPowerRating`, falling back to
  `device.inverterVaRating` for customer accounts and to 3600 W if neither is available)
  instead of hardcoding 3600 W in six places. The watt sliders now span 5–100 % of that
  rating, so 4.6 kW and 6 kW models are no longer capped at 3600 W.

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
