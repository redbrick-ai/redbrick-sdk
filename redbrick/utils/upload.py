"""Upload implementations."""

import json
import os
import shutil
from uuid import uuid4
from typing import List, Dict, Tuple, TypeVar, Union, Optional, Sequence
from urllib.parse import urlparse

import aiohttp

from redbrick.common.constants import LABELS_ARRAY_LIMIT
from redbrick.common.context import RBContext
from redbrick.common.storage import StorageMethod
from redbrick.types.taxonomy import Taxonomy
from redbrick.types.task import InputTask, OutputTask
from redbrick.utils.common_utils import config_path
from redbrick.utils.files import (
    NIFTI_FILE_TYPES,
    download_files,
    uniquify_path,
    upload_files,
)
from redbrick.utils.logging import log_error, logger


T = TypeVar("T", InputTask, OutputTask)


async def convert_rt_struct_to_nii_labels(
    context: RBContext,
    org_id: str,
    taxonomy: Taxonomy,
    tasks: List[T],
    storage_id: str,
    label_storage_id: str,
    label_validate: bool,
    task_dir: Optional[str] = None,
) -> List[T]:
    """Convert rt struct labels to nifti."""
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements, import-outside-toplevel
    from nibabel.loadsave import save as nib_save  # type: ignore
    from redbrick.utils.dicom import convert_rtstruct_to_nii

    if not task_dir:
        task_dir = os.getcwd()

    for task_idx, task in enumerate(tasks):
        for series_idx, series in enumerate(task.get("series", []) or []):
            if "segmentations" not in series and "segmentations" in task:
                series["segmentations"] = task["segmentations"]  # type: ignore
            if "segmentMap" not in series and "segmentMap" in task:
                series["segmentMap"] = task["segmentMap"]  # type: ignore

            if (
                not series.get("items")
                or not series.get("segmentations")
                or not series.get("segmentMap")
            ):
                logger.info(
                    "Skipping rt-struct processing for "
                    + f"task->{task_idx}->series->{series_idx}"
                )
                continue

            series_items = series.get("items", [])
            items: List[str] = (
                [series_items] if isinstance(series_items, str) else series_items
            )
            series_segmentations = series.get("segmentations", [])
            segmentations: List[str] = (
                [series_segmentations]
                if isinstance(series_segmentations, str)
                else series_segmentations
            )
            segment_map = series.get("segmentMap", {})
            if segment_map.get("binaryMask"):
                del segment_map["binaryMask"]
            if segment_map.get("semanticMask"):
                del segment_map["semanticMask"]
            if segment_map.get("pngMask"):
                del segment_map["pngMask"]

            temp_dir = os.path.join(config_path(), "temp", str(uuid4()))
            temp_img_dir = os.path.join(temp_dir, "images")
            temp_seg_dir = os.path.join(temp_dir, "segmentations")
            os.makedirs(temp_dir, exist_ok=True)
            os.makedirs(temp_img_dir, exist_ok=True)
            os.makedirs(temp_seg_dir, exist_ok=True)

            if storage_id == StorageMethod.REDBRICK:
                logger.info(
                    f"Copying items into: {temp_img_dir}",
                )
                for item in items:
                    shutil.copy(
                        (
                            item
                            if os.path.isabs(item)
                            or not os.path.exists(os.path.join(task_dir, item))
                            else os.path.abspath(os.path.join(task_dir, item))
                        ),
                        os.path.join(temp_img_dir, os.path.basename(item)),
                    )
            else:
                presigned_items = context.export.presign_items(
                    org_id, storage_id, items
                )
                await download_files(
                    list(
                        zip(
                            presigned_items,
                            [
                                os.path.join(temp_img_dir, f"{idx + 1}.dcm")
                                for idx in range(len(items))
                            ],
                        )
                    ),
                    f"Downloading items into: {temp_img_dir}",
                )

            if label_storage_id == StorageMethod.REDBRICK:
                logger.info(
                    f"Copying segmentations into: {temp_seg_dir}",
                )
                for seg in segmentations:
                    shutil.copy(
                        (
                            seg
                            if os.path.isabs(seg)
                            or not os.path.exists(os.path.join(task_dir, seg))
                            else os.path.abspath(os.path.join(task_dir, seg))
                        ),
                        os.path.join(temp_seg_dir, os.path.basename(seg)),
                    )
            else:
                presigned_segs = context.export.presign_items(
                    org_id, label_storage_id, segmentations
                )
                await download_files(
                    list(
                        zip(
                            presigned_segs,
                            [
                                os.path.join(temp_seg_dir, f"{idx + 1}.dcm")
                                for idx in range(len(presigned_segs))
                            ],
                        )
                    ),
                    f"Downloading segmentations into: {temp_seg_dir}",
                )

            mask, segment_map = await convert_rtstruct_to_nii(
                [os.path.join(temp_seg_dir, seg) for seg in os.listdir(temp_seg_dir)],
                temp_img_dir,
                segment_map,
                label_validate,
                [
                    cat
                    for cat in (taxonomy.get("objectTypes", []) or [])
                    if cat["labelType"] == "SEGMENTATION" and not cat.get("archived")
                ],
            )

            shutil.rmtree(temp_img_dir)
            if not mask:
                shutil.rmtree(temp_dir)
                log_error(
                    "Failed rt-struct processing for "
                    + f"task->{task_idx}->series->{series_idx}",
                    True,
                )

            assert mask
            series["segmentations"] = os.path.join(temp_seg_dir, "segmentations.nii.gz")
            series["segmentMap"] = segment_map
            nib_save(mask, series["segmentations"])  # type: ignore

        if "segmentations" in task and all(
            "segmentations" in series
            for series in task.get("series", []) or []  # type: ignore
        ):
            del task["segmentations"]  # type: ignore
        if "segmentMap" in task and all(
            "segmentMap" in series
            for series in task.get("series", []) or []  # type: ignore
        ):
            del task["segmentMap"]  # type: ignore

    return tasks


