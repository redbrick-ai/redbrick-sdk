"""Dicom/nifti related functions."""
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TypedDict
from asyncio import BoundedSemaphore
import shutil
from uuid import uuid4

from redbrick.utils.common_utils import config_path
from redbrick.utils.files import uniquify_path
from redbrick.utils.logging import log_error


# pylint: disable=too-many-locals, import-outside-toplevel, too-many-branches, too-many-statements


semaphore = BoundedSemaphore(1)


class LabelMapData(TypedDict):
    """Label map data."""

    semantic_mask: bool
    binary_mask: bool
    png_mask: bool
    masks: Optional[Union[str, List[str]]]


def merge_segmentations(
    input_file: str,
    input_instance: int,
    equals: bool,
    output_file: str,
    output_instance: int,
) -> bool:
    """Merge segmentations from input to output."""
    import numpy  # type: ignore
    from nibabel.loadsave import load as nib_load, save as nib_save  # type: ignore
    from nibabel.nifti1 import Nifti1Image  # type: ignore

    try:
        input_img = nib_load(input_file)

        if not isinstance(input_img, Nifti1Image):
            log_error(f"{input_file} is not a valid NIfTI1 file.")
            return False

        input_data = input_img.get_fdata(caching="unchanged")

        if os.path.isfile(output_file):
            output_img = nib_load(output_file)

            if not isinstance(output_img, Nifti1Image):
                log_error(f"{output_img} is not a valid NIfTI1 file.")
                return False

            output_affine = output_img.affine
            output_header = output_img.header
            output_data = output_img.get_fdata(caching="unchanged")
            output_data = numpy.round(output_data).astype(numpy.uint16)
        else:
            output_affine = input_img.affine
            output_header = input_img.header
            output_data = numpy.zeros(input_data.shape, dtype=numpy.uint16).astype(
                numpy.uint16
            )

        if equals:
            output_data[input_data == input_instance] = output_instance
        else:
            output_data[input_data != input_instance] = output_instance
        new_img = Nifti1Image(output_data, output_affine, output_header)
        new_img.set_data_dtype(output_data.dtype)
        nib_save(new_img, output_file)
        return True
    except Exception as err:  # pylint: disable=broad-except
        log_error(err)
        return False


def convert_to_binary(
    mask: str, labels: List[Dict], dirname: str
) -> Tuple[bool, List[str]]:
    """Convert segmentation to binary."""
    import numpy  # type: ignore
    from nibabel.loadsave import load as nib_load, save as nib_save  # type: ignore
    from nibabel.nifti1 import Nifti1Image  # type: ignore

    img = nib_load(mask)

    if not isinstance(img, Nifti1Image):
        log_error(f"{mask} is not a valid NIfTI1 file.")
        return False, [mask]

    affine = img.affine
    header = img.header
    data = img.get_fdata(caching="unchanged")

    files: List[str] = []

    for label in labels:
        instances: Set[int] = set(
            [label["dicom"]["instanceid"]] + (label["dicom"].get("groupids", []) or [])
        )
        new_data = numpy.zeros(
            data.shape, dtype=numpy.uint8 if max(instances) <= 255 else numpy.uint16
        )
        for instance in instances:
            new_data[data == instance] = 1

        if not numpy.any(new_data):
            continue

        filename = os.path.join(
            dirname, f"instance-{label['dicom']['instanceid']}.nii.gz"
        )
        if os.path.isfile(filename):
            os.remove(filename)

        new_img = Nifti1Image(new_data, affine, header)
        if new_data.dtype == numpy.uint16:
            new_img.set_data_dtype(numpy.uint16)
        nib_save(new_img, filename)
        files.append(filename)

    return True, files


def convert_to_semantic(
    masks: List[str],
    taxonomy: Dict,
    labels: List[Dict],
    dirname: str,
    binary_mask: bool,
) -> Tuple[bool, List[str]]:
    """Convert segmentation to semantic."""
    if not taxonomy.get("isNew"):
        log_error("Taxonomy V1 is not supported")
        return False, masks

    if not (binary_mask or len(masks) == 1):
        log_error(f"Cannot process labels: {labels}")
        return False, masks

    input_filename = output_filename = masks[0]
    if not binary_mask:
        input_filename = f"{output_filename}.old.nii.gz"
        os.rename(output_filename, input_filename)

    visited: Set[int] = set()
    files: Set[str] = set()
    for label in labels:
        instance = label["dicom"]["instanceid"]
        category = label["classid"] + 1
        if binary_mask:
            input_filename = os.path.join(dirname, f"instance-{instance}.nii.gz")
            output_filename = os.path.join(dirname, f"category-{category}.nii.gz")
            merged = merge_segmentations(input_filename, 1, True, output_filename, 1)
        else:
            merged = merge_segmentations(
                input_filename, instance, True, output_filename, category
            )
            visited.add(instance)
            for group_id in label["dicom"].get("groupids", []) or []:
                if group_id in visited:
                    continue
                group_merged = merge_segmentations(
                    input_filename, group_id, True, output_filename, category
                )
                if group_merged:
                    visited.add(group_id)
                else:
                    log_error(f"Error processing semantic mask for: {label}")

        if merged:
            files.add(output_filename)
        else:
            log_error(f"Error processing semantic mask for: {label}")

    if not binary_mask:
        os.remove(input_filename)

    return True, list(files)


