"""PNG utils."""

import os
from typing import Dict, List, Set, Tuple

import numpy  # type: ignore
from nibabel.loadsave import load as nib_load, save as nib_save  # type: ignore
from nibabel.nifti1 import Nifti1Image  # type: ignore
from PIL import Image  # type: ignore

from redbrick.utils.logging import log_error


def convert_nii_to_png(
    masks: List[str],
    color_map: Dict,
    labels: List[Dict],
    dirname: str,
    binary_mask: bool,
    semantic_mask: bool,
    is_tax_v2: bool = True,
) -> Tuple[bool, List[str]]:
    """Convert nifti masks to png."""
    # pylint: disable=too-many-locals
    cat_class_map: Dict[str, str] = {}
    instance_class_map: Dict[int, int] = {}
    for label in labels:
        instance_class_map[label["dicom"]["instanceid"]] = label["classid"] + 1
        category = (
            label["category"]
            if isinstance(label["category"], str)
            else "::".join(label["category"][0][1:])
        )
        cat_class_map[f"category-{label['classid'] + 1}"] = category
        cat_class_map[f"instance-{label['dicom']['instanceid']}"] = category
        for group_id in label["dicom"].get("groupids", []) or []:
            if f"instance-{group_id}" in cat_class_map:
                continue
            cat_class_map[f"instance-{group_id}"] = category

    files: Set[str] = set()
    for mask in masks:
        mask_img = nib_load(mask)
        if not isinstance(mask_img, Nifti1Image):
            log_error(f"{mask} is not a valid NIfTI1 file.")
            continue

        input_filename = os.path.basename(mask)[:-7]
        mask_data = mask_img.get_fdata(caching="unchanged")
        if mask_data.shape[2] != 1:
            log_error(f"{mask} is not a 2D image")
            continue

        mask_arr = numpy.round(mask_data).astype(numpy.uint16).swapaxes(0, 1)
        mask_arr = mask_arr.reshape(mask_arr.shape[0], mask_arr.shape[1])
        if binary_mask:
            color_mask = numpy.zeros((mask_arr.shape[0], mask_arr.shape[1], 3))
            cat = int(input_filename.split("-")[-1])
            if semantic_mask:
                cat = instance_class_map.get(cat, 0)
            color_mask[mask_arr == 1] = (255, 255, 255)
            filename = os.path.join(dirname, f"mask-{cat}.png")
            pil_color_mask = Image.fromarray(color_mask.astype(numpy.uint8))
            pil_color_mask.save(filename)
            files.add(filename)

        else:
            color_mask = numpy.zeros((mask_arr.shape[0], mask_arr.shape[1], 3))
            for seg in numpy.unique(mask_arr):
                if not seg:
                    continue
                cat = int(seg)
                if not semantic_mask:
                    cat = instance_class_map.get(cat, 0)
                color_mask[mask_arr == seg] = (
                    color_map.get(cat - 1, (255, 255, 255))
                    if is_tax_v2
                    else color_map.get(
                        cat_class_map.get(input_filename, ""), (255, 255, 255)
                    )
                )
            filename = os.path.join(dirname, f"{input_filename}.png")
            pil_color_mask = Image.fromarray(color_mask.astype(numpy.uint8))
            pil_color_mask.save(filename)
            files.add(filename)

    return bool(files), list(files)


def convert_png_to_nii(masks: Dict[str, Tuple[int, ...]]) -> None:
    """Convert png masks to nifti."""
    mask_items = list(masks.items())
    for mask, inst_ids in mask_items:
        img = Image.open(mask)
        png_mask = numpy.array(img)
        img.close()

        nib_save(
            Nifti1Image(
                numpy.any(png_mask, axis=2)
                .astype(numpy.uint8)
                .reshape(png_mask.shape[0], png_mask.shape[1], 1)
                .swapaxes(0, 1),
                numpy.diag([-1, -1, 1, 1]),
            ),
            mask + ".nii.gz",
        )

        del masks[mask]
        masks[mask + ".nii.gz"] = inst_ids
