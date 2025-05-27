"""DICOM RT Struct utils."""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
from asyncio import BoundedSemaphore

import numpy  # type: ignore
from nibabel.loadsave import load as nib_load  # type: ignore
from nibabel.nifti1 import Nifti1Image  # type: ignore
from nibabel.nifti2 import Nifti2Image  # type: ignore
from rt_utils import RTStructBuilder  # type: ignore

from redbrick.types.taxonomy import ObjectType
from redbrick.utils.logging import log_error, logger
from redbrick.types.task import SegmentMap as TypeSegmentMap


semaphore = BoundedSemaphore(1)


async def convert_nii_to_rt_struct(
    nifti_files: List[str],
    dicom_series_path: str,
    categories: List[ObjectType],
    segment_map: TypeSegmentMap,
    semantic_mask: bool,
    binary_mask: bool,
) -> Tuple[Optional[Any], TypeSegmentMap]:
    """Convert nifti mask to dicom rt-struct."""
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    async with semaphore:
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
        except Exception as error:  # pylint: disable=broad-exception-caught
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


async def convert_rt_struct_to_nii(
    rt_struct_files: List[str],
    dicom_series_path: str,
    segment_map: TypeSegmentMap,
    label_validate: bool,
    categories: List[ObjectType],
) -> Tuple[Optional[Any], TypeSegmentMap]:
    """Convert dicom rt-struct to nifti mask."""
    # pylint: disable=too-many-locals
    if not rt_struct_files:
        log_error("No segmentations found")
        return None, {}

    async with semaphore:
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
