"""Load fixtures for the test suite."""

from typing import Any
from unittest.mock import MagicMock

import pytest
import pytest_mock

pytest_plugins = 'tests.fixtures'


@pytest.fixture
def doctest_namespace(
    doctest_namespace: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
    mocker: pytest_mock.MockerFixture,
    dummy_event: MagicMock,
) -> dict[str, Any]:
    """Configure the global namespace for all `doctest` tests."""
    from pynetdicom.status import Status

    doctest_namespace['Status'] = Status
    doctest_namespace['caplog'] = caplog
    doctest_namespace['mocker'] = mocker
    doctest_namespace['dummy_event'] = dummy_event
    return doctest_namespace
