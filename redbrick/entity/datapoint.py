from typing import List, Optional, Union

import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.cm  # for colormaps
from matplotlib import patches

from .bounding_box import BoundingBox
from .segmentation import Segmentation
from .taxonomy import TaxonomyEntry
import copy


class DataPoint:
    def __init__(
        self,
        org_id: str,
        label_set_name: str,
        dp_id: str,
        image: np.ndarray,
        image_url: str,
        image_url_not_signed: str,
        task_type: str,
        labels: dict,
        taxonomy: Optional[TaxonomyEntry] = None,
    ) -> None:
        """Construct DataPoint."""
        self.org_id = org_id
        self.label_set_name = label_set_name
        self.dp_id = dp_id
        self.image: np.ndarray = image
        self.image_url: str = image_url
        self.image_url_not_signed: str = image_url_not_signed
        self.task_type: str = task_type
        self.gt: Optional[Union[BoundingBox, Segmentation]] = None
        self.gt_classes: Optional[List[str]] = None
        self.color_map = matplotlib.cm.get_cmap("tab10")
        self.taxonomy: Optional[TaxonomyEntry] = taxonomy

        # Set the ground truth of the datapoint
        if task_type == "BBOX":
            # Bounding box labels
            self.gt = BoundingBox.from_remote(labels, self.taxonomy)

        elif task_type == "SEGMENTATION":
            # Segmentation labels
            self.gt = Segmentation.from_remote(labels, self.taxonomy)

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
        if self.task_type == "SEGMENTATION":
            # Segmentation show image
            fig, ax = plt.subplots()
            color_mask = self.gt.color_mask(self.color_map)
            mask_image = copy.deepcopy(self.image).astype(float) / 256
            ax.imshow(mask_image)
            ax.imshow(color_mask, alpha=0.4)
            plt.show()
            return

        elif self.task_type == "BBOX":
            # Bounding box show image
            colors = [
                "xkcd:blue",
                "xkcd:red",
                "xkcd:green",
                "xkcd:orange",
                "xkcd:purple",
            ]

            fig, ax = plt.subplots(1)
            if show_gt and self.gt:
                for ii, box in enumerate(self.gt._labels):
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
                        str(list(box.get_class().keys())[0]),
                        backgroundcolor=color,
                        fontsize=10,
                    )

            ax.imshow(self.image)
            fig.tight_layout()
            plt.show()
