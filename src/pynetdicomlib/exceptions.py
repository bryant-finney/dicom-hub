"""Define exception classes for DICOM networking."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class DICOMError(Exception):
    """Base class for exceptions related to DICOM network communications."""


class DICOMAssociationError(DICOMError):
    """Failed to establish an association."""


logger.debug('successfully imported %s', __name__)
