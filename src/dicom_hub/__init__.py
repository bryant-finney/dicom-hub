"""A service class provider for storing DICOM images and triggering processing hooks."""

from __future__ import annotations

import sys
from typing import Any

__version__ = '0.0.0'
__version_tuple__ = (0, 0, 0)


def main(*args: Any) -> None:
    """Entrypoint for launching the DICOM hub.

    Parameters
    ----------
    *args : Any
        Command-line arguments to pass to the application; defaults to `sys.argv[1:]`
    """
    if args:
        sys.argv[1:] = list(args)

    from dicom_hub.cli import app

    app(prog_name='dicom-hub', auto_envvar_prefix='DICOM_HUB')
