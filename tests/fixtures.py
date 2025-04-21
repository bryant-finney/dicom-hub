"""Global fixtures defined here are available to all tests in the test suite."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pynetdicom import ae
from pynetdicom import transport as trans

from pynetdicomlib import DEFAULT_PRESENTATION_CONTEXTS


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
