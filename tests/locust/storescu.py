"""Define a locust for sending `C-ECHO` requests to a peer SCP."""

from __future__ import annotations

import logging
from typing import cast

import locust
import pydicom
from pydicom.data import get_testdata_file

from tests.locust import ServiceClassUserSession

__all__ = ['StoreSCU']

logger = logging.getLogger(__name__)


class StoreSCU(ServiceClassUserSession):
    """Send a `C-STORE` request to the SCP, sharing a single association throughout the test."""

    host = 'localhost:11112'

    def on_start(self) -> None:
        """Extend the parent `on_start` method to read the 'CT_small.dcm' test data file."""
        super().on_start()
        self.ct_small_dataset = cast(pydicom.Dataset, get_testdata_file('CT_small.dcm', read=True))

    @locust.task
    def send_c_store(self) -> None:
        """Send a `C-STORE` request to the SCP."""
        self.session.send_c_store(self.ct_small_dataset)


logger.debug('successfully imported %s', __name__)
