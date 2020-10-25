"""
Representation of a segmentation label.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import numpy as np  # type: ignore
import json
import copy
from skimage import draw  # type: ignore
import matplotlib.cm  # type: ignore


@dataclass
class ImageSegmentation:
    classes: Dict[str, int]
    remote_labels: List[Any]

    url: str = field(init=False)
    mask: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        """After init."""
        # TODO: Check this code for scenario with no label
        imagesize = self.remote_labels[0]["pixel"]["imagesize"]
        mask = np.zeros([imagesize[1], imagesize[0]])

        with open("debug.json", "w+") as file:
            json.dump(self.remote_labels, file, indent=2)

        for label_obj in self.remote_labels:
            label = label_obj["pixel"]
            category_name = label_obj["category"][0][-1]
            class_id = self.classes[category_name]
            regions = copy.deepcopy(label["regions"])
            holes = copy.deepcopy(label["holes"])
            imagesize = label["imagesize"]

            # Iterate through the regions and create mask
            if regions and len(regions):
                for region in regions:
                    if len(np.array(region).shape) == 1:
                        # Don't add empty regions to the mask
                        break

                    # [x,y] needs to correspond to [r,c]
                    region = np.flip(region, axis=1)

                    mask_ = (
                        draw.polygon2mask([imagesize[1], imagesize[0]], region).astype(
                            float
                        )
                        * class_id
                    )

                    # Add on new regions to root mask object
                    class_id_indexes = np.where(mask_ == class_id)
                    mask[class_id_indexes] = class_id

            # Iterate through the holes and create the negative mask
            neg_mask = np.zeros([imagesize[1], imagesize[0]])
            if holes and len(holes):
                for hole in holes:
                    if len(np.array(hole).shape) == 1:
                        # Don't add empty hole to the negative mask
                        break

                    # [x,y] needs to correspond to [r,c]
                    hole = np.flip(hole, axis=1)

                    neg_mask_ = (
                        draw.polygon2mask([imagesize[1], imagesize[0]], hole).astype(
                            float
                        )
                        * class_id
                    )

                    # Add on new holes to negative mask
                    neg_mask += neg_mask_

            mask -= neg_mask

        # Subtrack out the holes from the region mask
        self.mask = mask

    def color_mask(self, color_map: Any) -> np.ndarray:
        """Return a RGB colored mask."""
        mask_class_ids = np.unique(self.mask)
        color_mask = np.zeros([self.mask.shape[0], self.mask.shape[1], 3])

        # Loop through class range
        for id_ in mask_class_ids:
            if id_ == 0:
                # Do not color class id 0 i.e. the background
                continue

            pixel_class_index = np.where(self.mask == id_)

            # generate colors
            color_mask[pixel_class_index] = np.array(color_map(int(id_))[0:3]) * 256

        color_mask /= 256
        return color_mask

    def show(
        self, ax: Any = None, width: Optional[int] = None, height: Optional[int] = None
    ) -> None:
        """Show the segment labels."""
        cmap = matplotlib.cm.get_cmap("tab10")
        mask = self.color_mask(color_map=cmap)
        ax.imshow(mask, alpha=0.3)