async def convert_mhd_to_nii_labels(
    context: RBContext,
    org_id: str,
    tasks: List[T],
    label_storage_id: str,
    task_dir: Optional[str] = None,
) -> List[T]:
    """Convert mhd labels to nifti."""
    # pylint: disable=too-many-locals, import-outside-toplevel
    from redbrick.utils.dicom import convert_mhd_to_nii

    if not task_dir:
        task_dir = os.getcwd()

    for task_idx, task in enumerate(tasks):
        for series_idx, series in enumerate(task.get("series", []) or []):
            if "segmentations" not in series and "segmentations" in task:
                series["segmentations"] = task["segmentations"]  # type: ignore
            if "segmentMap" not in series and "segmentMap" in task:
                series["segmentMap"] = task["segmentMap"]  # type: ignore

            if (
                not series.get("items")
                or not series.get("segmentations")
                or not series.get("segmentMap")
            ):
                logger.info(
                    "Skipping mhd processing for "
                    + f"task->{task_idx}->series->{series_idx}"
                )
                continue

            series_segmentations = series.get("segmentations", [])
            segmentations: List[str] = (
                [series_segmentations]
                if isinstance(series_segmentations, str)
                else series_segmentations
            )

            temp_dir = os.path.join(config_path(), "temp", str(uuid4()))
            os.makedirs(temp_dir, exist_ok=True)

            if label_storage_id == StorageMethod.REDBRICK:
                logger.info(f"Copying segmentations into: {temp_dir}")
                for seg in segmentations:
                    shutil.copy(
                        (
                            seg
                            if os.path.isabs(seg)
                            or not os.path.exists(os.path.join(task_dir, seg))
                            else os.path.abspath(os.path.join(task_dir, seg))
                        ),
                        os.path.join(temp_dir, os.path.basename(seg)),
                    )
            else:
                presigned_segs = context.export.presign_items(
                    org_id, label_storage_id, segmentations
                )
                presigned_segs = [seg for seg in presigned_segs if seg]
                await download_files(
                    list(
                        zip(
                            presigned_segs,
                            [
                                os.path.join(
                                    temp_dir,
                                    str(urlparse(seg).path).rsplit("/", 1).pop(),
                                )
                                for seg in presigned_segs
                            ],
                        )
                    ),
                    f"Downloading segmentations into: {temp_dir}",
                )

            nii_mask = convert_mhd_to_nii(
                [os.path.join(temp_dir, seg) for seg in os.listdir(temp_dir)]
            )

            if not nii_mask:
                shutil.rmtree(temp_dir)
                log_error(
                    "Failed mhd processing for "
                    + f"task->{task_idx}->series->{series_idx}",
                    True,
                )

            assert nii_mask
            series["segmentations"] = nii_mask

        if "segmentations" in task and all(
            "segmentations" in series
            for series in task.get("series", []) or []  # type: ignore
        ):
            del task["segmentations"]  # type: ignore
        if "segmentMap" in task and all(
            "segmentMap" in series
            for series in task.get("series", []) or []  # type: ignore
        ):
            del task["segmentMap"]  # type: ignore

    return tasks


