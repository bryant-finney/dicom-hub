"""Interface module for the `pynetdicom` library provides abstractions and utilities for DICOM networking.

This package wraps all functionality provided by the `pynetdicom` library that is used by the rest of the application.
"""

import contextlib
import logging
from collections.abc import Iterable, Iterator
from typing import ParamSpec, TypedDict, TypeVar

import pynetdicom
from pydicom.dataset import Dataset
from pydicom.filereader import dcmread
from pydicom.uid import UID
from pynetdicom import ae, build_context
from pynetdicom import presentation as pres
from pynetdicom import transport as trans
from pynetdicom.ae import ApplicationEntity
from pynetdicom.association import Association
from pynetdicom.events import EVT_C_STORE, EventHandlerType
from pynetdicom.presentation import PresentationContext
from pynetdicom.sop_class import (
    ComputedRadiographyImageStorage,
    CTImageStorage,
    EnhancedCTImageStorage,
    SOPClass,
    Verification,
)
from pynetdicom.status import Status

# needed for Python 3.10
from typing_extensions import NotRequired

from dicomlib import exceptions

__all__ = [
    'DEFAULT_CLIENT_AE_TITLE',
    'DEFAULT_PRESENTATION_CONTEXTS',
    'DEFAULT_SERVER_AE_TITLE',
    'DEFAULT_TIMEOUTS',
    'EVT_C_STORE',
    'UID',
    'ApplicationEntity',
    'Association',
    'CTImageStorageContext',
    'ComputedRadiographyImageStorageContext',
    'Dataset',
    'EnhancedCTImageStorageContext',
    'PresentationContext',
    'SOPClass',
    'Status',
    'TimeoutOpts',
    'VerificationContext',
    'association',
    'dcmread',
    'get_association',
    'server',
]

P = ParamSpec('P')

DEFAULT_PRESENTATION_CONTEXTS = (
    CTImageStorageContext := build_context(CTImageStorage),
    ComputedRadiographyImageStorageContext := build_context(ComputedRadiographyImageStorage),
    EnhancedCTImageStorageContext := build_context(EnhancedCTImageStorage),
    VerificationContext := build_context(Verification),
)
"""These presentation contexts are used by default when establishing associations."""

DEFAULT_CLIENT_AE_TITLE = 'dicom-hub.client'
"""The default AE title to use for client `pynetdicom.ae.ApplicationEntity`s."""

DEFAULT_SERVER_AE_TITLE = 'dicom-hub.server'
"""The default AE title to use for server `pynetdicom.ae.ApplicationEntity`s."""

logger = logging.getLogger(__name__)


class TimeoutOpts(TypedDict):
    """Timeout options for the association.

    Attributes
    ----------
    acse_timeout
        The ACSE timeout in seconds; a value of `None` means no timeout (default: `30`)

    connection_timeout
        The connection timeout in seconds; a value of `None` means no timeout (default: `None`)

    dimse_timeout
        The DIMSE timeout in seconds; a value of `None` means no timeout (default: `30`)

    network_timeout
        The network timeout in seconds; a value of `None` means no timeout (default: `60`)

    References
    ----------
    - See [Application Entity | API Reference | pynetdicom](https://pydicom.github.io/pynetdicom/dev/reference/generated/pynetdicom.ae.ApplicationEntity.html)
      for the default timeout values
    """

    acse_timeout: NotRequired[int | float | None]
    """The ACSE timeout in seconds; a value of `None` means no timeout (default: `30`)."""

    connection_timeout: NotRequired[int | float | None]
    """The connection timeout in seconds; a value of `None` means no timeout (default: `None`)."""

    dimse_timeout: NotRequired[int | float | None]
    """The DIMSE timeout in seconds; a value of `None` means no timeout (default: `30`)."""

    network_timeout: NotRequired[int | float | None]
    """The network timeout in seconds; a value of `None` means no timeout (default: `60`)"""


DEFAULT_TIMEOUTS = TimeoutOpts(acse_timeout=30, connection_timeout=None, dimse_timeout=30, network_timeout=60)
"""Override the default timeout values used for associations.

References
----------
- See [Application Entity | API Reference | pynetdicom](https://pydicom.github.io/pynetdicom/dev/reference/generated/pynetdicom.ae.ApplicationEntity.html)
  for the default timeout values
"""

T = TypeVar('T', bound=int | float | TimeoutOpts | None)


