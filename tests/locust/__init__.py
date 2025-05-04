"""Define various `locustfile`s to configure `locust` for load testing.

## Usage

```sh
locust --host=${hostname}:${port}
```

## References

- [Writing a locustfile | docs.locust.io](https://docs.locust.io/en/stable/writing-a-locustfile.html)
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING

import locust

import dicomlib

# note: this import enables static type analysis of the `Session` class because mypy / pyright didn't pick up on the
# ...     `__getattr__` method
if TYPE_CHECKING:  # pragma: no cover
    import locust.env

    from tests.locust.session import SessionType as Session
else:
    from tests.locust.session import Session

__all__ = ['DICOMClient', 'ServiceClassUser', 'ServiceClassUserSession', 'Session']

logger = logging.getLogger(__name__)


class DICOMClient:
    """A client for communicating with a remote application entity."""

    def __init__(  # noqa: PLR0913
        self,
        environment: locust.env.Environment,
        host: str,
        called_ae_title: str,
        calling_ae_title: str,
        request_contexts: Iterable[dicomlib.PresentationContext],
        timeout: float,
    ) -> None:
        self.environment = environment
        self.hostname, port = host.rsplit(':', maxsplit=1)
        self.port = int(port)
        self.called_ae_title = called_ae_title
        self.calling_ae_title = calling_ae_title
        self.request_contexts = request_contexts
        self.timeout = timeout

    @property
    @contextlib.contextmanager
    def session(self) -> Iterator[Session]:
        """Context manager provides a similar API to `dicomlib.association()`."""
        session = self.get_session()
        try:
            yield session
        finally:
            if session.is_established:
                session.release()

    def get_session(self) -> Session:
        """Start a session by establishing an association with the SCP server."""
        return Session(
            self.environment,
            dicomlib.get_association(
                (self.hostname, self.port),
                self.calling_ae_title,
                self.called_ae_title,
                self.request_contexts,
                self.timeout,
            ),
        )


class ServiceClassUser(locust.User):
    """Define an abstract locust user for sending DICOM requests to an SCP under test.

    References
    ----------
    - [Testing other systems/protocols | locust](https://docs.locust.io/en/stable/testing-other-systems.html)
    """

    abstract = True
    """Mark this class as abstract."""

    environment: locust.env.Environment
    """The locust execution environment is set by the base `locust.User` class."""

    host: str  # pyright: ignore[reportIncompatibleVariableOverride]
    """The server AE's address (e.g. 'localhost:8000')."""

    calling_ae_title = dicomlib.DEFAULT_CLIENT_AE_TITLE
    """The client's AE title."""

    called_ae_title = dicomlib.DEFAULT_SERVER_AE_TITLE
    """The server's AE title."""

    request_contexts: Iterable[dicomlib.PresentationContext] = dicomlib.DEFAULT_PRESENTATION_CONTEXTS
    """Request these presentation contexts when establishing the association."""

    timeout = 10
    """Set the timeout for the DICOM communications."""

    def __init__(self, environment: locust.env.Environment) -> None:
        super().__init__(environment)
        self.client = DICOMClient(
            environment, self.host, self.called_ae_title, self.calling_ae_title, self.request_contexts, self.timeout
        )


class ServiceClassUserSession(ServiceClassUser):
    """Define a locust user for sending DICOM requests to an SCP under test, sharing a single association."""

    abstract = True
    """Mark this class as abstract."""

    session: Session
    """The session to use for sending requests."""

    def on_start(self) -> None:
        """Request an association with the server."""
        self.session = self.client.get_session()

    def on_stop(self) -> None:
        """Release the association with the server."""
        self.session.release()