def convert_to_png(
    masks: List[str],
    color_map: Dict,
    labels: List[Dict],
    dirname: str,
    binary_mask: bool,
    semantic_mask: bool,
    is_tax_v2: bool,
) -> Tuple[bool, List[str]]:
    """Convert masks to png."""
    import numpy  # type: ignore
    from nibabel.loadsave import load as nib_load  # type: ignore
    from nibabel.nifti1 import Nifti1Image  # type: ignore
    from PIL import Image  # type: ignore

    cat_class_map: Dict[str, str] = {}
    instance_class_map: Dict[int, int] = {}
    for label in labels:
        instance_class_map[label["dicom"]["instanceid"]] = label["classid"] + 1
        category = "::".join(label["category"][0][1:])
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
            if not semantic_mask:
                cat = instance_class_map.get(cat, 0)
            color_mask[mask_arr == 1] = (
                color_map.get(cat - 1, (255, 255, 255))
                if is_tax_v2
                else color_map.get(
                    cat_class_map.get(input_filename, ""), (255, 255, 255)
                )
            )
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


async def process_nifti_download(
    labels: List[Dict],
    labels_path: Optional[str],
    png_mask: bool,
    color_map: Dict,
    semantic_mask: bool,
    binary_mask: Optional[bool],
    taxonomy: Dict,
    volume_index: Optional[int],
) -> LabelMapData:
    """Process nifti download file."""
    label_map_data = LabelMapData(
        semantic_mask=False, binary_mask=False, png_mask=False, masks=labels_path
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

            if not (png_mask or binary_mask or semantic_mask):
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
                    [label_map_data["masks"]]
                    if isinstance(label_map_data["masks"], str)
                    else label_map_data["masks"],
                    taxonomy,
                    filtered_labels,
                    dirname,
                    label_map_data["binary_mask"],
                )

            if label_map_data["semantic_mask"]:
                for path in os.listdir(dirname):
                    if path.startswith("instance-"):
                        os.remove(os.path.join(dirname, path))

            if png_mask and label_map_data["masks"]:
                label_map_data["png_mask"], label_map_data["masks"] = convert_to_png(
                    [label_map_data["masks"]]
                    if isinstance(label_map_data["masks"], str)
                    else label_map_data["masks"],
                    color_map,
                    filtered_labels,
                    dirname,
                    label_map_data["binary_mask"],
                    label_map_data["semantic_mask"],
                    bool(taxonomy.get("isNew")),
                )

            if label_map_data["png_mask"]:
                for path in os.listdir(dirname):
                    if path.startswith("instance-") or path.startswith("category-"):
                        os.remove(os.path.join(dirname, path))

            if not os.listdir(dirname):
                shutil.rmtree(dirname)

        except Exception as error:  # pylint: disable=broad-except
            log_error(f"Failed to process {labels_path}: {error}")

        return label_map_data


