"""Main CLI entry point."""
import click
from rich.console import Console
from recon import __version__

console = Console()


@click.group()
@click.version_option(__version__, prog_name="recon")
@click.pass_context
def cli(ctx):
    """Recon Framework - Authorized Security Reconnaissance"""
    ctx.ensure_object(dict)


@cli.command()
def about():
    """Show framework information."""
    console.print(f"[bold green]Recon Framework[/] v{__version__}")
    console.print("Enterprise Reconnaissance for Authorized Assessments")


# Import and register subcommands
from .project import project
from .scan import scan
from .report import report
from .plugin import plugin
from .config import config

cli.add_command(project)
cli.add_command(scan)
cli.add_command(report)
cli.add_command(plugin)
cli.add_command(config)