def _set_timeout(application_entity: ae.ApplicationEntity, timeout: T) -> T:
    """Set the timeout values for the given `pynetdicom.ae.ApplicationEntity`.

    >>> _set_timeout(ae.ApplicationEntity(), None) is None
    True
    """
    if timeout is None:
        return timeout

    if isinstance(timeout, dict):
        val = {k: timeout.get(k, v) for k, v in DEFAULT_TIMEOUTS.items()}
        for k, v in val.items():
            setattr(application_entity, k, v)
        return val  # type: ignore[return-value]  # if `timeout` is a dict, it must be a TimeoutOpts

    for k in DEFAULT_TIMEOUTS:
        setattr(application_entity, k, timeout)

    return timeout


def get_association(
    address: tuple[str, int],
    calling_ae_title: str = DEFAULT_CLIENT_AE_TITLE,
    called_ae_title: str = DEFAULT_SERVER_AE_TITLE,
    request_contexts: Iterable[pres.PresentationContext] = DEFAULT_PRESENTATION_CONTEXTS,
    timeout: int | float | TimeoutOpts | None = DEFAULT_TIMEOUTS,
) -> pynetdicom.Association:
    """Establish a `pynetdicom.Association` with the given remote `pynetdicom.ae.ApplicationEntity`.

    Examples
    --------
    Send a `C-ECHO` request to an `pynetdicom.ae.ApplicationEntity` for a local `storescp` server:

    <!-- run a `storescp` server in the background

    >>> host, port = getfixture('storescp').server_address

    -->

    >>> assoc = get_association((host, port))
    >>> try:
    ...     res = assoc.send_c_echo()
    ... finally:
    ...     assoc.release()
    >>> Status(res.Status)
    <Status.SUCCESS: 0>

    An `int | float` can be passed as the `timeout` argument to override the values all timeout values:

    >>> assoc = get_association((host, port), timeout=0)
    Traceback (most recent call last):
        ...
    dicomlib.exceptions.DICOMAssociationError: ...

    Additionally, specific timeout values can be overridden by passing a `TimeoutOpts` dictionary:

    >>> assoc = get_association((host, port), timeout={'connection_timeout': 0})
    >>> try:
    ...     res = assoc.send_c_echo()
    ... finally:
    ...     assoc.release()
    >>> Status(res.Status)
    <Status.SUCCESS: 0>

    Parameters
    ----------
    addr
        The hostname or IP address of the remote `pynetdicom.ae.ApplicationEntity`
    port
        The port number of the remote `pynetdicom.ae.ApplicationEntity`
    calling_ae_title
        The title of this `pynetdicom.ae.ApplicationEntity` (SCU); defaults to `'dicom-hub.client'`
    called_ae_title
        The title of the remote `pynetdicom.ae.ApplicationEntity` (SCP); defaults to `'dicom-hub.server'`
    request_contexts
        The presentation contexts to request for the association; defaults to `DEFAULT_PRESENTATION_CONTEXTS`
    timeout
        Behavior varies according to type; defaults to `DEFAULT_TIMEOUTS`
        - If `None`, use the default values defined in `pynetdicom`
        - If a `dict` (`TimeoutOpts`), override `DEFAULT_TIMEOUTS` with the provided key/value pairs
        - Otherwise, set all timeouts to that value

    Yields
    ------
    association
        The `pynetdicom.association.Association` object for communicating with the remote peer

    Raises
    ------
    dicomlib.exceptions.DICOMAssociationError
        If the association could not be established with the remote peer

    References
    ----------
    - [Writing your first SCU | `pynetdicom`](https://pydicom.github.io/pynetdicom/dev/tutorials/create_scu.html#create-an-application-entity-and-associate)
    """
    addr, port = address

    application_entity = ae.ApplicationEntity(ae_title=calling_ae_title)
    _set_timeout(application_entity, timeout)

    if not (
        assoc := application_entity.associate(addr, port, contexts=list(request_contexts), ae_title=called_ae_title)
    ).is_established:
        raise exceptions.DICOMAssociationError(f'Association with {called_ae_title}@{addr}:{port} failed')

    return assoc


