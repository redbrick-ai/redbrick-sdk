"""Upload interact."""

import shutil
import asyncio
import os
from copy import deepcopy
from typing import List, Dict, Optional, Set
import json

import aiohttp
import tenacity
from tenacity.stop import stop_after_attempt
import tqdm  # type: ignore

from redbrick.config import config
from redbrick.common.constants import DUMMY_FILE_PATH, MAX_CONCURRENCY
from redbrick.common.context import RBContext
from redbrick.common.storage import StorageMethod
from redbrick.types.task import InputTask
from redbrick.types.taxonomy import Taxonomy
from redbrick.utils.async_utils import gather_with_concurrency, get_session
from redbrick.utils.common_utils import config_path
from redbrick.utils.upload import (
    convert_mhd_to_nii_labels,
    convert_rt_struct_to_nii_labels,
    process_segmentation_upload,
)
from redbrick.utils.logging import assert_validation, log_error, logger
from redbrick.utils.files import get_file_type, upload_files


@tenacity.retry(
    stop=stop_after_attempt(1),
    retry_error_callback=lambda _: {},
)
async def create_task(
    *,
    context: RBContext,
    session: aiohttp.ClientSession,
    org_id: str,
    workspace_id: Optional[str],
    project_id: Optional[str],
    storage_id: str,
    point: Dict,
    is_ground_truth: bool,
    label_storage_id: str,
    project_label_storage_id: str,
    label_validate: bool,
    prune_segmentations: bool,
    update_items: bool,
) -> Dict:
    """Create task interact function."""
    # pylint:disable=too-many-locals
    logger.debug(
        f"org_id={org_id}, workspace_id={workspace_id}, project_id={project_id}, "
        + f"storage={storage_id}, gt={is_ground_truth}, label_storage={label_storage_id}, "
        + f"project_label_storage={project_label_storage_id}, validate={label_validate}"
    )
    if storage_id == StorageMethod.REDBRICK and point.get("items"):
        logger.debug("Uploading files to Redbrick")
        file_types, upload_items, presigned_items = [], [], []
        try:
            for item in point["items"]:
                file_types.append(get_file_type(item)[1])
                upload_items.append(os.path.split(item)[-1])
            for heat_map in point.get("heatMaps") or []:
                file_types.append(get_file_type(heat_map["item"])[1])
                upload_items.append(os.path.split(heat_map["item"])[-1])
            presigned_items = generate_upload_presigned_url(
                context, org_id, workspace_id, project_id, upload_items, file_types
            )
        except Exception:  # pylint:disable=broad-except
            log_error(f"Failed to upload {point['name']}")
            return {
                "name": point["name"],
                "error": f"Failed to upload {point['name']}",
            }

        files = [
            (
                item,
                presigned_items[idx]["presignedUrl"],
                file_types[idx],
            )
            for idx, item in enumerate(point["items"])
        ]
        heatmap_start_idx = len(point["items"])
        heat_maps = [
            (
                heat_map["item"],
                presigned_items[heatmap_start_idx + idx]["presignedUrl"],
                file_types[heatmap_start_idx + idx],
            )
            for idx, heat_map in enumerate(point.get("heatMaps") or [])
        ]

        uploaded_items, uploaded_heatmaps = await asyncio.gather(
            upload_files(
                files,
                f"Uploading items for {point['name'][:57]}{point['name'][57:] and '...'}",
            ),
            upload_files(
                heat_maps,
                f"Uploading heat maps for {point['name'][:57]}{point['name'][57:] and '...'}",
            ),
        )

        if not all(uploaded_items) or not all(uploaded_heatmaps):
            log_error(f"Failed to upload {point['name']}")
            return {
                "name": point["name"],
                "error": f"Failed to upload {point['name']}",
            }

        point["items"] = [
            presigned_items[idx]["filePath"] for idx in range(len(point["items"]))
        ]
        for idx, heat_map in enumerate(point.get("heatMaps") or []):
            heat_map["item"] = presigned_items[heatmap_start_idx + idx]["filePath"]

    try:
        labels_data_path, labels_map = (
            (
                await process_segmentation_upload(
                    context,
                    session,
                    org_id,
                    project_id,
                    point,
                    label_storage_id,
                    project_label_storage_id,
                    label_validate,
                    prune_segmentations,
                )
            )
            if project_id
            else (None, None)
        )
    except ValueError as err:
        logger.warning(
            f"Failed to process segmentations: `{err}` for `{point['name']}`"
        )
        return {}

    try:
        # Basic structural validations, rest handled by API
        assert_validation(
            isinstance(point, dict) and point,
            "Task object must be a non-empty dictionary",
        )
        assert_validation(
            "response" not in point and "error" not in point,
            "Task object must not contain `response` or `error`",
        )
        assert_validation(
            "name" in point and isinstance(point["name"], str) and point["name"],
            "Task object must contain a valid `name`",
        )
        assert_validation(
            (update_items and "items" not in point)
            or (
                "items" in point
                and isinstance(point["items"], list)
                and point["items"]
                and all(
                    map(lambda item: isinstance(item, str) and item, point["items"])
                )
            ),
            "`items` must be a list of urls (one for image and multiple for videoframes)",
        )
        assert_validation(
            "labels" not in point
            or (
                isinstance(point["labels"], list)
                and all(
                    map(
                        lambda label: isinstance(label, dict) and label,
                        point["labels"],
                    )
                )
            ),
            "`labels` must be a list of label objects",
        )

        if update_items:
            response = await context.upload.update_items_async(
                session,
                org_id,
                storage_id,
                point.get("dpId"),
                project_id,
                point.get("taskId"),
                point.get("items"),
                (
                    [
                        {
                            **{
                                series_key: series_val
                                for series_key, series_val in series_info.items()
                                if series_key
                                not in (
                                    "binaryMask",
                                    "semanticMask",
                                    "pngMask",
                                    "masks",
                                )
                            },
                            "metaData": (
                                json.dumps(
                                    series_info["metaData"], separators=(",", ":")
                                )
                                if series_info.get("metaData")
                                else None
                            ),
                            "imageHeaders": (
                                json.dumps(
                                    series_info["imageHeaders"],
                                    separators=(",", ":"),
                                )
                                if series_info.get("imageHeaders")
                                else None
                            ),
                        }
                        for series_info in point["seriesInfo"]
                    ]
                    if point.get("seriesInfo")
                    else None
                ),
                point.get("heatMaps"),
                point.get("transforms"),
                point.get("centerline"),
                point.get("metaData"),
            )
            assert_validation(
                response.get("ok"),
                response.get("message", "Failed to update items"),
            )
        else:
            response = await context.upload.create_datapoint_async(
                session,
                org_id,
                workspace_id,
                project_id,
                storage_id,
                point["name"],
                point["items"],
                point.get("heatMaps"),
                point.get("transforms"),
                point.get("centerline"),
                (
                    json.dumps(point.get("labels") or [], separators=(",", ":"))
                    if "labels" in point
                    else None
                ),
                labels_data_path,
                labels_map,
                (
                    [
                        {
                            **{
                                series_key: series_val
                                for series_key, series_val in series_info.items()
                                if series_key
                                not in (
                                    "binaryMask",
                                    "semanticMask",
                                    "pngMask",
                                    "masks",
                                )
                            },
                            "metaData": (
                                json.dumps(
                                    series_info["metaData"], separators=(",", ":")
                                )
                                if series_info.get("metaData")
                                else None
                            ),
                            "imageHeaders": (
                                json.dumps(
                                    series_info["imageHeaders"],
                                    separators=(",", ":"),
                                )
                                if series_info.get("imageHeaders")
                                else None
                            ),
                        }
                        for series_info in point["seriesInfo"]
                    ]
                    if point.get("seriesInfo")
                    else None
                ),
                point.get("metaData"),
                is_ground_truth,
                point.get("preAssign"),
                point.get("priority"),
                attributes=point.get("attributes"),
            )
            assert_validation(response.get("dpId"), "Failed to create task")

        point_success = deepcopy(point)
        point_success["response"] = response
        return point_success
    except Exception as error:  # pylint:disable=broad-except
        if isinstance(error, AssertionError):
            log_error(error)
        point_error = deepcopy(point)
        point_error["error"] = error
        return point_error


