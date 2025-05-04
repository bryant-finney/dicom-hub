"""The `locust.User` classes in this package define representative service behaviors."""

from collections.abc import Iterable
from pathlib import Path

import locust
from locust.env import Environment

import dicomlib
from tests.locust import ServiceClassUser


class UploadStudy(ServiceClassUser):
    """Upload a study of DICOM images to the remote SCP."""

    _data: Iterable[dicomlib.Dataset]
    """Container for DICOM images loaded on initialization"""

    abstract = True

    data_path: Path
    """Child classes must define the path to the DICOM images to upload"""

    wait_time = locust.between(0.1, 1)
    """By default, wait between 0.1 and 1.0 seconds in between uploads"""

    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        if not hasattr(self, 'data_path') or not self.data_path.is_dir():
            raise NotImplementedError(
                f'Class {self.__class__.__name__} must define the path to a directory of DICOM images to upload'
            )

        self._data = self.load_data()

    @property
    def data(self) -> Iterable[dicomlib.Dataset]:
        """Return the DICOM images to upload."""
        return self._data

    def load_data(self) -> Iterable[dicomlib.Dataset]:
        """Load DICOM images from the `locust.User`'s `data_path` directory."""
        return [dicomlib.dcmread(fname) for fname in self.data_path.glob('*.dcm')]

    @locust.task
    def upload_all(self) -> None:
        """Upload all DICOM images in the study."""
        with self.client.session as session:
            for dataset in self.data:
                session.send_c_store(dataset)
