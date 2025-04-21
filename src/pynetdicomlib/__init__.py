"""Interface module for the `pynetdicom` library provides abstractions and utilities for DICOM networking.

This package wraps all functionality provided by the `pynetdicom` library that is used by the rest of the application.
"""

import contextlib
import logging
from collections.abc import Iterable, Iterator

import pynetdicom
from pynetdicom import ae, build_context
from pynetdicom import presentation as pres
from pynetdicom import transport as trans
from pynetdicom.sop_class import ComputedRadiographyImageStorage, CTImageStorage, EnhancedCTImageStorage, Verification

from pynetdicomlib import exceptions

__all__ = [
    'DEFAULT_PRESENTATION_CONTEXTS',
    'CTImageStorageContext',
    'ComputedRadiographyImageStorageContext',
    'EnhancedCTImageStorageContext',
    'VerificationContext',
    'association',
    'server',
]

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


@contextlib.contextmanager
def association(
    address: tuple[str, int],
    calling_ae_title: str = DEFAULT_CLIENT_AE_TITLE,
    called_ae_title: str = DEFAULT_SERVER_AE_TITLE,
    request_contexts: Iterable[pres.PresentationContext] = DEFAULT_PRESENTATION_CONTEXTS,
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

    Yields
    ------
    association
        The `pynetdicom.association.Association` object for communicating with the remote peer

    Raises
    ------
    pynetdicomlib.exceptions.DICOMAssociationError
        If the association could not be established with the remote peer

    References
    ----------
    - [ ] TODO: add references to documentation sources

    """
    addr, port = address
    application_entity = ae.ApplicationEntity(ae_title=calling_ae_title)
    remote_aehost = f'{called_ae_title}@{addr}:{port}'

    if not (
        assoc := application_entity.associate(addr, port, contexts=list(request_contexts), ae_title=called_ae_title)
    ).is_established:
        raise exceptions.DICOMAssociationError(f'Association with {remote_aehost} failed')

    try:
        logger.debug('Association established with %s', remote_aehost)
        yield assoc
    finally:
        assoc.release()


@contextlib.contextmanager
def server(
    address: tuple[str, int],
    ae_title: str = DEFAULT_SERVER_AE_TITLE,
    presentation_contexts: Iterable[pres.PresentationContext] = DEFAULT_PRESENTATION_CONTEXTS,
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
    server : pynetdicom.transport.AssociationServer
        The `pynetdicom.transport.AssociationServer` object for handling incoming associations
    """
    application_entity = ae.ApplicationEntity(ae_title=ae_title)
    application_entity.supported_contexts = list(presentation_contexts)

    if not (server := application_entity.start_server(address, block=False)):
        raise RuntimeError(f'Failed to bind server to address: {address}')

    try:
        logger.info('Server started and listening on %s', address)
        yield server
    finally:
        server.shutdown()
