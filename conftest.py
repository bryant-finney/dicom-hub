"""Load fixtures for the test suite."""

from typing import Any

import pytest

pytest_plugins = 'tests.fixtures'


@pytest.fixture
def doctest_namespace(doctest_namespace: dict[str, Any]) -> dict[str, Any]:
    """Configure the global namespace for all `doctest` tests."""
    from pynetdicom.status import Status

    doctest_namespace['Status'] = Status
    return doctest_namespace
