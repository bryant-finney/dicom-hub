"""Define a locust for sending `C-ECHO` requests to a peer SCP, establishing separate associations for each `C-ECHO`."""

from __future__ import annotations

import locust

from tests.locust import ServiceClassUser


class EchoSCUReassociate(ServiceClassUser):
    """Send an echo request to the SCP, establishing separate associations each time."""

    host = 'localhost:11112'

    @locust.task
    def send_c_echo(self) -> None:
        """Send a `C-ECHO` request to the SCP."""
        with self.client.session as session:
            session.send_c_echo()
