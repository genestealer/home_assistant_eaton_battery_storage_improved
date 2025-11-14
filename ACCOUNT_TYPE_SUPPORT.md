# Customer and Technician Account Support

## Overview

The Eaton xStorage Home integration now supports both **Customer** and **Technician** account types, allowing users to configure the integration based on their access level.

## Account Types

### Customer Account

- **Access Level**: Basic monitoring and control
- **Required Credentials**:
  - Device IP Address or Hostname
  - Username (default: `user`)
  - Password (default: `user`)
- **Available Features**:
  - Device status and information
  - Battery state of charge (SOC)
  - Energy flow monitoring
  - Power state control
  - Operation mode commands
  - Device settings
  - Notifications
  - Metrics and historical data
  - Schedules

### Technician Account

- **Access Level**: Full system access including advanced diagnostics
- **Required Credentials**:
  - Device IP Address or Hostname
  - Username (default: `admin`)
  - Password (default: `jlwgK41G`)
  - Inverter Serial Number
- **Additional Features** (beyond Customer access):
  - Technical status diagnostics
  - Detailed inverter information
  - BMS (Battery Management System) detailed data
  - Grid voltage and frequency monitoring
  - DC current injection measurements
  - PV (Photovoltaic) voltage and current (if applicable)
  - Maintenance diagnostics

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Eaton xStorage Home"
3. Select your **Account Type**:
   - **Customer**: For basic monitoring (most users)
   - **Technician**: For advanced diagnostics (requires technician credentials)
4. Enter your credentials:
   - **For Customer accounts**: Host, Username, Password
   - **For Technician accounts**: Host, Username, Password, Inverter Serial Number
5. Optional: Enable PV sensors if you have solar panels connected

### Updating Configuration

You can change your account type or credentials at any time:

1. Go to **Settings** → **Devices & Services**
2. Find your Eaton xStorage Home integration
3. Click **Configure**
4. Update the account type and/or credentials
5. The integration will automatically enable/disable sensors based on your access level

## Default Credentials

If you haven't changed your credentials (or the installer didn't change them), try these defaults:

### Customer Account

- Username: `user`
- Password: `user`

### Technician Account

- Username: `admin`
- Password: `jlwgK41G`

> ⚠️ **Security Note**: It's recommended to change default passwords after initial setup for security reasons.

## Sensor Availability

### Always Available (Both Account Types)

- Battery State of Charge
- Battery Status (Charging/Discharging/Idle)
- Energy Flow (Grid, Load, Battery)
- Operation Mode
- Current Mode Information
- Device Information
- Network Status
- Firmware Versions
- Battery Capacity
- Self Consumption/Sufficiency

### Technician Account Only

All sensors with the prefix `technical_status.*`:

- Grid Voltage & Frequency
- Inverter Power & Temperature
- Bus Voltage
- Grid Code
- DC Current Injection (R, S, T phases)
- PV Voltage & Current (PV1, PV2)
- BMS Voltage, Current, Temperature
- BMS Cell Voltages (Highest, Lowest, Delta)
- BMS Total Charge/Discharge
- Inverter Model & Bootloader Version

## API Endpoint Access

### Customer Account (`userType: "customer"`)

- ✅ `/api/device/status`
- ✅ `/api/device`
- ✅ `/api/config/state`
- ✅ `/api/settings`
- ✅ `/api/metrics`
- ✅ `/api/metrics/daily`
- ✅ `/api/schedule/`
- ✅ `/api/notifications/`
- ✅ `/api/device/command`
- ✅ `/api/device/power`
- ❌ `/api/technical/status` (403 Forbidden)
- ❌ `/api/device/maintenance/diagnostics` (403 Forbidden)

### Technician Account (`userType: "tech"`)

- ✅ All endpoints including:
  - `/api/technical/status`
  - `/api/device/maintenance/diagnostics`

## Migration from Existing Installations

If you have an existing installation configured with technician credentials, it will continue to work without any changes. The integration defaults to technician account type for backward compatibility.

To switch to a customer account:

1. Go to the integration's **Configure** option
2. Change **Account Type** to "Customer"
3. Update the credentials if different
4. Remove the Inverter Serial Number field (not needed for customer accounts)
5. Save the configuration

Technical sensors will be automatically disabled when switching to a customer account.

## Troubleshooting

### "Authentication failed" Error

- **Customer Account**: Verify username and password are correct
- **Technician Account**: Verify username, password, AND inverter serial number are correct

### "403 Forbidden" Errors in Logs

- This is normal for customer accounts accessing technical endpoints
- The integration will gracefully handle these errors
- Technical sensors will show as "unavailable"

### Missing Sensors

- **Customer Account**: Technical diagnostic sensors will not be created (this is expected behavior)
- **Technician Account**: If sensors are missing, ensure credentials are correct and you have the inverter serial number
- **After Switching Account Types**: Reload the integration to recreate the sensor set

### Account Locked

If you see "Error during authentication: 10":

- Too many failed login attempts
- Wait 10 minutes before trying again
- Verify your credentials are correct

## References

- [Eaton xStorage Home API Documentation](https://github.com/genestealer/eaton-xstorage-home-api-doc/)
- Authentication endpoints in API docs show the difference between customer and technician authentication payloads

## Implementation Details

### Authentication Payload Differences

**Customer Account**:

```json
{
  "username": "user",
  "pwd": "user",
  "userType": "customer"
}
```

**Technician Account**:

```json
{
  "username": "admin",
  "pwd": "jlwgK41G",
  "inverterSn": "YOUR_SERIAL_NUMBER",
  "email": "anything@anything.com",
  "userType": "tech"
}
```

### Automatic Sensor Management

The integration automatically creates sensors based on:

1. **Account Type**: Technician sensors are only **created** for tech accounts (not just disabled)
2. **PV Configuration**: PV sensors only created when `has_pv` is enabled
3. **Data Availability**: Sensors show as "unavailable" if data is not accessible

For customer accounts, technician-only sensors **will not appear at all** in your entity list. When you switch from customer to technician account (or vice versa), reload the integration to recreate the appropriate sensor set.
