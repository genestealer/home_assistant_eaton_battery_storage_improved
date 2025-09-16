# Eaton xStorage Home Battery Integration for Home Assistant

This is a Home Assistant custom component that integrates Eaton xStorage Home battery systems via local REST API. The integration provides real-time monitoring, control capabilities, and automation support for Eaton xStorage battery systems.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap and Validate the Repository
- **Essential Dependencies**: `pip install homeassistant-stubs` (takes 90+ seconds, NEVER CANCEL, set timeout to 300+ seconds. May fail due to network timeouts - this is normal)
- **Core Validation** (works without dependencies): 
  ```bash
  python3 -c "
  import json, ast
  from pathlib import Path
  
  # Validate all integration components quickly (~0.05 seconds)
  manifest = json.load(open('custom_components/eaton_battery_storage/manifest.json'))
  py_files = list(Path('custom_components/eaton_battery_storage').glob('*.py'))
  for f in py_files:
      ast.parse(open(f).read())
  hacs = json.load(open('hacs.json'))
  
  print(f'✓ Manifest: {manifest[\"name\"]} v{manifest[\"version\"]}')
  print(f'✓ Python syntax: {len(py_files)} files valid')
  print(f'✓ HACS: {hacs[\"name\"]}')
  print('✓ All validations passed')
  "
  ```
- **Syntax Check**: `python3 -m py_compile custom_components/eaton_battery_storage/*.py` (compiles all Python files in ~0.05 seconds)
- **Manual Integration Test**: `python3 -c "import custom_components.eaton_battery_storage; print('Integration loads successfully')"` (basic import test)

### Validation Commands (CRITICAL - Always Run Before Committing)
- **NEVER CANCEL builds or validation**: Home Assistant installations can take 90+ seconds but may timeout due to network issues, validation scripts run quickly but dependency installs are slow
- **Complete Validation**: Run all validation steps with timeouts of 300+ seconds for pip installs, 30+ seconds for other operations
- **PRACTICAL APPROACH**: Skip dependency installation if network is slow, use fast validation instead
- **CI Validation Simulation**: 
  ```bash
  # Manifest validation (simulates hassfest)
  python3 -c "
  import json
  manifest = json.load(open('custom_components/eaton_battery_storage/manifest.json'))
  required = ['domain', 'name', 'documentation', 'requirements', 'version', 'config_flow']
  missing = [f for f in required if f not in manifest]
  assert not missing, f'Missing manifest fields: {missing}'
  print(f'✓ Manifest valid: {manifest[\"name\"]} v{manifest[\"version\"]}')
  "
  ```
- **HACS Validation**: 
  ```bash
  python3 -c "
  import json
  hacs = json.load(open('hacs.json'))
  assert 'name' in hacs, 'HACS name missing'
  print(f'✓ HACS config valid: {hacs[\"name\"]}')
  "
  ```

### No Traditional Build Process
- **THIS IS NOT A BUILDABLE APPLICATION** - it's a Home Assistant integration that gets loaded by Home Assistant runtime
- **Do not try to build or run the integration standalone** - it requires Home Assistant framework and an actual Eaton xStorage device
- **No npm, make, or docker builds** - validation is done through Python syntax checking and integration structure validation

## Validation Scenarios

### Always Test After Making Changes
- **CRITICAL VALIDATION STEP**: Always test the complete validation workflow after any code changes:
  ```bash
  # Run comprehensive validation (creates script if needed)
  python3 -c "
  import json, ast, importlib.util
  from pathlib import Path
  
  # Validate manifest
  manifest = json.load(open('custom_components/eaton_battery_storage/manifest.json'))
  print(f'✓ Manifest: {manifest[\"name\"]} v{manifest[\"version\"]}')
  
  # Validate Python syntax
  py_files = list(Path('custom_components/eaton_battery_storage').glob('*.py'))
  for f in py_files:
      ast.parse(open(f).read())
  print(f'✓ Python syntax: {len(py_files)} files valid')
  
  # Validate HACS config
  hacs = json.load(open('hacs.json'))
  print(f'✓ HACS: {hacs[\"name\"]}')
  print('✓ All basic validations passed')
  "
  ```
- **Manual Integration Testing**: Always verify imports work: `python3 -c "import custom_components.eaton_battery_storage"`
- **Configuration Testing**: Verify config flow can be imported: `python3 -c "from custom_components.eaton_battery_storage.config_flow import EatonXStorageConfigFlow"`
- **API Testing**: Ensure API module loads: `python3 -c "from custom_components.eaton_battery_storage.api import EatonBatteryAPI"`

