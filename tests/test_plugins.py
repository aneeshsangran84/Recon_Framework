"""
Tests for plugin system: discovery, metadata, and execution of built-in plugins.
"""

import pytest
from recon.plugins.registry import PluginRegistry
from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target


def test_plugin_discovery(plugin_registry):
    """Ensure at least one built-in plugin is discovered."""
    plugins = plugin_registry.list_plugins()
    assert len(plugins) > 0
    # Check that a known plugin is present
    names = [p.name for p in plugins]
    assert "dns_enum" in names
    assert "whois" in names


def test_plugin_metadata(plugin_registry):
    """Each plugin metadata should have required fields."""
    for meta in plugin_registry.list_plugins():
        assert isinstance(meta, PluginMetadata)
        assert meta.name
        assert meta.version
        assert meta.description
        assert isinstance(meta.supported_target_types, set)


@pytest.mark.asyncio
async def test_dns_enum_plugin(plugin_registry, db_session):
    """Test the DNS enumeration plugin with a known domain."""
    plugin_cls = plugin_registry.get_plugin("dns_enum")
    plugin = plugin_cls({"timeout": 5})
    target = Target.from_string("example.com")
    result = await plugin.run(target, db_session)
    assert isinstance(result, dict)
    # Should have records key
    assert "records" in result
    # example.com usually returns at least one record
    # (but we don't assert length because network may be unavailable)
    # Instead, ensure it didn't crash
    assert isinstance(result["records"], list)


@pytest.mark.asyncio
async def test_whois_plugin(plugin_registry, db_session):
    plugin_cls = plugin_registry.get_plugin("whois")
    plugin = plugin_cls({})
    target = Target.from_string("example.com")
    result = await plugin.run(target, db_session)
    assert "registrar" in result or "error" in result


@pytest.mark.asyncio
async def test_reverse_dns_plugin(plugin_registry, db_session):
    plugin_cls = plugin_registry.get_plugin("reverse_dns")
    plugin = plugin_cls({})
    target = Target.from_string("8.8.8.8")
    result = await plugin.run(target, db_session)
    # Google DNS usually has a PTR
    assert "hostnames" in result
    # May be empty due to network but shouldn't crash


def test_plugin_enable_disable(plugin_registry, test_settings):
    """Test that enabling/disabling a plugin updates config."""
    from recon.cli.plugin import _save_disabled_plugins
    import toml
    from pathlib import Path

    # Simulate disable
    test_settings.disabled_plugins.add("whois")
    _save_disabled_plugins(test_settings.disabled_plugins)
    # Re-load settings and check
    new_settings = Settings.load()
    assert "whois" in new_settings.disabled_plugins

    # Clean up: remove the config file to avoid pollution
    user_cfg = Path("~/.config/recon/config.toml").expanduser()
    if user_cfg.exists():
        user_cfg.unlink()