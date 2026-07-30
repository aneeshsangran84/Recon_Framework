"""Configuration management commands."""

import click
from recon.config.settings import Settings
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def config():
    """View and modify framework configuration."""
    pass


@config.command("show")
def show():
    """Display current effective configuration."""
    settings = Settings.load()
    table = Table(title="Current Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    for field_name, field_value in sorted(settings.model_dump().items()):
        if isinstance(field_value, (dict, list, set)):
            field_value = str(field_value)
        table.add_row(field_name, str(field_value))

    console.print(table)


@config.command("set")
@click.argument("key")
@click.argument("value")
def set_value(key, value):
    """Set a configuration value (e.g., general.threads 20)."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    from pathlib import Path

    user_cfg_path = Path("~/.config/recon/config.toml").expanduser()
    user_cfg_path.parent.mkdir(parents=True, exist_ok=True)

    config_data = {}
    if user_cfg_path.exists():
        with open(user_cfg_path, "rb") as f:
            config_data = tomllib.load(f)

    parts = key.split(".")
    if len(parts) < 2:
        console.print("[red]Key must be in format 'section.option'[/]")
        return

    section, option = parts[0], parts[1]
    if section not in config_data:
        config_data[section] = {}

    # Type coercion
    if value.isdigit():
        typed_value = int(value)
    elif value.lower() in ("true", "false"):
        typed_value = value.lower() == "true"
    else:
        typed_value = value

    config_data[section][option] = typed_value

    # Write with tomli_w or manually
    try:
        import tomli_w
    except ImportError:
        console.print("[red]Install tomli_w: pip install tomli_w[/]")
        return

    with open(user_cfg_path, "wb") as f:
        tomli_w.dump(config_data, f)

    console.print(f"[green]Set {key} = {typed_value}[/]")