async def process_segmentation_upload(
    context: RBContext,
    session: aiohttp.ClientSession,
    org_id: str,
    project_id: str,
    task: Dict,
    label_storage_id: str,
    project_label_storage_id: str,
    label_validate: bool = False,
    prune_segmentations: bool = False,
) -> Tuple[Optional[str], Sequence[Optional[Dict]]]:
    """Process segmentation upload."""
    # pylint: disable=too-many-branches, too-many-locals, too-many-statements
    # pylint: disable=import-outside-toplevel, too-many-nested-blocks
    from redbrick.utils.dicom import process_upload

    labels_map: List[Dict] = []

    if (
        "labelsMap" not in task
        and task.get("segmentations")
        and len(task["segmentations"]) == len(task["items"])
    ):
        logger.debug("Converting segmentations to labelsMap")
        task["labelsMap"] = [
            {"labelName": segmentation, "seriesIndex": idx}
            for idx, segmentation in enumerate(task["segmentations"])
        ]
        del task["segmentations"]
    elif "labelsMap" not in task and task.get("labelsPath"):
        logger.debug("Converting labelsPath to labelsMap")
        task["labelsMap"] = [{"labelName": task["labelsPath"], "seriesIndex": 0}]
        del task["labelsPath"]

    labels_map = task.get("labelsMap", []) or []  # type: ignore
    download_dir = os.path.join(config_path(), "temp", str(uuid4()))
    os.makedirs(download_dir, exist_ok=True)
    for volume_index, label_map in enumerate(labels_map):
        logger.debug(f"Processing label map: {label_map} for volume {volume_index}")
        if not isinstance(label_map, dict) or not label_map.get("labelName"):
            logger.debug(f"Skipping label map: {label_map} for volume {volume_index}")
            continue

        input_labels_path: Optional[Union[str, List[str]]] = label_map["labelName"]
        path_mapping: Dict[str, str] = {}
        if isinstance(input_labels_path, str) and os.path.isdir(input_labels_path):
            logger.debug("Label path is a directory")
            input_labels_path = [
                os.path.join(input_labels_path, input_file)
                for input_file in os.listdir(input_labels_path)
            ]
            if any(not os.path.isfile(input_path) for input_path in input_labels_path):
                logger.debug("Not all paths are files")
                input_labels_path = None
        elif input_labels_path:
            if isinstance(input_labels_path, str):
                logger.debug("Label path is string")
                input_labels_path = [input_labels_path]

            if not input_labels_path or any(
                not isinstance(input_path, str) for input_path in input_labels_path
            ):
                input_labels_path = None
            else:
                external_paths: List[str] = [
                    input_path
                    for input_path in input_labels_path
                    if not os.path.isfile(input_path)
                ]
                downloaded_paths: Sequence[Optional[str]] = []
                if external_paths:
                    presigned_paths = context.export.presign_items(
                        org_id,
                        label_storage_id,
                        external_paths,
                    )

                    download_paths = [
                        os.path.join(
                            download_dir,
                            str(uuid4())
                            + ".nii"
                            + (".gz" if ".nii.gz" in external_path.lower() else ""),
                        )
                        for external_path in external_paths
                    ]
                    downloaded_paths = await download_files(
                        list(zip(presigned_paths, download_paths)),
                        f"Downloading labels for {task.get('name') or task['items'][0]}",
                        False,
                    )
                    for ext_path, down_path in zip(external_paths, downloaded_paths):
                        if down_path:
                            path_mapping[ext_path] = down_path
                if any(not downloaded_path for downloaded_path in downloaded_paths):
                    input_labels_path = None
                else:
                    input_labels_path = [
                        input_path
                        for input_path in input_labels_path
                        if input_path and os.path.isfile(input_path)
                    ] + [
                        downloaded_path
                        for downloaded_path in downloaded_paths
                        if downloaded_path
                    ]

        if input_labels_path:
            all_series_info = task.get("seriesInfo", []) or []
            series_info = (
                all_series_info[volume_index]
                if len(all_series_info) > volume_index
                else {}
            )
            output_labels_path, instances, labels_error = await process_upload(
                input_labels_path,
                {
                    label["dicom"]["instanceid"]: label["dicom"].get("groupids")
                    for label in (task.get("labels") or [])
                    if (
                        label.get("volumeindex") is None
                        or int(label.get("volumeindex")) == volume_index
                    )
                    and label.get("dicom", {}).get("instanceid")
                },
                series_info.get("binaryMask", False) or False,
                series_info.get("pngMask", False) or False,
                {
                    series_key: path_mapping.get(series_val, series_val) or series_val
                    for series_key, series_val in (
                        series_info.get("masks", {}) or {}
                    ).items()
                },
                label_validate,
                prune_segmentations,
            )

            pos = len(task.get("labels") or []) - 1
            while pos >= 0:
                label = task["labels"][pos]
                if (
                    label.get("volumeindex") is None
                    or int(label.get("volumeindex")) == volume_index
                ) and label.get("dicom", {}).get("instanceid"):
                    if label["dicom"]["instanceid"] in instances:
                        group_ids = set(instances[label["dicom"]["instanceid"]] or [])
                        if group_ids:
                            label["dicom"]["groupids"] = list(group_ids)
                        elif "groupids" in label["dicom"]:
                            del label["dicom"]["groupids"]
                    else:
                        task["labels"].pop(pos)
                pos -= 1

            if (
                output_labels_path
                and not os.path.isfile(output_labels_path)
                and label_storage_id != project_label_storage_id
            ):
                presigned_path = context.export.presign_items(
                    org_id, label_storage_id, [output_labels_path]
                )[0]
                output_labels_path = (
                    await download_files(
                        [
                            (
                                presigned_path,
                                os.path.join(
                                    download_dir,
                                    str(uuid4())
                                    + ".nii"
                                    + (
                                        ".gz"
                                        if ".nii.gz" in (presigned_path or "").lower()
                                        else ""
                                    ),
                                ),
                            )
                        ],
                        f"Downloading labels for {task.get('name') or task['items'][0]}",
                        False,
                    )
                )[0]

            if output_labels_path and os.path.isfile(output_labels_path):
                file_type = NIFTI_FILE_TYPES["nii"]
                _, presigned = await context.labeling.presign_labels_path(
                    session, org_id, project_id, str(uuid4()), str(uuid4()), 0, 1
                )
                if (
                    await upload_files(
                        [
                            (
                                output_labels_path,
                                presigned[0]["presignedUrl"],
                                file_type,
                            )
                        ],
                        "Uploading segmentations for "
                        + f"{task['name'][:57]}{task['name'][57:] and '...'}",
                        True,
                    )
                )[0]:
                    label_map["labelName"] = presigned[0]["filePath"]
            elif output_labels_path:
                label_map["labelName"] = output_labels_path
            else:
                task_name = task.get("name") or task["items"][0]
                if labels_error:
                    raise ValueError(
                        f"Error processing labels for {task_name}: {labels_error}"
                    )

                logger.warning(f"Skipping empty labels for {task_name}")
                label_map["labelName"] = None
        else:
            raise ValueError("Invalid label files")

    labels_data_path: Optional[str] = None

    if len(task.get("labels") or []) > LABELS_ARRAY_LIMIT:
        presigned, _ = await context.labeling.presign_labels_path(
            session, org_id, project_id, str(uuid4()), str(uuid4()), 1, 0
        )
        dirname = os.path.join(config_path(), "temp", str(uuid4()))
        os.makedirs(dirname, exist_ok=True)
        tmp_labels_data = uniquify_path(os.path.join(dirname, "labels.json"))
        with open(tmp_labels_data, "w", encoding="utf-8") as f:
            json.dump(task["labels"], f)

        if (
            await upload_files(
                [
                    (
                        tmp_labels_data,
                        presigned[0]["presignedUrl"],
                        "application/json",
                    )
                ],
                "Uploading labels for "
                + f"{task['name'][:57]}{task['name'][57:] and '...'}",
                True,
                True,
            )
        )[0]:
            os.remove(tmp_labels_data)
            labels_data_path = presigned[0]["filePath"]
            task["labels"] = []
        else:
            raise ValueError("Error uploading labels")

    return labels_data_path, [
        label_map if label_map and label_map.get("labelName") else None
        for label_map in (labels_map or [])
    ]
