"""NIfTI I/O."""

import functools
import gzip
from typing import Optional

import numpy as np  # type: ignore
from nibabel.nifti1 import Nifti1Header  # type: ignore

from redbrick.utils.files import is_gzipped_data


class NiftiIO:
    """NIfTI I/O."""

    def __init__(self, path: str, load_data: bool = True) -> None:
        """Initialize NIfTI I/O."""
        gzipped = False
        with open(path, "rb") as f:
            if is_gzipped_data(f.read(2)):
                gzipped = True

        with gzip.open(path, "rb") if gzipped else open(path, "rb") as f:
            self._header = Nifti1Header(f.read(348))  # type: ignore
            self.size = functools.reduce(
                lambda x, y: x * y, self._header.get_data_shape()
            )
            self._extra_info = f.read(4)
            self.data: Optional[np.ndarray] = None
            if load_data:
                dtype = self._header.get_data_dtype()
                buffer = f.read()
                self.data = np.frombuffer(
                    buffer,
                    dtype=(
                        np.uint8
                        # special case for handling single byte masks
                        if len(buffer) == self.size and dtype != np.int8
                        else dtype
                    ),
                )
                if self.data.dtype not in (np.uint8, np.uint16):
                    self.data = np.round(self.data).astype(np.uint16)

    def save(self, path: str, data: Optional[np.ndarray] = None) -> None:
        """Save NIfTI file."""
        data = data if data is not None else self.data
        assert data is not None

        if data.dtype != self._header.get_data_dtype():
            self._header.set_data_dtype(data.dtype)

        with gzip.open(path, "wb", compresslevel=1) as f:
            f.write(self._header.binaryblock)
            f.write(self._extra_info)
            f.write(data.tobytes())
