#!/usr/bin/env python3
"""
Simple validation script to check basic code quality without external dependencies.
This simulates what CI would check.
"""

import ast
import json
import os
import sys
from pathlib import Path


def check_python_syntax(directory):
    """Check Python files for syntax errors."""
    errors = []
    python_files = list(Path(directory).glob("**/*.py"))
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            print(f"✓ {file_path}")
        except SyntaxError as e:
            errors.append(f"Syntax error in {file_path}: {e}")
            print(f"✗ {file_path}: {e}")
        except Exception as e:
            errors.append(f"Error reading {file_path}: {e}")
            print(f"✗ {file_path}: {e}")
    
    return errors


def check_json_files():
    """Check JSON files for syntax errors."""
    errors = []
    json_files = [
        "custom_components/eaton_battery_storage/manifest.json",
        "custom_components/eaton_battery_storage/translations/en.json",
        "hacs.json"
    ]
    
    for file_path in json_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"✓ {file_path}")
            except json.JSONDecodeError as e:
                errors.append(f"JSON error in {file_path}: {e}")
                print(f"✗ {file_path}: {e}")
        else:
            errors.append(f"Missing file: {file_path}")
            print(f"✗ Missing: {file_path}")
    
    return errors


def check_required_files():
    """Check for required files."""
    errors = []
    required_files = [
        "custom_components/eaton_battery_storage/__init__.py",
        "custom_components/eaton_battery_storage/manifest.json",
        "custom_components/eaton_battery_storage/config_flow.py",
        "hacs.json",
        "requirements-test.txt",
        "pytest.ini"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            errors.append(f"Missing required file: {file_path}")
            print(f"✗ Missing: {file_path}")
    
    return errors


def main():
    """Run all validation checks."""
    print("Running local validation checks...\n")
    
    errors = []
    
    print("1. Checking Python syntax...")
    errors.extend(check_python_syntax("custom_components"))
    errors.extend(check_python_syntax("tests"))
    
    print("\n2. Checking JSON files...")
    errors.extend(check_json_files())
    
    print("\n3. Checking required files...")
    errors.extend(check_required_files())
    
    print(f"\n{'='*50}")
    if errors:
        print(f"❌ Found {len(errors)} issues:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()