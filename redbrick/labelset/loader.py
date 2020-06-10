"""A higher level abstraction."""

from typing import Optional, List
from random import randint

import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import patches

from redbrick.base import BBOXImageItem, get_bbox_item
from redbrick.api import get_datapoint, get_datapoint_ids


class LabelsetLoader:
    """A basic high level loader class."""

    def __init__(
        self, org_id: str, label_set_name: str, dp_ids: Optional[List[str]] = None
    ) -> None:
        """Construct Loader."""
        self.org_id = org_id
        self.label_set_name = label_set_name

        print("Counting available data points... ", end="")
        if dp_ids:
            self.dp_ids = dp_ids
        else:
            self.dp_ids = get_datapoint_ids(self.org_id, self.label_set_name)
        print(len(self.dp_ids))

    def get_item(self, index: int) -> BBOXImageItem:
        """Get information needed for a single item."""
        datum = get_datapoint(self.org_id, self.label_set_name, self.dp_ids[index])

        return get_bbox_item(datum)

    def number_of_datapoints(self) -> int:
        """Get number of datapoints."""
        return len(self.dp_ids)

    def show_random_image(self) -> None:
        """Show a random image."""
        idx = randint(0, self.number_of_datapoints() - 1)
        self.show_image(self.get_item(idx))

    def show_image(self, bbox_item: BBOXImageItem) -> None:
        """
        Display an image.

        If no idx specified, then a random example
        will be chosen.
        """
        colors = ["xkcd:blue", "xkcd:red", "xkcd:green", "xkcd:orange", "xkcd:purple"]

        fig, ax = plt.subplots(1)
        dims = bbox_item.image.shape[0:2]
        for ii, object_ in enumerate(bbox_item.objects):
            color = colors[ii % (len(colors) - 1)]
            height = object_[3] * dims[0]
            width = object_[2] * dims[1]

            bottom_left = (object_[0] * dims[1], object_[1] * dims[0])
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
                str(bbox_item.class_ids[ii]),
                backgroundcolor=color,
                fontsize=10,
            )
        image = bbox_item.image

        ax.imshow(image)
        fig.tight_layout()
        plt.show()
