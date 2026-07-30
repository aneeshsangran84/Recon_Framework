"""
Recon Framework - CLI Package

Provides all command-line commands (project, scan, report, plugin, config).
"""

from .main import cli
from .project import project
from .scan import scan
from .report import report
from .plugin import plugin
from .config import config

# Register subcommands with the main group (done in main.py)
__all__ = ["cli", "project", "scan", "report", "plugin", "config"]