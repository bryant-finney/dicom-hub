"""Upload a single DICOM series from a single study, stored at the path `data/ct_nonequi_tilt`.

This series is available at https://www.aliza-dicom-viewer.com/download/datasets -> https://drive.google.com/file/d/15Wc-KboUAE0vqahedcExCYskOEVf6Zub/view
"""

from __future__ import annotations

import logging
import pathlib

from tests.locust.scenarios import UploadStudy

logger = logging.getLogger(__name__)


class UploadCTNonequistantTilt(UploadStudy):
    """Upload the DICOM study at the path `data/ct_nonequi_tilt`."""

    data_path = pathlib.Path('data/ct_nonequi_tilt')


logger.debug('successfully imported %s', __name__)
