"""Dicom/nifti related functions."""

import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TypedDict
from asyncio import BoundedSemaphore
import shutil
from uuid import uuid4

from redbrick.utils.common_utils import config_path
from redbrick.utils.files import uniquify_path
from redbrick.utils.logging import log_error, logger


# pylint: disable=too-many-locals, too-many-branches, broad-except
# pylint: disable=import-outside-toplevel, too-many-statements, too-many-return-statements


semaphore = BoundedSemaphore(1)


class LabelMapData(TypedDict):
    """Label map data."""

    semantic_mask: bool
    binary_mask: bool
    png_mask: bool
    masks: Optional[Union[str, List[str]]]


def merge_instances(
    input_data: Any,
    output_data: Any,
    instances: Dict[Tuple[int, ...], int],
) -> None:
    """Merge instances."""
    import numpy as np  # type: ignore

    if not any(0 in input_instances for input_instances in instances.keys()):
        all_indices = np.nonzero(input_data)
        for input_instances, output_instance in instances.items():
            if not input_instances:
                continue

            instances_arr = np.array(list(set(input_instances)), dtype=np.uint16)
            indices = np.isin(input_data[all_indices], instances_arr)

            output_data[
                tuple(all_indices[i][indices] for i in range(output_data.ndim))
            ] = output_instance
    else:
        for input_instances, output_instance in instances.items():
            if not input_instances:
                continue

            instances_arr = np.array(list(set(input_instances)), dtype=np.uint16)
            indices = np.isin(input_data, instances_arr)
            output_data[indices] = output_instance


def merge_segmentations(
    input_file: str, output_file: str, instances: Dict[Tuple[int, ...], int]
) -> bool:
    """Merge segmentations from input to output."""
    import numpy as np  # type: ignore
    from redbrick.utils.nifti_io import NiftiIO  # type: ignore

    try:
        nii = NiftiIO(input_file, False)
        data = np.zeros(
            (nii.size,), dtype=np.uint8 if max(instances.values()) < 256 else np.uint16
        )
        merge_instances(NiftiIO(input_file).data, data, instances)
        nii.save(output_file, data)
        return True
    except Exception as err:
        log_error(err)
        return False


def convert_to_binary(
    mask: str, labels: List[Dict], dirname: str
) -> Tuple[bool, List[str]]:
    """Convert segmentation to binary."""
    import numpy as np  # type: ignore
    from redbrick.utils.nifti_io import NiftiIO  # type: ignore

    nii = NiftiIO(mask)
    data = nii.data
    assert data is not None
    files: List[str] = []

    non_zero = np.nonzero(data)
    new_data = np.zeros(data.shape, dtype=np.uint8)
    for idx, label in enumerate(labels):
        instance_id: int = label["dicom"]["instanceid"]
        group_ids: List[int] = label["dicom"].get("groupids") or []
        instances = np.array(list({instance_id} | set(group_ids)), dtype=np.uint16)

        indices = np.isin(data[non_zero], instances)

        if not indices.any():
            continue

        filename = os.path.join(
            dirname, f"instance-{label['dicom']['instanceid']}.nii.gz"
        )
        files.append(filename)
        if os.path.isfile(filename):
            os.remove(filename)

        coords = tuple(non_zero[i][indices] for i in range(new_data.ndim))
        new_data[coords] = 1
        nii.save(filename, new_data)
        if idx < (len(labels) - 1):
            new_data[coords] = 0

    return True, files


def convert_to_semantic(
    masks: List[str],
    labels: List[Dict],
    dirname: str,
    binary_mask: bool,
    is_tax_v2: bool = True,
) -> Tuple[bool, List[str]]:
    """Convert segmentation to semantic."""
    import numpy as np  # type: ignore
    from redbrick.utils.nifti_io import NiftiIO  # type: ignore

    if not labels:
        return True, []

    if not is_tax_v2:
        log_error("Taxonomy V1 is not supported")
        return False, masks

    if not (binary_mask or len(masks) == 1):
        log_error(f"Cannot process labels: {labels}")
        return False, masks

    labels.sort(key=lambda label: label["classid"])
    files: Set[str] = set()

    if binary_mask:
        pos = 0
        while pos < len(labels):
            start_pos = pos
            nii = NiftiIO(
                os.path.join(
                    dirname,
                    f"instance-{labels[start_pos]['dicom']['instanceid']}.nii.gz",
                ),
                False,
            )
            data = np.zeros((nii.size,), dtype=np.uint8)
            while (
                pos < len(labels)
                and labels[pos]["classid"] == labels[start_pos]["classid"]
            ):
                merge_instances(
                    NiftiIO(
                        os.path.join(
                            dirname,
                            f"instance-{labels[pos]['dicom']['instanceid']}.nii.gz",
                        ),
                    ).data,
                    data,
                    {(1,): 1},
                )
                pos += 1
            filename = os.path.join(
                dirname, f"category-{labels[start_pos]['classid'] + 1}.nii.gz"
            )
            files.add(filename)
            if os.path.isfile(filename):
                os.remove(filename)
            nii.save(filename, data)
    else:
        visited: Set[int] = set()
        instances_to_merge: Dict[Tuple[int, ...], int] = {}
        for label in labels:
            instances = (
                {label["dicom"]["instanceid"]}
                | set(label["dicom"].get("groupids") or [])
            ) - visited

            if instances:
                instances_to_merge[tuple(sorted(instances))] = label["classid"] + 1
                visited.update(instances)

        if instances_to_merge:
            input_filename, output_filename = f"{masks[0]}.old.nii.gz", masks[0]
            os.rename(output_filename, input_filename)
            if merge_segmentations(input_filename, output_filename, instances_to_merge):
                files.add(output_filename)
                os.remove(input_filename)
            else:
                log_error("Error processing semantic mask")

    return True, list(files)


