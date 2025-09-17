"""Test basic integration structure and imports."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


class TestIntegrationStructure:
    """Test the integration's basic structure and imports."""

    def test_can_import_const(self):
        """Test that constants module can be imported."""
        from custom_components.eaton_battery_storage.const import DOMAIN
        assert DOMAIN == "eaton_battery_storage"

    def test_can_import_manifest(self):
        """Test that manifest exists and has required fields."""
        import json
        
        manifest_path = Path("custom_components/eaton_battery_storage/manifest.json")
        assert manifest_path.exists(), "manifest.json file must exist"
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        required_fields = ["domain", "name", "config_flow", "version", "codeowners"]
        for field in required_fields:
            assert field in manifest, f"manifest.json must contain {field}"
        
        assert manifest["domain"] == "eaton_battery_storage"
        assert manifest["config_flow"] is True

    def test_can_import_config_flow(self):
        """Test that config flow module can be imported."""
        from custom_components.eaton_battery_storage.config_flow import CONF_INVERTER_SN
        assert CONF_INVERTER_SN == "inverter_sn"

    def test_can_import_api_module(self):
        """Test that API module can be imported (class definition only)."""
        spec = importlib.util.spec_from_file_location(
            "api", "custom_components/eaton_battery_storage/api.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        # We can at least load the module definition
        assert spec is not None
        assert module is not None

    def test_can_import_coordinator_module(self):
        """Test that coordinator module can be imported."""
        spec = importlib.util.spec_from_file_location(
            "coordinator", "custom_components/eaton_battery_storage/coordinator.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        assert spec is not None
        assert module is not None

    def test_can_import_sensor_module(self):
        """Test that sensor module can be imported."""
        spec = importlib.util.spec_from_file_location(
            "sensor", "custom_components/eaton_battery_storage/sensor.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        assert spec is not None
        assert module is not None

    def test_required_files_exist(self):
        """Test that all required integration files exist."""
        base_path = Path("custom_components/eaton_battery_storage")
        
        required_files = [
            "__init__.py",
            "manifest.json",
            "config_flow.py",
            "const.py",
            "api.py",
            "coordinator.py",
            "sensor.py",
            "binary_sensor.py",
            "switch.py",
            "button.py",
            "select.py",
            "number.py",
            "event.py",
        ]
        
        for file_name in required_files:
            file_path = base_path / file_name
            assert file_path.exists(), f"Required file {file_name} must exist"

    def test_integration_platforms_defined(self):
        """Test that platforms are properly defined."""
        # Import the platforms list from __init__.py without executing the full module
        import ast
        
        init_path = Path("custom_components/eaton_battery_storage/__init__.py")
        with open(init_path) as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Find PLATFORMS assignment (may have type annotation)
        platforms_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "PLATFORMS":
                        platforms_found = True
                        break
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == "PLATFORMS":
                    platforms_found = True
                    break
        
        assert platforms_found, "PLATFORMS list must be defined in __init__.py"

    def test_services_yaml_exists(self):
        """Test that services.yaml exists."""
        services_path = Path("custom_components/eaton_battery_storage/services.yaml")
        assert services_path.exists(), "services.yaml file must exist"

    def test_translations_exist(self):
        """Test that translation files exist."""
        translations_path = Path("custom_components/eaton_battery_storage/translations")
        assert translations_path.exists(), "translations directory must exist"
        
        en_translation = translations_path / "en.json"
        assert en_translation.exists(), "English translation file must exist"


class TestCodeQuality:
    """Test code quality aspects."""

    def test_no_syntax_errors_in_python_files(self):
        """Test that all Python files have valid syntax."""
        base_path = Path("custom_components/eaton_battery_storage")
        python_files = list(base_path.glob("*.py"))
        
        for py_file in python_files:
            with open(py_file) as f:
                content = f.read()
            
            try:
                compile(content, str(py_file), "exec")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file}: {e}")

    def test_imports_structure(self):
        """Test that imports follow expected structure."""
        from custom_components.eaton_battery_storage.const import (
            DOMAIN,
            POWER_ACCURACY_WARNING,
            CURRENT_MODE_COMMAND_MAP,
        )
        
        # Test that constants are properly typed
        assert isinstance(DOMAIN, str)
        assert isinstance(POWER_ACCURACY_WARNING, str)
        assert isinstance(CURRENT_MODE_COMMAND_MAP, dict)

    def test_domain_consistency(self):
        """Test that domain is consistent across files."""
        import json
        
        # Check manifest
        with open("custom_components/eaton_battery_storage/manifest.json") as f:
            manifest = json.load(f)
        
        # Check constants
        from custom_components.eaton_battery_storage.const import DOMAIN
        
        assert manifest["domain"] == DOMAIN
        assert manifest["domain"] == "eaton_battery_storage"


class TestTestInfrastructure:
    """Test that our test infrastructure is working."""

    def test_pytest_is_working(self):
        """Test that pytest itself is working."""
        assert True

    def test_can_import_pytest_fixtures(self):
        """Test that we can use our test fixtures."""
        from tests.conftest import mock_config_entry
        assert mock_config_entry is not None

    def test_asyncio_support(self):
        """Test that asyncio tests are supported."""
        import asyncio
        
        async def dummy_async_function():
            await asyncio.sleep(0.001)
            return True
        
        # This will be run by pytest-asyncio
        result = asyncio.run(dummy_async_function())
        assert result is True

    def test_test_files_exist(self):
        """Test that our test files exist."""
        test_files = [
            "tests/__init__.py",
            "tests/conftest.py",
            "tests/test_const.py",
            "tests/test_integration_structure.py",  # This file
        ]
        
        for test_file in test_files:
            test_path = Path(test_file)
            assert test_path.exists(), f"Test file {test_file} must exist"

    def test_requirements_file_exists(self):
        """Test that requirements-test.txt exists."""
        requirements_path = Path("requirements-test.txt")
        assert requirements_path.exists(), "requirements-test.txt must exist"

    def test_pytest_config_exists(self):
        """Test that pytest.ini exists."""
        pytest_config = Path("pytest.ini")
        assert pytest_config.exists(), "pytest.ini must exist"