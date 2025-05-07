"""Dicom/nifti related functions."""

import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TypedDict
from asyncio import BoundedSemaphore
import shutil
from uuid import uuid4

import aiohttp

from redbrick.common.constants import DEFAULT_URL, MAX_CONCURRENCY, MAX_FILE_BATCH_SIZE
from redbrick.types.taxonomy import ObjectType
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.common_utils import config_path
from redbrick.utils.files import uniquify_path
from redbrick.utils.logging import log_error, logger
from redbrick.types.task import SegmentMap as TypeSegmentMap

# pylint: disable=too-many-lines, too-many-locals, too-many-branches, too-many-statements
# pylint: disable=import-outside-toplevel, broad-except, too-many-return-statements


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
    import numpy  # type: ignore
    from nibabel.loadsave import load as nib_load  # type: ignore
    from nibabel.nifti1 import Nifti1Image  # type: ignore
    from PIL import Image  # type: ignore

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
    import numpy  # type: ignore
    from nibabel.loadsave import save as nib_save  # type: ignore
    from nibabel.nifti1 import Nifti1Image  # type: ignore
    from PIL import Image  # type: ignore

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


def convert_nii_to_mhd(masks: List[str]) -> Tuple[bool, List[str]]:
    """Convert nifti masks to mhd."""
    import SimpleITK as sitk

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
    import SimpleITK as sitk

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
    async with semaphore:
        import numpy as np  # type: ignore
        from nibabel.loadsave import load as nib_load, save as nib_save  # type: ignore
        from nibabel.nifti1 import Nifti1Image  # type: ignore
        from nibabel.nifti2 import Nifti2Image  # type: ignore

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


async def convert_nii_to_rtstruct(
    nifti_files: List[str],
    dicom_series_path: str,
    categories: List[ObjectType],
    segment_map: TypeSegmentMap,
    semantic_mask: bool,
    binary_mask: bool,
) -> Tuple[Optional[Any], TypeSegmentMap]:
    """Convert nifti mask to dicom rt-struct."""
    async with semaphore:
        import numpy  # type: ignore
        from nibabel.loadsave import load as nib_load  # type: ignore
        from nibabel.nifti1 import Nifti1Image  # type: ignore
        from nibabel.nifti2 import Nifti2Image  # type: ignore
        from rt_utils import RTStructBuilder  # type: ignore

        try:
            category_map = {
                category.get("category", ""): (
                    int(category.get("classId", -1)),
                    category.get("color", ""),
                    category.get("parents", []) or [],
                )
                for category in categories
            }
            rtstruct = RTStructBuilder.create_new(dicom_series_path=dicom_series_path)
            rtstruct.ds.InstitutionName = "RedBrick AI"
            rtstruct.ds.Manufacturer = "RedBrick AI"
            rtstruct.ds.ManufacturerModelName = "redbrick-sdk"

            new_segment_map: TypeSegmentMap = {}
            for nifti_file in nifti_files:
                img: Nifti1Image = nib_load(nifti_file)  # type: ignore

                if not isinstance(img, Nifti1Image) and not isinstance(
                    img, Nifti2Image
                ):
                    return None, {}

                # Load NIfTI file
                data = img.get_fdata(caching="unchanged")
                data = numpy.round(data).astype(numpy.uint16)  # type: ignore

                if data.ndim != 3:
                    return None, {}

                data = data.swapaxes(0, 1)
                unique_instances: Set[int] = set(numpy.unique(data))
                if 0 in unique_instances:
                    unique_instances.remove(0)

                if binary_mask:
                    unique_instances = {
                        int(nifti_file.replace(".nii.gz", "").rsplit("-")[-1])
                    }

                cat: Optional[Union[str, Dict]] = None
                category: Optional[str] = None
                segment_remap: Dict[str, Union[str, Dict]] = {}
                if semantic_mask:
                    new_data = numpy.zeros_like(data)
                    for instance in unique_instances:
                        cat = segment_map.get(str(instance))  # type: ignore
                        category = cat.get("category") if isinstance(cat, dict) else cat
                        if not (
                            category
                            and category_map.get(category)
                            and category_map[category][0] >= 0
                        ):
                            continue

                        new_instance = category_map[category][0] + 1
                        if binary_mask:
                            new_data[data != 0] = new_instance
                        else:
                            new_data[data == instance] = new_instance
                        if str(new_instance) not in segment_remap:
                            segment_remap[str(new_instance)] = cat  # type: ignore

                    data = new_data
                    unique_instances.clear()
                    unique_instances.update({int(new_key) for new_key in segment_remap})

                for instance in unique_instances:
                    kwargs = {}
                    cat = segment_remap.get(str(instance), segment_map.get(str(instance)))  # type: ignore
                    category = cat.get("category") if isinstance(cat, dict) else cat
                    roi_name = (
                        category
                        if category and semantic_mask
                        else f"Segment_{instance}"
                    )
                    if cat:
                        new_segment_map[roi_name] = cat  # type: ignore

                    if category and category_map.get(category):
                        selected_cat = category_map[category]
                        kwargs["color"] = selected_cat[1]
                        kwargs["description"] = (
                            f"{selected_cat[0]} - "
                            + "".join((parent + "/") for parent in selected_cat[2])
                            + category
                        )

                    if binary_mask:
                        rtstruct.add_roi(mask=data != 0, name=roi_name, **kwargs)
                    else:
                        rtstruct.add_roi(mask=data == instance, name=roi_name, **kwargs)

            return rtstruct, new_segment_map
        except Exception as error:
            log_error(error)
            return None, {}


