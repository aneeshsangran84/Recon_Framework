"""
Tests for CLI commands using Click's CliRunner.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from recon.cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_version(runner):
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


def test_cli_about(runner):
    result = runner.invoke(cli, ["about"])
    assert result.exit_code == 0
    assert "Recon Framework" in result.output


@patch("recon.cli.project.Settings.load")
@patch("recon.cli.project.init_db")
@patch("recon.cli.project.get_session")
def test_project_create(mock_session, mock_init_db, mock_settings_load, runner, tmp_path):
    mock_settings_load.return_value.workspace_dir = tmp_path / "workspace"
    result = runner.invoke(cli, ["project", "create", "testproj"])
    assert result.exit_code == 0
    assert "created" in result.output


@patch("recon.cli.scan.Settings.load")
@patch("recon.cli.scan.init_db")
@patch("recon.cli.scan.get_session")
@patch("recon.cli.scan.PluginRegistry")
@patch("recon.cli.scan.ReconEngine")
def test_scan_basic(mock_engine, mock_registry, mock_session, mock_init_db, mock_settings_load, runner, tmp_path):
    mock_settings_load.return_value.workspace_dir = tmp_path / "workspace"
    (tmp_path / "workspace" / "projects" / "testproj").mkdir(parents=True)
    result = runner.invoke(cli, ["scan", "--project", "testproj", "example.com"])
    assert result.exit_code == 0
    mock_engine.return_value.run_scan.assert_called_once()