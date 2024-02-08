"""Public API to exporting."""

import asyncio
import re
import shutil
from typing import Iterator, List, Dict, Optional, Set, Tuple, Any
from functools import partial
import os
import json
import copy
from datetime import datetime, timezone

import tqdm  # type: ignore

from redbrick.common.context import RBContext
from redbrick.common.enums import ReviewStates, TaskFilters, TaskStates
from redbrick.common.export import TaskFilterParams
from redbrick.stage import LabelStage, ReviewStage
from redbrick.utils.files import (
    DICOM_FILE_TYPES,
    IMAGE_FILE_TYPES,
    NIFTI_FILE_TYPES,
    VIDEO_FILE_TYPES,
    download_files,
    uniquify_path,
)
from redbrick.utils.logging import log_error, logger
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_label_utils import (
    dicom_rb_format,
    parse_entry_latest,
    user_format,
    assignee_format,
)
from redbrick.utils.rb_event_utils import task_event_format
from redbrick.types.task import OutputTask as TypeTask, Series as TypeTaskSeries


# pylint: disable=too-many-lines


class Export:
    """Primary interface for various export methods."""

    def __init__(
        self,
        context: RBContext,
        org_id: str,
        project_id: str,
        output_stage_name: str,
        consensus_enabled: bool,
        label_stages: List[LabelStage],
        review_stages: List[ReviewStage],
        taxonomy_name: str,
    ) -> None:
        """Construct Export object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.output_stage_name = output_stage_name
        self.consensus_enabled = consensus_enabled
        self.label_stages = label_stages
        self.review_stages = review_stages
        self.taxonomy_name = taxonomy_name

    def _get_raw_data_latest(
        self,
        concurrency: int,
        stage_name: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        presign_items: bool = False,
        with_consensus: bool = False,
        task_id: Optional[str] = None,
    ) -> Iterator[Dict]:
        # pylint: disable=too-many-locals
        if task_id:
            logger.info(f"Fetching task: {task_id}")
            val = self.context.export.get_datapoint_latest(
                self.org_id, self.project_id, task_id, presign_items, with_consensus
            )
            task = parse_entry_latest(val)
            yield task
            return

        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.get_datapoints_latest,
                self.org_id,
                self.project_id,
                stage_name,
                (
                    datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
                    if from_timestamp is not None
                    else None
                ),
                presign_items,
                with_consensus,
            ),
            concurrency,
        )

        logger.info(
            "Downloading tasks"
            + (
                f" updated since {datetime.fromtimestamp(from_timestamp)}"
                if from_timestamp is not None
                else ""
            )
        )

        for val in my_iter:
            task = parse_entry_latest(val)
            if task:
                yield task

    @staticmethod
    def _get_color(class_id: int, color_hex: Optional[str] = None) -> Any:
        """Get a color from class id."""
        if color_hex:
            color_hex = color_hex.lstrip("#")
            return [int(color_hex[i : i + 2], 16) for i in (0, 2, 4)]
        num = (374761397 + int(class_id) * 3266489917) & 0xFFFFFFFF
        num = ((num ^ num >> 15) * 2246822519) & 0xFFFFFFFF
        num = ((num ^ num >> 13) * 3266489917) & 0xFFFFFFFF
        num = (num ^ num >> 16) >> 8
        return list(num.to_bytes(3, "big"))

    @staticmethod
    def tax_class_id_mapping(
        parent: List,
        children: Dict,
        class_id: Dict,
        color_map: Dict,
        taxonomy_color: Optional[List] = None,
    ) -> None:
        """Create a class mapping from taxonomy categories to class_id."""
        for category in children:
            trail = parent + [category["name"]]
            key = "::".join(trail[1:])
            class_id[key] = category["classId"] + 1
            color_map[key] = Export._get_color(
                category["classId"],
                (
                    next(
                        (
                            color.get("color")
                            for color in (taxonomy_color or [])
                            if not color.get("taskcategory")
                            and color.get("trail", []) == trail
                        ),
                        None,
                    )
                    if taxonomy_color
                    else None
                ),
            )
            Export.tax_class_id_mapping(
                trail, category["children"], class_id, color_map, taxonomy_color
            )

    @staticmethod
    def _get_task_series(task: TypeTask) -> List[TypeTaskSeries]:
        return (
            (  # type: ignore
                task.get("series")
                or (task.get("superTruth", {}) or {}).get("series")
                or (task.get("consensusTasks", []) or [])[0].get("series")
            )
            if (
                task.get("series")
                or task.get("superTruth")
                or task.get("consensusTasks")
            )
            else []
        )

    async def _download_task(
        self,
        original_task: TypeTask,
        storage_id: str,
        taxonomy: Dict,
        image_dir: str,
        dcm_to_nii: bool,
        rt_struct: bool,
        semantic_mask: bool,
    ) -> TypeTask:
        # pylint: disable=too-many-locals, import-outside-toplevel, too-many-nested-blocks
        task, series_dirs = await self._download_task_items(
            original_task, storage_id, image_dir, taxonomy, rt_struct, semantic_mask
        )

        if not dcm_to_nii:
            return task

        import numpy as np  # type: ignore
        import nibabel as nb  # type: ignore
        from dicom2nifti import settings, dicom_series_to_nifti  # type: ignore

        settings.disable_validate_slice_increment()

        logger.info("Converting DICOM image volumes to NIfTI")

        dcm_ext = re.compile(
            r"\.("
            + "|".join(
                (
                    IMAGE_FILE_TYPES.keys()
                    | VIDEO_FILE_TYPES.keys()
                    | NIFTI_FILE_TYPES.keys()
                )
                - DICOM_FILE_TYPES.keys()
            )
            + r")(\.gz)?$"
        )

        task_series = Export._get_task_series(task)
        if not task_series or len(task_series) != len(series_dirs):
            return task

        for series, series_dir in zip(task_series, series_dirs):
            series_items = series.get("items") or []
            items = [series_items] if isinstance(series_items, str) else series_items
            if (
                dcm_to_nii
                and len(items) > 1
                and not any(
                    re.search(dcm_ext, item.split("?", 1)[0].rstrip("/"))
                    for item in items
                )
            ):
                logger.info(f"Converting {task['taskId']} image to nifti")
                try:
                    nii_img = dicom_series_to_nifti(
                        series_dir, uniquify_path(series_dir + ".nii.gz")
                    )
                except Exception as err:  # pylint: disable=broad-except
                    logger.warning(
                        f"Task {task['taskId']} : Failed to convert {series_dir} - {err}"
                    )
                    return task

                series["items"] = nii_img["NII_FILE"]
                if series.get("segmentations"):
                    logger.debug(f"{task['taskId']} matching headers")
                    try:
                        nii_seg = nb.load(  # type: ignore
                            os.path.abspath(
                                series["segmentations"]
                                if isinstance(series["segmentations"], str)
                                else series["segmentations"][0]
                            )
                        )
                        imgh = nii_img["NII"].header
                        segh = nii_seg.header
                        if not (
                            imgh.get_data_shape() == segh.get_data_shape()  # type: ignore
                            and imgh.get_data_offset() == segh.get_data_offset()  # type: ignore
                            and np.array_equal(
                                imgh.get_best_affine(), segh.get_best_affine()  # type: ignore
                            )
                            and np.array_equal(
                                imgh.get_qform(), segh.get_qform()  # type: ignore
                            )
                            and np.array_equal(
                                imgh.get_sform(), segh.get_sform()  # type: ignore
                            )
                        ):
                            logger.warning(
                                f"Task: {task['taskId']} : Headers of converted "
                                + "nifti image and segmentation do not match."
                            )
                    except Exception as err:  # pylint: disable=broad-except
                        logger.warning(
                            f"Task {task['taskId']} : Failed to match headers - {err}"
                        )

        return task

    async def _download_task_items(
        self,
        task: TypeTask,
        storage_id: str,
        parent_dir: str,
        taxonomy: Dict,
        rt_struct: bool,
        semantic_mask: bool,
    ) -> Tuple[TypeTask, List[str]]:
        # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        path_pattern = re.compile(r"[^\w.]+")
        task_name = re.sub(path_pattern, "-", task.get("name", "")) or task.get(
            "taskId", ""
        )
        task_dir = os.path.join(parent_dir, task_name)

        if os.path.exists(task_dir) and not os.path.isdir(task_dir):
            os.remove(task_dir)

        os.makedirs(task_dir, exist_ok=True)

        series_dirs: List[str] = []
        items_lists: List[List[str]] = []

        try:  # pylint: disable=too-many-nested-blocks
            task_series = Export._get_task_series(task)
            if task_series:
                for series_idx, series in enumerate(task_series):
                    series_dir = os.path.join(
                        task_dir,
                        re.sub(path_pattern, "-", series.get("name", "") or "")
                        or (
                            task_name
                            if len(task_series) == 1
                            else chr(series_idx + ord("A"))
                        ),
                    )

                    if os.path.exists(series_dir) and not os.path.isdir(series_dir):
                        os.remove(series_dir)

                    os.makedirs(series_dir, exist_ok=True)
                    series_dirs.append(series_dir)
                    items_lists.append(
                        [series["items"]]
                        if isinstance(series["items"], str)
                        else series["items"]
                    )
            else:
                series_dir = os.path.join(task_dir, task_name)
                os.makedirs(series_dir, exist_ok=True)
                series_dirs.append(series_dir)
                items_lists.append(task.get("items", []) or [])  # type: ignore

            to_presign = []
            local_files = []
            for series_dir, paths in zip(series_dirs, items_lists):
                file_names = [
                    re.sub(
                        path_pattern,
                        "-",
                        os.path.basename(path.split("?", 1)[0].rstrip("/")),
                    )
                    for path in paths
                ]
                fill_index = (
                    0
                    if all(file_names) and len(file_names) == len(set(file_names))
                    else len(str(len(file_names)))
                )
                to_presign.extend(paths)
                for index, item in enumerate(file_names):
                    file_name, file_ext = os.path.splitext(item)
                    local_files.append(
                        os.path.join(
                            series_dir,
                            file_name
                            + (
                                ("-" + str(index).zfill(fill_index))
                                if fill_index
                                else ""
                            )
                            + file_ext,
                        )
                    )

            presigned = self.context.export.presign_items(
                self.org_id, storage_id, to_presign
            )

            if any(not presigned_path for presigned_path in presigned):
                raise Exception("Failed to presign some files")

            downloaded = await download_files(
                list(zip(presigned, local_files)),
                "Downloading files",
                False,
                verify_ssl=self.context.config.verify_ssl,
            )

            if any(not downloaded_file for downloaded_file in downloaded):
                raise Exception("Failed to download some files")

            if task_series:
                series_items: List[List[Optional[str]]] = []
                prev_count = 0
                for series_dir, series in zip(series_dirs, task_series):
                    count = (
                        1 if isinstance(series["items"], str) else len(series["items"])
                    )
                    series_items.append(downloaded[prev_count : prev_count + count])
                    prev_count += count

                for idx, series in enumerate(task.get("series", []) or []):
                    series["items"] = series_items[idx]  # type: ignore
                for idx, series in enumerate(
                    (task.get("superTruth", {}) or {}).get("series", []) or []
                ):
                    series["items"] = series_items[idx]  # type: ignore
                for sub_task in task.get("consensusTasks", []) or []:
                    for idx, series in enumerate(sub_task.get("series", []) or []):
                        series["items"] = series_items[idx]  # type: ignore

                if taxonomy.get("isNew") and rt_struct:
                    # pylint: disable=import-outside-toplevel
                    from redbrick.utils.dicom import convert_nii_to_rtstruct

                    for idx, (series_dir, series) in enumerate(
                        zip(series_dirs, task_series)
                    ):
                        if len(series.get("items", []) or []) <= 1:
                            continue
                        segmentations = series.get("segmentations")
                        if not (
                            (isinstance(segmentations, str) and segmentations)
                            or (
                                isinstance(segmentations, list)
                                and all(
                                    isinstance(segmentation, str) and segmentation
                                    for segmentation in segmentations
                                )
                            )
                        ):
                            continue

                        if isinstance(segmentations, str):
                            segmentations = [segmentations]

                        rtstruct, new_segment_map = await convert_nii_to_rtstruct(
                            segmentations,
                            series_dir,
                            taxonomy.get("objectTypes", []) or [],
                            series.get("segmentMap", {}) or {},
                            semantic_mask,
                        )

                        if not rtstruct:
                            continue

                        name, ext = os.path.splitext(
                            segmentations[0]
                            if len(segmentations) == 1
                            else os.path.dirname(segmentations[0])
                        )
                        if ext == ".gz":
                            name, ext = os.path.splitext(name)

                        series["segmentations"] = name + ".dcm"
                        series["segmentMap"] = new_segment_map
                        for roi_name in series["segmentMap"].keys():
                            if "mask" in series["segmentMap"][roi_name]:  # type: ignore
                                del series["segmentMap"][roi_name]["mask"]  # type: ignore
                        rtstruct.save(series["segmentations"])

            else:
                task["items"] = downloaded  # type: ignore

        except Exception as err:  # pylint: disable=broad-except
            log_error(
                f"Error for task {task.get('taskId', '')}: {err}"
                + "\n Please try using a lower --concurrency"
            )
            shutil.rmtree(task_dir, ignore_errors=True)

        return task, series_dirs

    async def process_labels(
        self,
        datapoint: Dict,
        segmentation_dir: Optional[str],
        color_map: Dict,
        semantic_mask: bool,
        binary_mask: Optional[bool],
        old_format: bool,
        no_consensus: bool,
        png_mask: bool,
        taxonomy: Dict,
    ) -> TypeTask:
        """Process labels."""
        # pylint: disable=too-many-locals
        task = copy.deepcopy(datapoint)
        files: List[Tuple[Optional[str], Optional[str]]] = []
        labels_map: List[Optional[Dict]] = []

        series_info: List[Dict] = task.get("seriesInfo", []) or []
        has_series_info = sum(
            list(
                map(
                    lambda val: (
                        len(val["itemsIndices"])
                        if isinstance(val, dict)
                        and len(val.get("itemsIndices", []) or [])
                        else -1000000
                    ),
                    series_info,
                )
            )
        ) == len(task["items"])

        image_index_map: Dict[int, int] = {}
        if has_series_info:
            for volume_index, series in enumerate(series_info):
                image_index_map.update(
                    {
                        image_index: volume_index
                        for image_index in series["itemsIndices"]
                    }
                )
            labels_map = [None] * len(series_info)
            for idx, label_map in enumerate(task.get("labelsMap", []) or []):
                if label_map and "seriesIndex" in label_map:
                    index = label_map["seriesIndex"]
                elif label_map and "imageIndex" in label_map:
                    index = image_index_map[label_map["imageIndex"]]
                else:
                    index = idx
                labels_map[index] = label_map

        else:
            labels_map = task.get("labelsMap", []) or []

        presign_paths: List[Optional[str]] = [
            label_map.get("labelName") if label_map else None
            for label_map in labels_map
        ]

        if task.get("consensusTasks"):
            for consensus_task in task["consensusTasks"]:
                presign_paths.extend(
                    [
                        (
                            consensus_label_map.get("labelName")
                            if consensus_label_map
                            and consensus_task.get("labelStorageId")
                            == task["labelStorageId"]
                            else None
                        )
                        for consensus_label_map in (
                            consensus_task.get("labelsMap", []) or []
                        )
                    ]
                )

        if any(presign_path for presign_path in presign_paths):
            await self.download_and_process_segmentations(
                task,
                presign_paths,
                files,
                segmentation_dir,
                has_series_info,
                series_info,
                labels_map,
                image_index_map,
                color_map,
                semantic_mask,
                binary_mask,
                png_mask,
                taxonomy,
            )

        return dicom_rb_format(
            task, taxonomy, old_format, no_consensus, self.review_stages
        )

    async def download_and_process_segmentations(
        self,
        task: Dict,
        presign_paths: List[Optional[str]],
        files: List[Tuple[Optional[str], Optional[str]]],
        segmentation_dir: Optional[str],
        has_series_info: bool,
        series_info: List[Dict],
        labels_map: List[Optional[Dict]],
        image_index_map: Dict[int, int],
        color_map: Dict,
        semantic_mask: bool,
        binary_mask: Optional[bool],
        png_mask: bool,
        taxonomy: Dict,
    ) -> None:
        """Download and process segmentations."""
        # pylint: disable=import-outside-toplevel, too-many-locals
        # pylint: disable=too-many-branches, too-many-statements
        from redbrick.utils.dicom import process_nifti_download

        presigned = self.context.export.presign_items(
            self.org_id, task["labelStorageId"], presign_paths
        )

        path_pattern = re.compile(r"[^\w.]+")
        task_name: str = (
            re.sub(path_pattern, "-", task.get("name", "")) or task["taskId"]
        )
        if segmentation_dir:
            task_dir = os.path.join(segmentation_dir, task_name)
            shutil.rmtree(task_dir, ignore_errors=True)
            os.makedirs(task_dir, exist_ok=True)
        else:
            task_dir = task_name
        series_names: List[str] = []

        if has_series_info and (len(series_info) > 1 or series_info[0].get("name")):
            for series_idx, series in enumerate(series_info):
                series_name = os.path.join(
                    task_dir,
                    re.sub(path_pattern, "-", series.get("name", "") or "")
                    or chr(series_idx + ord("A")),
                )
                series_names.append(series_name)
        else:
            total_volumes = len(labels_map) or 1
            if total_volumes == 1:
                series_names = [os.path.join(task_dir, task_name)]
            else:
                series_names = [
                    os.path.join(task_dir, chr(series_idx + ord("A")))
                    for series_idx in range(total_volumes)
                ]

        if len(presigned) > len(series_names):
            series_names *= (len(presigned) // len(series_names)) + 1

        added: Set[str] = set()
        for url, series_name in zip(presigned, series_names):
            counter = 1
            new_series_name = series_name
            while new_series_name in added:
                new_series_name = f"{series_name}_{counter}"
                counter += 1
            added.add(new_series_name)
            files.append((url, f"{new_series_name}.nii.gz"))

        paths: List[Optional[str]]
        if segmentation_dir:
            paths = await download_files(
                files,
                "Downloading segmentations",
                False,
                True,
                True,
                verify_ssl=self.context.config.verify_ssl,
            )
        else:
            paths = list(list(zip(*files))[0])

        for label, path in zip(labels_map, paths):  # type: ignore
            if label and label.get("labelName"):
                label_map_data = await process_nifti_download(
                    task.get("labels", []) or [],
                    path,
                    png_mask,
                    color_map,
                    semantic_mask,
                    binary_mask,
                    taxonomy,
                    label.get(
                        "seriesIndex", image_index_map.get(label.get("imageIndex", -1))
                    ),
                )
                label["labelName"] = label_map_data["masks"]
                label["binaryMask"] = label_map_data["binary_mask"]
                label["semanticMask"] = label_map_data["semantic_mask"]
                label["pngMask"] = label_map_data["png_mask"]

        if len(paths) > len(labels_map) and task.get("consensusTasks"):
            index = len(labels_map)
            for consensus_task in task["consensusTasks"]:
                consensus_labels = consensus_task.get("labels", []) or []
                consensus_labels_map = consensus_task.get("labelsMap", []) or []
                for consensus_label_map in consensus_labels_map:
                    label_map_data = await process_nifti_download(
                        consensus_labels,
                        paths[index],
                        png_mask,
                        color_map,
                        semantic_mask,
                        binary_mask,
                        taxonomy,
                        consensus_label_map.get(
                            "seriesIndex",
                            image_index_map.get(consensus_label_map.get("imageIndex")),
                        ),
                    )
                    consensus_label_map["labelName"] = label_map_data["masks"]
                    consensus_label_map["binaryMask"] = label_map_data["binary_mask"]
                    consensus_label_map["semanticMask"] = label_map_data[
                        "semantic_mask"
                    ]
                    consensus_label_map["pngMask"] = label_map_data["png_mask"]
                    index += 1

    def preprocess_export(
        self, taxonomy: Dict, get_color_map: bool
    ) -> Tuple[Dict, Dict]:
        """Get classMap and colorMap."""
        class_map: Dict = {}
        color_map: Dict = {}
        if get_color_map:
            if bool(taxonomy.get("isNew")):
                object_types = taxonomy.get("objectTypes", []) or []
                for object_type in object_types:
                    if object_type["labelType"] == "SEGMENTATION":
                        color = Export._get_color(0, object_type["color"])
                        color_map[object_type["classId"]] = color

                        category: str = object_type["category"]
                        if category in class_map:  # rare case
                            category += f' ({object_type["classId"]})'
                        class_map[category] = color
            else:
                Export.tax_class_id_mapping(
                    [taxonomy["categories"][0]["name"]],  # object
                    taxonomy["categories"][0]["children"],  # categories
                    {},
                    color_map,
                    taxonomy.get("colorMap"),
                )
                class_map = color_map

        return class_map, color_map

    async def export_nifti_label_data(
        self,
        datapoint: Dict,
        taxonomy: Dict,
        task_file: Optional[str],
        image_dir: Optional[str],
        segmentation_dir: Optional[str],
        semantic_mask: bool,
        binary_mask: Optional[bool],
        old_format: bool,
        no_consensus: bool,
        color_map: Dict,
        dicom_to_nifti: bool,
        png_mask: bool,
        rt_struct: bool,
        get_task: bool,
    ) -> Optional[TypeTask]:
        """Export nifti label maps."""
        # pylint: disable=too-many-locals
        task = await self.process_labels(
            datapoint,
            segmentation_dir,
            color_map,
            semantic_mask,
            binary_mask,
            old_format,
            no_consensus,
            png_mask,
            taxonomy,
        )
        if image_dir:
            try:
                task = await self._download_task(
                    task,
                    datapoint["storageId"],
                    taxonomy,
                    image_dir,
                    dicom_to_nifti,
                    rt_struct,
                    semantic_mask,
                )
            except Exception as err:  # pylint: disable=broad-except
                log_error(f"Failed to download files: {err}")

        if not task_file:
            return task if get_task else None

        if os.path.isfile(task_file):
            with open(task_file, "rb+") as task_file_:
                task_file_.seek(-1, 2)
                task_file_.write(
                    b"," + json.dumps(task, indent=2).encode("utf-8") + b"]"
                )
        else:
            with open(task_file, "wb") as task_file_:
                task_file_.write(
                    b"[" + json.dumps(task, indent=2).encode("utf-8") + b"]"
                )

        return task if get_task else None

    def export_tasks(
        self,
        *,
        concurrency: int = 10,
        only_ground_truth: bool = False,
        stage_name: Optional[str] = None,
        task_id: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        old_format: bool = False,
        without_masks: bool = False,
        without_json: bool = False,
        semantic_mask: bool = False,
        binary_mask: Optional[bool] = None,
        no_consensus: Optional[bool] = None,
        with_files: bool = False,
        dicom_to_nifti: bool = False,
        png: bool = False,
        rt_struct: bool = False,
        destination: Optional[str] = None,
    ) -> Iterator[TypeTask]:
        """Export annotation data.

        Meta-data and category information returned as an Object. Segmentations are written to
        your disk in NIfTI-1 format. Please `visit our
        documentation <https://docs.redbrickai.com/python-sdk/format-reference>`_
        for more information on the format.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> project.export.export_tasks()

        Parameters
        -----------
        concurrency: int = 10

        only_ground_truth: bool = False
            If set to True, will only return data that has
            been completed in your workflow. If False, will
            export latest state.

        stage_name: Optional[str] = None
            If set, will only export tasks that are currently
            in the given stage.

        task_id: Optional[str] = None
            If the unique task_id is mentioned, only a single
            datapoint will be exported.

        from_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated since the given timestamp.
            Format - output from datetime.timestamp()

        old_format: bool = False
            Whether to export tasks in old format.

        without_masks: bool = False
            Exports only tasks JSON without downloading any segmentation masks.
            Note: This is not recommended for tasks with overlapping labels.

        without_json: bool = False
            Doesn't create the tasks JSON file.

        semantic_mask: bool = False
            Whether to export all segmentations as semantic_mask.
            This will create one instance per class.
            If this is set to True and a task has multiple instances per class,
            then attributes belonging to each instance will not be exported.

        binary_mask: Optional[bool] = None
            Whether to export all segmentations as binary masks.
            This will create one segmentation file per instance.
            If this is set to None and a task has overlapping labels,
            then binary_mask option will be True for that particular task.

        no_consensus: Optional[bool] = None
            Whether to export tasks without consensus info.
            If None, will default to export with consensus info,
            if it is enabled for the given project.
            (Applicable only for new format export)

        with_files: bool = False
            Export with files (e.g. images/video frames)

        dicom_to_nifti: bool = False
            Convert DICOM images to NIfTI. Applicable when `with_files` is True.

        png: bool = False
            Export labels as PNG masks.

        rt_struct: bool = False
            Export labels as DICOM RT-Struct. (Only for DICOM images)

        destination: Optional[str] = None
            Destination directory (Default: current directory)

        Returns
        -----------
        Iterator[:obj:`~redbrick.types.task.OutputTask`]
            Datapoint and labels in RedBrick AI format. See
            https://docs.redbrickai.com/python-sdk/format-reference


        .. note:: If both `semantic_mask` and `binary_mask` options are True,
            then one binary mask will be generated per class.
        """
        # pylint: disable=too-many-locals

        no_consensus = (
            no_consensus if no_consensus is not None else not self.consensus_enabled
        )

        taxonomy = self.context.project.get_taxonomy(
            self.org_id, tax_id=None, name=self.taxonomy_name
        )

        # Create output directory
        destination = destination or self.project_id

        image_dir: Optional[str] = None
        if with_files or rt_struct:
            image_dir = os.path.join(destination, "images")
            os.makedirs(image_dir, exist_ok=True)

        segmentation_dir: Optional[str] = None
        if not without_masks:
            segmentation_dir = os.path.join(destination, "segmentations")
            os.makedirs(segmentation_dir, exist_ok=True)
            logger.info(f"Saving masks to {segmentation_dir} directory")

        task_file: Optional[str] = None
        if not without_json:
            task_file = os.path.join(destination, "tasks.json")
            if not image_dir and not segmentation_dir:
                os.makedirs(destination, exist_ok=True)

        class_map, color_map = self.preprocess_export(taxonomy, png)

        if png:
            with open(
                os.path.join(destination, "class_map.json"), "w", encoding="utf-8"
            ) as classes_file:
                json.dump(class_map, classes_file, indent=2)

        datapoints = self._get_raw_data_latest(
            concurrency,
            "END" if only_ground_truth else stage_name,
            None if task_id else from_timestamp,
            True,
            bool(self.label_stages)
            and not bool(self.review_stages)
            and not no_consensus,
            task_id,
        )

        if task_file and os.path.isfile(task_file):
            os.remove(task_file)

        loop = asyncio.get_event_loop()
        for datapoint in datapoints:
            task: TypeTask = loop.run_until_complete(
                self.export_nifti_label_data(  # type: ignore
                    datapoint,
                    taxonomy,
                    task_file,
                    image_dir,
                    segmentation_dir,
                    semantic_mask,
                    binary_mask,
                    old_format,
                    no_consensus,
                    color_map,
                    dicom_to_nifti,
                    png,
                    rt_struct,
                    True,
                )
            )
            yield task

        if task_file and not os.path.isfile(task_file):
            with open(task_file, "w", encoding="utf-8") as task_file_:
                task_file_.write("[]")

    def list_tasks(
        self,
        search: TaskFilters = TaskFilters.ALL,
        concurrency: int = 10,
        limit: Optional[int] = 50,
        *,
        stage_name: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        completed_at: Optional[Tuple[Optional[float], Optional[float]]] = None,
    ) -> Iterator[Dict]:
        """
        Search tasks based on multiple queries for a project.
        This function returns minimal meta-data about the queried tasks.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> result = project.export.list_tasks()

        Parameters
        -----------
        search: :obj:`~redbrick.common.enums.TaskFilters` = TaskFilters.ALL
            Task filter type.

        concurrency: int = 10
            The number of requests that will be made in parallel.

        limit: Optional[int] = 50
            The number of tasks to return.
            Use None to return all tasks matching the search query.

        stage_name: Optional[str] = None
            If present, will return tasks that are:
                a. Available in stage_name: If search == TaskFilters.QUEUED
                b. Completed in stage_name: If search == TaskFilters.COMPLETED

        user_id: Optional[str] = None
            User id/email. If present, will return tasks that are:
                a. Assigned to user_id: If search == TaskFilters.QUEUED
                b. Completed by user_id: If search == TaskFilters.COMPLETED

        task_id: Optional[str] = None
            If present, will return data for the given task id.

        task_name: Optional[str] = None
            If present, will return data for the given task name.
            This will do a prefix search with the given task name.

        completed_at: Optional[Tuple[Optional[float], Optional[float]]] = None
            If present, will return tasks that were completed in the given time range.
            The tuple contains the `from` and `to` timestamps respectively.

        Returns
        -----------
        Iterator[Dict]
            >>> [{
                "taskId": str,
                "name": str,
                "createdAt": str,
                "updatedAt": str,
                "currentStageName": str,
                "createdBy"?: {"userId": str, "email": str},
                "priority"?: float([0, 1]),
                "metaData"?: dict,
                "series"?: [{"name"?: str, "metaData"?: dict}],
                "assignees"?: [{
                    "user": str,
                    "status": str,
                    "assignedAt": datetime,
                    "lastSavedAt"?: datetime,
                    "completedAt"?: datetime,
                    "timeSpentMs"?: float,
                }]
            }]
        """
        # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        label_stages: List[str] = [stage.stage_name for stage in self.label_stages]
        review_stages: List[str] = [stage.stage_name for stage in self.review_stages]
        all_stages: List[str] = label_stages + review_stages + [self.output_stage_name]

        if stage_name and stage_name not in all_stages:
            raise ValueError(f"Invalid stage name: {stage_name}")

        filters: TaskFilterParams = TaskFilterParams()

        if user_id:
            filters["userId"] = user_id
        if task_id:
            filters["taskId"] = task_id
            task_name = task_id

        if search == TaskFilters.ALL:
            stage_name = None
            filters.pop("userId", None)
        elif search == TaskFilters.GROUNDTRUTH:
            stage_name = self.output_stage_name
            filters.pop("userId", None)
        elif search == TaskFilters.UNASSIGNED:
            stage_name = stage_name or all_stages[0]
            filters["userId"] = None
        elif search == TaskFilters.QUEUED:
            stage_name = stage_name or all_stages[0]
        elif search == TaskFilters.DRAFT:
            stage_name = stage_name or all_stages[0]
            filters["status"] = TaskStates.STAGED
        elif search == TaskFilters.SKIPPED:
            stage_name = stage_name or all_stages[0]
            filters["status"] = TaskStates.SKIPPED
        elif search == TaskFilters.COMPLETED:
            stage_name = stage_name or all_stages[0]
            filters["recentlyCompleted"] = True
            if completed_at:
                if completed_at[0] is not None:
                    filters["completedAtFrom"] = datetime.fromtimestamp(
                        completed_at[0], tz=timezone.utc
                    ).isoformat()
                if completed_at[1] is not None:
                    filters["completedAtTo"] = datetime.fromtimestamp(
                        completed_at[1], tz=timezone.utc
                    ).isoformat()
        elif search == TaskFilters.FAILED:
            stage_name = (
                stage_name
                if stage_name and stage_name in review_stages
                else review_stages[0]
            )
            filters["reviewState"] = ReviewStates.FAILED
            filters.pop("userId", None)
        elif search == TaskFilters.ISSUES:
            stage_name = label_stages[0]
            filters["status"] = TaskStates.PROBLEM
            filters.pop("userId", None)
        elif search == TaskFilters.BENCHMARK:
            stage_name = self.output_stage_name
            filters["benchmark"] = True
            filters.pop("userId", None)
        else:
            raise ValueError(f"Invalid task filter: {search}")

        members = self.context.project.get_members(self.org_id, self.project_id)
        users = {}
        for member in members:
            user = member.get("member", {}).get("user", {})
            if user.get("userId") and user.get("email"):
                users[user["userId"]] = user["email"]

        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.task_search,
                self.org_id,
                self.project_id,
                stage_name,
                task_name,
                filters,
                True,
            ),
            concurrency,
            limit,
        )

        for task in my_iter:
            datapoint = task["datapoint"] or {}
            task_obj = {
                "taskId": task["taskId"],
                "name": datapoint.get("name"),
                "createdAt": task["createdAt"],
                "currentStageName": task["currentStageName"],
            }

            if task["updatedAt"]:
                task_obj["updatedAt"] = task["updatedAt"]

            if datapoint.get("createdByEntity"):
                task_obj["createdBy"] = user_format(
                    datapoint["createdByEntity"].get("userId"), users
                )
            if task["priority"]:
                task_obj["priority"] = task["priority"]
            if datapoint.get("metaData"):
                task_obj["metaData"] = json.loads(datapoint["metaData"])

            if isinstance(datapoint.get("seriesInfo"), list):
                series_list = []
                for series in datapoint["seriesInfo"]:
                    series_obj = {}
                    if series["name"]:
                        series_obj["name"] = series["name"]
                    if series["metaData"]:
                        series_obj["metaData"] = json.loads(series["metaData"])
                    series_list.append(series_obj)
                if any(series for series in series_list):
                    task_obj["series"] = series_list

            stage_task = task.get("currentStageSubTask", {}) or {}
            assignees = [assignee_format(stage_task, users)] + [
                assignee_format(sub_task, users)
                for sub_task in (stage_task.get("subTasks", []) or [])
            ]
            assignees = [assignee for assignee in assignees if assignee]

            if assignees:
                task_obj["assignees"] = assignees

            yield task_obj

    def get_task_events(
        self,
        *,
        task_id: Optional[str] = None,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        from_timestamp: Optional[float] = None,
        with_labels: bool = False,
    ) -> Iterator[Dict]:
        """Generate an audit log of all actions performed on tasks.

        Use this method to get a detailed summary of all the actions performed on your
        tasks, including:

        - Who uploaded the data
        - Who annotated your tasks
        - Who reviewed your tasks
        - and more.

        This can be particulary useful to present to auditors who are interested in your
        quality control workflows.

        Parameters
        -----------
        task_id: Optional[str] = None
            If set, returns events only for the given task.

        only_ground_truth: bool = True
            If set to True, will return events for tasks
            that have been completed in your workflow.

        concurrency: int = 10
            The number of requests that will be made in parallel.

        from_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated since the given timestamp.
            Format - output from datetime.timestamp()

        with_labels: bool = False
            Get metadata of labels submitted in each stage.

        Returns
        -----------
        Iterator[Dict]
            >>> [{
                "taskId": string,
                "currentStageName": string,
                "events": List[Dict]
            }]
        """
        # pylint: disable=too-many-locals
        taxonomy: Dict = {}
        if with_labels:
            taxonomy = self.context.project.get_taxonomy(
                self.org_id, tax_id=None, name=self.taxonomy_name
            )
        members = self.context.project.get_members(self.org_id, self.project_id)
        users = {}
        for member in members:
            user = member.get("member", {}).get("user", {})
            if user.get("userId") and user.get("email"):
                users[user["userId"]] = user["email"]

        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.task_events,
                self.org_id,
                self.project_id,
                task_id,
                "END" if only_ground_truth else None,
                (
                    datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
                    if from_timestamp is not None
                    else None
                ),
                with_labels,
            ),
            concurrency,
        )

        with tqdm.tqdm(my_iter, unit=" datapoints") as progress:
            for task in progress:
                task = task_event_format(task, users, with_labels)
                for event in task["events"]:
                    if "labels" not in event:
                        continue
                    labels = dicom_rb_format(
                        event["labels"], taxonomy, False, True, self.review_stages
                    )
                    event["labels"] = {"series": labels.get("series") or []}
                    if labels.get("classification") is not None:
                        event["labels"]["classification"] = labels["classification"]
                yield task

    def get_active_time(
        self,
        *,
        stage_name: str,
        task_id: Optional[str] = None,
        concurrency: int = 100,
    ) -> Iterator[Dict]:
        """Get active time spent on tasks for labeling/reviewing.

        Parameters
        -----------
        stage_name: str
            Stage for which to return the time info.

        task_id: Optional[str] = None
            If set, will return info for the given task in the given stage.

        concurrency: int = 100
            Request batch size.

        Returns
        -----------
        Iterator[Dict]
            >>> [{
                "orgId": string,
                "projectId": string,
                "stageName": string,
                "taskId": string,
                "completedBy": string,
                "timeSpent": number,  # In milliseconds
                "completedAt": datetime,
                "cycle": number  # Task cycle
            }]
        """
        members = self.context.project.get_members(self.org_id, self.project_id)
        users = {}
        for member in members:
            user = member.get("member", {}).get("user", {})
            if user.get("userId") and user.get("email"):
                users[user["userId"]] = user["email"]

        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.active_time,
                self.org_id,
                self.project_id,
                stage_name,
                task_id,
            ),
            concurrency,
        )

        with tqdm.tqdm(my_iter, unit=" datapoints") as progress:
            for task in progress:
                yield {
                    "orgId": self.org_id,
                    "projectId": self.project_id,
                    "stageName": stage_name,
                    "taskId": task["taskId"],
                    "completedBy": user_format(task["user"]["userId"], users),
                    "timeSpent": task["timeSpent"],
                    "completedAt": task["date"],
                    "cycle": task["cycle"],
                }
