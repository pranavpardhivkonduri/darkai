"""
Pytest configuration for DarkAI backend tests.
"""

import pytest
import os

# Set test environment before any imports
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_darkai.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-64-chars-long-for-testing-purposes-xyz12")
os.environ.setdefault("DEBUG", "false")