async def process_nifti_upload(
    files: Union[str, List[str]],
    instances: Set[int],
    binary_mask: bool,
    semantic_mask: bool,
    png_mask: bool,
    masks: Dict[str, str],
    label_validate: bool,
) -> Tuple[Optional[str], Dict[int, List[int]]]:
    """Process nifti upload files."""
    # pylint: disable=too-many-locals, too-many-branches, import-outside-toplevel
    # pylint: disable=too-many-statements, too-many-return-statements, unused-argument
    async with semaphore:
        import numpy  # type: ignore
        from nibabel.loadsave import load as nib_load, save as nib_save  # type: ignore
        from nibabel.nifti1 import Nifti1Image  # type: ignore
        from nibabel.nifti2 import Nifti2Image  # type: ignore

        if png_mask:
            log_error("PNG mask upload is not supported yet")
            return None, {}

        if isinstance(files, str):
            files = [files]
        if not files or any(
            not isinstance(file_, str) or not os.path.isfile(file_) for file_ in files
        ):
            return None, {}

        if len(files) == 1 and not label_validate:
            return files[0], {}

        try:
            reverse_masks: Dict[str, Tuple[int, ...]] = {}
            for inst_id, mask in masks.items():
                if mask not in reverse_masks:
                    reverse_masks[mask] = tuple()
                reverse_masks[mask] = reverse_masks[mask] + (int(inst_id),)

            delete_files: List[str] = []
            if binary_mask:
                for file_idx, file_path in enumerate(files):
                    new_filename = uniquify_path(f"{file_idx}.nii.gz")
                    if len(
                        reverse_masks.get(file_path, tuple()) or tuple()
                    ) == 1 and merge_segmentations(
                        file_path,
                        0,
                        False,
                        new_filename,
                        reverse_masks[file_path][0],
                    ):
                        delete_files.append(new_filename)
                        files[file_idx] = new_filename

            base_img = nib_load(files[0])
            instance_map: Dict[int, List[int]] = {}
            reverse_instance_map: Dict[Tuple[int, ...], int] = {}

            if not isinstance(base_img, Nifti1Image) and not isinstance(
                base_img, Nifti2Image
            ):
                return None, {}

            base_data = base_img.get_fdata(caching="unchanged")

            if base_img.get_data_dtype() != numpy.uint16:
                base_img.set_data_dtype(numpy.uint16)
                base_data = numpy.round(base_data).astype(numpy.uint16)  # type: ignore

            if base_data.ndim != 3:
                return None, {}

            unique_instances = numpy.unique(base_data)  # type: ignore
            for instance in unique_instances:
                inst = int(round(instance))
                if not inst:
                    continue
                if inst not in instance_map:
                    instance_map[inst] = [inst]
                    reverse_instance_map[(inst,)] = inst

            for img_idx, file_ in enumerate(files):
                if not img_idx:
                    continue

                img = nib_load(file_)
                data = img.get_fdata(caching="unchanged")  # type: ignore
                if base_data.shape != data.shape:
                    return None, {}

                unique_instances = numpy.unique(data)  # type: ignore
                for instance in unique_instances:
                    inst = int(round(instance))
                    if not inst:
                        continue
                    if inst not in instance_map:
                        instance_map[inst] = [inst]
                        reverse_instance_map[(inst,)] = inst

            used_instances = set(instance_map.keys())

            if label_validate and instances != used_instances:
                raise ValueError(
                    "Instance IDs in segmentation file(s) and segmentMap do not match.\n"
                    + f"Segmentation file(s) have instances: {used_instances} and "
                    + f"segmentMap has instances: {instances}\n"
                    + f"Segmentation(s): {files}"
                )

            group_instances = sorted(
                set(range(1, 65536)) - instances - used_instances, reverse=True
            )

            for file_ in files[1:]:
                img = nib_load(file_)
                if not isinstance(img, Nifti1Image) and not isinstance(
                    img, Nifti2Image
                ):
                    return None, {}

                data = img.get_fdata(caching="unchanged")
                if img.get_data_dtype() != numpy.uint16:
                    data = numpy.round(data).astype(numpy.uint16)  # type: ignore

                for i, j, k in zip(  # type: ignore
                    *numpy.where(numpy.logical_and(base_data, data))
                ):
                    sub_instances = tuple(
                        sorted(
                            instance_map[int(base_data[i, j, k])]
                            + instance_map[int(data[i, j, k])]
                        )
                    )
                    if sub_instances not in reverse_instance_map:
                        if not group_instances:
                            return None, {}
                        reverse_instance_map[sub_instances] = group_instances.pop()
                        instance_map[reverse_instance_map[sub_instances]] = list(
                            sub_instances
                        )
                    data[i, j, k] = reverse_instance_map[sub_instances]

                base_data = numpy.where(data, data, base_data)

            if group_instances and group_instances[0] <= 255:
                base_img.set_data_dtype(numpy.uint8)
                base_data = numpy.asarray(base_data, dtype=numpy.uint8)
            else:
                base_data = numpy.asarray(base_data, dtype=numpy.uint16)

            if isinstance(base_img, Nifti1Image):
                new_img = Nifti1Image(base_data, base_img.affine, base_img.header)
            else:
                new_img = Nifti2Image(base_data, base_img.affine, base_img.header)

            dirname = os.path.join(config_path(), "temp", str(uuid4()))
            os.makedirs(dirname, exist_ok=True)
            filename = uniquify_path(os.path.join(dirname, "label.nii.gz"))
            nib_save(new_img, filename)

            group_map: Dict[int, List[int]] = {}
            for sub_ids, group_id in reverse_instance_map.items():
                if len(sub_ids) > 1:
                    for sub_id in sub_ids:
                        if sub_id not in group_map:
                            group_map[sub_id] = []
                        group_map[sub_id].append(group_id)

            for delete_file in delete_files:
                os.remove(delete_file)

            return (filename, group_map)

        except Exception as error:  # pylint: disable=broad-except
            log_error(error)
            return None, {}


