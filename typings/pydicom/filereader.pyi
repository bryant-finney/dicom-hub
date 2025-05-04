from __future__ import annotations

from typing import BinaryIO

from pydicom.dataset import FileDataset
from pydicom.dicomdir import DicomDir
from pydicom.filebase import DicomFileLike
from pydicom.fileutil import PathType
from pydicom.tag import TagListType

def dcmread(
    fp: PathType | BinaryIO | DicomFileLike,
    defer_size: str | int | float | None = None,
    stop_before_pixels: bool = False,
    force: bool = False,
    specific_tags: TagListType | None = None,
) -> FileDataset | DicomDir: ...
