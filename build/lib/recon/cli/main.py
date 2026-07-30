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
    # ctx.ensure_object(dict) will be used later for shared state
    ctx.ensure_object(dict)

@cli.command()
def about():
    """Show framework information."""
    console.print("[bold green]Recon Framework[/] v{}".format(__version__))
    console.print("Enterprise Reconnaissance for Authorized Assessments")