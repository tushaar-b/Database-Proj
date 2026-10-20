"""Pytest configuration and global fixtures for IntelliVest."""
import pytest


@pytest.fixture(scope="session")
def env_settings():
    """Provides test settings."""
    from backend.config import settings
    return settings
