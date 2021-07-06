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

    def _create_bbox_labels(self, labels: List) -> ImageBoundingBox:
        """Create Bbox type labels."""
        bbox_remote_labels: List[ImageBoundingBoxRemoteLabel] = []
        try:
            bbox_remote_labels = [
                ImageBoundingBoxRemoteLabel.from_dict(label) for label in labels
            ]
        except Exception as err:
            print(err)
            print_error("Parsing error. Please reach out to contact@redbrickai.com")

        # Create label object
        return ImageBoundingBox(labels=bbox_remote_labels)

    def _create_segmentation_labels(self, labels: List) -> ImageSegmentation:
        """Create Segmentations labels."""
        segment_remote_labels: List[ImageSegmentationRemoteLabel] = []
        try:
            segment_remote_labels = [
                ImageSegmentationRemoteLabel.from_dict(label) for label in labels
            ]
        except Exception as err:
            print_error(err)

        # Create label object
        return ImageSegmentation(
            remote_labels=segment_remote_labels, classes=self.taxonomy
        )

    def _create_polygon_labels(self, labels: List) -> ImageSegmentation:
        """Create Polygon type labels."""
        for label in labels:
            width, height = self._get_image_size()
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

        # Using segmentation label type for polygon labels.
        return self._create_segmentation_labels(labels)

    def _create_classify_labels(self, labels: List) -> ImageClassify:
        """Create Classify type labels."""
        return ImageClassify(self.remote_labels)

    def __post_init__(self) -> None:
        """Run after init."""
        if self.task_type == "BBOX":
            self.labels = self._create_bbox_labels(self.remote_labels)

        elif self.task_type == "SEGMENTATION":
            self.labels = self._create_segmentation_labels(self.remote_labels)

        elif self.task_type == "POLYGON":
            self.labels = self._create_polygon_labels(self.remote_labels)

        elif self.task_type == "CLASSIFY":
            self.labels = self._create_classify_labels(self.remote_labels)

        elif self.task_type == "MULTI":
            for labels in self.remote_labels:
                if labels.get("bbox"):
                    # self.labels = self._create_bbox_labels([labels])
                    print("do nothing for bbox2d")
                elif labels.get("polygon"):
                    self.labels = self._create_polygon_labels([labels])

        else:
            raise ValueError(
                f"{self.task_type} task type is not supported. "
                f"Please reach out to contact@redbrickai.com."
            )

    def _get_image_size(self) -> List:
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
