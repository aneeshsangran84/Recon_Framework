"""Report generation commands."""

import click
from pathlib import Path
from recon.config.settings import Settings
from recon.data.database import init_db, get_session
from recon.reporting.engine import ReportEngine


@click.group()
def report():
    """Generate and export assessment reports."""
    pass


@report.command("generate")
@click.option("--project", "-p", required=True, help="Project name")
@click.option("--format", "-f", "fmt",
              type=click.Choice(["html", "pdf", "md", "json", "csv", "xml"]),
              default="html", help="Output format")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file path")
def generate(project, fmt, output):
    """Generate a report for a project."""
    settings = Settings.load()
    project_path = settings.workspace_dir / "projects" / project
    if not project_path.exists():
        click.echo(f"Project '{project}' not found.")
        return

    init_db(settings, project_path)
    session = get_session()

    if output is None:
        ext_map = {"html": ".html", "pdf": ".pdf", "md": ".md",
                   "json": ".json", "csv": ".csv", "xml": ".xml"}
        output = Path(f"{project}_report{ext_map.get(fmt, '.html')}")

    engine = ReportEngine(settings=settings)
    try:
        result = engine.generate(
            session=session, project_name=project,
            output_format=fmt, output_path=output,
        )
        click.echo(f"Report generated: {result}")
    except Exception as e:
        click.echo(f"Error: {e}")
    finally:
        session.close()