### CI/CD Compliance Validation
- **GitHub Actions Simulation**: The CI runs HACS validation and hassfest - simulate locally with the validation commands above
- **Quality Scale Requirements**: Check `custom_components/eaton_battery_storage/quality_scale.yaml` for bronze-level compliance requirements
- **Always run all validation steps** before committing - the CI will fail if basic validation doesn't pass

## Common Tasks

### Repository Structure Overview
```
.
├── README.md                          # User documentation
├── hacs.json                          # HACS distribution config
├── custom_components/
│   └── eaton_battery_storage/         # Main integration directory
│       ├── __init__.py                # Integration setup and platforms
│       ├── manifest.json              # Integration metadata
│       ├── config_flow.py             # Configuration UI flow
│       ├── api.py                     # Eaton xStorage API client
│       ├── coordinator.py             # Data update coordinator
│       ├── const.py                   # Constants and configuration
│       ├── sensor.py                  # Sensor entities
│       ├── binary_sensor.py           # Binary sensor entities
│       ├── number.py                  # Number input entities
│       ├── select.py                  # Selection entities
│       ├── switch.py                  # Switch entities
│       ├── button.py                  # Button entities
│       ├── event.py                   # Event entities
│       ├── quality_scale.yaml         # HA quality requirements
│       ├── services.yaml              # Service definitions
│       └── translations/en.json       # UI translations
├── docs/                              # User setup documentation
├── examples/                          # Example automations
└── .github/workflows/main.yml         # CI/CD pipeline
```

### Key Configuration Files
**manifest.json** - Integration metadata:
```json
{
  "domain": "eaton_battery_storage",
  "name": "Eaton xStorage Home Battery",
  "version": "0.2.0",
  "config_flow": true,
  "dependencies": [],
  "requirements": []
}
```

**hacs.json** - HACS distribution config:
```json
{
    "name": "Eaton xStorage Home Battery Storage System",
    "content_in_root": false,
    "homeassistant": "2023.5.0"
}
```

### Working with Integration Code
- **Main Integration Entry**: `custom_components/eaton_battery_storage/__init__.py` - handles platform setup and entry configuration
- **API Communication**: `custom_components/eaton_battery_storage/api.py` - manages REST API communication with xStorage device
- **Configuration Flow**: `custom_components/eaton_battery_storage/config_flow.py` - handles user setup UI and device connection testing
- **Data Coordination**: `custom_components/eaton_battery_storage/coordinator.py` - manages data fetching and entity updates
- **Entity Definitions**: Sensor, switch, number, select, button, and event entities in respective Python files

### Common Development Patterns
- **Entity Creation**: All entities inherit from Home Assistant base classes and use the coordinator for data updates
- **Configuration**: Uses Home Assistant config flow pattern for user setup
- **API Interaction**: Async HTTP client with authentication and error handling
- **Data Updates**: Centralized through DataUpdateCoordinator with configurable refresh intervals

### Documentation Structure
- **User Documentation**: `docs/` directory contains setup guides for Home Assistant, HACS, and integration installation
- **Example Automations**: `examples/` directory provides ready-to-use Home Assistant automation examples
- **API Documentation**: Referenced in README.md, maintained separately at https://github.com/genestealer/eaton-xstorage-home-api-doc/

### Debugging and Troubleshooting
- **Enable Debug Logging**: Add to Home Assistant configuration.yaml:
  ```yaml
  logger:
    logs:
      custom_components.eaton_battery_storage: debug
  ```
- **Common Issues**: Check `quality_scale.yaml` for known limitations and TODO items
- **Connection Testing**: The config flow includes built-in connection testing to validate device credentials

### Making Changes
- **Always check imports** after modifying any Python file
- **Update version** in `manifest.json` for releases
- **Test configuration flow** if modifying connection or setup logic
- **Validate entity definitions** if adding new sensors or controls
- **Check quality scale compliance** if adding new features

### Important Notes
- **Accuracy Warning**: The xStorage Home inverter has poor energy monitoring accuracy (~30% higher than actual values)
- **Local API Only**: Integration communicates directly with device, no cloud dependency
- **Device Requirements**: Requires Eaton xStorage Home (Tiida) on same network as Home Assistant
- **HACS Distribution**: Integration is distributed through HACS (Home Assistant Community Store)

## CRITICAL REMINDERS
- **NEVER CANCEL** pip install commands - they take 60-300 seconds to complete, may timeout due to network issues
- **ALWAYS validate** before committing - run all validation commands
- **Set timeouts** of 300+ seconds for dependency installations  
- **Use fast validation** when network is slow or dependencies aren't needed
- **This is not a traditional application** - it's a Home Assistant integration that requires the HA runtime environment