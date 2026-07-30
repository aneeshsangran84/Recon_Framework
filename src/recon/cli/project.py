"""Project management commands."""

import uuid
import click
from pathlib import Path
from datetime import datetime
from recon.config.settings import Settings
from recon.data.database import init_db, get_session
from recon.data.models import Project


@click.group()
def project():
    """Manage recon projects."""
    pass


@project.command("create")
@click.argument("name")
def create(name):
    """Create a new project."""
    settings = Settings.load()
    projects_dir = settings.workspace_dir / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    project_path = projects_dir / name
    if project_path.exists():
        click.echo(f"Project '{name}' already exists.")
        return
    project_path.mkdir()
    init_db(settings, project_path)
    session = get_session()
    proj = Project(id=str(uuid.uuid4()), name=name)
    session.add(proj)
    session.commit()
    click.echo(f"Project '{name}' created at {project_path}")


@project.command("list")
def list_projects():
    """List all projects."""
    settings = Settings.load()
    projects_dir = settings.workspace_dir / "projects"
    if not projects_dir.exists():
        click.echo("No projects found.")
        return
    for p in projects_dir.iterdir():
        if p.is_dir():
            click.echo(p.name)
