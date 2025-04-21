"""Verify the `dicom_hub.cli` works as expected."""

from __future__ import annotations

from unittest.mock import MagicMock

import click.testing
import pytest
import sh
from pytest_mock import MockerFixture
from typer import testing

from dicom_hub import cli, main

runner = testing.CliRunner()


def dicom_hub(*args: str) -> click.testing.Result:
    """Execute the `dicom-hub` command with the given arguments."""
    return runner.invoke(cli.app, args, prog_name='dicom-hub')


@pytest.fixture
def mock_sys_exit(mocker: MockerFixture) -> MagicMock:
    """Mock `sys.exit` to prevent exiting the test session."""
    return mocker.patch('sys.exit')


def test_main_function(mock_sys_exit: MagicMock) -> None:
    """Verify that the main function can be invoked to override `sys.argv`."""
    main('--help')
    mock_sys_exit.assert_called_once()


def test_version_command_or_arg() -> None:
    """Verify the 'version' command produces the same output as the '--version' argument."""
    version_out = dicom_hub('version')
    version_arg_out = dicom_hub('--version')

    assert 0 == version_out.exit_code == version_arg_out.exit_code
    assert version_out.output == version_arg_out.output


def test_help_by_default() -> None:
    """Verify that the help text is shown when `dicom-hub` is invoked without arguments."""
    help_out = dicom_hub('--help')
    no_args_out = dicom_hub()

    assert 0 == help_out.exit_code == no_args_out.exit_code
    assert help_out.output == no_args_out.output


def test_call_module() -> None:
    """Verify that the `dicom_hub.cli` CLI is invoked when calling the `dicom_hub` module."""
    stdout = sh.python('-m', 'dicom_hub')

    assert 'Usage:' in stdout
    assert 'dicom-hub' in stdout
