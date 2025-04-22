"""Define handlers for DICOM events."""

from __future__ import annotations

import logging
import tempfile
import uuid
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import ParamSpec, TypeVar

import pydicom
from pynetdicom import events
from pynetdicom.status import Status

__all__ = [
    'c_store_tmp_dir',
]

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


def log_event(level: int | str = logging.DEBUG) -> Callable[[events.Handler[P]], events.Handler[P]]:
    """Log that the event at the given level.

    Examples
    --------
    This decorator can be used to log events at the DEBUG level:

    >>> @log_event(logging.DEBUG)
    ... def my_handler(event: events.Event) -> int:
    ...     return 0

    >>> with caplog.at_level(logging.DEBUG, logger=__name__):
    ...     _ = my_handler(dummy_event)

    >>> len(caplog.records), caplog.messages[0]
    (1, "handle event '...' with handler 'dicomlib.handlers.my_handler()'")

    >>> caplog.clear()  # clean up

    Index errors are handled and a warning message is logged:

    >>> with caplog.at_level(logging.WARNING, logger=__name__):
    ...     _ = my_handler(None)

    >>> len(caplog.records), caplog.messages[0]
    (1, 'failed to log event for handler <function my_handler at ...>')

    Parameters
    ----------
    level
        The logging level to use; defaults to `logging.DEBUG`

    Returns
    -------
    The wrapped event handler
    """
    log_level = logging.getLevelNamesMapping()[level] if isinstance(level, str) else level

    def decorator(handler: events.Handler[P]) -> events.Handler[P]:
        """Create a wrapper to log the events handled by the given event handler.

        Parameters
        ----------
        handler
            The event handler to wrap with a logging statement
        """

        @wraps(handler)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> pydicom.Dataset | int:
            """Log the event and call the handler."""
            try:
                event = str(args[0].event)  # type: ignore[attr-defined]
            except (IndexError, AttributeError):
                logger.warning('failed to log event for handler %s', handler)
            else:
                logger.log(
                    log_level,
                    "handle event '%s' with handler '%s.%s()'",
                    event,
                    __name__,
                    handler.__name__,
                    stacklevel=2,
                )

            return handler(*args, **kwargs)

        return wrapper

    return decorator


@log_event(logging.DEBUG)
def c_store_tmp_dir(event: events.Event) -> pydicom.Dataset | int:
    """Handle C-STORE requests by writing the data to a temporary directory in the filesystem.

    Examples
    --------
    This handler writes the received DICOM dataset to a file in the system's temporary directory:

    >>> mock_gettempdir = mocker.patch('tempfile.gettempdir', return_value='/tmp/pytest')
    >>> with caplog.at_level(logging.DEBUG, logger=__name__):
    ...     _ = c_store_tmp_dir(dummy_event)

    >>> len(caplog.records), caplog.messages[1]
    (2, 'writing to file: /tmp/pytest/dicomlib.handlers/...')

    Parameters
    ----------
    event
        The C-STORE event to handle
    """
    uid = uuid.uuid4()
    tmp_file = Path(tempfile.gettempdir()) / __name__ / f'{uid}.dcm'
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    logger.debug('writing to file: %s', tmp_file)
    event.dataset.save_as(tmp_file)
    return Status.SUCCESS


logger.debug('successfully imported %s', __name__)
