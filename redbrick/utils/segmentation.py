"""Segmentation helper functions."""

from typing import Dict, Tuple

import numpy as np


def check_mask_map_format(mask: np.ndarray, color_map: Dict):
    """
    Validate format of masks.

    Checks the following:
        - If mask dimensions are [m, n, 3]
        - If all the values in mask, are present in color_map
    """
    if len(mask.shape) != 3 or mask.shape[2] != 3:
        raise ValueError("Your mask must have shape (m, n, 3), not %s" % mask.shape)

    if mask.dtype != np.uint8:
        raise ValueError(
            "Your masks must be of type np.uint8, with pixel values between [0, 255]."
        )

    # Creates a map of all the colors
    unique_color_map = np.zeros((len(color_map), 3))
    for i, category in enumerate(color_map):
        unique_color_map[i, :] = color_map[category]

    indexes = np.where(
        (mask[:, :, 0] in unique_color_map[:, 0])
        & (mask[:, :, 1] in unique_color_map[:, 1])
        & (mask[:, :, 2] in unique_color_map[:, 2])
    )
    return indexes


def get_file_type(image_path: str) -> Tuple[str, str]:
    """
    Return the image file types.

    Return
    ------------
    [file_ext, file_type]
        file_ext: .png, .jpeg, .jpg etc.
        file_type: this is the MIME file type e.g. image/png
    """
    file_ext = image_path.split(".")[-1]
    if file_ext == "png":
        file_type = "image/png"
    elif file_ext in ["jpg", "jpeg"]:
        file_type = "image/jpeg"
    else:
        raise ValueError(
            ".%s file type not supported! Only .png, .jpeg, and .jpg are supported. "
            % file_ext
        )
    return file_ext, file_type
