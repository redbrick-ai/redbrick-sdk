from typing import List, Optional

import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import patches

from .bounding_box import BoundingBox


class Taxonomy:
    """Classes for detection."""


class DataPoint:
    def __init__(
        self, org_id: str, label_set_name: str, dp_id: str, image: np.ndarray
    ) -> None:
        """Construct DataPoint."""
        self.org_id = org_id
        self.label_set_name = label_set_name
        self.dp_id = dp_id
        self.image: np.ndarray = image

        self.gt_boxes: Optional[List[BoundingBox]] = None
        self.gt_boxes_classes: Optional[List[str]] = None

    def __repr__(self) -> str:
        """Get a str representation of DataPoint."""
        return f"{self.__class__.__name__}<dp={self.dp_id}>"

    @property
    def height(self) -> int:
        return self.image.shape[0]  # type: ignore

    @property
    def width(self) -> int:
        return self.image.shape[1]  # type: ignore

    def show_image(self, show_gt: bool = True, show_pred: bool = False) -> None:
        """Use matplotlib to show the image."""
        colors = ["xkcd:blue", "xkcd:red", "xkcd:green", "xkcd:orange", "xkcd:purple"]

        fig, ax = plt.subplots(1)
        if show_gt and self.gt_boxes and self.gt_boxes_classes:
            for ii, box in enumerate(self.gt_boxes):
                object_ = box.as_array()
                color = colors[ii % (len(colors) - 1)]
                height = object_[3] * self.height
                width = object_[2] * self.width

                bottom_left = (object_[0] * self.width, object_[1] * self.height)
                rect = patches.Rectangle(
                    bottom_left,
                    width,
                    height,
                    linewidth=1.5,
                    edgecolor=color,
                    facecolor="none",
                )
                ax.add_patch(rect)
                ax.text(
                    bottom_left[0] + 1.4,
                    bottom_left[1] - 2,
                    str(self.gt_boxes_classes[ii]),
                    backgroundcolor=color,
                    fontsize=10,
                )

        ax.imshow(self.image)
        fig.tight_layout()
        plt.show()
