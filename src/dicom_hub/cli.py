"""Entrypoint CLI for launching the application."""

from __future__ import annotations

import sys
import typing
from pathlib import Path

import rich
import typer

import dicom_hub

app = typer.Typer(
    context_settings={'help_option_names': ['-h', '--help']}, no_args_is_help=True, rich_markup_mode='rich'
)
this = Path(sys.argv[0]).resolve()
command = this.name if this.name != '__main__.py' else this.parent.name


def help_callback(ctx: typer.Context, value: bool | None = None) -> None:
    """Print the help message for the command."""
    if ctx.resilient_parsing:  # pragma: no cover
        return

    if value:
        rich.print(ctx.get_help())
        raise typer.Exit()


HelpAnnotation = typing.Annotated[
    bool | None,
    typer.Option(
        '-h',
        '--help',
        callback=help_callback,
        rich_help_panel='Global',
        show_default=False,
        is_eager=True,
        help='Show this message and exit.',
    ),
]


def version_callback(ctx: typer.Context, value: bool | None) -> None:
    """Print the version of this program."""
    if not value:
        return

    rich.print(f'[bold bright_black]{command}[/bold bright_black] {dicom_hub.__version__}')
    raise typer.Exit()


VersionAnnotation = typing.Annotated[
    bool | None,
    typer.Option(
        '-V',
        '--version',
        callback=version_callback,
        rich_help_panel='Global',
        show_default=False,
        show_envvar=False,
        is_eager=True,
        help='Print the version and exit.',
    ),
]


@app.command()
def version(ctx: typer.Context, get_help: HelpAnnotation = None, version: VersionAnnotation = None) -> None:
    """Print the version and exit."""
    version_callback(ctx, True)


@app.callback(invoke_without_command=True, no_args_is_help=True)
def main(ctx: typer.Context, get_help: HelpAnnotation = None, version: VersionAnnotation = None) -> None:
    r"""
    CLI for exercising hub functionality.

    [cyan]  ____    ____ ___ ____ ___  __  __   _   _       _        ____
     / / /   |  _ \_ _/ ___/ _ \|  \/  | | | | |_   _| |__     \ \ \
    / / /    | | | | | |  | | | | |\/| | | |_| | | | | '_ \     \ \ \
    \ \ \    | |_| | | |__| |_| | |  | | |  _  | |_| | |_) |    / / /
     \_\_\   |____/___\____\___/|_|  |_| |_| |_|\__,_|_.__/    /_/_/[/]
    """
