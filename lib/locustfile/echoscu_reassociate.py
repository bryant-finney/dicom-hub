"""Define a locust for sending `C-ECHO` requests to a peer SCP, establishing separate associations for each `C-ECHO`."""

from __future__ import annotations

import dicomlib
import locust
import locustfile
from dicomlib.exceptions import DICOMError


class EchoSCUReassociate(locustfile.ServiceClassUser):
    """Send an echo request to the SCP, establishing separate associations each time.."""

    host = 'localhost:11112'

    def on_start(self) -> None:
        """Override the parent method to skip the association."""
        self.counter = 0
        hostname, port = self.host.rsplit(':', maxsplit=1)
        self.hostname, self.port = hostname, int(port)

    def on_stop(self) -> None:
        """Override the parent method (there is no association to close)."""

    def _send_request(self) -> dicomlib.Dataset:
        self.counter = (self.counter + 1) % locustfile.MSG_ID_MAX
        with dicomlib.association(
            (self.host, self.port), self.calling_ae_title, self.called_ae_title, self.request_contexts
        ) as client:
            resp = client.send_c_echo(msg_id=self.counter)
            if resp.Status != dicomlib.Status.SUCCESS:
                raise DICOMError(f'request failed: {resp}')
            return resp

    @locust.task
    def send_c_echo(self) -> None:
        """Send a `C-ECHO` request to the SCP."""
        with self.environment.events.request.measure(
            request_type='DICOM',
            name=dicomlib.Verification.name,
        ) as _:
            self._send_request()
