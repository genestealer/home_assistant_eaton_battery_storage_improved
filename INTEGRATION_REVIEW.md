# In-Depth Review: Eaton Battery Storage HACS Integration

**Review Date:** February 15, 2026  
**Integration Version:** 0.2.1  
**Reviewer:** GitHub Copilot (Claude Opus 4.5)

---

## Executive Summary

This is a **well-implemented HACS custom integration** with 70+ entities, proper async patterns, and good UX considerations. It follows most Home Assistant development guidelines correctly, but has notable gaps: **no tests**, **no diagnostics.py**, **no system_health.py**, some deprecated patterns (`datetime.utcnow()`), and code duplication. The claimed **Bronze quality scale is partially accurate** – most bronze requirements are met, but test coverage is completely missing.

---

## Table of Contents

1. [Integration Structure Compliance](#1-integration-structure-compliance)
2. [Config Flow Implementation](#2-config-flow-implementation)
3. [Data Fetching Patterns](#3-data-fetching-patterns)
4. [Async Patterns](#4-async-patterns)
5. [Entity Implementation](#5-entity-implementation)
6. [Services](#6-services)
7. [Integration Events](#7-integration-events)
8. [Setup Failures](#8-setup-failures)
9. [Documentation](#9-documentation)
10. [Testing](#10-testing)
11. [Missing Features](#11-missing-features-silvergold)
12. [CI/CD](#12-cicd)
13. [Improvement Roadmap](#13-improvement-roadmap)
14. [Code Quality Details](#14-code-quality-details)

---

## 1. Integration Structure Compliance

**Reference:** [Creating Integration File Structure](https://developers.home-assistant.io/docs/creating_integration_file_structure)

### File Structure

```
custom_components/eaton_battery_storage/
├── __init__.py          (157 lines) - Integration setup, platforms, PV sensor migration
├── api.py               (320 lines) - HTTP API client for Eaton xStorage Home
├── binary_sensor.py     (117 lines) - 4 binary sensors
├── button.py            (110 lines) - 2 button entities
├── config_flow.py       (356 lines) - ConfigFlow + OptionsFlow
├── const.py             (107 lines) - Constants, mappings, sensor lists
├── coordinator.py       (201 lines) - DataUpdateCoordinator
├── event.py             (135 lines) - Notification event entity
├── manifest.json        - Integration manifest
├── number_constants.py  (123 lines) - Number entity definitions
├── number.py            (488 lines) - 11 number entities
├── quality_scale.yaml   - Bronze quality scale progress
├── select.py            (376 lines) - 2 select entities
├── sensor.py            (1086 lines) - 70+ sensor types
├── services.yaml        - Empty (no custom services)
├── switch.py            (361 lines) - 2 switch entities
└── translations/
    └── en.json          - English translations
```

### File Compliance Matrix

| File | Status | Notes |
|------|--------|-------|
| `manifest.json` | ✅ Complete | All required fields present |
| `__init__.py` | ✅ Good | Proper setup flow |
| `config_flow.py` | ✅ Good | ConfigFlow + OptionsFlow |
| `const.py` | ✅ Good | Domain, mappings, sensor lists |
| `translations/` | ⚠️ Partial | Config strings only, missing entity strings |
| `diagnostics.py` | ❌ Missing | Required for debugging support |
| `system_health.py` | ❌ Missing | Recommended for integration health |
| `strings.json` | ❌ Missing | Should have strings.json as base |
| `tests/` | ❌ Missing | No test directory exists |

### Manifest Analysis

```json
{
  "domain": "eaton_battery_storage",
  "name": "Eaton xStorage Home Battery",
  "codeowners": ["@greyfold", "@genestealer"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/greyfold/home_assistant_eaton_battery_storage",
  "integration_type": "device",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/greyfold/home_assistant_eaton_battery_storage/issues",
  "loggers": ["eaton_battery_storage"],
  "quality_scale": "bronze",
  "requirements": [],
  "version": "0.2.1"
}
```

**Evaluation:**
- ✅ `domain`: `"eaton_battery_storage"` - follows naming conventions
- ✅ `iot_class`: `"local_polling"` - correct for local API polling
- ✅ `integration_type`: `"device"` - correct for hardware
- ✅ `config_flow`: `true`
- ✅ `version`: `"0.2.1"` - semver compliant
- ✅ `requirements`: `[]` - uses HA core aiohttp (no external deps)
- ⚠️ `quality_scale`: `"bronze"` - claim requires test coverage which is missing

---

## 2. Config Flow Implementation

**Reference:** [Config Entries Config Flow Handler](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)

### Strengths

```python
# config_flow.py - Good patterns observed:

class EatonXStorageConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> EatonXStorageOptionsFlow:
        return EatonXStorageOptionsFlow(config_entry)
```

- ✅ Uses `ConfigFlow` base class with proper domain decorator
- ✅ `VERSION = 1`, `MINOR_VERSION = 1` for future migrations
- ✅ Unique ID via `async_set_unique_id()` + `_abort_if_unique_id_configured()`
- ✅ Connection test before entry creation (`_test_connection()`)
- ✅ Options flow implemented via `async_get_options_flow()`
- ✅ Modern selectors: `sel.TextSelector()`, `sel.SelectSelector()`, `sel.BooleanSelector()`
- ✅ Conditional validation (inverter_sn only required for technician accounts)
- ✅ Multi-device support via host + serial unique ID

### Issues Found

#### Issue 2.1: Error Keys Contain Spaces/Special Characters
**Location:** `config_flow.py` lines 62-68  
**Severity:** Medium  
**Problem:**
```python
# Current (bad):
errors["base"] = "Error during authentication: 10"
errors["base"] = "Authentication failed: non-JSON response"

# Should be (good):
errors["base"] = "auth_error_locked"
errors["base"] = "auth_non_json_response"
```
Translation keys should be simple slugs, not full error messages.

#### Issue 2.2: Code Duplication
**Location:** `config_flow.py` lines 122-168 and 250-296  
**Severity:** Low  
**Problem:** `_test_connection()` is essentially duplicated between `EatonXStorageConfigFlow` and `EatonXStorageOptionsFlow`.  
**Recommendation:** Extract to shared helper function.

#### Issue 2.3: Missing Reauth Flow
**Severity:** Medium  
**Problem:** No `async_step_reauth()` method for credential refresh.  
**Recommendation:** Implement reauth flow per HA guidelines for when credentials expire.

---

## 3. Data Fetching Patterns

**Reference:** [Integration Fetching Data](https://developers.home-assistant.io/docs/integration_fetching_data)

### Coordinator Implementation

```python
# coordinator.py - Good implementation:

class EatonXstorageHomeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: EatonBatteryAPI, config_entry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Eaton xStorage Home",
            update_interval=timedelta(minutes=1),
            config_entry=config_entry,
        )
        self.api = api
        self.config_entry = config_entry  # ⚠️ Duplicate storage
```

### Data Fetching Strategy

```python
# Endpoints fetched in _async_update_data():
# Core (required): status, device
# Optional: config_state, settings, metrics, metrics_daily, schedule
# Technician-only: technical_status, maintenance_diagnostics
# Always: notifications, unread_notifications_count
```

### Strengths

- ✅ Inherits `DataUpdateCoordinator[dict[str, Any]]` with generic type
- ✅ `update_interval=timedelta(minutes=1)` - appropriate polling rate for battery status
- ✅ Passes `config_entry` to parent (modern pattern since HA 2024.x)
- ✅ `_async_update_data()` properly implemented with try/except
- ✅ Raises `UpdateFailed` for critical failures
- ✅ Graceful handling of optional endpoints (doesn't fail if non-critical endpoint unavailable)
- ✅ `device_info` property returns proper `DeviceInfo` object

### Issues Found

#### Issue 3.1: Duplicate Config Entry Storage
**Location:** `coordinator.py` lines 31-39  
**Severity:** Low  
**Problem:** `config_entry` is stored both via `super().__init__()` and explicitly on line 39.
```python
# config_entry is passed to parent AND stored again:
super().__init__(..., config_entry=config_entry)
self.config_entry = config_entry  # Unnecessary - already available via self.config_entry
```

#### Issue 3.2: Unused Property
**Location:** `coordinator.py` lines 42-51  
**Severity:** Low  
**Problem:** `battery_level` property is defined but never used anywhere in the codebase.

---

## 4. Async Patterns

**References:**
- [AsyncIO Working with Async](https://developers.home-assistant.io/docs/asyncio_working_with_async)
- [AsyncIO Thread Safety](https://developers.home-assistant.io/docs/asyncio_thread_safety)
- [AsyncIO Blocking Operations](https://developers.home-assistant.io/docs/asyncio_blocking_operations/)

### API Implementation Strengths

```python
# api.py - Good async patterns:

class EatonBatteryAPI:
    def __init__(self, ...):
        self.session = async_get_clientsession(hass)  # ✅ Proper session management
        self.timeout = aiohttp.ClientTimeout(total=15, connect=5)  # ✅ Proper timeout
        
    async def make_request(self, method: str, endpoint: str, **kwargs):
        # ✅ Fully async
        # ✅ asyncio.CancelledError propagated correctly
        # ✅ Token auto-refresh via ensure_token_valid()
```

- ✅ Fully async using `aiohttp`
- ✅ Uses `async_get_clientsession(hass)` for proper session lifecycle
- ✅ `asyncio.CancelledError` propagated correctly (not caught)
- ✅ Appropriate timeouts: `ClientTimeout(total=15, connect=5)`
- ✅ Token storage via `homeassistant.helpers.storage.Store`
- ✅ Automatic token refresh with `ensure_token_valid()`

### Critical Issues Found

#### Issue 4.1: Deprecated datetime.utcnow()
**Location:** `api.py` lines 100, 157  
**Severity:** High  
**Problem:**
```python
# Current (deprecated since Python 3.12):
self.token_expiration = datetime.utcnow() + timedelta(minutes=55)
if datetime.utcnow() >= self.token_expiration:

# Should be:
from datetime import timezone
self.token_expiration = datetime.now(timezone.utc) + timedelta(minutes=55)
if datetime.now(timezone.utc) >= self.token_expiration:
```
`datetime.utcnow()` is deprecated and returns a naive datetime. Use `datetime.now(timezone.utc)` for timezone-aware datetimes.

#### Issue 4.2: Fire-and-Forget Anti-Pattern
**Location:** `switch.py` lines 140, 144, 349, 353; `select.py` line 204  
**Severity:** High  
**Problem:**
```python
# Current (anti-pattern):
def turn_on(self, **kwargs) -> None:
    asyncio.create_task(self.async_turn_on(**kwargs))  # No error handling!

def turn_off(self, **kwargs) -> None:
    asyncio.create_task(self.async_turn_off(**kwargs))  # No error handling!
```

This pattern:
1. Creates orphan tasks without error handling
2. Exceptions in `async_turn_on` are silently lost
3. Violates HA guidelines for async patterns

**Recommendation:** Remove sync wrappers entirely. Home Assistant will call `async_turn_on()` directly if it exists. Or if sync is needed:
```python
def turn_on(self, **kwargs) -> None:
    asyncio.run_coroutine_threadsafe(
        self.async_turn_on(**kwargs), 
        self.hass.loop
    ).result()  # Blocks but handles errors
```

---

## 5. Entity Implementation

**Reference:** [Creating Platform Index](https://developers.home-assistant.io/docs/creating_platform_index)

### Platform Summary

| Platform | File | Entity Count | Lines | Compliance |
|----------|------|--------------|-------|------------|
| sensor | `sensor.py` | 70+ | 1086 | ✅ Good |
| binary_sensor | `binary_sensor.py` | 4 | 117 | ✅ Excellent |
| switch | `switch.py` | 2 | 361 | ⚠️ Async issues |
| select | `select.py` | 2 | 376 | ⚠️ Async issues |
| number | `number.py` | 11 | 488 | ✅ Good |
| button | `button.py` | 2 | 110 | ✅ Good |
| event | `event.py` | 1 | 135 | ✅ Modern pattern |

### Entity Best Practices Compliance

```python
# Example from binary_sensor.py - Excellent pattern:

@dataclass(kw_only=True, frozen=True)
class EatonBatteryStorageBinarySensorEntityDescription(BinarySensorEntityDescription):
    is_on_fn: Callable[[dict[str, Any]], bool | None]

class EatonBatteryStorageBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    entity_description: EatonBatteryStorageBinarySensorEntityDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info
```

**Compliance Checklist:**
- ✅ `_attr_has_entity_name = True` - modern naming pattern
- ✅ `CoordinatorEntity` used throughout all platforms
- ✅ `unique_id` scoped to entry: `f"{coordinator.config_entry.entry_id}_{key}"`
- ✅ Device classes properly applied (`SensorDeviceClass.POWER`, `ENERGY`, `BATTERY`, `TEMPERATURE`)
- ✅ State classes for long-term statistics (`SensorStateClass.MEASUREMENT`, `TOTAL_INCREASING`)
- ✅ Entity categories (`EntityCategory.DIAGNOSTIC`, `EntityCategory.CONFIG`)
- ✅ `device_info` returns coordinator's device info for device grouping
- ✅ `PARALLEL_UPDATES = 0` to prevent API overwhelm
- ✅ Dataclass entity descriptions for clean entity definitions

### Issues Found

#### Issue 5.1: Monolithic Sensor File
**Location:** `sensor.py`  
**Severity:** Low  
**Problem:** 1086 lines with 70+ sensor definitions in a single file.  
**Recommendation:** Split into logical groups or use dedicated constants file for sensor descriptions.

#### Issue 5.2: Settings Logic Duplication
**Location:** `switch.py`, `select.py`, `number.py`  
**Severity:** Medium  
**Problem:** Settings transformation and API update logic is duplicated across multiple entity platforms.  
**Recommendation:** Extract to shared helper module.

---

## 6. Services

**Reference:** [Dev 101 Services](https://developers.home-assistant.io/docs/dev_101_services)

### Current State

```yaml
# services.yaml - Currently empty (comments only):
# Services for Eaton Battery Storage integration
# This file defines available services that users can call
# Currently no custom services are defined
```

### Service Registration

```python
# __init__.py lines 106-109:
async def reload_service_handler(_call):
    await async_reload_integration_platforms(hass, DOMAIN, PLATFORMS)

hass.services.async_register(
    DOMAIN, SERVICE_RELOAD, reload_service_handler, schema=vol.Schema({})
)
```

### Assessment

- ✅ **Acceptable** - Custom services are not required when all functionality is available through entity controls
- ✅ All control exposed via switches, selects, numbers, and buttons
- ✅ `reload` service registered for development convenience
- ℹ️ Consider adding services for batch operations or complex scheduling in future

---

## 7. Integration Events

**Reference:** [Integration Events](https://developers.home-assistant.io/docs/integration_events)

### Event Entity Implementation

```python
# event.py - Modern EventEntity usage:

class EatonXStorageNotificationEvent(CoordinatorEntity, EventEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "notification_event"
    _attr_event_types = ["notification"]
    
    def _handle_coordinator_update(self) -> None:
        # Detect new notifications
        # Fire events for unseen alerts
        self._trigger_event("notification", {"title": alert["title"], ...})
```

### Strengths

- ✅ Uses new `EventEntity` platform (introduced HA 2023.x)
- ✅ Tracks seen alerts via `_seen_alerts` set to prevent duplicates
- ✅ Primes seen set on `async_added_to_hass()` to avoid flooding on startup
- ✅ Fires structured `notification` events with full alert details
- ✅ Good example automation provided in `examples/` folder

---

## 8. Setup Failures

**Reference:** [Integration Setup Failures](https://developers.home-assistant.io/docs/integration_setup_failures)

### Implementation

```python
# __init__.py - Proper error handling:

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        await api.connect()
    except Exception as err:
        raise ConfigEntryNotReady(f"Device not reachable: {err}") from err

    try:
        await coordinator.async_config_entry_first_refresh()
    except asyncio.CancelledError:
        raise  # Let HA handle cancellations
    except Exception as err:
        raise ConfigEntryNotReady(f"Initial data refresh failed: {err}") from err
```

### Strengths

- ✅ Raises `ConfigEntryNotReady` on connection failures
- ✅ Properly chains exceptions with `from err`
- ✅ Propagates `asyncio.CancelledError` for shutdown handling
- ✅ Wraps both connection and first refresh failures

### Issues Found

#### Issue 8.1: Broad Exception Catch
**Location:** `__init__.py` line 112  
**Severity:** Low  
**Problem:**
```python
except Exception as ex:
    _LOGGER.exception("Unexpected error during Eaton xStorage Home setup: %s", ex)
    raise ConfigEntryNotReady(f"Integration not ready: {ex}") from ex
```
Broad `except Exception` could mask specific issues that should be handled differently.

---

## 9. Documentation

**References:**
- [Documenting Standards](https://developers.home-assistant.io/docs/documenting/standards/)
- [General Style Guide](https://developers.home-assistant.io/docs/documenting/general-style-guide)

### Existing Documentation

| Document | Location | Quality |
|----------|----------|---------|
| README | `README.md` | ✅ Good - Installation, entities, troubleshooting |
| Setup Guides | `docs/` folder | ✅ Good - Step-by-step guides |
| API Warning | README + sensors | ✅ Excellent - Prominent accuracy warning |
| Example Automations | `examples/` | ✅ Excellent - 3 well-documented examples |
| Quality Scale | `quality_scale.yaml` | ⚠️ Honest self-assessment |

### Quality Scale Self-Assessment

```yaml
# quality_scale.yaml - Honest tracking:
rules:
  # Bronze (done)
  appropriate-polling: done
  common-modules: done
  config-flow: done
  entity-unique-id: done
  has-entity-name: done
  
  # Bronze (todo)
  config-flow-test-coverage: todo  # ❌ Critical gap
  brands: todo
  docs-high-level-description: todo
  docs-installation-instructions: todo
  docs-removal-instructions: todo
  runtime-data: todo  # Note: Actually implemented correctly
  test-before-setup: todo
```

### Missing Documentation

- ❌ High-level description in HA documentation format
- ❌ Step-by-step installation in HA format
- ❌ Removal/uninstallation instructions

---

## 10. Testing

**Reference:** [Development Testing](https://developers.home-assistant.io/docs/development_testing)

### Current State

**❌ CRITICAL GAP: No tests exist**

No `tests/` directory found. Zero test coverage.

### Required Test Files (per HA guidelines)

```
tests/
├── __init__.py
├── conftest.py           # Fixtures for mocking
├── test_config_flow.py   # Config flow tests
├── test_init.py          # Setup/unload tests
├── test_sensor.py        # Sensor entity tests
├── test_binary_sensor.py
├── test_switch.py
├── test_select.py
├── test_number.py
├── test_button.py
├── test_event.py
└── test_coordinator.py   # Data coordinator tests
```

### Minimum Bronze Requirements

Per the quality scale, Bronze requires:
- Config flow test coverage
- Basic setup/teardown tests
- Entity creation tests

### Impact

- Cannot claim Bronze quality scale without tests
- No CI validation of code correctness
- Regression risk on future changes

---

## 11. Missing Features (Silver/Gold)

| Feature | Status | Description | Effort |
|---------|--------|-------------|--------|
| `diagnostics.py` | ❌ Missing | Debug data download | Medium |
| `system_health.py` | ❌ Missing | Integration health reporting | Low |
| Device triggers | ❌ Missing | Automation triggers | Medium |
| Repairs | ❌ Missing | Repair issue flow | Medium |
| Reconfigure flow | ❌ Missing | Modify entry without delete | Medium |
| `strings.json` | ❌ Missing | Base translation file | Low |

### Sample Diagnostics Implementation

```python
# diagnostics.py (recommended):
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

TO_REDACT = {"password", "token", "inverter_sn", "email"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
```

### Sample System Health Implementation

```python
# system_health.py (recommended):
from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    register.async_register_info(system_health_info)

async def system_health_info(hass: HomeAssistant):
    # Get first config entry
    entries = hass.config_entries.async_entries("eaton_battery_storage")
    if not entries:
        return {}
    
    coordinator = entries[0].runtime_data
    return {
        "device_reachable": coordinator.last_update_success,
        "api_host": coordinator.api.host,
        "last_update": coordinator.last_update_success_time,
    }
```

---

## 12. CI/CD

### Current GitHub Actions

```yaml
# .github/workflows/main.yml:
jobs:
  hacs:
    steps:
      - uses: hacs/action@main          # ✅ HACS validation
      - uses: home-assistant/actions/hassfest@master  # ✅ Manifest validation
  
  release:
    steps:
      - run: zip -r eaton_battery_storage.zip .  # ✅ Release artifact
```

### Missing CI Steps

| Check | Status | Recommendation |
|-------|--------|----------------|
| HACS validation | ✅ Present | - |
| hassfest | ✅ Present | - |
| pytest | ❌ Missing | Add when tests exist |
| ruff (linting) | ❌ Missing | Add for code quality |
| mypy (types) | ❌ Missing | Add for type checking |
| black (formatting) | ❌ Missing | Add for consistency |

### Recommended CI Addition

```yaml
# Add to workflow:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff mypy
      - run: ruff check custom_components/
      - run: ruff format --check custom_components/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install pytest pytest-homeassistant-custom-component
      - run: pytest tests/
```

---

## 13. Improvement Roadmap

### Priority 1: Critical (Required for Bronze)

| Task | Description | Effort |
|------|-------------|--------|
| Add test infrastructure | Create `tests/` with config flow, coordinator, entity tests | High |
| Fix `datetime.utcnow()` | Replace with `datetime.now(timezone.utc)` in `api.py` | Low |
| Fix async anti-pattern | Remove sync wrappers using `asyncio.create_task()` | Medium |

### Priority 2: High (Quality Improvements)

| Task | Description | Effort |
|------|-------------|--------|
| Add `diagnostics.py` | Implement debug data download | Medium |
| Add `system_health.py` | Report integration health | Low |
| Fix translation keys | Change error keys to slugs | Low |
| Add reauth flow | Implement `async_step_reauth()` | Medium |

### Priority 3: Medium (Code Quality)

| Task | Description | Effort |
|------|-------------|--------|
| Extract common code | Move settings logic to helper module | Medium |
| Add CI linting | Add ruff, mypy to GitHub workflow | Low |
| Add `strings.json` | Create base English strings file | Low |
| Split `sensor.py` | Break into logical groups | Medium |

### Priority 4: Low (Polish)

| Task | Description | Effort |
|------|-------------|--------|
| Remove duplicate storage | Fix `config_entry` in coordinator | Low |
| Remove unused code | Delete unused `battery_level` property | Low |
| Add entity translations | Add `entity` section to translations | Low |

---

## 14. Code Quality Details

### Positive Patterns Observed

1. **Proper Type Hints**
   ```python
   async def _async_update_data(self) -> dict[str, Any]:
   def __init__(self, hass: HomeAssistant, api: EatonBatteryAPI, config_entry) -> None:
   ```

2. **Modern Entity Patterns**
   ```python
   _attr_has_entity_name = True
   _attr_device_class = SensorDeviceClass.POWER
   _attr_state_class = SensorStateClass.MEASUREMENT
   ```

3. **Dataclass Entity Descriptions**
   ```python
   @dataclass(kw_only=True, frozen=True)
   class EatonBatteryStorageBinarySensorEntityDescription(BinarySensorEntityDescription):
       is_on_fn: Callable[[dict[str, Any]], bool | None]
   ```

4. **Proper Error Handling**
   ```python
   except asyncio.CancelledError:
       raise  # Propagate cancellation
   except Exception as err:
       raise ConfigEntryNotReady(...) from err  # Chain exceptions
   ```

5. **Device Info Pattern**
   ```python
   @property
   def device_info(self) -> DeviceInfo:
       return DeviceInfo(
           identifiers={(DOMAIN, self.api.host)},
           name="Eaton xStorage Home",
           manufacturer="Eaton",
           ...
       )
   ```

### Code Smells Identified

1. **Fire-and-Forget Tasks** (switch.py, select.py)
2. **Deprecated datetime API** (api.py)
3. **Error keys with spaces** (config_flow.py)
4. **Duplicate config_entry storage** (coordinator.py)
5. **Monolithic sensor file** (sensor.py - 1086 lines)
6. **Duplicated settings logic** (across multiple platforms)

---

## Verification Checklist

After implementing improvements:

- [ ] Run `pytest tests/` - all tests pass
- [ ] Run `ruff check custom_components/` - no errors
- [ ] Run `mypy custom_components/` - no type errors
- [ ] Run `python -m script.hassfest` - manifest valid
- [ ] Test diagnostics download in HA UI
- [ ] Verify System Health entry shows integration
- [ ] Test full config flow in HA UI
- [ ] Test options flow in HA UI
- [ ] Verify all entities load correctly
- [ ] Test entity controls (switches, selects, numbers)

---

## Final Assessment

| Category | Score | Notes |
|----------|-------|-------|
| Structure | 8/10 | Good, missing diagnostics/system_health |
| Config Flow | 8/10 | Good, needs reauth and error key fixes |
| Data Fetching | 9/10 | Excellent coordinator implementation |
| Async Patterns | 6/10 | Critical issues with datetime and create_task |
| Entity Quality | 9/10 | Excellent entity implementation |
| Services | 8/10 | Acceptable, no custom services needed |
| Events | 9/10 | Modern EventEntity usage |
| Documentation | 7/10 | Good but missing HA format docs |
| Testing | 0/10 | No tests exist |
| CI/CD | 6/10 | Basic validation only |

**Overall: 7/10** - Well-implemented integration with comprehensive entity coverage. Main gaps are testing infrastructure and async pattern issues.

**Quality Scale Claim:** Bronze is **overstated** without test coverage. Either implement tests or remove the claim from manifest.json.

---

## References

- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [Creating Integration File Structure](https://developers.home-assistant.io/docs/creating_integration_file_structure)
- [Config Entries Config Flow Handler](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [Integration Fetching Data](https://developers.home-assistant.io/docs/integration_fetching_data)
- [AsyncIO Working with Async](https://developers.home-assistant.io/docs/asyncio_working_with_async)
- [Creating Platform Index](https://developers.home-assistant.io/docs/creating_platform_index)
- [Integration Events](https://developers.home-assistant.io/docs/integration_events)
- [Development Testing](https://developers.home-assistant.io/docs/development_testing)
- [Documenting Standards](https://developers.home-assistant.io/docs/documenting/standards/)
