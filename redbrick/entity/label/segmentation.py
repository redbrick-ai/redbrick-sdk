"""
Representation of a segmentation label.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import copy
import numpy as np  # type: ignore
from skimage import draw  # type: ignore
import matplotlib.cm  # type: ignore
import matplotlib.pyplot as plt


@dataclass
class Pixel:
    """Representation of pixel field in RemoteLabel."""

    imagesize: List[int]
    regions: List[List[List[int]]]
    holes: List[List[List[int]]]


@dataclass
class ImageSegmentationRemoteLabel:
    """Single Remote label object for image segmentation."""

    category: List[List[str]]
    pixel: Pixel
    labelid: str

    @classmethod
    def from_dict(cls, obj: Dict[Any, Any]) -> "ImageSegmentationRemoteLabel":
        """Create a remote label object from dict."""
        pixel = Pixel(
            imagesize=obj["pixel"]["imagesize"],
            regions=obj["pixel"]["regions"],
            holes=obj["pixel"]["holes"],
        )
        return cls(category=obj["category"], pixel=pixel, labelid=obj["labelid"],)


@dataclass
class ImageSegmentation:
    """Image segmentation object."""

    classes: Dict[str, int]
    remote_labels: List[ImageSegmentationRemoteLabel]

    url: str = field(init=False)
    mask: np.ndarray = field(init=False)

    # Matplotlib CMAP returns color code
    # RGB 0-256 numpy array of int's
    color_map: Any = lambda idx: (
        np.array(matplotlib.cm.get_cmap("tab10")(idx))[0:3] * 256
    ).astype(int)

    def __post_init__(self) -> None:
        """
        Convert remote label format to mask format to be stored.
        """
        # TODO: Check this code for scenario with no label
        imagesize = self.remote_labels[0].pixel.imagesize
        mask = np.zeros([imagesize[1], imagesize[0]])

        for label_obj in self.remote_labels:
            label = label_obj.pixel
            category_name = label_obj.category[0][-1]
            class_id = self.classes[category_name]
            regions = copy.deepcopy(label.regions)
            holes = copy.deepcopy(label.holes)
            imagesize = label.imagesize

            # Iterate through the regions and create mask
            mask_ = np.zeros([imagesize[1], imagesize[0]])
            if regions and len(regions) > 0:
                for region in regions:
                    if len(np.array(region).shape) == 1:
                        # Don't add empty regions to the mask
                        break

                    # [x,y] needs to correspond to [r,c]
                    region = np.flip(region, axis=1)

                    mask__ = (
                        draw.polygon2mask([imagesize[1], imagesize[0]], region).astype(
                            float
                        )
                        * class_id
                    )

                    # Add on new regions to root mask object
                    # class_id_indexes = np.where(mask__ == class_id)
                    # mask_[class_id_indexes] = class_id
                    mask_ += mask__

            # Iterate through the holes and create the negative mask
            neg_mask = np.zeros([imagesize[1], imagesize[0]])
            if holes and len(holes) > 0:
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

            # create the holes for this label object,
            # and remove any negative values that arise from holes
            # "spilling outside" the region
            mask_ -= neg_mask
            neg_idxs = np.where(mask_ < 0)
            mask_[neg_idxs] = 0

            # overlapping regions would have gotten added together
            # set the overlapped regions back to the classid.
            overlap_indexes = np.where(mask_ > class_id)
            mask_[overlap_indexes] = class_id

            # Merge
            class_idx_not_zero = np.where(mask_ != 0)
            mask[class_idx_not_zero] = mask_[class_idx_not_zero]

        # Subtrack out the holes from the region mask
        self.mask = mask

    def color_mask(self) -> np.ndarray:
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
            color_mask[pixel_class_index] = self.color_map(int(id_))

        color_mask /= 256
        return color_mask

    def show(
        self, ax: Any = None, width: Optional[int] = None, height: Optional[int] = None
    ) -> None:
        """Show the segment labels."""
        mask = self.color_mask()
        ax.imshow(mask, alpha=0.3)
