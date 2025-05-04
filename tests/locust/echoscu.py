"""Define a locust for sending `C-ECHO` requests to a peer SCP."""

from __future__ import annotations

import locust

from tests.locust import ServiceClassUser, ServiceClassUserSession

__all__ = ['EchoSCU']


class EchoSCU(ServiceClassUser):
    """Send an echo request to the SCP, establishing separate associations each time."""

    @locust.task
    def send_c_echo(self) -> None:
        """Send a `C-ECHO` request to the SCP."""
        with self.client.session as session:
            session.send_c_echo()


class EchoSCUSession(ServiceClassUserSession):
    """Send an echo request to the SCP."""

    @locust.task
    def send_c_echo(self) -> None:
        """Send a `C-ECHO` request to the SCP."""
        self.session.send_c_echo()