@contextlib.contextmanager
def association(
    address: tuple[str, int],
    calling_ae_title: str = DEFAULT_CLIENT_AE_TITLE,
    called_ae_title: str = DEFAULT_SERVER_AE_TITLE,
    request_contexts: Iterable[pres.PresentationContext] = DEFAULT_PRESENTATION_CONTEXTS,
    timeout: int | float | TimeoutOpts | None = DEFAULT_TIMEOUTS,
) -> Iterator[pynetdicom.Association]:
    """Context manager that establishes and releases a `pynetdicom.Association` with a remote `pynetdicom.ae.ApplicationEntity`.

    Examples
    --------
    Send a `C-ECHO` request to an `pynetdicom.ae.ApplicationEntity` for a local `storescp` server:

    <!-- run a `storescp` server in the background

    >>> host, port = getfixture('storescp').server_address

    -->

    >>> with association((host, port)) as assoc:
    ...     res = assoc.send_c_echo()
    >>> Status(res.Status)
    <Status.SUCCESS: 0>

    An `int | float` can be passed as the `timeout` argument to override the values all timeout values:

    >>> with association((host, port), timeout=0) as assoc:
    ...     pass
    Traceback (most recent call last):
        ...
    dicomlib.exceptions.DICOMAssociationError: ...

    Additionally, specific timeout values can be overridden by passing a `TimeoutOpts` dictionary:

    >>> with association((host, port), timeout={'connection_timeout': 0}) as assoc:
    ...    res = assoc.send_c_echo()
    >>> Status(res.Status)
    <Status.SUCCESS: 0>

    Parameters
    ----------
    addr
        The hostname or IP address of the remote `pynetdicom.ae.ApplicationEntity`
    port
        The port number of the remote `pynetdicom.ae.ApplicationEntity`
    calling_ae_title
        The title of this `pynetdicom.ae.ApplicationEntity` (SCU); defaults to `'dicom-hub.client'`
    called_ae_title
        The title of the remote `pynetdicom.ae.ApplicationEntity` (SCP); defaults to `'dicom-hub.server'`
    request_contexts
        The presentation contexts to request for the association; defaults to `DEFAULT_PRESENTATION_CONTEXTS`
    timeout
        Behavior varies according to type; defaults to `DEFAULT_TIMEOUTS`
        - If `None`, use the default values defined in `pynetdicom`
        - If a `dict` (`TimeoutOpts`), override `DEFAULT_TIMEOUTS` with the provided key/value pairs
        - Otherwise, set all timeouts to that value

    Yields
    ------
    association
        The `pynetdicom.association.Association` object for communicating with the remote peer

    Raises
    ------
    dicomlib.exceptions.DICOMAssociationError
        If the association could not be established with the remote peer

    References
    ----------
    - [Writing your first SCU | `pynetdicom`](https://pydicom.github.io/pynetdicom/dev/tutorials/create_scu.html#create-an-application-entity-and-associate)
    """
    assoc = get_association(address, calling_ae_title, called_ae_title, request_contexts, timeout)
    try:
        logger.debug('Association established with %s', f'{called_ae_title}@{address[0]}:{address[1]}')
        yield assoc
    finally:
        assoc.release()


@contextlib.contextmanager
def server(
    address: tuple[str, int],
    ae_title: str = DEFAULT_SERVER_AE_TITLE,
    presentation_contexts: Iterable[pres.PresentationContext] = DEFAULT_PRESENTATION_CONTEXTS,
    evt_handlers: list[EventHandlerType] | None = None,  # pyright: ignore[reportMissingTypeArgument]  # false positive
) -> Iterator[trans.AssociationServer]:
    """Context manager for running a `pynetdicom.ae.ApplicationEntity` server in a background thread.

    Examples
    --------
    Start a background server and send a `C-ECHO` request to it:

    >>> address = ('', 0)           # bind to an ephemeral port on all interfaces
    >>> ae_title = 'doctest.server'
    >>> with server(address, ae_title) as scp:
    ...     with association(scp.server_address) as scu:
    ...         res = scu.send_c_echo()
    >>> Status(res.Status)
    <Status.SUCCESS: 0>

    Parameters
    ----------
    address
        The hostname and port number of the server
    ae_title
        The title of this `pynetdicom.ae.ApplicationEntity` (SCP)
    presentation_contexts
        The presentation contexts to use for the server; defaults to `DEFAULT_PRESENTATION_CONTEXTS`

    Yields
    ------
    server
        The `pynetdicom.transport.AssociationServer` object for handling incoming associations

    References
    ----------
    - [Writing your first SCP | `pynetdicom`](https://pydicom.github.io/pynetdicom/dev/tutorials/create_scp.html#creating-a-storage-scp)
    """
    application_entity = ae.ApplicationEntity(ae_title=ae_title)
    application_entity.supported_contexts = list(presentation_contexts)

    if not (server := application_entity.start_server(address, evt_handlers=evt_handlers, block=False)):
        raise RuntimeError(f'Failed to bind server to address: {address}')  # pragma: no cover

    try:
        logger.info('Server started and listening on %s', address)
        yield server
    finally:
        server.shutdown()
