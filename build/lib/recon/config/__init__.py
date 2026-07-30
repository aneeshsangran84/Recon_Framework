"""
Recon Framework Configuration Package.

Central configuration management using Pydantic settings with TOML files
and environment variable overrides.

Exports:
    Settings: The main configuration class.
    load_config: Convenience function to load settings from files.
"""

from .settings import Settings, load_config

__all__ = ["Settings", "load_config"]