"""Dicom/nifti related functions."""
import os
from typing import Dict, List, Optional, Union

import nibabel  # type: ignore
import numpy

from redbrick.utils.logging import print_error


def process_nifti_download(task: Dict) -> Optional[Union[str, List[str]]]:
    """Process nifti download file."""
    labels_path: Optional[str] = task.get("labelsPath")
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

        if not isinstance(img, nibabel.nifti1.Nifti1Image):
            print_error(f"{labels_path} is not a valid NIfTI1 file.")
            return labels_path

        affine = img.affine
        header = img.header
        data = img.get_fdata()

        dirname = os.path.splitext(labels_path)[0]
        os.mkdir(dirname)
        files: List[str] = []

        for label in task["labels"]:
            if label.get("dicom"):
                instances: List[int] = [label["dicom"]["instanceid"]] + label[
                    "dicom"
                ].get("groupids", [])
                filename = (
                    dirname + os.path.sep + str(label["dicom"]["instanceid"]) + ".nii"
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
