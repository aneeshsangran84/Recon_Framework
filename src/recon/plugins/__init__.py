"""
Recon Framework - Plugin System

Auto‑discovers built‑in and user‑provided plugins, manages their lifecycle,
and provides the PluginRegistry used by the engine.
"""

from .base import BasePlugin, PluginMetadata
from .registry import PluginRegistry

__all__ = ["BasePlugin", "PluginMetadata", "PluginRegistry"]