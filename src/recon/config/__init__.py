"""
Recon Framework Configuration Package.

Central configuration management using Pydantic settings with TOML files
and environment variable overrides.

Exports:
    Settings: The main configuration class.
"""

from .settings import Settings

__all__ = ["Settings"]
