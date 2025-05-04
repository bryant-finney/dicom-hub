"""Define an abstraction to connect `dicomlib.Association`s with `locust` sessions."""

from __future__ import annotations

# Standard Library
import functools
import logging
from collections.abc import Callable
from typing import Any, ClassVar, ParamSpec

import locust
import locust.env

import dicomlib
from dicomlib.exceptions import DICOMError

MSG_ID_MAX = 0xFFFF
"""The maximum value for the DICOM message ID (a `unit4`)."""

logger = logging.getLogger(__name__)

P = ParamSpec('P')


class SessionType(dicomlib.Association):
    """A type stub for the `Session` class."""

    def __init__(self, environment: locust.env.Environment, inst: dicomlib.Association) -> None: ...


class Session:
    """Adapter class delegates method calls to the `dicomlib.Association` instance."""

    REQUEST_EVENT_TRIGGERS: ClassVar = {
        'send_c_echo': dicomlib.Verification,
        'send_c_store': dicomlib.CTImageStorage,
    }
    """Map SOP classes (request types) to the method names that trigger them."""

    def __init__(self, environment: locust.env.Environment, inst: dicomlib.Association) -> None:
        self.counter = 0
        self.environment = environment
        self.inst = inst

        for method_name, sop_class in self.REQUEST_EVENT_TRIGGERS.items():
            meth = getattr(inst, method_name)
            wrapped = self._wrap(meth, sop_class)
            setattr(self, method_name, wrapped)

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying `dicomlib.Association` instance."""
        return getattr(self.inst, name)

    def _wrap(
        self, meth: Callable[P, dicomlib.Dataset], request_class: dicomlib.SOPClass
    ) -> Callable[P, dicomlib.Dataset]:
        @functools.wraps(meth)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> dicomlib.Dataset:
            """Trigger a request event when the method is called."""
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
