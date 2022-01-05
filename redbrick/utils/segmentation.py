"""Segmentation helper functions."""

from typing import Dict, Any

import numpy as np


def check_mask_map_format(mask: np.ndarray, color_map: Dict) -> Any:
    """
    Validate format of masks.

    Checks the following:
        - If mask dimensions are [m, n, 3]
        - If all the values in mask, are present in color_map
    """
    if len(mask.shape) != 3 or mask.shape[2] != 3:
        raise ValueError(f"Your mask must have shape (m, n, 3), not {mask.shape}")

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
