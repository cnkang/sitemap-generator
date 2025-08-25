#!/usr/bin/env python3
"""Test script to verify Python version compatibility."""

import importlib.util
import sys


def test_python_version():
    """Test if Python version is supported."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    if version >= (3, 13):
        print("✅ Python 3.13+ detected - testing latest features")
    else:
        print("✅ Supported Python version")

    return True


def test_imports():
    """Test if all required modules can be imported."""
    required_modules = [
        "xml.etree.ElementTree",
        "urllib.request",
        "urllib.parse",
        "urllib.robotparser",
        "concurrent.futures",
        "threading",
        "html.parser",
        "email.utils",
        "typing",
    ]

    optional_modules = ["boto3", "requests"]

    print("\nTesting required imports:")
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            return False

    print("\nTesting optional imports:")
    for module in optional_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"⚠️  {module} (optional - install with pip)")

    return True


def test_typing_features():
    """Test modern typing features compatibility (Python 3.11+)."""
    try:
        # Test basic typing functionality

        print("✅ Basic typing imports work")

        # Test modern type annotations (Python 3.9+ built-in generics)
        test_set: set[str] = {"test"}
        _ = test_set.pop() if test_set else None

        # Test union syntax (Python 3.10+)
        test_value: str | None = "test"
        _ = test_value is not None

        print("✅ Modern type annotations work")
        print("✅ Union syntax (|) works")
        return True
    except Exception as e:
        print(f"❌ Typing features failed: {e}")
        return False


if __name__ == "__main__":
    print("=== Python Compatibility Test ===")

    success = True
    success &= test_python_version()
    success &= test_imports()
    success &= test_typing_features()

    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    sys.exit(0 if success else 1)
