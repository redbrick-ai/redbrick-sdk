"""
Base class for export controller.
"""
import os
import uuid
from dataclasses import dataclass, field

from redbrick.labelset.labelset_base import LabelsetBase


@dataclass
class ExportBase:
    """Base class for export controller."""

    format: str
    labelset: LabelsetBase
    cache_dir: str = field(init=False)
    export_dir: str = field(init=False)

    def __post_init__(self) -> None:
        """Run after init."""
        salt = uuid.uuid4()
        self.cache_dir = "RB_Export_%s_%s" % (self.format, salt)
        self.export_dir = "RB_Export_%s_%s" % (self.format, salt)

    def export(self) -> None:
        """Export the data and labels in the correct format."""
        raise NotImplementedError()

    def cache(self) -> None:
        """Cache the data and labels."""
        os.mkdir(self.cache_dir)

        if self.labelset.task_type == "SEGMENTATION":
            self.cache_segmentation()
        elif self.labelset.task_type == "BBOX":
            self.cache_bbox()
        elif self.labelset.task_type == "CLASSIFY":
            self.cache_classify()

    def cache_bbox(self) -> None:
        """Cache image bounding boxes."""
        raise NotImplementedError()

    def cache_segmentation(self) -> None:
        """Cache image segmentation."""
        raise NotImplementedError

    def cache_classify(self) -> None:
        """Cache image classification."""
        raise NotImplementedError
