# Account Type Selection Guide

## Quick Decision Tree

```
Do you need advanced technical diagnostics?
│
├─ NO  ─→ Use CUSTOMER account
│         ✓ Simpler setup (no serial number needed)
│         ✓ All monitoring features
│         ✓ Full control capabilities
│         ✓ Default credentials: user / user
│
└─ YES ─→ Use TECHNICIAN account
          ✓ All customer features PLUS
          ✓ Technical diagnostics
          ✓ Detailed BMS information
          ✓ Grid voltage/frequency monitoring
          ✓ Requires inverter serial number
          ✓ Default credentials: admin / jlwgK41G
```

## Feature Comparison Matrix

| Feature                                | Customer      | Technician  |
| -------------------------------------- | ------------- | ----------- |
| **Configuration**                      |
| Device IP/Hostname                     | ✅ Required   | ✅ Required |
| Username                               | ✅ Required   | ✅ Required |
| Password                               | ✅ Required   | ✅ Required |
| Inverter Serial Number                 | ❌ Not needed | ✅ Required |
| **Monitoring**                         |
| Battery State of Charge                | ✅            | ✅          |
| Battery Status (Charge/Discharge/Idle) | ✅            | ✅          |
| Energy Flow (Grid/Battery/Load)        | ✅            | ✅          |
| Operation Mode                         | ✅            | ✅          |
| Self Consumption/Sufficiency           | ✅            | ✅          |
| Device Information                     | ✅            | ✅          |
| Firmware Versions                      | ✅            | ✅          |
| Network Status                         | ✅            | ✅          |
| **Technical Diagnostics**              |
| Grid Voltage & Frequency               | ❌            | ✅          |
| Inverter Temperature                   | ❌            | ✅          |
| Bus Voltage                            | ❌            | ✅          |
| Grid Code                              | ❌            | ✅          |
| DC Current Injection                   | ❌            | ✅          |
| BMS Voltage & Current                  | ❌            | ✅          |
| BMS Cell Voltages (High/Low/Delta)     | ❌            | ✅          |
| BMS Temperature Details                | ❌            | ✅          |
| PV Voltage & Current                   | ❌            | ✅          |
| Inverter Bootloader Version            | ❌            | ✅          |
| **Control Features**                   |
| Power On/Off                           | ✅            | ✅          |
| Set Operation Mode                     | ✅            | ✅          |
| Manual Charge/Discharge                | ✅            | ✅          |
| Schedule Management                    | ✅            | ✅          |
| Settings Updates                       | ✅            | ✅          |
| **Notifications**                      |
| View Notifications                     | ✅            | ✅          |
| Mark as Read                           | ✅            | ✅          |
| Unread Count                           | ✅            | ✅          |
| **Historical Data**                    |
| Hourly Metrics                         | ✅            | ✅          |
| Daily Metrics                          | ✅            | ✅          |
| 30-Day Summary                         | ✅            | ✅          |

## Sensor Count by Account Type

### Customer Account

- **~40 sensors** covering all essential monitoring and control

### Technician Account

- **~73 sensors** including all customer sensors plus 33 technical diagnostic sensors

## Typical Use Cases

### Use CUSTOMER Account If You:

- ✓ Want simple setup
- ✓ Only need energy monitoring
- ✓ Want to control charge/discharge
- ✓ Don't need electrical system details
- ✓ Don't have the inverter serial number
- ✓ Installer changed credentials and didn't provide them

### Use TECHNICIAN Account If You:

- ✓ Need detailed electrical diagnostics
- ✓ Want to monitor grid quality
- ✓ Need BMS cell-level information
- ✓ Troubleshooting system issues
- ✓ Professional installer or technician
- ✓ Have access to the inverter serial number

## Setup Complexity

### Customer Account: ⭐⭐ (Simple)

```
1. Enter device IP
2. Enter username (default: user)
3. Enter password (default: user)
4. Done! ✅
```

### Technician Account: ⭐⭐⭐ (Moderate)

```
1. Enter device IP
2. Select "Technician" account type
3. Enter username (default: admin)
4. Enter password (default: jlwgK41G)
5. Enter inverter serial number (from device label)
6. Optional: Enable PV sensors if you have solar
7. Done! ✅
```

## Finding Your Inverter Serial Number

The inverter serial number is typically found:

1. On a label on the inverter unit itself
2. In the web interface under Device Information
3. On the installation documentation
4. Format: Usually starts with "XSTH" followed by numbers

⚠️ **Note**: If you can't find the serial number, use a Customer account instead!

## Switching Between Account Types

You can change account types at any time:

1. Go to **Settings** → **Devices & Services**
2. Find **Eaton xStorage Home**
3. Click **Configure**
4. Change **Account Type**
5. Update credentials as needed
6. Save

When you switch:

- Customer → Technician: Integration will reload and create technical sensors
- Technician → Customer: Integration will reload without technical sensors (existing ones removed)

## Common Questions

**Q: Will my existing installation break?**
A: No! Existing installations automatically default to Technician account type.

**Q: Can I use technician credentials with a customer account type?**
A: Yes, but you won't get technical sensors. Better to use the Technician account type.

**Q: What happens if I enter wrong credentials?**
A: You'll get an authentication error. After too many attempts, the account locks for 10 minutes.

**Q: Do customer accounts have any limitations on control features?**
A: No! Both account types can control the system equally. Only diagnostic sensors differ.

**Q: Can I have both account types configured?**
A: No, but you can easily switch between them in the configuration at any time.

## Recommendations

### For Most Home Users:

**Choose CUSTOMER Account**

- Simpler setup
- All features you need
- No serial number hunting

### For Power Users / Technicians:

**Choose TECHNICIAN Account**

- Maximum visibility
- Detailed diagnostics
- Professional troubleshooting

---

**Need Help?** Check the [full documentation](ACCOUNT_TYPE_SUPPORT.md) for more details.
