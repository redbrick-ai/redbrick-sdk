"""MHD utils."""

import os
from typing import List, Tuple

import SimpleITK as sitk


def convert_nii_to_mhd(masks: List[str]) -> Tuple[bool, List[str]]:
    """Convert nifti masks to mhd."""
    new_masks: List[str] = []
    for mask in masks:
        new_mask = mask.removesuffix(".gz").removesuffix(".nii") + ".mhd"
        new_masks.append(new_mask)
        new_masks.append(new_mask.removesuffix(".mhd") + ".zraw")

        sitk_image = sitk.ReadImage(mask)
        sitk.WriteImage(sitk_image, new_mask, True)

        os.remove(mask)

    return True, new_masks


def convert_mhd_to_nii(masks: List[str]) -> List[str]:
    """Convert mhd masks to nifti."""
    new_masks: List[str] = []
    for mask in masks:
        if mask.endswith(".raw") or mask.endswith(".zraw") or mask.endswith(".img"):
            continue

        new_mask = mask.removesuffix(".mhd") + ".nii.gz"
        new_masks.append(new_mask)

        sitk_image = sitk.ReadImage(mask)
        sitk.WriteImage(sitk_image, new_mask, True)

        os.remove(mask)

    return new_masks
