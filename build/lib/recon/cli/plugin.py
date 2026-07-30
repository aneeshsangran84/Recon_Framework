"""
Plugin management commands.

Usage:
    recon plugin list
    recon plugin info <name>
    recon plugin enable <name>
    recon plugin disable <name>
"""

import click
from recon.plugins.registry import PluginRegistry
from recon.config.settings import Settings
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def plugin():
    """Manage reconnaissance plugins."""
    pass

@plugin.command("list")
def list_plugins():
    """List all available plugins."""
    registry = PluginRegistry()
    plugins = registry.list_plugins()

    if not plugins:
        console.print("[yellow]No plugins discovered.[/]")
        return

    table = Table(title="Available Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Description")
    table.add_column("Author")
    table.add_column("Targets")

    settings = Settings.load()
    disabled = settings.disabled_plugins

    for meta in plugins:
        enabled = meta.name not in disabled
        style = "" if enabled else "[dim]"
        table.add_row(
            f"{style}{meta.name}{'[/]' if not enabled else ''}",
            meta.version,
            meta.description,
            meta.author,
            ", ".join(meta.supported_target_types),
        )

    console.print(table)

@plugin.command("info")
@click.argument("name")
def info(name):
    """Show detailed information about a plugin."""
    registry = PluginRegistry()
    try:
        meta = registry.get_plugin(name).get_metadata()
        console.print(f"[bold]Name:[/] {meta.name}")
        console.print(f"[bold]Version:[/] {meta.version}")
        console.print(f"[bold]Author:[/] {meta.author}")
        console.print(f"[bold]Description:[/] {meta.description}")
        console.print(f"[bold]Supported targets:[/] {', '.join(meta.supported_target_types)}")
        if meta.dependencies:
            console.print(f"[bold]Dependencies:[/] {', '.join(meta.dependencies)}")
        if meta.system_tools:
            console.print(f"[bold]System tools:[/] {', '.join(meta.system_tools)}")
    except KeyError:
        console.print(f"[red]Plugin '{name}' not found.[/]")

@plugin.command("enable")
@click.argument("name")
def enable(name):
    """Enable a previously disabled plugin."""
    settings = Settings.load()
    if name not in settings.disabled_plugins:
        console.print(f"Plugin '{name}' is already enabled.")
        return

    # Modify the set and save config
    new_disabled = settings.disabled_plugins - {name}
    # We need to save the updated config
    _save_disabled_plugins(new_disabled)
    console.print(f"Plugin '{name}' enabled.")

@plugin.command("disable")
@click.argument("name")
def disable(name):
    """Disable a plugin (exclude from scans)."""
    settings = Settings.load()
    if name in settings.disabled_plugins:
        console.print(f"Plugin '{name}' is already disabled.")
        return

    new_disabled = settings.disabled_plugins | {name}
    _save_disabled_plugins(new_disabled)
    console.print(f"Plugin '{name}' disabled.")


def _save_disabled_plugins(disabled_set):
    """
    Persist the set of disabled plugins to the user config file.
    """
    import toml
    from pathlib import Path

    user_cfg_path = Path("~/.config/recon/config.toml").expanduser()
    user_cfg_path.parent.mkdir(parents=True, exist_ok=True)

    config_data = {}
    if user_cfg_path.exists():
        with open(user_cfg_path, "r") as f:
            config_data = toml.load(f)

    # Ensure plugins section exists
    if "plugins" not in config_data:
        config_data["plugins"] = {}
    config_data["plugins"]["disabled_plugins"] = sorted(disabled_set)

    with open(user_cfg_path, "w") as f:
        toml.dump(config_data, f)