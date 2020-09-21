
from typing import List, Optional, Dict
import numpy as np
import copy
from skimage import draw
import matplotlib.pyplot as plt
import json


class Segmentation:
    """Object to represent a segmentation label."""

    def __init__(self) -> None:
        """Construct a segmentation label object."""
        self._mask: np.ndarray

    @classmethod
    def from_remote(cls, obj: dict, taxonomy: dict) -> "Segmentation":
        """Convert return value from server into Segmentation mask entity."""
        this = cls()

        class_id = 1
        # TODO: Check this code for scenario with no label
        imagesize = obj[0]['pixel']['imagesize']
        mask = np.zeros([imagesize[1], imagesize[0]])
        neg_mask = np.zeros([imagesize[1], imagesize[0]])

        with open('debug.json', 'w+') as file:
            json.dump(obj, file, indent=2)

        for label_obj in obj:
            label = label_obj['pixel']
            regions = copy.deepcopy(label['regions'])
            holes = copy.deepcopy(label['holes'])
            imagesize = label['imagesize']

            # Iterate through the regions and create mask
            if (regions and len(regions)):
                for region in regions:
                    if (len(np.array(region).shape) == 1):
                        # Don't add empty regions to the mask
                        break

                    # [x,y] needs to correspond to [r,c]
                    region = np.flip(region, axis=1)

                    mask_ = draw.polygon2mask(
                        [imagesize[1], imagesize[0]], region).astype(float)*class_id

                    # Add on new regions to root mask object
                    mask += mask_

            # Iterate through the holes and create the negative mask
            if (holes and len(holes)):
                for hole in holes:
                    if (len(np.array(hole).shape) == 1):
                        # Don't add empty hole to the negative mask
                        break

                    # [x,y] needs to correspond to [r,c]
                    hole = np.flip(hole, axis=1)

                    neg_mask_ = draw.polygon2mask(
                        [imagesize[1], imagesize[0]], hole).astype(float)*class_id

                    # Add on new holes to negative mask
                    neg_mask += neg_mask_

            class_id += 1

        # Subtrack out the holes from the region mask
        mask -= neg_mask
        this._mask = mask
        return this

    def color_mask(self, color_map, taxonomy, classes) -> np.ndarray:
        """Return a RGB colored mask."""
        num_classes = int(np.max(self._mask))
        color_mask = np.zeros([self._mask.shape[0], self._mask.shape[1], 3])

        # Loop through class range
        class_index = 1
        for idx in range(num_classes):
            pixel_class_index = np.where(self._mask == class_index)

            # generate colors
            tax_class_id = taxonomy[classes[idx]]
            color_mask[pixel_class_index] = np.array(
                color_map(tax_class_id)[0:3])*256
            class_index += 1

        color_mask /= 256
        return color_mask