def map_segmentation_category(segmentation_mapping: Dict) -> List[Dict]:
    """Map segmentation category interact function."""
    rb_segmentations = []
    for class_id, cat in segmentation_mapping.items():
        if isinstance(cat, dict):
            category = cat["category"]
            attributes = cat.get("attributes", []) or []
        else:
            category = cat
            attributes = []
        instance_id = int(class_id)
        if isinstance(category, int):
            rb_segmentations.append(
                {
                    "categoryclass": category,
                    "attributes": attributes,
                    "dicom": {"instanceid": instance_id},
                }
            )
        elif isinstance(category, str):
            rb_segmentations.append(
                {
                    "categoryname": [category],
                    "attributes": attributes,
                    "dicom": {"instanceid": instance_id},
                }
            )
        elif (
            isinstance(category, list)
            and len(category) == 1
            and isinstance(category[0], list)
            and category[0]
            and all(isinstance(item, str) for item in category[0])
        ):
            rb_segmentations.append(
                {
                    "category": category,
                    "attributes": attributes,
                    "dicom": {"instanceid": instance_id},
                }
            )
        elif (
            isinstance(category, list)
            and category
            and all(isinstance(item, str) for item in category)
        ):
            rb_segmentations.append(
                {
                    "categoryname": category,
                    "attributes": attributes,
                    "dicom": {"instanceid": instance_id},
                }
            )
        else:
            raise ValueError(f"Upload failed: Invalid category {category}")

    return rb_segmentations


