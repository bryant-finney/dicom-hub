"""Global fixtures defined here are available to all tests in the test suite."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from pynetdicom import ae, events
from pynetdicom import transport as trans
from pytest_mock import MockerFixture

from dicomlib import DEFAULT_PRESENTATION_CONTEXTS


@pytest.fixture
def storescp() -> Iterator[trans.AssociationServer]:
    """Launch a `storescp` server for testing."""
    app = ae.ApplicationEntity(ae_title='pytest')
    app.supported_contexts = list(DEFAULT_PRESENTATION_CONTEXTS)

    scp = app.start_server(('', 0), block=False)
    assert scp is not None

    try:
        yield scp
    finally:
        scp.shutdown()


@pytest.fixture
def dummy_event(mocker: MockerFixture) -> MagicMock:
    """Create a mock event for testing."""
    return mocker.MagicMock(spec=events.Event)
