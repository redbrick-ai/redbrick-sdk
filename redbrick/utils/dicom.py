"""Dicom/nifti related functions."""
import os
from typing import Dict, List, Optional, Tuple, Union

import nibabel  # type: ignore
import numpy

from redbrick.utils.files import uniquify_path
from redbrick.utils.logging import print_error


def process_nifti_download(
    task: Dict, labels_path: Optional[str]
) -> Optional[Union[str, List[str]]]:
    """Process nifti download file."""
    try:
        if not (
            labels_path
            and os.path.isfile(labels_path)
            and any(
                label.get("dicom", {}).get("groupids")
                for label in task.get("labels", [])
            )
        ):
            return labels_path

        img = nibabel.load(labels_path)

        if not isinstance(img, nibabel.Nifti1Image):
            print_error(f"{labels_path} is not a valid NIfTI1 file.")
            return labels_path

        affine = img.affine
        header = img.header
        data = img.get_fdata()

        dirname = uniquify_path(os.path.splitext(labels_path)[0])
        os.mkdir(dirname)
        files: List[str] = []

        for label in task["labels"]:
            if label.get("dicom"):
                instances: List[int] = [label["dicom"]["instanceid"]] + (
                    label["dicom"].get("groupids", []) or []
                )
                filename = uniquify_path(
                    os.path.join(dirname, f"{label['dicom']['instanceid']}.nii")
                )

                new_img = nibabel.Nifti1Image(
                    numpy.where(
                        numpy.isin(data, instances),  # type: ignore
                        label["dicom"]["instanceid"],
                        0,
                    ),
                    affine,
                    header,
                )
                nibabel.save(new_img, filename)
                files.append(filename)

        return files

    except Exception as error:  # pylint: disable=broad-except
        print_error(f"Failed to process {labels_path}: {error}")
        return labels_path


def process_nifti_upload(
    files: List[str],
) -> Tuple[Optional[str], Dict[int, List[int]]]:
    """Process nifti upload files."""
    # pylint: disable=too-many-locals, too-many-branches
    # pylint: disable=too-many-statements, too-many-return-statements
    if not files or any(
        not isinstance(file_, str) or not os.path.isfile(file_) for file_ in files
    ):
        return None, {}

    if len(files) == 1:
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

        group_instances = sorted(
            set(range(1, 65536)) - set(instance_map.keys()), reverse=True
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

            for i, j, k in zip(*numpy.where(numpy.logical_and(base_data, data))):
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

        base_data = numpy.asarray(base_data, dtype=numpy.uint16)

        if isinstance(base_img, nibabel.Nifti1Image):
            new_img = nibabel.Nifti1Image(base_data, base_img.affine, base_img.header)
        else:
            new_img = nibabel.Nifti2Image(base_data, base_img.affine, base_img.header)

        dirname = os.path.join(os.path.expanduser("~"), ".redbrickai", "temp")
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        filename = uniquify_path(os.path.join(dirname, "label.nii"))
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
        print_error(error)
        return None, {}
