"""Scan command."""

import asyncio
import click
from pathlib import Path
from recon.config.settings import Settings
from recon.data.database import init_db, get_session
from recon.core.engine import ReconEngine
from recon.plugins.registry import PluginRegistry


@click.command()
@click.option("--project", required=True, help="Project name")
@click.argument("target")
def scan(project, target):
    """Start a scan against a target within a project."""
    settings = Settings.load()
    project_path = settings.workspace_dir / "projects" / project
    if not project_path.exists():
        click.echo(f"Project '{project}' not found.")
        return

    init_db(settings, project_path)
    registry = PluginRegistry()
    engine = ReconEngine(registry, settings)
    session = get_session()

    try:
        asyncio.run(engine.run_scan(target, session))
        session.commit()
        click.echo("Scan complete.")
    except Exception as e:
        click.echo(f"Scan failed: {e}")
    finally:
        session.close()
