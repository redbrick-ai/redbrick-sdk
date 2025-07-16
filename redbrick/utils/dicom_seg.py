"""DICOM Seg utils."""

import os
from typing import List, Optional, Set
import pathlib

import numpy as np
import nibabel as nib
import pydicom
import pydicom_seg_rb  # type: ignore
from pydicom.filereader import dcmread
import SimpleITK

from redbrick.types.taxonomy import ObjectType
from redbrick.utils.common_utils import get_color
from redbrick.types.task import SegmentMap as TypeSegmentMap


def convert_nii_to_dicom_seg(
    label: str,
    dicom_series_path: str,
    categories: List[ObjectType],
    segment_map: TypeSegmentMap,
    binary_mask: bool,
) -> Optional[str]:
    """Convert nifti label to dicom seg."""
    # pylint: disable=too-many-locals
    unique_labels: Set[int]
    if binary_mask:
        unique_labels = {
            int(label.removesuffix(".gz").removesuffix(".nii").rsplit("-")[-1])
        }
    else:
        unique_labels = set(
            np.unique(nib.load(label).get_fdata(caching="unchanged").astype(np.uint16))  # type: ignore
        ) - {0}

    segment_attributes = []
    for inst in unique_labels:
        info = segment_map.get(inst, segment_map.get(str(inst)))
        if info is None:
            continue

        if isinstance(info, int) or (
            isinstance(info, dict) and isinstance(info.get("category"), int)
        ):
            class_id = info["category"] if isinstance(info, dict) else info  # type: ignore
            obj = next((ol for ol in categories if ol["classId"] == class_id), None)
        else:
            if isinstance(info, list) or (
                isinstance(info, dict) and isinstance(info.get("category"), list)
            ):
                cat = info["category"][-1] if isinstance(info, dict) else info[-1]  # type: ignore
                if isinstance(cat, list) and cat and isinstance(cat[-1], str):
                    cat = cat[-1]
            else:
                cat = info["category"] if isinstance(info, dict) else info  # type: ignore
            obj = next(
                (
                    ol
                    for ol in categories
                    if ol["category"] == cat and ol["labelType"] == "SEGMENTATION"
                ),
                None,
            )

        if not obj:
            continue

        segment_attribute = {
            "labelID": 1 if binary_mask else int(inst),
            "SegmentLabel": obj["category"],
            "SegmentAlgorithmType": "SEMIAUTOMATIC",
            "SegmentAlgorithmName": "RedBrick AI",
            "SegmentedPropertyCategoryCodeSequence": {
                "CodeValue": "385432009",
                "CodingSchemeDesignator": "SCT",
                "CodeMeaning": "Not applicable",
            },
            "SegmentedPropertyTypeCodeSequence": {
                "CodeValue": "385432009",
                "CodingSchemeDesignator": "SCT",
                "CodeMeaning": "Not applicable",
            },
            "recommendedDisplayRGBValue": get_color(obj.get("color"), obj["classId"]),
        }
        segment_attributes.append(segment_attribute)

    if not segment_attributes:
        return None

    image_files = pathlib.Path(dicom_series_path).glob("*")
    image_datasets = [dcmread(str(f), stop_before_pixels=True) for f in image_files]

    mask = SimpleITK.ReadImage(label)
    mask = SimpleITK.Cast(mask, SimpleITK.sitkUInt16)

    writer = pydicom_seg_rb.MultiClassWriter(
        template=pydicom_seg_rb.template.from_dcmqi_metainfo(
            {
                "ContentCreatorName": "redbrick-sdk",
                "ClinicalTrialSeriesID": "1",
                "ClinicalTrialTimePointID": "1",
                "SeriesNumber": "1",
                "InstanceNumber": "1",
                "segmentAttributes": [segment_attributes],
            }
        ),
        inplane_cropping=False,
        skip_empty_slices=False,
        skip_missing_segment=False,
    )
    dcm = writer.write(mask, image_datasets)  # type: ignore

    dicom_seg_file = label.removesuffix(".gz").removesuffix(".nii") + ".dcm"
    dcm.save_as(dicom_seg_file)
    return dicom_seg_file


def convert_dicom_seg_to_nii(
    masks: List[str],
    dicom_series_path: str,  # pylint: disable=unused-argument
) -> List[str]:
    """Convert dicom seg to nifti."""
    new_masks: List[str] = []
    for mask in masks:
        new_mask = mask.removesuffix(".dcm") + ".nii.gz"
        new_masks.append(new_mask)

        dcm = pydicom.dcmread(mask)
        reader = pydicom_seg_rb.MultiClassReader()
        result = reader.read(dcm)

        SimpleITK.WriteImage(result.image, new_mask, True)
        os.remove(mask)

    return new_masks
