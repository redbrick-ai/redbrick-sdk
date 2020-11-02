"""
Representation for the image datapoint type.
"""
from dataclasses import dataclass, field
from .base_datapoint import BaseDatapoint
import numpy as np  # type: ignore
from typing import Union, Any
import matplotlib.pyplot as plt  # type: ignore
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

    def __post_init__(self) -> None:
        """Run after init."""
        if self.task_type == "BBOX":
            self.labels = ImageBoundingBox(labels=self.remote_labels)
        elif self.task_type == "CLASSIFY":
            self.labels = ImageClassify(remote_labels=self.remote_labels)
        elif self.task_type == "SEGMENTATION":
            self.labels = ImageSegmentation(
                remote_labels=self.remote_labels, classes=self.taxonomy
            )
        else:
            raise ValueError(
                "%s task type is not supported. Please reach out to contact@redbrickai.com"
                % self.task_type
            )

    def show_data(self, ax: Any = None) -> None:
        """Show the data with the ground truth."""
        if ax is None:
            _, ax = plt.subplots()

        # Show the image
        ax.imshow(self.image_data)

        # Render labels
        height, width, _ = self.image_data.shape
        self.labels.show(ax=ax, width=width, height=height)
        title = (
            "..." + self.image_url_not_signed[-10:]
            if len(self.image_url_not_signed) > 10
            else self.image_url_not_signed
        )
        ax.set_title("%s" % title)

        if ax is None:
            plt.show()
