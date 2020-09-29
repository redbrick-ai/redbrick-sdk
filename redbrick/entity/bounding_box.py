import numpy as np
from typing import Dict, List, Optional
from .taxonomy import TaxonomyEntry


class BoundingBox:
    """Object representing bounding boxes for a single datapoint."""

    def __init__(self) -> None:
        self._labels: List[BoundingBoxEntry]

    @classmethod
    def from_remote(cls, obj: Dict, taxonomy: Optional[TaxonomyEntry]) -> "BoundingBox":
        """Convert return value from servier into Bounding box entity."""
        this = cls()
        labels = []
        for label in obj:
            labels += [BoundingBoxEntry.from_remote(label, taxonomy)]

        this._labels = labels
        return this


class BoundingBoxEntry:
    """Object representing a single bounding box label."""

    def __init__(self) -> None:
        """Construct BoundingBox."""
        self._xnorm: float
        self._ynorm: float
        self._wnorm: float
        self._hnorm: float
        self._class: TaxonomyEntry

    def __repr__(self) -> str:
        """Get a string representation of object."""
        return f"BBOX<xmin={self._xnorm}, ymin={self._ynorm}, width={self._wnorm}, height={self._hnorm}>"

    def get_class(self) -> TaxonomyEntry:
        """Get the class of this label."""
        return self._class

    def as_array(self, min_max: bool = False) -> np.ndarray:
        """Get array representation of bounding box."""
        if not min_max:
            return np.array([self._xnorm, self._ynorm, self._wnorm, self._hnorm])
        return np.array(
            [
                self._xnorm,
                self._ynorm,
                self._xnorm + self._wnorm,
                self._ynorm + self._hnorm,
            ]
        )

    @classmethod
    def from_remote(
        cls, obj: Dict, taxonomy: Optional[TaxonomyEntry]
    ) -> "BoundingBoxEntry":
        """Convert return value from server into BoundingBox entity."""
        this = cls()
        this._xnorm = obj["bbox2d"]["xnorm"]
        this._ynorm = obj["bbox2d"]["ynorm"]
        this._wnorm = obj["bbox2d"]["wnorm"]
        this._hnorm = obj["bbox2d"]["hnorm"]

        category = str(obj["category"][0][-1])
        this._class = {category: taxonomy[category]}
        return this

    @classmethod
    def from_array(cls, obj: np.ndarray) -> "BoundingBoxEntry":
        """Convert a numpy array to BoundingBox."""
        if not obj.shape == (1, 4):
            raise ValueError("box.shape must be (1,4)")
        for val in obj:
            if val > 1 or val < 0:
                raise ValueError("Box points must be [0,1]")
        this = cls()
        this._xnorm = obj[0]
        this._ynorm = obj[1]
        this._wnorm = obj[2]
        this._hnorm = obj[3]
        return this

    @staticmethod
    def normalize(boxes: np.ndarray, height: int, width: int) -> np.ndarray:
        """
        Normalize all values of box.

        boxes: nx4
        height: height of image in pixels
        width: width of image in pixels
        """
        boxes[:, 0] = boxes[:, 0] / width
        boxes[:, 2] = boxes[:, 2] / width
        boxes[:, 1] = boxes[:, 1] / height
        boxes[:, 3] = boxes[:, 3] / height
        return boxes

    @staticmethod
    def get_coords_absolute(boxes: np.ndarray, height: int, width: int) -> np.ndarray:
        """
        Normalize all values of box.

        boxes: nx4
        height: height of image in pixels
        width: width of image in pixels
        """
        boxes[:, 0] = width * boxes[:, 0]
        boxes[:, 2] = width * boxes[:, 2]
        boxes[:, 1] = height * boxes[:, 1]
        boxes[:, 3] = height * boxes[:, 3]
        return boxes
