"""
Shared pytest fixtures for Recon Framework tests.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recon.config.settings import Settings
from recon.data.database import init_db, get_session
from recon.data.models import Base
from recon.plugins.registry import PluginRegistry


@pytest.fixture(scope="session")
def temp_dir_session():
    """Create a temporary directory for the whole test session."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace directory for a single test."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


@pytest.fixture
def test_settings(temp_workspace):
    """Return a Settings object pointing to the temporary workspace."""
    return Settings(
        workspace_dir=temp_workspace,
        threads=2,
        timeout=5,
        log_level="WARNING",
        log_file_enabled=False,
        disabled_plugins=set(),
    )


@pytest.fixture
def db_session(test_settings, tmp_path):
    """Create an isolated SQLite database and return a session."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    init_db(test_settings, project_dir)
    session = get_session()
    yield session
    session.close()


@pytest.fixture
def plugin_registry():
    """Return a fresh PluginRegistry (discovers built-in plugins)."""
    return PluginRegistry()