def merge_rtstructs(rtstruct1: Any, rtstruct2: Any) -> Any:
    """Merge two rtstructs."""
    for roi_contour_seq, struct_set_roi_seq, rt_roi_observation_seq in zip(
        rtstruct1.ds.ROIContourSequence,
        rtstruct1.ds.StructureSetROISequence,
        rtstruct1.ds.RTROIObservationsSequence,
    ):
        roi_name = struct_set_roi_seq.ROIName

        # Check for ROI name duplication in rtstruct2
        duplicate_roi = next(
            (
                roi_seq2
                for roi_seq2 in rtstruct2.ds.StructureSetROISequence
                if roi_seq2.ROIName == roi_name
            ),
            None,
        )

        if duplicate_roi:
            # If ROI name already exists in rtstruct2, append contours to the existing ROI
            duplicate_roi_contour_seq = next(
                (
                    contour_seq
                    for contour_seq in rtstruct2.ds.ROIContourSequence
                    if contour_seq.ReferencedROINumber == duplicate_roi.ROINumber
                ),
                None,
            )
            if duplicate_roi_contour_seq:
                duplicate_roi_contour_seq.ContourSequence.extend(
                    roi_contour_seq.ContourSequence
                )
            else:
                # If no contour sequence found for the duplicate ROI, create a new one
                rtstruct2.ds.ROIContourSequence.append(roi_contour_seq)
                duplicate_roi.ROINumber = len(rtstruct2.ds.StructureSetROISequence)
        else:
            # If ROI name is unique, proceed with existing logic
            roi_number = len(rtstruct2.ds.StructureSetROISequence) + 1
            roi_contour_seq.ReferencedROINumber = roi_number
            struct_set_roi_seq.ROINumber = roi_number
            rt_roi_observation_seq.ReferencedROINumber = roi_number

            rtstruct2.ds.ROIContourSequence.append(roi_contour_seq)
            rtstruct2.ds.StructureSetROISequence.append(struct_set_roi_seq)
            rtstruct2.ds.RTROIObservationsSequence.append(rt_roi_observation_seq)

    return rtstruct2


