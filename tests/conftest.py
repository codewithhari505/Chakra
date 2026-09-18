"""
pytest configuration and shared fixtures.
"""
import pytest

# Enable asyncio mode for all async tests
pytest_plugins = ["pytest_asyncio"]