async def process_download(
    labels: List[Dict],
    labels_path: Optional[str],
    png_mask: bool,
    color_map: Dict,
    semantic_mask: bool,
    binary_mask: Optional[bool],  # None for auto-judgement
    mhd_mask: bool,
    volume_index: Optional[int],
    is_tax_v2: bool = True,
) -> LabelMapData:
    """Process nifti download file."""
    from redbrick.utils.png import convert_nii_to_png
    from redbrick.utils.mhd import convert_nii_to_mhd

    label_map_data = LabelMapData(
        semantic_mask=False,
        binary_mask=False,
        png_mask=False,
        masks=labels_path,
    )
    async with semaphore:
        try:
            if not (labels_path and os.path.isfile(labels_path)):
                return label_map_data

            filtered_labels = [
                label
                for label in labels
                if label.get("dicom")
                and (
                    volume_index is None
                    or label.get("volumeindex") is None
                    or label["volumeindex"] == volume_index
                )
            ]

            binary_mask = (
                binary_mask
                if binary_mask is not None
                else any(label["dicom"].get("groupids") for label in filtered_labels)
            )

            if not (png_mask or binary_mask or semantic_mask or mhd_mask):
                return label_map_data

            dirname = (
                os.path.splitext(labels_path)[0]
                if labels_path.endswith(".gz")
                else labels_path
            )
            dirname = os.path.splitext(dirname)[0]
            shutil.rmtree(dirname, ignore_errors=True)
            os.makedirs(dirname, exist_ok=True)

            if binary_mask:
                (
                    label_map_data["binary_mask"],
                    label_map_data["masks"],
                ) = convert_to_binary(labels_path, filtered_labels, dirname)
            else:
                label_map_data["masks"] = [labels_path]

            if semantic_mask and label_map_data["masks"]:
                (
                    label_map_data["semantic_mask"],
                    label_map_data["masks"],
                ) = convert_to_semantic(
                    (
                        [label_map_data["masks"]]
                        if isinstance(label_map_data["masks"], str)
                        else label_map_data["masks"]
                    ),
                    filtered_labels,
                    dirname,
                    label_map_data["binary_mask"],
                    is_tax_v2,
                )

            if label_map_data["semantic_mask"]:
                for path in os.listdir(dirname):
                    if path.startswith("instance-"):
                        os.remove(os.path.join(dirname, path))

            if png_mask and label_map_data["masks"]:
                label_map_data["png_mask"], label_map_data["masks"] = (
                    convert_nii_to_png(
                        (
                            [label_map_data["masks"]]
                            if isinstance(label_map_data["masks"], str)
                            else label_map_data["masks"]
                        ),
                        color_map,
                        filtered_labels,
                        dirname,
                        label_map_data["binary_mask"],
                        label_map_data["semantic_mask"],
                        is_tax_v2,
                    )
                )

            if label_map_data["png_mask"]:
                for path in os.listdir(dirname):
                    if path.startswith("instance-") or path.startswith("category-"):
                        os.remove(os.path.join(dirname, path))

            if mhd_mask and label_map_data["masks"]:
                _, label_map_data["masks"] = convert_nii_to_mhd(
                    (
                        [label_map_data["masks"]]
                        if isinstance(label_map_data["masks"], str)
                        else label_map_data["masks"]
                    )
                )

            if not os.listdir(dirname):
                shutil.rmtree(dirname)

        except Exception as error:
            log_error(f"Failed to process {labels_path}: {error}")

        return label_map_data