async def create_tasks(
    *,
    context: RBContext,
    org_id: str,
    workspace_id: Optional[str],
    project_id: Optional[str],
    points: List[Dict],
    segmentation_mapping: Dict,
    is_ground_truth: bool,
    storage_id: str,
    label_storage_id: str,
    label_validate: bool = False,
    prune_segmentations: bool = False,
    concurrency: int = 50,
    update_items: bool = False,
) -> List[Dict]:
    """Create tasks interact function."""
    # pylint: disable=too-many-locals
    try:
        global_segmentations = map_segmentation_category(segmentation_mapping)
        for point in points:
            local_segmentations: List[Dict] = []
            if point.get("segmentMap"):
                local_segmentations = map_segmentation_category(point["segmentMap"])
            if local_segmentations or global_segmentations:
                labels = point.get("labels", [])
                for label in labels:
                    if label.get("dicom", {}).get("instanceid"):
                        log_error(
                            "Cannot have dicom segmentations in `labels` "
                            + f" when segmentMap is given: {point}"
                        )
                        return points
                point["labels"] = labels + (
                    local_segmentations if local_segmentations else global_segmentations
                )
    except ValueError as err:
        log_error(err)
        return points

    project_label_storage_id, _ = (
        context.project.get_label_storage(org_id, project_id)
        if project_id
        else (None, None)
    )

    async with get_session() as session:
        coros = [
            create_task(
                context=context,
                session=session,
                org_id=org_id,
                workspace_id=workspace_id,
                project_id=project_id,
                storage_id=storage_id,
                point=point,
                is_ground_truth=is_ground_truth,
                label_storage_id=label_storage_id,
                project_label_storage_id=project_label_storage_id or label_storage_id,
                label_validate=label_validate,
                prune_segmentations=prune_segmentations,
                update_items=update_items,
            )
            for point in points
        ]
        tasks = await gather_with_concurrency(
            min(concurrency, 10),
            *coros,
            progress_bar_name=("Updating items" if update_items else "Creating tasks"),
            keep_progress_bar=True,
        )

    temp_dir = os.path.join(config_path(), "temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    for point, task in zip(points, tasks):  # type: ignore
        if not task:
            if update_items:
                log_error(f"Error updating items for {point}")
            else:
                log_error(f"Error uploading {point}")

    return tasks


def generate_upload_presigned_url(
    context: RBContext,
    org_id: str,
    workspace_id: Optional[str],
    project_id: Optional[str],
    files: List[str],
    file_type: List[str],
) -> List[Dict]:
    """
    Generate presigned url's to perform upload.

    Parameters:
    -------------
    files: List[str]
        This needs to be names of the files when it's uploaded.
        i.e. locally, the file can be image.png, but after
        uploading if you want it named image001.png, the files
        List must contain [image001.png].

    file_type: List[str]
        Corresponding file types.

    Returns
    ------------
    List[Dict]
        >>> [
            {
                "presignedUrl: "...", # url to upload to
                "filePath": "..." # remote file path
                "fileName": "..." # the same as values in files
            }
        ]
    """
    dataset = workspace_id or project_id
    try:
        assert dataset, "Please specify either a workspace or a project"
        result = context.upload.items_upload_presign(org_id, dataset, files, file_type)
    except ValueError as error:
        log_error(error)
        raise error
    return result


def prepare_json_files(
    *,
    context: RBContext,
    org_id: str,
    taxonomy: Optional[Taxonomy],
    files_data: List[List[InputTask]],
    storage_id: str,
    label_storage_id: str,
    task_segment_map: Optional[Dict] = None,
    task_dirs: Optional[List[str]] = None,
    uploaded: Optional[Set[str]] = None,
    rt_struct: bool = False,
    mhd_mask: bool = False,
    label_validate: bool = False,
    concurrency: int = 50,
) -> List[Dict]:
    """Prepare items from json files for upload."""
    # pylint: disable=too-many-locals, too-many-branches
    # pylint: disable=too-many-statements, import-outside-toplevel
    logger.debug(f"Preparing {len(files_data)} files for upload")
    points: List[Dict] = []
    uploading = set()
    logger.info("Validating files")
    if not task_dirs:
        cur_dir = os.getcwd()
        task_dirs = [cur_dir] * len(files_data)
    for file_data, task_dir in tqdm.tqdm(  # pylint: disable=too-many-nested-blocks
        zip(files_data, task_dirs), leave=config.log_info
    ):
        if not file_data:
            continue
        if not isinstance(file_data, list) or any(
            not isinstance(obj, dict) for obj in file_data
        ):
            logger.warning("Invalid items list")
            continue

        for item in file_data:
            if (
                item.get("items")
                and isinstance(item.get("segmentations"), list)
                and len(item.get("segmentations", [])) > 1
            ):
                logger.warning(
                    "Items list contains multiple segmentations."
                    + " Please use new import format: "
                    + "https://sdk.redbrickai.com/formats/index.html#import"
                )
                continue

        if task_segment_map:
            for item in file_data:
                item["segmentMap"] = item.get("segmentMap", task_segment_map)  # type: ignore

        if rt_struct and taxonomy:
            converted = asyncio.run(
                gather_with_concurrency(
                    concurrency,
                    *[
                        convert_rt_struct_to_nii_labels(
                            context,
                            org_id,
                            taxonomy,
                            [fdata],
                            storage_id,
                            label_storage_id,
                            label_validate,
                            task_dir,
                        )
                        for fdata in file_data
                    ],
                    progress_bar_name="Converting RTSTRUCT files to NIfTI",
                )
            )
            file_data = [items[0] for items in converted]

        if mhd_mask:
            converted = asyncio.run(
                gather_with_concurrency(
                    concurrency,
                    *[
                        convert_mhd_to_nii_labels(
                            context,
                            org_id,
                            [fdata],
                            label_storage_id,
                            task_dir,
                        )
                        for fdata in file_data
                    ],
                    progress_bar_name="Converting MHD files to NIfTI",
                )
            )
            file_data = [items[0] for items in converted]

        file_data = asyncio.run(
            validate_json(context, file_data, storage_id, concurrency)
        )
        if not file_data:
            continue

        if storage_id == str(StorageMethod.REDBRICK):
            logger.info("Looking in your local file system for items")
        for item in file_data:
            if (
                not isinstance(item.get("items"), list)
                or not item["items"]
                or not all(isinstance(i, str) for i in item["items"])
            ):
                logger.warning(f"Invalid {item}")
                continue

            if "name" not in item:
                item["name"] = item["items"][0]
            if (uploaded and item["name"] in uploaded) or item["name"] in uploading:
                logger.info(f"Skipping duplicate item name: {item['name']}")
                continue

            if "segmentations" in item:
                if isinstance(item["segmentations"], list):
                    item["segmentations"] = {
                        str(idx): segmentation
                        for idx, segmentation in enumerate(item["segmentations"])
                    }
                if "labelsMap" not in item and isinstance(item["segmentations"], dict):
                    item["labelsMap"] = [
                        (
                            {"labelName": segmentation, "seriesIndex": int(idx)}
                            if segmentation
                            else None
                        )
                        for idx, segmentation in item["segmentations"].items()
                    ]
                del item["segmentations"]
            elif "labelsPath" in item:
                if "labelsMap" not in item:
                    item["labelsMap"] = [
                        {
                            "labelName": item["labelsPath"],
                            "seriesIndex": 0,
                        }
                    ]
                del item["labelsPath"]

            for label_map in item.get("labelsMap", []) or []:
                if not isinstance(label_map, dict) or not label_map.get("labelName"):
                    continue
                if not isinstance(label_map["labelName"], list):
                    label_map["labelName"] = [label_map["labelName"]]
                label_map["labelName"] = [
                    (
                        label_name
                        if os.path.isabs(label_name)
                        or not os.path.exists(os.path.join(task_dir, label_name))
                        else os.path.abspath(os.path.join(task_dir, label_name))
                    )
                    for label_name in label_map["labelName"]
                ]
                if len(label_map["labelName"]) == 1:
                    label_map["labelName"] = label_map["labelName"][0]

            for series_info in item.get("seriesInfo", []) or []:
                for instance_id, mask in (series_info.get("masks", {}) or {}).items():
                    series_info["masks"][instance_id] = (
                        mask
                        if not isinstance(mask, str)
                        or os.path.isabs(mask)
                        or not os.path.exists(os.path.join(task_dir, mask))
                        else os.path.abspath(os.path.join(task_dir, mask))
                    )

            if storage_id != str(StorageMethod.REDBRICK):
                uploading.add(item["name"])
                points.append(item)
                continue

            for idx, path in enumerate(item["items"]):
                item_path = (
                    path if os.path.isabs(path) else os.path.join(task_dir, path)
                )
                if os.path.isfile(item_path):
                    item["items"][idx] = item_path
                else:
                    if path != DUMMY_FILE_PATH:
                        logger.warning(
                            f"Could not find {path}. "
                            + "Perhaps you forgot to supply the --storage argument"
                        )
                    break

            for idx, heat_map in enumerate(item.get("heatMaps") or []):
                heat_map_path = (
                    heat_map["item"]
                    if os.path.isabs(heat_map["item"])
                    else os.path.join(task_dir, heat_map["item"])
                )
                if os.path.isfile(heat_map_path):
                    item["heatMaps"][idx]["item"] = heat_map_path
                else:
                    logger.warning(
                        f"Could not find {heat_map['item']}. "
                        + "Perhaps you forgot to supply the --storage argument"
                    )
                    break

            else:
                uploading.add(item["name"])
                points.append(item)

    return points


def upload_datapoints(
    *,
    context: RBContext,
    org_id: str,
    workspace_id: Optional[str],
    project_id: Optional[str],
    taxonomy: Optional[Taxonomy],
    storage_id: str,
    points: List[InputTask],
    is_ground_truth: bool = False,
    segmentation_mapping: Optional[Dict] = None,
    rt_struct: bool = False,
    mhd: bool = False,
    label_storage_id: Optional[str] = None,
    label_validate: bool = False,
    prune_segmentations: bool = False,
    concurrency: int = 50,
) -> List[Dict]:
    """Prepare items from json files for upload."""
    # pylint: disable=too-many-locals
    converted_points = prepare_json_files(
        context=context,
        org_id=org_id,
        taxonomy=taxonomy,
        files_data=[points],
        storage_id=storage_id,
        label_storage_id=label_storage_id or storage_id,
        task_segment_map=segmentation_mapping,
        rt_struct=rt_struct,
        mhd_mask=mhd,
        label_validate=label_validate,
        concurrency=concurrency,
    )
    return asyncio.run(
        create_tasks(
            context=context,
            org_id=org_id,
            workspace_id=workspace_id,
            project_id=project_id,
            points=converted_points,
            segmentation_mapping={},
            is_ground_truth=is_ground_truth,
            storage_id=storage_id,
            label_storage_id=label_storage_id or storage_id,
            label_validate=label_validate,
            prune_segmentations=prune_segmentations,
            concurrency=concurrency,
        )
    )


async def validate_json(
    context: RBContext,
    input_data: List[InputTask],
    storage_id: str,
    concurrency: int,
) -> List[Dict]:
    """Validate and convert to import format."""
    # pylint: disable=too-many-locals
    total_input_data = len(input_data)
    logger.debug(f"Concurrency: {concurrency} for {total_input_data} items")
    inputs: List[List[InputTask]] = []
    for batch in range(0, total_input_data, concurrency):
        inputs.append(input_data[batch : batch + concurrency])

    async with get_session() as session:
        coros = []
        for data in inputs:
            # temp handler for missing properties
            temp_data = deepcopy(data)
            for task in temp_data:
                if "status" in task:
                    del task["status"]  # type: ignore

            coros.append(
                context.upload.validate_and_convert_to_import_format(
                    session, temp_data, True, storage_id
                )
            )
        outputs = await gather_with_concurrency(MAX_CONCURRENCY, *coros)

    output_data: List[Dict] = []
    for idx, (inp, out) in enumerate(zip(inputs, outputs)):
        if not out.get("isValid"):
            start = idx * concurrency
            logger.debug(f"Error for batch: {idx}")
            logger.warning(
                f"Batch: {start}-{start + len(inp)} of {total_input_data}\n"
                + out.get(
                    "error",
                    "Error: Invalid format\nDocs: "
                    + "https://sdk.redbrickai.com/formats/index.html#import",
                )
            )
            return []

        output_data.extend(
            json.loads(out["converted"]) if out.get("converted") else inp  # type: ignore
        )

    return output_data
