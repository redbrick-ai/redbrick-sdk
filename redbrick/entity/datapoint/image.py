"""
Representation for the image datapoint type.
"""
from dataclasses import dataclass, field
from .base_datapoint import BaseDatapoint
import numpy as np
from typing import Union
from redbrick.entity.label import ImageBoundingBox, ImageClassify, ImageSegmentation


@dataclass
class Image(BaseDatapoint):
    """Image object."""

    dp_id: str
    image_url: str
    image_url_not_signed: str
    image_data: np.ndarray
    labels: Union[ImageBoundingBox, ImageClassify, ImageSegmentation] = field(
        init=False
    )

    def __post_init__(self):
        """Run after init."""
        if self.task_type == "BBOX":
            self.labels = ImageBoundingBox(labels=self.remote_labels)
        elif self.task_type == "CLASSIFY":
            self.labels = ImageClassify(labels=self.remote_labels)
        elif self.task_type == "SEGMENTATION":
            self.labels = ImageSegmentation(
                remote_labels=self.remote_labels, classes=self.taxonomy
            )
        else:
            raise ValueError(
                "%s task type is not supported. Please reach out to contact@redbrickai.com"
                % self.task_type
            )
