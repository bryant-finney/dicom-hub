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


def version_callback(ctx: typer.Context, value: bool | None) -> None:
    """Print the version of this program."""
    if not value:
        return

    rich.print(f'[bold bright_black]{command}[/bold bright_black] {dicom_hub.__version__}')
    raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: typing.Annotated[
        bool | None,
        typer.Option(
            '-V',
            '--version',
            callback=version_callback,
            show_default=False,
            is_eager=True,
            help='Print the version and exit',
        ),
    ] = None,
) -> None:
    r"""
    CLI for exercising hub functionality.

    [cyan]  ____    ____ ___ ____ ___  __  __   _   _       _        ____
     / / /   |  _ \_ _/ ___/ _ \|  \/  | | | | |_   _| |__     \ \ \
    / / /    | | | | | |  | | | | |\/| | | |_| | | | | '_ \     \ \ \
    \ \ \    | |_| | | |__| |_| | |  | | |  _  | |_| | |_) |    / / /
     \_\_\   |____/___\____\___/|_|  |_| |_| |_|\__,_|_.__/    /_/_/[/]
    """
    if version:
        version_callback(ctx, True)

    if not ctx.invoked_subcommand:
        rich.print(ctx.get_help())
