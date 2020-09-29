from typing import List, Optional, Dict
import numpy as np
import copy
from skimage import draw
import matplotlib.pyplot as plt
import json
from .taxonomy import TaxonomyEntry


class Segmentation:
    """Object to represent a segmentation label."""

    def __init__(self) -> None:
        """Construct a segmentation label object."""
        self._mask: np.ndarray
        self._classes: TaxonomyEntry
        self._url: str

    @classmethod
    def from_remote(
        cls, obj: dict, taxonomy: Optional[TaxonomyEntry]
    ) -> "Segmentation":
        """Convert return value from server into Segmentation mask entity."""
        this = cls()

        # TODO: Check this code for scenario with no label
        imagesize = obj[0]["pixel"]["imagesize"]
        mask = np.zeros([imagesize[1], imagesize[0]])

        with open("debug.json", "w+") as file:
            json.dump(obj, file, indent=2)

        for label_obj in obj:
            label = label_obj["pixel"]
            category_name = label_obj["category"][0][-1]
            class_id = taxonomy[category_name]
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
        this._mask = mask
        this._classes = taxonomy
        return this

    def color_mask(self, color_map) -> np.ndarray:
        """Return a RGB colored mask."""
        mask_class_ids = np.unique(self._mask)
        color_mask = np.zeros([self._mask.shape[0], self._mask.shape[1], 3])

        # Loop through class range
        for id_ in mask_class_ids:
            if id_ == 0:
                # Do not color class id 0 i.e. the background
                continue

            pixel_class_index = np.where(self._mask == id_)

            # generate colors
            color_mask[pixel_class_index] = np.array(color_map(int(id_))[0:3]) * 256

        color_mask /= 256
        return color_mask
