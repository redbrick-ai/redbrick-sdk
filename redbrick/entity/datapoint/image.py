"""
Representation for the image datapoint type.
"""
from io import BytesIO
from math import floor
from typing import Union, Any, List, Tuple

import requests
from dataclasses import dataclass, field
import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from PIL import Image as PILimage

from redbrick.entity.label import ImageBoundingBox, ImageClassify, ImageSegmentation
from redbrick.entity.label.segmentation import ImageSegmentationRemoteLabel
from redbrick.entity.label.bbox import ImageBoundingBoxRemoteLabel
from redbrick.logging import print_error
from .base_datapoint import BaseDatapoint


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
            # Read in remote labels
            bbox_remote_labels: List[ImageBoundingBoxRemoteLabel] = []
            try:
                bbox_remote_labels = [
                    ImageBoundingBoxRemoteLabel.from_dict(label)
                    for label in self.remote_labels
                ]
            except Exception as error:
                print_error("Parsing error. Please reach out to contact@redbrickai.com")
                print(error)

            # Create label object
            self.labels = ImageBoundingBox(labels=bbox_remote_labels)

        elif self.task_type == "SEGMENTATION":
            # Read in remote labels
            segment_remote_labels: List[ImageSegmentationRemoteLabel] = []
            try:
                segment_remote_labels = [
                    ImageSegmentationRemoteLabel.from_dict(label)
                    for label in self.remote_labels
                ]
            except Exception as err:
                print_error(err)
                return

            # Create label object
            self.labels = ImageSegmentation(
                remote_labels=segment_remote_labels, classes=self.taxonomy
            )

        elif self.task_type == "POLYGON":
            for label in self.remote_labels:
                width, height = self.__get_image_size()
                regions = [
                    (floor((i["ynorm"] * height)), floor(i["xnorm"] * width))
                    for i in label["polygon"]
                ]
                pixel = {
                    "regions": [[regions]],
                    "holes": None,
                    "imagesize": [width, height],
                }
                label["pixel"] = pixel
            try:
                segment_remote_labels = [
                    ImageSegmentationRemoteLabel.from_dict(label)
                    for label in self.remote_labels
                ]
            except Exception as err:
                print_error(err)
                return

            # Create label object
            self.labels = ImageSegmentation(
                remote_labels=segment_remote_labels, classes=self.taxonomy
            )

        elif self.task_type == "CLASSIFY":
            # Read in remote labels
            self.labels = ImageClassify(self.remote_labels)

        else:
            raise ValueError(
                "%s task type is not supported. Please reach out to contact@redbrickai.com."
                % self.task_type
            )

    def __get_image_size(self) -> Tuple[int, int]:
        """Return the size of the image from url"""
        img_data = requests.get(self.image_url_not_signed).content
        im = PILimage.open(BytesIO(img_data))
        return im.size

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