async def process_upload(
    files: Union[str, List[str]],
    instances: Dict[int, Optional[List[int]]],
    binary_mask: bool,
    png_mask: bool,
    masks: Dict[str, str],
    label_validate: bool = False,
    prune_segmentations: bool = False,
) -> Tuple[Optional[str], Dict[int, Optional[List[int]]], Optional[str]]:
    """Process nifti upload files."""
    import numpy as np  # type: ignore
    from nibabel.loadsave import load as nib_load, save as nib_save  # type: ignore
    from nibabel.nifti1 import Nifti1Image  # type: ignore
    from nibabel.nifti2 import Nifti2Image  # type: ignore
    from redbrick.utils.png import convert_png_to_nii

    async with semaphore:
        if isinstance(files, str):
            files = [files]

        if not files or any(
            not isinstance(file_, str) or not os.path.isfile(file_) for file_ in files
        ):
            return None, {}, "Files do not exist"

        reverse_masks: Dict[str, Tuple[int, ...]] = {}
        for inst_id, mask in masks.items():
            reverse_masks[mask] = reverse_masks.setdefault(mask, tuple()) + (
                int(inst_id),
            )

        if binary_mask or png_mask:
            if not binary_mask:
                return None, {}, "PNG mask upload only supports binary masks"

            for mask, inst_ids in reverse_masks.items():
                if len(inst_ids) > 1:
                    return (
                        None,
                        {},
                        f"Binary mask upload only supports single instance per file: '{mask}'",
                    )

            if png_mask:
                convert_png_to_nii(reverse_masks)
                files = list(reverse_masks.keys())

        try:
            base_img = nib_load(files[0])

            if not isinstance(base_img, (Nifti1Image, Nifti2Image)):
                return None, {}, "Invalid base mask type"

            base_img_dtype = base_img.get_data_dtype()
            if base_img_dtype in (np.uint8, np.uint16):
                base_data = np.asanyarray(base_img.dataobj, dtype=np.uint16)
            else:
                base_data = np.round(base_img.get_fdata(caching="unchanged")).astype(
                    np.uint16
                )
                base_img.set_data_dtype(np.uint16)

            if base_data.ndim != 3:
                return None, {}, "Invalid base mask shape"

            group_map: Dict[int, Set[int]] = {}
            map_instances: Set[int] = set()
            file_instances: Set[int] = set()
            reverse_map: Dict[Tuple[int, ...], int] = {}
            for instance_id, instance_groups in instances.items():
                map_instances.add(instance_id)
                reverse_map[(instance_id,)] = instance_id
                if instance_groups:
                    map_instances.update(instance_groups)
                    for instance_group in instance_groups:
                        group_map.setdefault(instance_group, set()).add(instance_id)

            if group_map:
                if common_instances := (set(instances.keys()) & set(group_map.keys())):
                    raise ValueError(
                        f"Found common instance and group ids: {common_instances}"
                    )
                for group_id, instance_ids in group_map.items():
                    reverse_map[tuple(sorted(instance_ids))] = group_id

            base_nz = np.nonzero(base_data)
            if binary_mask:
                if files[0] in reverse_masks:
                    inst = reverse_masks[files[0]][0]
                    base_data[base_nz] = inst
                    file_instances.add(inst)
            else:
                file_instances.update([x.item() for x in np.unique(base_data[base_nz])])

            final_instances: Set[int] = set(file_instances)

            mask_data: List[Tuple[Tuple[np.ndarray, ...], Union[int, np.ndarray]]] = []
            for file_ in files[1:]:
                img = nib_load(file_)
                if not isinstance(img, (Nifti1Image, Nifti2Image)):
                    return None, {}, "Invalid mask type"

                if (img_dtype := img.get_data_dtype()) in (np.uint8, np.uint16):
                    data = np.asanyarray(img.dataobj, dtype=img_dtype)
                else:
                    data = np.round(img.get_fdata(caching="unchanged")).astype(
                        np.uint16
                    )

                if data.ndim != 3:
                    return None, {}, "Invalid mask shape"

                # Take the non-zero indices of the mask. These are the indices
                # that we want to merge from the current mask into the base mask.
                data_nz = np.nonzero(data)

                if data_nz[0].size == 0:
                    continue

                if binary_mask:
                    if file_ in reverse_masks:
                        inst = reverse_masks[file_][0]
                        mask_data.append((data_nz, inst))
                        file_instances.add(inst)
                else:
                    data_nz_data = data[data_nz]
                    mask_data.append((data_nz, data_nz_data))
                    file_instances.update([x.item() for x in np.unique(data_nz_data)])

            for inst in list(file_instances):
                if inst in group_map:
                    file_instances.update(group_map[inst])

            instance_pool = set(range(1, 65536)) - map_instances - file_instances
            file_excess: Set[int] = set()
            map_excess: Set[int] = set()

            if prune_segmentations:
                if file_excess := file_instances - map_instances:
                    logger.info(
                        f"Pruning segmentation instances: {file_excess}\n"
                        + f"Segmentation(s): {files}"
                    )
                    excess_instances = np.array(list(file_excess), dtype=np.uint16)
                    match = np.isin(base_data[base_nz], excess_instances)
                    base_data[
                        base_nz[0][match], base_nz[1][match], base_nz[2][match]
                    ] = 0
                    file_instances -= file_excess
                    final_instances -= file_excess

                if map_excess := map_instances - file_instances:
                    logger.info(
                        f"Pruning segmentMap instances: {map_excess}\n"
                        + f"Segmentation(s): {files}"
                    )
                    map_instances -= map_excess

            if label_validate and (file_instances != map_instances):
                raise ValueError(
                    "Instance IDs in segmentation file(s) and segmentMap do not match.\n"
                    + f"Segmentation file(s) have instances: {file_instances} and "
                    + f"segmentMap has instances: {map_instances}\n"
                    + f"Segmentation(s): {files}"
                )

            for nzidx, maskv in mask_data:
                # Take the values of the base mask at the current mask's non-zero
                # indices. These may be:
                #   - 0 (no instance),
                #   - a value from instances (an instance), or
                #   - another value not in instances (an overlap group).
                basev = base_data[nzidx]

                if is_int := isinstance(maskv, int):
                    if maskv in file_excess:  # has been pruned
                        continue
                    unique_pairs, inv = np.unique(basev, return_inverse=True)
                else:
                    # We identify the unique pairs of base and mask values, and update all
                    # indices that have the same pair at once.
                    unique_pairs, inv = np.unique(
                        np.column_stack([basev, maskv]), axis=0, return_inverse=True
                    )
                for idx, unique_idxs in enumerate(unique_pairs):
                    mask_v: int = maskv if is_int else unique_idxs[1].item()  # type: ignore
                    if mask_v in file_excess:  # has been pruned
                        continue

                    base_v: int = (unique_idxs if is_int else unique_idxs[0]).item()
                    mask_instances = group_map.get(mask_v, {mask_v})
                    if base_v == 0:
                        # No instance, so we can just set the base value to the instance number
                        group_key = tuple(sorted(mask_instances))
                    else:
                        # An existing instance or group, so we create a new group with the
                        # current instance/group and merge it with the overlapping instance/group
                        base_instances = group_map.get(base_v, {base_v})

                        if base_instances == mask_instances:
                            continue

                        group_instances = base_instances | mask_instances
                        group_key = tuple(sorted(group_instances))
                        if group_key in reverse_map:
                            mask_v = reverse_map[group_key]
                        else:
                            mask_v = min(instance_pool)
                            group_map[mask_v] = group_instances

                    # Determine the indices into the base mask that have the current value pair
                    midx = inv == idx

                    base_data[nzidx[0][midx], nzidx[1][midx], nzidx[2][midx]] = mask_v
                    reverse_map[group_key] = mask_v
                    if mask_v in instance_pool:
                        instance_pool.remove(mask_v)
                    if mask_v in group_map:
                        instance_pool -= group_map[mask_v]

            if mask_data:
                final_instances = {
                    x.item() for x in np.unique(base_data[np.nonzero(base_data)])
                }

            if not final_instances:  # no segmentations
                return None, {}, None

            if max(final_instances) < 256:
                base_img.set_data_dtype(np.uint8)
                base_data = base_data.astype(np.uint8)

            filename = files[0]
            if (  # base_data or base_img changed
                binary_mask
                or file_excess
                or mask_data
                or base_img_dtype != base_img.get_data_dtype()
            ):
                if isinstance(base_img, Nifti1Image):
                    new_img = Nifti1Image(base_data, base_img.affine, base_img.header)
                else:
                    new_img = Nifti2Image(base_data, base_img.affine, base_img.header)

                dirname = os.path.join(config_path(), "temp", str(uuid4()))
                os.makedirs(dirname, exist_ok=True)
                filename = uniquify_path(os.path.join(dirname, "label.nii.gz"))
                nib_save(new_img, filename)

            segment_map: Dict[int, Optional[List[int]]] = {}
            for instance in final_instances:
                if instance in group_map:
                    for instance_id in group_map[instance]:
                        groups = segment_map.get(instance_id)
                        if groups is None:
                            groups = []
                            segment_map[instance_id] = groups
                        groups.append(instance)
                elif instance not in segment_map:
                    segment_map[instance] = None

            return (filename, segment_map, None)

        except Exception as error:
            return None, {}, str(error)