async def convert_rtstruct_to_nii(
    rt_struct_files: List[str],
    dicom_series_path: str,
    segment_map: TypeSegmentMap,
    label_validate: bool,
    categories: List[ObjectType],
) -> Tuple[Optional[Any], TypeSegmentMap]:
    """Convert dicom rt-struct to nifti mask."""
    if not rt_struct_files:
        log_error("No segmentations found")
        return None, {}

    async with semaphore:
        import numpy  # type: ignore
        from nibabel.nifti1 import Nifti1Image  # type: ignore
        from rt_utils import RTStructBuilder  # type: ignore

        rt_struct = RTStructBuilder.create_from(dicom_series_path, rt_struct_files[0])
        for rt_struct_file in rt_struct_files[1:]:
            rt_struct = merge_rtstructs(
                rt_struct,
                RTStructBuilder.create_from(dicom_series_path, rt_struct_file),
            )

        roi_names = set(rt_struct.get_roi_names())

        for name in set(segment_map.keys()):
            if name not in roi_names:
                del segment_map[name]

        misses = roi_names - set(segment_map.keys())  # type: ignore
        if misses:
            logger.warning(
                f"Following ROI names are present in the file, but not in segmentMap: {misses}"
            )

        if label_validate:
            category_names = {cat["category"] for cat in categories}
            for cat in segment_map.values():
                if isinstance(cat, dict):
                    cat = cat.get("category")  # type: ignore
                if cat not in category_names:
                    log_error(
                        f"ROI '{cat}' of labelType SEGMENTATION is not present in the taxonomy"
                    )
                    return None, {}

        new_segment_map: TypeSegmentMap = {}
        dtype = numpy.uint16 if len(roi_names) >= 250 else numpy.uint8

        nii_mask = numpy.zeros(
            (
                rt_struct.series_data[0].Columns,
                rt_struct.series_data[0].Rows,
                len(rt_struct.series_data),
            ),
            dtype,
        )

        for idx, name in enumerate(segment_map.keys()):
            if name not in roi_names:
                continue

            try:
                roi_mask = rt_struct.get_roi_mask_by_name(name)
            except Exception as error:  # pylint: disable=broad-except
                logger.warning(f"Error processing mask for ROI: {name} - {error}")
                continue

            new_segment_map[str(idx + 1)] = segment_map[name]
            nii_mask[roi_mask] = idx + 1

        return (
            Nifti1Image(nii_mask.swapaxes(0, 1), numpy.diag([-1, -1, 1, 1])),
            new_segment_map,
        )


def move_group2_to_file_meta(dataset: Any) -> Any:
    """Move all group 2 elements to file meta.

    Args
    ----
    metadata_dcm_dataset: pydicom.Dataset
        The metadata of the DICOM file.
    """
    # pylint: disable=import-outside-toplevel
    import pydicom.dataset

    if not hasattr(dataset, "file_meta"):
        dataset.file_meta = pydicom.dataset.FileMetaDataset()

    for elem in dataset:
        if elem.tag.group == 2:
            dataset.file_meta.add(elem)
            del dataset[elem.tag]

    return dataset


