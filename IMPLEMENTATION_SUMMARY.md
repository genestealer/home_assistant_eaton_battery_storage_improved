# Implementation Summary: Customer and Technician Account Support

## Changes Made

### 1. Constants (`const.py`)

**Added:**

- `ACCOUNT_TYPE_CUSTOMER = "customer"`
- `ACCOUNT_TYPE_TECHNICIAN = "tech"`
- `TECHNICIAN_ONLY_SENSORS`: List of 33 sensor keys that require technician access

### 2. API Client (`api.py`)

**Modified:**

- Added `user_type` parameter to `__init__()` (defaults to "tech" for backward compatibility)
- Updated `connect()` method to build authentication payload based on user type:
  - Customer: Only sends `username`, `pwd`, `userType`
  - Technician: Also sends `inverterSn`, `email`, `userType`

### 3. Config Flow (`config_flow.py`)

**Modified:**

- Added `CONF_USER_TYPE` configuration constant
- Updated `async_step_user()`:
  - Added account type selection dropdown (Customer/Technician)
  - Dynamic form fields: inverter_sn and has_pv only shown for technician accounts
  - Updated unique ID generation based on account type
- Updated `_test_connection()` to accept and pass `user_type` parameter
- Updated `EatonXStorageOptionsFlow.async_step_init()`:
  - Added account type selection in options flow
  - Dynamic form fields based on selected account type
- Updated second `_test_connection()` in options flow to accept `user_type`

### 4. Integration Setup (`__init__.py`)

**Modified:**

- Updated `async_setup_entry()`:
  - Retrieves `user_type` from config (defaults to "tech" for backward compatibility)
  - Passes `user_type` to API client initialization
  - Uses `.get()` for optional fields (inverter_sn, email)
- Added `async_migrate_technician_sensors()` function:
  - Enables/disables technician-only sensors based on user type
  - Called during setup and options updates
- Updated `async_update_options()` to call technician sensor migration

### 5. Translations (`translations/en.json`)

**Modified:**

- Updated config step descriptions to mention both account types
- Added `user_type` field with description explaining the differences
- Updated field labels to be generic (removed "Technician" prefix)
- Added note about technician-only fields in data_description

### 6. Data Coordinator (`coordinator.py`)

**No changes needed:**

- Already handles missing technical_status data gracefully
- Returns empty dict for unavailable endpoints
- Logs debug messages when technical endpoints fail (expected for customer accounts)

### 7. Sensor Platform (`sensor.py`)

**Modified:**

- Added user_type check in `async_setup_entry()`
- Technician-only sensors are **not created** for customer accounts (checked against TECHNICIAN_ONLY_SENSORS list)
- Already handles missing data gracefully in `native_value` property
- Returns None when data path doesn't exist
- Sensors show as "unavailable" when data is not accessible

## Backward Compatibility

All changes maintain full backward compatibility:

1. **Default user_type**: Existing installations default to "tech" account type
2. **Optional fields**: `inverter_sn` and `email` use `.get()` with defaults
3. **Graceful degradation**: Missing data is handled without errors
4. **API compatibility**: Authentication still works with existing payloads

## User Experience

### For New Installations:

1. User selects account type during setup
2. Form dynamically shows/hides fields based on selection
3. Only relevant sensors are created

### For Existing Installations:

1. Continue working without changes (defaults to technician)
2. Can switch account type via Configure option
3. Sensors automatically enable/disable when switching types

### For Customer Accounts:

1. Simpler configuration (no serial number needed)
2. All core monitoring features available
3. Technical diagnostic sensors show as "disabled"
4. No error messages for unavailable endpoints

### For Technician Accounts:

1. Full diagnostic capabilities
2. All sensors available
3. Requires additional credentials

## Testing Recommendations

1. **New Installation - Customer Account:**

   - Verify form only shows: host, username, password
   - Verify authentication works without inverter_sn
   - Verify technical sensors are disabled by default
   - Verify core sensors work correctly

2. **New Installation - Technician Account:**

   - Verify form shows all fields including inverter_sn and has_pv
   - Verify authentication requires inverter_sn
   - Verify all sensors are available
   - Verify technical sensors populate correctly

3. **Existing Installation - Upgrade:**

   - Verify integration continues working
   - Verify user_type defaults to "tech"
   - Verify all sensors remain available

4. **Account Type Switching:**

   - Switch from tech to customer: verify technical sensors disable
   - Switch from customer to tech: verify technical sensors enable
   - Verify forms update dynamically when changing selection

5. **Error Handling:**
   - Wrong credentials: verify appropriate error message
   - Missing serial number for tech account: verify validation
   - 403 errors for customer on technical endpoints: verify graceful handling

## Files Modified

1. `/custom_components/eaton_battery_storage/const.py`
2. `/custom_components/eaton_battery_storage/api.py`
3. `/custom_components/eaton_battery_storage/config_flow.py`
4. `/custom_components/eaton_battery_storage/__init__.py`
5. `/custom_components/eaton_battery_storage/translations/en.json`

## Files Created

1. `/ACCOUNT_TYPE_SUPPORT.md` - User-facing documentation

## API Reference

Based on https://github.com/genestealer/eaton-xstorage-home-api-doc/

### Customer Authentication

```bash
curl -X POST "https://device-ip/api/auth/signin" \
  -H "Content-Type: application/json" \
  --data '{
    "username": "user",
    "pwd": "user",
    "userType": "customer"
  }'
```

### Technician Authentication

```bash
curl -X POST "https://device-ip/api/auth/signin" \
  -H "Content-Type: application/json" \
  --data '{
    "username": "admin",
    "pwd": "jlwgK41G",
    "inverterSn": "SERIAL_NUMBER",
    "email": "anything@anything.com",
    "userType": "tech"
  }'
```

### Endpoint Access

| Endpoint                            | Customer | Technician |
| ----------------------------------- | -------- | ---------- |
| /api/device/status                  | ✅       | ✅         |
| /api/device                         | ✅       | ✅         |
| /api/settings                       | ✅       | ✅         |
| /api/device/command                 | ✅       | ✅         |
| /api/technical/status               | ❌ 403   | ✅         |
| /api/device/maintenance/diagnostics | ❌ 403   | ✅         |

## Future Enhancements

Potential improvements for future releases:

1. Auto-detect account type based on successful endpoint access
2. Provide in-UI option to test endpoint availability
3. Add tooltip explaining which features require technician access
4. Migrate existing installations to prompt for account type selection
