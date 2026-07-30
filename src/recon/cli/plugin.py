"""Plugin management commands."""

import click
from pathlib import Path
from recon.plugins.registry import PluginRegistry
from recon.config.settings import Settings
from rich.console import Console
from rich.table import Table

console = Console()


def _get_disabled_plugins():
    """Read disabled plugins directly from config file."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    user_cfg_path = Path("~/.config/recon/config.toml").expanduser()
    if user_cfg_path.exists():
        with open(user_cfg_path, "rb") as f:
            config = tomllib.load(f)
        plugins_cfg = config.get("plugins", {})
        disabled = plugins_cfg.get("disabled_plugins", [])
        return set(disabled) if disabled else set()
    return set()


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

    # Read disabled list directly from config file
    disabled = _get_disabled_plugins()

    table = Table(title="Available Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Description")
    table.add_column("Targets")

    for meta in plugins:
        status = "[red]disabled[/]" if meta.name in disabled else "[green]enabled[/]"
        table.add_row(
            meta.name, meta.version, status, meta.description,
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
        console.print(f"[bold]Description:[/] {meta.description}")
        console.print(f"[bold]Author:[/] {meta.author}")
        console.print(f"[bold]Targets:[/] {', '.join(meta.supported_target_types)}")
        if meta.dependencies:
            console.print(f"[bold]Dependencies:[/] {', '.join(meta.dependencies)}")
    except KeyError:
        console.print(f"[red]Plugin '{name}' not found.[/]")


@plugin.command("enable")
@click.argument("name")
def enable(name):
    """Enable a disabled plugin."""
    disabled = _get_disabled_plugins()
    if name not in disabled:
        console.print(f"Plugin '{name}' is already enabled.")
        return
    disabled.remove(name)
    _save_disabled_plugins(disabled)
    console.print(f"[green]Plugin '{name}' enabled.[/]")


@plugin.command("disable")
@click.argument("name")
def disable(name):
    """Disable a plugin."""
    disabled = _get_disabled_plugins()
    if name in disabled:
        console.print(f"Plugin '{name}' is already disabled.")
        return
    disabled.add(name)
    _save_disabled_plugins(disabled)
    console.print(f"[yellow]Plugin '{name}' disabled.[/]")


def _save_disabled_plugins(disabled_set):
    """Save disabled plugins to user config."""
    try:
        import tomli_w
    except ImportError:
        console.print("[red]Install tomli_w: pip install tomli_w[/]")
        return

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    user_cfg_path = Path("~/.config/recon/config.toml").expanduser()
    user_cfg_path.parent.mkdir(parents=True, exist_ok=True)

    config_data = {}
    if user_cfg_path.exists():
        with open(user_cfg_path, "rb") as f:
            config_data = tomllib.load(f)

    if "plugins" not in config_data:
        config_data["plugins"] = {}
    config_data["plugins"]["disabled_plugins"] = sorted(disabled_set)

    with open(user_cfg_path, "wb") as f:
        tomli_w.dump(config_data, f)
