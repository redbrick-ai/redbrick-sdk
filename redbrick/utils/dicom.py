"""Dicom/nifti related functions."""
import os
from typing import Dict, List, Optional, Set, Tuple, Union
import shutil

from redbrick.utils.files import uniquify_path
from redbrick.utils.logging import log_error


def process_nifti_download(
    labels: List[Dict],
    labels_path: Optional[str],
    png_mask: bool,
    color_map: Dict,
    is_tax_v2: bool,
) -> Optional[Union[str, List[str]]]:
    """Process nifti download file."""
    # pylint: disable=too-many-locals, import-outside-toplevel
    import nibabel  # type: ignore
    import numpy
    from PIL import Image  # type: ignore

    try:
        if not (labels_path and os.path.isfile(labels_path)):
            return labels_path

        overlapping_labels = any(
            label.get("dicom", {}).get("groupids") for label in labels
        )

        if not (png_mask or overlapping_labels):
            return labels_path

        img = nibabel.load(labels_path)

        if not isinstance(img, nibabel.Nifti1Image):
            log_error(f"{labels_path} is not a valid NIfTI1 file.")
            return labels_path

        affine = img.affine
        header = img.header
        data = img.get_fdata()

        dirname = (
            os.path.splitext(labels_path)[0]
            if labels_path.endswith(".gz")
            else labels_path
        )
        dirname = os.path.splitext(dirname)[0]

        mask_arr: numpy.ndarray = numpy.array([0])
        if png_mask:
            mask_arr = numpy.transpose(data, (1, 0, 2))
            mask_arr = mask_arr.reshape(mask_arr.shape[0], mask_arr.shape[1])

            if not overlapping_labels:
                color_mask = numpy.zeros((mask_arr.shape[0], mask_arr.shape[1], 3))
                for label in labels:
                    if label.get("dicom"):
                        color_mask[mask_arr == label["dicom"]["instanceid"]] = (
                            color_map.get(label.get("classid", -1), (255, 255, 255))
                            if is_tax_v2
                            else color_map.get(
                                "::".join(label["category"][0][1:]), (255, 255, 255)
                            )
                        )

                pil_color_mask = Image.fromarray(color_mask.astype(numpy.uint8))
                pil_color_mask.save(uniquify_path(f"{dirname}.png"))
                return [labels_path]

        shutil.rmtree(dirname, ignore_errors=True)
        os.makedirs(dirname, exist_ok=True)
        files: List[str] = []

        for label in labels:
            if label.get("dicom"):
                instances: List[int] = [label["dicom"]["instanceid"]] + (
                    label["dicom"].get("groupids", []) or []
                )

                if png_mask:
                    color_mask = numpy.where(
                        numpy.isin(mask_arr, instances),
                        color_map.get(
                            "::".join(label["category"][0][1:]), (255, 255, 255)
                        ),
                        (0, 0, 0),
                    )
                    filename = uniquify_path(
                        os.path.join(dirname, f"{label['dicom']['instanceid']}.png")
                    )
                    pil_color_mask = Image.fromarray(color_mask.astype(numpy.uint8))
                    pil_color_mask.save(filename)
                else:
                    new_data = numpy.where(
                        numpy.isin(data, instances), label["dicom"]["instanceid"], 0  # type: ignore
                    )
                    filename = uniquify_path(
                        os.path.join(dirname, f"{label['dicom']['instanceid']}.nii.gz")
                    )
                    new_img = nibabel.Nifti1Image(new_data, affine, header)
                    nibabel.save(new_img, filename)

                files.append(filename)

        return files

    except Exception as error:  # pylint: disable=broad-except
        log_error(f"Failed to process {labels_path}: {error}")
        return labels_path


def process_nifti_upload(
    files: Union[str, List[str]], instances: Set[int], label_validate: bool
) -> Tuple[Optional[str], Dict[int, List[int]]]:
    """Process nifti upload files."""
    # pylint: disable=too-many-locals, too-many-branches, import-outside-toplevel
    # pylint: disable=too-many-statements, too-many-return-statements
    import nibabel  # type: ignore
    import numpy

    if isinstance(files, str):
        files = [files]
    if not files or any(
        not isinstance(file_, str) or not os.path.isfile(file_) for file_ in files
    ):
        return None, {}

    if len(files) == 1 and not label_validate:
        return files[0], {}

    try:
        instance_map: Dict[int, List[int]] = {}
        reverse_instance_map: Dict[Tuple[int, ...], int] = {}
        base_img = nibabel.load(files[0])

        if not isinstance(base_img, nibabel.Nifti1Image) and not isinstance(
            base_img, nibabel.Nifti2Image
        ):
            return None, {}

        base_data = base_img.get_fdata()

        if base_img.get_data_dtype() != numpy.uint16:
            base_img.set_data_dtype(numpy.uint16)
            base_data = numpy.round(base_data).astype(numpy.uint16)  # type: ignore

        if base_data.ndim != 3:
            return None, {}

        for instance in numpy.unique(base_data):  # type: ignore
            if instance and instance not in instance_map:
                inst = int(instance)
                instance_map[inst] = [inst]
                reverse_instance_map[(inst,)] = inst

        for file_ in files[1:]:
            img = nibabel.load(file_)
            data = img.get_fdata()
            if base_data.shape != data.shape:
                return None, {}

            for instance in numpy.unique(data):  # type: ignore
                if instance and instance not in instance_map:
                    inst = int(instance)
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
            img = nibabel.load(file_)
            if not isinstance(img, nibabel.Nifti1Image) and not isinstance(
                img, nibabel.Nifti2Image
            ):
                return None, {}

            data = img.get_fdata()
            if img.get_data_dtype() != numpy.uint16:
                data = numpy.round(data).astype(numpy.uint16)  # type: ignore

            for i, j, k in zip(*numpy.where(numpy.logical_and(base_data, data))):  # type: ignore
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

        if isinstance(base_img, nibabel.Nifti1Image):
            new_img = nibabel.Nifti1Image(base_data, base_img.affine, base_img.header)
        else:
            new_img = nibabel.Nifti2Image(base_data, base_img.affine, base_img.header)

        dirname = os.path.join(os.path.expanduser("~"), ".redbrickai", "temp")
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        filename = uniquify_path(os.path.join(dirname, "label.nii.gz"))
        nibabel.save(new_img, filename)

        group_map: Dict[int, List[int]] = {}
        for sub_ids, group_id in reverse_instance_map.items():
            if len(sub_ids) > 1:
                for sub_id in sub_ids:
                    if sub_id not in group_map:
                        group_map[sub_id] = []
                    group_map[sub_id].append(group_id)

        return (filename, group_map)

    except Exception as error:  # pylint: disable=broad-except
        log_error(error)
        return None, {}