async def convert_nii_to_rtstruct(
    nifti_files: List[str],
    dicom_series_path: str,
    categories: List[Dict],
    segment_map: Dict,
) -> Tuple[Optional[Any], Dict]:
    """Convert nifti mask to dicom rt-struct."""
    # pylint: disable=too-many-locals, too-many-branches, import-outside-toplevel
    # pylint: disable=too-many-statements, too-many-return-statements
    async with semaphore:
        import numpy  # type: ignore
        from nibabel.loadsave import load as nib_load  # type: ignore
        from nibabel.nifti1 import Nifti1Image  # type: ignore
        from nibabel.nifti2 import Nifti2Image  # type: ignore
        from rt_utils import RTStructBuilder  # type: ignore

        try:
            category_map = {
                category.get("category", ""): (
                    category.get("classId"),
                    category.get("color", ""),
                    category.get("parents", []) or [],
                )
                for category in categories
            }
            rtstruct = RTStructBuilder.create_new(dicom_series_path=dicom_series_path)
            rtstruct.ds.InstitutionName = "RedBrick AI"
            rtstruct.ds.Manufacturer = "RedBrick AI"
            rtstruct.ds.ManufacturerModelName = "redbrick-sdk"

            new_segment_map = {}
            for nifti_file in nifti_files:
                img: Nifti1Image = nib_load(nifti_file)  # type: ignore

                if not isinstance(img, Nifti1Image) and not isinstance(
                    img, Nifti2Image
                ):
                    return None, {}

                # Load NIfTI file
                data = img.get_fdata(caching="unchanged")

                if data.ndim != 3:
                    return None, {}

                data = data.swapaxes(0, 1)

                if img.get_data_dtype() != numpy.uint16:
                    img.set_data_dtype(numpy.uint16)
                    data = numpy.round(data).astype(numpy.uint16)  # type: ignore

                for label in numpy.unique(data):
                    if not label:
                        continue
                    kwargs = {}
                    cat = segment_map.get(str(label))
                    roi_name = f"Segment_{label}"
                    if cat:
                        new_segment_map[roi_name] = cat
                    if (
                        cat
                        and cat.get("category")
                        and category_map.get(cat["category"])
                    ):
                        selected_cat = category_map[cat["category"]]
                        kwargs["color"] = selected_cat[1]
                        kwargs["description"] = (
                            f"{selected_cat[0]} - "
                            + "".join((parent + "/") for parent in selected_cat[2])
                            + cat["category"]
                        )

                    rtstruct.add_roi(mask=data == label, name=roi_name, **kwargs)

            return rtstruct, new_segment_map
        except Exception as error:  # pylint: disable=broad-except
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
    segment_map: Dict,
    label_validate: bool,
) -> Tuple[Optional[Any], Dict]:
    """Convert dicom rt-struct to nifti mask."""
    # pylint: disable=too-many-locals, too-many-branches, import-outside-toplevel
    # pylint: disable=too-many-statements, too-many-return-statements
    if not rt_struct_files:
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

        if label_validate:
            for roi_name in segment_map.keys():
                if roi_name not in roi_names:
                    log_error(f"ROI '{roi_name}' not found in DICOM RT-Struct")
                    return None, {}

        new_segment_map = {}
        dtype = numpy.uint16 if len(roi_names) >= 250 else numpy.uint8

        nii_mask = numpy.zeros(
            (
                rt_struct.series_data[0].Columns,
                rt_struct.series_data[0].Rows,
                len(rt_struct.series_data),
            ),
            dtype,
        )

        for idx, roi_name in enumerate(segment_map.keys()):
            if roi_name not in roi_names:
                continue
            new_segment_map[str(idx + 1)] = segment_map[roi_name]
            roi_mask = rt_struct.get_roi_mask_by_name(roi_name)
            nii_mask[roi_mask] = idx + 1

        return (
            Nifti1Image(nii_mask.swapaxes(0, 1), numpy.diag([1, 2, 3, 1])),
            new_segment_map,
        )
