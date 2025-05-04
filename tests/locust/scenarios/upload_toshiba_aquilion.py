"""Upload a single DICOM series from a single study, stored at the path `data/Toshiba_Aquilion`.

This series is available at https://www.aliza-dicom-viewer.com/download/datasets -> https://drive.google.com/file/d/0ByBLJ2-U1t9xRGtZRXVtazBMWXM/view
"""

from __future__ import annotations

import logging
import pathlib
from collections.abc import Iterable

import dicomlib
from tests.locust.scenarios import UploadStudy

logger = logging.getLogger(__name__)


class UploadToshibaAquilion(UploadStudy):
    """Upload the DICOM study at the path `data/Toshiba_Aquilion`."""

    data_path = pathlib.Path('data/Toshiba_Aquilion')
    request_contexts: Iterable[dicomlib.PresentationContext] = [
        dicomlib.CTImageStorageContext,
        dicomlib.build_context(dicomlib.ExplicitVRLittleEndian),
    ]

    def load_data(self) -> Iterable[dicomlib.Dataset]:
        """Override the parent method to force loading the datasets (despite missing tags)."""
        data: list[dicomlib.Dataset] = []
        for fname in self.data_path.glob('*.dcm'):
            dataset = dicomlib.dcmread(fname, force=True)
            dataset.TransferSyntaxUID = dicomlib.ExplicitVRLittleEndian
            dataset.ensure_file_meta()
            dataset.file_meta.TransferSyntaxUID = dicomlib.ExplicitVRLittleEndian
            data.append(dataset)
        return data


logger.debug('successfully imported %s', __name__)
