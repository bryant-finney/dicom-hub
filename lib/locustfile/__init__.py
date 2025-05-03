"""Define various `locustfile`s to configure `locust` for load testing.

## Usage

```sh
locust --host=${hostname}:${port}
```

## References

- [Writing a locustfile | docs.locust.io](https://docs.locust.io/en/stable/writing-a-locustfile.html)
"""

from __future__ import annotations

import functools
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, ParamSpec, TypeVar

import locust

import dicomlib
from dicomlib.exceptions import DICOMError

if TYPE_CHECKING:
    import locust.env

__all__ = ['REQUEST_EVENT_TRIGGERS', 'ServiceClassUser']

MSG_ID_MAX = 0xFFFF
"""The maximum value for the DICOM message ID (a `unit4`)."""

REQUEST_EVENT_TRIGGERS = {dicomlib.Verification: 'send_c_echo', dicomlib.CTImageStorage: 'send_c_store'}
"""Map SOP classes (request types) to the method names that trigger them."""

P = ParamSpec('P')
T = TypeVar('T', bound=dicomlib.Dataset)


def trigger_event_on_call(
    meth: Callable[P, T], environment: locust.env.Environment, request_class: dicomlib.SOPClass
) -> Callable[P, T]:
    """Wrap the given request method to trigger a locust request event on invocation.

    The `msg_id` parameter is incremented for each request and passed to the method.
    """
    counter = 0

    @functools.wraps(meth)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        """Trigger a request event when the method is called."""
        nonlocal counter
        counter = (counter + 1) % MSG_ID_MAX

        with environment.events.request.measure(
            request_type='DICOM',
            name=request_class.name,
        ) as _:
            resp = meth(*args, **({'msg_id': counter} | kwargs))  # type: ignore[arg-type]
            if resp.Status != dicomlib.Status.SUCCESS:
                raise DICOMError(f'request failed: {resp}')
            return resp

    return wrapper


class ServiceClassUser(locust.User):
    """Define an abstract locust user for sending DICOM requests to an SCP under test.

    References
    ----------
    - [Testing other systems/protocols](https://docs.locust.io/en/stable/testing-other-systems.html)
    """

    """"""

    abstract = True
    """Mark this class as abstract."""

    client: dicomlib.Association
    """The association with the SCP is established during the `ServiceClassUser.on_start()` method."""

    calling_ae_title = dicomlib.DEFAULT_CLIENT_AE_TITLE
    """The client's AE title."""

    called_ae_title = dicomlib.DEFAULT_SERVER_AE_TITLE
    """The server's AE title."""

    environment: locust.env.Environment
    """The locust execution environment is set by the base `locust.User` class."""

    host: str  # pyright: ignore[reportIncompatibleVariableOverride]
    """The server AE's address (e.g. 'localhost:8000')."""

    request_contexts: Iterable[dicomlib.PresentationContext] = dicomlib.DEFAULT_PRESENTATION_CONTEXTS
    """Request these presentation contexts when establishing the association."""

    timeout = 10
    """Set the timeout for the DICOM communications."""

    def __init__(self, environment: locust.env.Environment) -> None:
        super().__init__(environment)

        if not self.host:
            raise AttributeError("The 'host' attribute must be defined as the SCP's address (e.g., 'localhost:8000').")

        if ':' not in self.host:
            raise AttributeError("The port must be included in the SCP's address (the 'host' property).")

    def on_start(self) -> None:
        """Request an association with the server."""
        host, port = self.host.rsplit(':', maxsplit=1)

        self.client = dicomlib.get_association(
            (host, int(port)), self.calling_ae_title, self.called_ae_title, self.request_contexts
        )
        for sop_class, method_name in REQUEST_EVENT_TRIGGERS.items():
            meth = getattr(self.client, method_name)
            wrapped = trigger_event_on_call(meth, self.environment, sop_class)
            setattr(self.client, method_name, wrapped)

    def on_stop(self) -> None:
        """Release the association with the server."""
        self.client.release()