async def save_dicom_dataset(
    instance_metadata: Dict,
    instance_frames_metadata: List[Dict],
    presigned_image_urls: List[str],
    destination_file: str,
    aiosession: aiohttp.ClientSession,
) -> None:
    """Create and save a DICOM dataset using metadata and image frame URLs.

    Args
    ------------
    instance_metadata: Dict
        Metadata of the instance.
    instance_frames_metadata: List[Dict]
        Metadata of the instance frames.
    presigned_image_urls: List[str]
        Presigned URLs of the image frames.
    destination_file: str
        Destination file to save the DICOM dataset.
    aiosession: aiohttp.ClientSession
        aiohttp ClientSession to be used for the HTTP requests.
    """
    # pylint: disable=import-outside-toplevel
    import pydicom
    import pydicom.dataset
    import pydicom.encaps
    import pydicom.tag
    import pydicom.uid
    from pydicom.uid import (
        UID_dictionary,  # type: ignore
        AllTransferSyntaxes,
        JPEG2000TransferSyntaxes,
    )

    HTJ2KLosslessRPCL = pydicom.uid.UID(  # pylint: disable=invalid-name
        "1.2.840.10008.1.2.4.202"
    )
    AllTransferSyntaxes.append(HTJ2KLosslessRPCL)
    JPEG2000TransferSyntaxes.append(HTJ2KLosslessRPCL)
    UID_dictionary[HTJ2KLosslessRPCL] = (
        "High-Throughput JPEG 2000 with RPCL Options Image Compression (Lossless Only)",
        "Transfer Syntax",
        "",
        "",
        "HTJ2KLosslessRPCL",
    )

    async def get_image_content(
        aiosession: aiohttp.ClientSession, image_url: str
    ) -> bytes:
        """Get image content."""
        async with aiosession.get(image_url) as response:
            return await response.content.read()

    frame_contents = await gather_with_concurrency(
        MAX_FILE_BATCH_SIZE,
        *[
            get_image_content(aiosession, image_url=image_frame_url)
            for image_frame_url in presigned_image_urls
        ],
    )

    ds_file = pydicom.Dataset.from_json(instance_metadata)
    ds_file.TransferSyntaxUID = pydicom.uid.UID(
        instance_frames_metadata[0]["metaData"]["00020010"]["Value"][0]
    )

    move_group2_to_file_meta(ds_file)

    ds_file.PixelData = pydicom.encaps.encapsulate(frame_contents)

    if ds_file.file_meta.TransferSyntaxUID == HTJ2KLosslessRPCL:
        ds_file.is_little_endian = True
        ds_file.is_implicit_VR = False
    ds_file.save_as(destination_file, write_like_original=False)
    logger.debug(f"Saved DICOM dataset to {destination_file}")


async def save_dicom_series(
    altadb_meta_content_url: str,
    series_dir: str,
    base_url: str = DEFAULT_URL,
    headers: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Save DICOM files using AltaDB URLs.
    Given an AltaDB URL containing the metadata and image frames.

    Save the DICOM files to the destination directory.
    One DICOM file can contain multiple image frames.

    Args
    ------------
    altadb_meta_content_url: str
        AltaDB URL containing the metadata and image frames.
        This URL can be signed or unsigned.
    base_dir: str
        Destination directory to save the DICOM files.
    base_url: str
        Base URL for the AltaDB API.
    headers: Optional[Dict[str, str]]
        Headers to be used for the HTTP requests.
        If the altaDB_meta_content_url is unsigned, the headers should contain the authorization token.

    Returns
    ------------
    List[str]
        List of the saved DICOM files relative to the dataset root.
    """
    # pylint: disable=too-many-locals
    os.makedirs(series_dir, exist_ok=True)

    res: List[str] = []
    if altadb_meta_content_url.startswith("altadb:///"):
        altadb_meta_content_url = "".join([base_url, "/", altadb_meta_content_url[10:]])
    elif altadb_meta_content_url.startswith("altadb://"):
        altadb_meta_content_url = altadb_meta_content_url.replace(
            "altadb://", "https://"
        )

    async with aiohttp.ClientSession() as aiosession:
        async with aiosession.get(altadb_meta_content_url, headers=headers) as response:
            res_json = await response.json()
            frameid_url_map: Dict[str, str] = {
                frame["id"]: frame["path"] for frame in res_json.get("imageFrames", [])
            }

            tasks = []
            metadata_url = res_json["metaData"]
            instances: List[Dict[str, Any]] = []
            async with aiosession.get(metadata_url) as response:
                response.raise_for_status()
                instances = (await response.json())["instances"]
            for instance in instances:
                frame_ids = [frame["id"] for frame in instance["frames"]]
                image_frames_urls = [
                    frameid_url_map[frame_id] for frame_id in frame_ids
                ]
                file_from_dataset_root = os.path.join(
                    series_dir, f"{instance['frames'][0]['id']}.dcm"
                )
                tasks.append(
                    save_dicom_dataset(
                        instance["metaData"],
                        instance["frames"],
                        image_frames_urls,
                        file_from_dataset_root,
                        aiosession,
                    )
                )
                res.append(file_from_dataset_root)

            await gather_with_concurrency(
                MAX_CONCURRENCY,
                *tasks,
                progress_bar_name=f"Saving series {series_dir.split('/')[-1]}",
                keep_progress_bar=False,
            )

    return res
