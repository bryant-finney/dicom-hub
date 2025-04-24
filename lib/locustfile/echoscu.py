"""Define a locust for sending `C-ECHO` requests to a peer SCP."""

from __future__ import annotations

import locust

import dicomlib
import locustfile
from dicomlib.exceptions import DICOMError


class EchoSCU(locustfile.ServiceClassUser):
    """Send an echo request to the SCP."""

    host = 'localhost:11112'

    @locust.task
    def send_c_echo(self) -> None:
        """Send a `C-ECHO` request to the SCP."""
        resp = self.client.send_c_echo()
        if resp.Status != dicomlib.Status.SUCCESS:
            raise DICOMError(f'C-ECHO request failed: {resp}')
