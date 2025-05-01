"""Define a locust for sending `C-ECHO` requests to a peer SCP."""

from __future__ import annotations

import time

import locust

import dicomlib
import locustfile
from dicomlib.exceptions import DICOMError


class EchoSCU(locustfile.ServiceClassUser):
    """Send an echo request to the SCP."""

    host = 'localhost:11112'

    def on_start(self) -> None:
        """Override the parent method to skip the association."""
        self.counter = 0

    def on_stop(self) -> None:
        """Override the parent method (no association to close)."""

    def _send_request(self) -> dicomlib.Dataset:
        host, port = self.host.rsplit(':', maxsplit=1)
        self.counter = (self.counter + 1) % locustfile.MSG_ID_MAX
        with dicomlib.association(
            (host, int(port)), self.calling_ae_title, self.called_ae_title, self.request_contexts
        ) as client:
            return client.send_c_echo(msg_id=self.counter)

    @locust.task
    def send_c_echo(self) -> None:
        """Send a `C-ECHO` request to the SCP."""
        t_start = time.perf_counter()
        try:
            resp = self._send_request()
        except Exception as e:
            self.environment.events.request.fire(
                request_type='DICOM',
                name=dicomlib.Verification.name,
                response_time=(time.perf_counter() - t_start) * 1000,
                response_length=0,
                exception=e,
            )
            raise

        exc = DICOMError(f'request failed: {resp}') if resp.Status != dicomlib.Status.SUCCESS else None
        self.environment.events.request.fire(
            request_type='DICOM',
            name=dicomlib.Verification.name,
            response_time=(time.perf_counter() - t_start) * 1000,
            response_length=len(resp),
            exception=exc,
        )
