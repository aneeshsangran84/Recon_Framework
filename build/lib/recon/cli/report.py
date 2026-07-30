"""
Report generation commands.

Usage:
    recon report generate --project <name> --format pdf --output report.pdf
    recon report generate --project <name> --format html --output report.html
    recon report generate --project <name> --format json --output data.json
"""

import click
from pathlib import Path
from recon.config.settings import Settings
from recon.data.database import init_db, get_session
from recon.reporting.engine import ReportEngine

@click.command(name="generate")
@click.option("--project", "-p", required=True, help="Project name to report on")
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["html", "pdf", "md", "json", "csv", "xml"], case_sensitive=False),
    default="html",
    help="Output format"
)
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file path")
@click.option("--template", "-t", help="Custom template name (optional)")
@click.pass_context
def generate(ctx, project, fmt, output, template):
    """Generate a report for a project."""
    settings = Settings.load()
    project_path = settings.workspace_dir / "projects" / project
    if not project_path.exists():
        click.echo(f"Project '{project}' not found.")
        return

    # Initialise database connection for the project
    init_db(settings, project_path)
    session = get_session()

    # Default output path if not provided
    if output is None:
        ext_map = {"html": ".html", "pdf": ".pdf", "md": ".md", "json": ".json", "csv": ".csv", "xml": ".xml"}
        suffix = ext_map.get(fmt, ".html")
        output = Path(f"{project}_report{suffix}")

    engine = ReportEngine(settings=settings)
    try:
        result = engine.generate(
            session=session,
            project_name=project,
            output_format=fmt,
            output_path=output,
            template_name=template,
        )
        click.echo(f"Report generated: {result}")
    except Exception as e:
        click.echo(f"Error generating report: {e}")
    finally:
        session.close()


# Create the report command group (we'll attach 'generate' as its subcommand)
@click.group()
def report():
    """Generate and export assessment reports."""
    pass

report.add_command(generate)