"""Define an abstraction to connect `dicomlib.Association`s with `locust` sessions."""

from __future__ import annotations

# Standard Library
import functools
import logging
from collections.abc import Callable
from typing import Any, ClassVar, ParamSpec

import locust
import locust.env
import locust.exception

import dicomlib
from dicomlib.exceptions import DICOMError

__all__ = ['Session', 'SessionType']

MSG_ID_MAX = 0xFFFF
"""The maximum value for the DICOM message ID (a `unit4`)."""

logger = logging.getLogger(__name__)

P = ParamSpec('P')


class SessionType(dicomlib.Association):
    """A type stub for the `Session` class."""

    def __init__(self, environment: locust.env.Environment, inst: dicomlib.Association) -> None: ...


class Session:
    """Adapter class delegates method calls to the `dicomlib.Association` instance."""

    FAILURE_THRESHOLD: ClassVar[int] = 5
    """The number of failures before the locust user is stopped."""

    REQUEST_EVENT_TRIGGERS: ClassVar = {
        'send_c_echo': dicomlib.Verification,
        'send_c_store': dicomlib.CTImageStorage,
    }
    """Map SOP classes (request types) to the method names that trigger them."""

    def __init__(self, environment: locust.env.Environment, inst: dicomlib.Association) -> None:
        self.counter, self.failures = 0, 0
        self.environment = environment
        self.inst = inst

        for method_name, sop_class in self.REQUEST_EVENT_TRIGGERS.items():
            meth = getattr(inst, method_name)
            wrapped = self._wrap(meth, sop_class)
            setattr(self, method_name, wrapped)

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying `dicomlib.Association` instance."""
        return getattr(self.inst, name)

    def _maybe_abort(self) -> None:
        """Stop the locust user after the failure threshold has been exceeded."""
        self.failures += 1
        if self.failures >= self.FAILURE_THRESHOLD:
            raise locust.exception.StopUser(f'Aborting user after {self.failures} association failures')
        raise locust.exception.RescheduleTask(f'Association is not established (failures: {self.failures})')

    def _wrap(
        self, meth: Callable[P, dicomlib.Dataset], request_class: dicomlib.SOPClass
    ) -> Callable[P, dicomlib.Dataset]:
        @functools.wraps(meth)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> dicomlib.Dataset:
            """Trigger a request event when the method is called."""
            if not self.is_established:
                logger.warning('association must be established in order to send %s', request_class.name)
                self._maybe_abort()

            self.counter = (self.counter + 1) % MSG_ID_MAX
            with self.environment.events.request.measure(
                request_type='DICOM',
                name=request_class.name,
            ) as _:
                resp = meth(*args, **({'msg_id': self.counter} | kwargs))  # type: ignore[arg-type]
                if resp.Status != dicomlib.Status.SUCCESS:
                    raise DICOMError(f'request failed: {resp}')
                return resp

        return wrapper


logger.debug('successfully imported %s', __name__)
