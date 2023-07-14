"""Public API to exporting."""
import asyncio
import re
import shutil
from typing import List, Dict, Optional, Set, Tuple, Any
from functools import partial
import os
import json
import copy
from datetime import datetime, timezone

import aiohttp
import tqdm  # type: ignore

from redbrick.common.constants import MAX_CONCURRENCY, MAX_FILE_BATCH_SIZE
from redbrick.common.context import RBContext
from redbrick.common.enums import ReviewStates, TaskFilters, TaskStates
from redbrick.common.export import TaskFilterParams
from redbrick.utils.async_utils import gather_with_concurrency
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
    clean_rb_label,
    dicom_rb_format,
    from_rb_assignee,
    parse_entry_latest,
)
from redbrick.utils.rb_event_utils import task_event_format


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
        label_stages: List[Dict],
        review_stages: List[Dict],
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
        only_ground_truth: bool = False,
        from_timestamp: Optional[float] = None,
        presign_items: bool = False,
        with_consensus: bool = False,
        task_id: Optional[str] = None,
    ) -> Tuple[List[Dict], Dict]:
        # pylint: disable=too-many-locals
        taxonomy = self.context.project.get_taxonomy(
            self.org_id, tax_id=None, name=self.taxonomy_name
        )
        if task_id:
            logger.info(f"Fetching task: {task_id}")
            val = self.context.export.get_datapoint_latest(
                self.org_id, self.project_id, task_id, presign_items, with_consensus
            )
            task = parse_entry_latest(val)
            return ([task] if task else []), taxonomy

        stage_name = "END" if only_ground_truth else None
        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.get_datapoints_latest,
                self.org_id,
                self.project_id,
                stage_name,
                datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
                if from_timestamp is not None
                else None,
                presign_items,
                with_consensus,
            ),
            concurrency,
        )

        datapoint_count = self.context.export.datapoints_in_project(
            self.org_id, self.project_id, stage_name
        )

        logger.info(
            f"Downloading {'groundtruth' if only_ground_truth else 'all'} tasks"
            + (
                f" updated since {datetime.fromtimestamp(from_timestamp)}"
                if from_timestamp is not None
                else ""
            )
        )

        with tqdm.tqdm(my_iter, unit=" datapoints", total=datapoint_count) as progress:
            datapoints = []
            for val in progress:
                task = parse_entry_latest(val)
                if task:
                    datapoints.append(task)
            try:
                disable = progress.disable
                progress.disable = False
                progress.update(datapoint_count - progress.n)
                progress.disable = disable
            except Exception:  # pylint: disable=broad-except
                pass

        return datapoints, taxonomy

    async def _get_input_labels(self, dp_ids: List[str]) -> List[Dict]:
        conn = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=conn) as session:
            coros = [
                self.context.export.get_labels(
                    session, self.org_id, self.project_id, dp_id
                )
                for dp_id in dp_ids
            ]
            input_data = await gather_with_concurrency(MAX_CONCURRENCY, coros)

        await asyncio.sleep(0.250)  # give time to close ssl connections
        labels = [
            [clean_rb_label(label) for label in json.loads(data["labelsData"])]
            for data in input_data
        ]
        return [
            {**data, "inputLabels": label}
            for data, label in zip(input_data, labels)  # type: ignore
        ]

    def get_latest_data(
        self,
        concurrency: int,
        only_ground_truth: bool = False,
        from_timestamp: Optional[float] = None,
        get_input_labels: bool = False,
    ) -> Tuple[List[Dict], float]:
        """Export latest data."""
        # pylint: disable=too-many-locals
        stage_name = "END" if only_ground_truth else None
        cache_time = (
            datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
            if from_timestamp is not None
            else None
        )
        logger.info(
            f"Downloading {'groundtruth' if only_ground_truth else 'all'} tasks"
            + (
                f" updated since {datetime.fromtimestamp(from_timestamp)}"
                if from_timestamp is not None
                else ""
            )
        )
        tasks = []
        cursor = None
        new_cache_time = cache_time
        dp_ids = []
        while True:
            entries, cursor, new_cache_time = self.context.export.get_datapoints_latest(
                self.org_id,
                self.project_id,
                stage_name,
                cache_time,
                False,
                False,
                concurrency,
                cursor,
            )
            for val in entries:
                tasks.append(parse_entry_latest(val))
                dp_ids.append(val["dpId"])

            if cursor is None:
                break

        if get_input_labels:
            loop = asyncio.get_event_loop()
            input_labels = loop.run_until_complete(self._get_input_labels(dp_ids))
            for idx, input_label in enumerate(input_labels):
                tasks[idx] = {**tasks[idx], "inputLabels": input_label["inputLabels"]}

        return tasks, (new_cache_time.timestamp() if new_cache_time else 0)

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
                else None,
            )
            Export.tax_class_id_mapping(
                trail, category["children"], class_id, color_map, taxonomy_color
            )

    @staticmethod
    def _get_task_series(task: Dict) -> List[Dict]:
        return (
            (
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

    async def _download_tasks(
        self,
        tasks: List[Dict],
        storage_ids: List[str],
        taxonomy: Dict,
        export_dir: str,
        dcm_to_nii: bool,
        rt_struct: bool,
        is_tax_v2: bool,
        concurrency: int = 5,
    ) -> List[Dict]:
        # pylint: disable=too-many-locals, import-outside-toplevel, too-many-nested-blocks

        images_dir = os.path.join(export_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        downloaded_tasks = await gather_with_concurrency(
            min(concurrency, MAX_FILE_BATCH_SIZE),
            [
                self._download_task(
                    task, storage_id, images_dir, taxonomy, rt_struct, is_tax_v2
                )
                for task, storage_id in zip(tasks, storage_ids)
            ],
            progress_bar_name="Downloading images",
            keep_progress_bar=False,
        )
        tasks = [task for task, _ in downloaded_tasks]

        logger.info(f"Exported images to: {images_dir}")

        if not dcm_to_nii:
            return tasks

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
        for task, series_dirs in downloaded_tasks:
            task_series = Export._get_task_series(task)
            if not task_series or len(task_series) != len(series_dirs):
                continue
            for series, series_dir in zip(task_series, series_dirs):
                items = (
                    [series["items"]]
                    if isinstance(series["items"], str)
                    else series["items"]
                )
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
                        continue
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

        return tasks

    async def _download_task(
        self,
        task: Dict,
        storage_id: str,
        parent_dir: str,
        taxonomy: Dict,
        rt_struct: bool,
        is_tax_v2: bool,
    ) -> Tuple[Dict, List[str]]:
        # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        path_pattern = re.compile(r"[^\w.]+")
        task_name = re.sub(path_pattern, "-", task.get("name", "")) or task["taskId"]
        task_dir = os.path.join(parent_dir, task_name)

        if os.path.exists(task_dir) and not os.path.isdir(task_dir):
            os.remove(task_dir)

        os.makedirs(task_dir, exist_ok=True)

        series_dirs: List[str] = []
        items_lists: List[List[str]] = []

        try:
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
                items_lists.append(task["items"])

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
                list(zip(presigned, local_files)), "Downloading files", False
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
                    series["items"] = series_items[idx]
                for idx, series in enumerate(
                    (task.get("superTruth", {}) or {}).get("series", []) or []
                ):
                    series["items"] = series_items[idx]
                for sub_task in task.get("consensusTasks", []) or []:
                    for idx, series in enumerate(sub_task.get("series", []) or []):
                        series["items"] = series_items[idx]

                if is_tax_v2 and rt_struct:
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

                        rtstruct = await convert_nii_to_rtstruct(
                            segmentations,
                            series_dir,
                            taxonomy.get("objectTypes", []) or [],
                            series.get("segmentMap", {}) or {},
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
                        rtstruct.save(series["segmentations"])

            else:
                task["items"] = downloaded

        except Exception as err:  # pylint: disable=broad-except
            log_error(
                f"Error for task {task['taskId']}: {err}\n Please try using a lower --concurrency"
            )
            shutil.rmtree(task_dir, ignore_errors=True)

        return task, series_dirs

    async def process_labels(
        self,
        datapoint: Dict,
        nifti_dir: str,
        color_map: Dict,
        old_format: bool,
        no_consensus: bool,
        png_mask: bool,
        is_tax_v2: bool,
    ) -> Dict:
        """Process labels."""
        # pylint: disable=too-many-locals
        task = copy.deepcopy(datapoint)
        files: List[Tuple[Optional[str], Optional[str]]] = []
        labels_map: List[Optional[Dict]] = []

        series_info: List[Dict] = task.get("seriesInfo", []) or []
        has_series_info = sum(
            list(
                map(
                    lambda val: len(val["itemsIndices"])
                    if isinstance(val, dict) and len(val.get("itemsIndices", []) or [])
                    else -1000000,
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
                if label_map and "imageIndex" in label_map:
                    labels_map[image_index_map[label_map["imageIndex"]]] = label_map
                else:
                    labels_map[idx] = label_map

        else:
            labels_map = task.get("labelsMap", []) or []

        presign_paths: List[Optional[str]] = [
            label_map.get("labelName") if label_map else None
            for label_map in labels_map
        ]

        if task.get("consensusTasks"):
            presign_paths = [None for _ in presign_paths]
            for consensus_task in task["consensusTasks"]:
                presign_paths.extend(
                    [
                        consensus_label_map.get("labelName")
                        if consensus_label_map
                        and consensus_task.get("labelStorageId")
                        == task["labelStorageId"]
                        else None
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
                nifti_dir,
                has_series_info,
                series_info,
                labels_map,
                image_index_map,
                color_map,
                png_mask,
                is_tax_v2,
            )

        return dicom_rb_format(
            task,
            old_format,
            no_consensus,
            self.label_stages,
            self.review_stages,
            self.output_stage_name,
        )

    async def download_and_process_segmentations(
        self,
        task: Dict,
        presign_paths: List[Optional[str]],
        files: List[Tuple[Optional[str], Optional[str]]],
        nifti_dir: str,
        has_series_info: bool,
        series_info: List[Dict],
        labels_map: List[Optional[Dict]],
        image_index_map: Dict[int, int],
        color_map: Dict,
        png_mask: bool,
        is_tax_v2: bool,
    ) -> None:
        """Download and process segmentations."""
        # pylint: disable=import-outside-toplevel, too-many-locals
        # pylint: disable=too-many-branches, too-many-statements
        from redbrick.utils.dicom import process_nifti_download

        presigned = self.context.export.presign_items(
            self.org_id, task["labelStorageId"], presign_paths
        )

        path_pattern = re.compile(r"[^\w.]+")
        task_name = re.sub(path_pattern, "-", task.get("name", "")) or task["taskId"]
        task_dir = os.path.join(nifti_dir, task_name)
        shutil.rmtree(task_dir, ignore_errors=True)
        os.makedirs(task_dir, exist_ok=True)
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

        paths = await download_files(
            files, "Downloading segmentations", False, True, True
        )

        for label, path in zip(labels_map, paths):  # type: ignore
            if label and label.get("labelName"):
                label["labelName"] = await process_nifti_download(
                    task.get("labels", []) or [],
                    path,
                    png_mask,
                    color_map,
                    is_tax_v2,
                    image_index_map.get(label.get("imageIndex", -1)),
                )

        if len(paths) > len(labels_map) and task.get("consensusTasks"):
            index = len(labels_map)
            for consensus_task in task["consensusTasks"]:
                consensus_labels = consensus_task.get("labels", []) or []
                consensus_labels_map = consensus_task.get("labelsMap", []) or []
                for consensus_label_map in consensus_labels_map:
                    consensus_label_map["labelName"] = await process_nifti_download(
                        consensus_labels,
                        paths[index],
                        png_mask,
                        color_map,
                        is_tax_v2,
                        image_index_map.get(consensus_label_map.get("imageIndex")),
                    )
                    index += 1

    def export_nifti_label_data(
        self,
        datapoints: List[Dict],
        concurrency: int,
        taxonomy: Dict,
        export_dir: str,
        nifti_dir: str,
        old_format: bool,
        no_consensus: bool,
        with_files: bool,
        dicom_to_nifti: bool,
        png_mask: bool,
        rt_struct: bool,
    ) -> Tuple[List[Dict], Dict]:
        """Export nifti label maps."""
        # pylint: disable=too-many-locals
        class_map: Dict = {}
        color_map: Dict = {}
        is_tax_v2 = bool(taxonomy.get("isNew"))
        if png_mask:
            if is_tax_v2:
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
        os.makedirs(nifti_dir, exist_ok=True)
        loop = asyncio.get_event_loop()
        tasks = loop.run_until_complete(
            gather_with_concurrency(
                min(concurrency, MAX_FILE_BATCH_SIZE),
                [
                    self.process_labels(
                        datapoint,
                        nifti_dir,
                        color_map,
                        old_format,
                        no_consensus,
                        png_mask,
                        is_tax_v2,
                    )
                    for datapoint in datapoints
                ],
                "Processing labels",
            )
        )

        if with_files or rt_struct:
            try:
                loop.run_until_complete(
                    self._download_tasks(
                        tasks,
                        [datapoint["storageId"] for datapoint in datapoints],
                        taxonomy,
                        export_dir,
                        dicom_to_nifti,
                        rt_struct,
                        is_tax_v2,
                        concurrency,
                    )
                )
            except Exception as err:  # pylint: disable=broad-except
                log_error(f"Failed to download files: {err}")

        return tasks, class_map

    def export_tasks(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        *,
        task_id: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        old_format: bool = False,
        no_consensus: Optional[bool] = None,
        with_files: bool = False,
        dicom_to_nifti: bool = False,
        png: bool = False,
        rt_struct: bool = False,
        destination: Optional[str] = None,
    ) -> List[Dict]:
        """Export annotation data.

        Meta-data and category information returned as an Object. Segmentations are written to
        your disk in NIfTI-1 format. Please `visit our
        documentation <https://docs.redbrickai.com/python-sdk/reference/annotation-format>`_
        for more information on the format.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> project.export.export_tasks()

        Parameters
        -----------
        only_ground_truth: bool = True
            If set to True, will only return data that has
            been completed in your workflow. If False, will
            export latest state

        concurrency: int = 10

        task_id: Optional[str] = None
            If the unique task_id is mentioned, only a single
            datapoint will be exported.

        from_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated since the given timestamp.
            Format - output from datetime.timestamp()

        old_format: bool = False
            Whether to export tasks in old format.

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
        List[Dict]
            Datapoint and labels in RedBrick AI format. See
            https://docs.redbrickai.com/python-sdk/reference/annotation-format
        """
        # pylint: disable=too-many-locals

        no_consensus = (
            no_consensus if no_consensus is not None else not self.consensus_enabled
        )

        datapoints, taxonomy = self._get_raw_data_latest(
            concurrency,
            False if task_id else only_ground_truth,
            None if task_id else from_timestamp,
            True,
            bool(self.label_stages)
            and not bool(self.review_stages)
            and not no_consensus,
            task_id,
        )

        if task_id:
            datapoints = [
                datapoint for datapoint in datapoints if datapoint["taskId"] == task_id
            ]

        # Create output directory
        destination = destination or self.project_id
        nifti_dir = os.path.join(destination, "nifti")
        os.makedirs(nifti_dir, exist_ok=True)
        logger.info(f"Saving NIfTI files to {destination} directory")
        tasks, class_map = self.export_nifti_label_data(
            datapoints,
            concurrency,
            taxonomy,
            destination,
            nifti_dir,
            old_format,
            no_consensus,
            with_files,
            dicom_to_nifti,
            png,
            rt_struct,
        )
        with open(
            os.path.join(destination, "tasks.json"), "w", encoding="utf-8"
        ) as tasks_file:
            json.dump(tasks, tasks_file, indent=2)

        if png:
            with open(
                os.path.join(destination, "class_map.json"), "w", encoding="utf-8"
            ) as classes_file:
                json.dump(class_map, classes_file, indent=2)

        return tasks

    def redbrick_nifti(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        old_format: bool = False,
        no_consensus: Optional[bool] = None,
        png: bool = False,
    ) -> List[Dict]:
        """
        .. admonition:: Deprecation Notice

            .. deprecated:: 2.11.0

            Use :obj:`~redbrick.export.Export.export_tasks` instead.

        Alias to export_tasks method.
        """
        logger.warning(
            "`Export.redbrick_nifti` method has been deprecated and will be removed "
            + "in a future release. Please use `Export.export_tasks` method instead."
        )
        return self.export_tasks(
            only_ground_truth,
            concurrency,
            task_id=task_id,
            from_timestamp=from_timestamp,
            old_format=old_format,
            no_consensus=no_consensus,
            png=png,
        )

    def search_tasks(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        name: Optional[str] = None,
    ) -> List[Dict]:
        """
        .. admonition:: Deprecation Notice

            .. deprecated:: 2.11.0

            Use :obj:`~redbrick.export.Export.list_tasks` instead.

        Search tasks by ``task_id`` or ``name`` in any stage of your project workflow.
        This function returns minimal meta-data about the queried tasks.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> result = project.export.search_tasks()

        Parameters
        -----------
        only_ground_truth: bool = True
            If set to True, will return all tasks
            that have been completed in your workflow.

        concurrency: int = 10
            The number of requests that will be made in parallel.

        name: Optional[str] = None
            If present, will return the task with task_id == name.
            If no match found, will return the task with task name == name

        Returns
        -----------
        List[Dict]
            [{"taskId": str, "name": str, "createdAt": str, "currentStageName": str}]
        """
        logger.warning(
            "`Export.search_tasks` method has been deprecated and will be removed "
            + "in a future release. Please use `Export.list_tasks` method instead."
        )
        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.task_search,
                self.org_id,
                self.project_id,
                self.output_stage_name if only_ground_truth else None,
                name,
                None,
                True,
            ),
            concurrency,
        )

        with tqdm.tqdm(my_iter, unit=" datapoints") as progress:
            datapoints = [
                {
                    "taskId": task["taskId"],
                    "name": task["datapoint"]["name"],
                    "createdAt": task["createdAt"],
                    "currentStageName": task["currentStageName"],
                }
                for task in progress
                if (task.get("datapoint", {}) or {}).get("name")
                and (not only_ground_truth or task["currentStageName"] == "END")
            ]

        return datapoints

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
    ) -> List[Dict]:
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
            If present, will return tasks that are available in or
            completed in the given stage based on the search query.

        user_id: Optional[str] = None
            If present, will return tasks that are assigned to or
            completed by the given user id/email based on the search query.

        task_id: Optional[str] = None
            If present, will return data for the given task id.

        task_name: Optional[str] = None
            If present, will return data for the given task name.
            This will do a prefix search with the given task name.

        Returns
        -----------
        List[Dict]
            [{
                "taskId": str,
                "name": str,
                "createdAt": str,
                "currentStageName": str,
                "createdBy"?: {"userId": str, "email": str},
                "priority"?: float([0, 1]),
                "metaData"?: dict,
                "series"?: [{"name"?: str, "metaData"?: dict}],
                "assignees"?: [{"userId": str, "email": str}]
            }]
        """
        # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        label_stages: List[str] = [stage["stageName"] for stage in self.label_stages]
        review_stages: List[str] = [stage["stageName"] for stage in self.review_stages]
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

        tasks: List[Dict] = []
        with tqdm.tqdm(my_iter, unit=" datapoints") as progress:
            for task in progress:
                datapoint = task["datapoint"] or {}
                task_obj = {
                    "taskId": task["taskId"],
                    "name": datapoint.get("name"),
                    "createdAt": task["createdAt"],
                    "currentStageName": task["currentStageName"],
                }

                if datapoint.get("createdByEntity"):
                    task_obj["createdBy"] = from_rb_assignee(
                        datapoint["createdByEntity"]
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

                assignees = [
                    from_rb_assignee(assignee)
                    for assignee in (
                        (task["currentStageSubTask"] or {}).get(
                            "consensusAssignees", []
                        )
                        or []
                    )
                ]

                if assignees:
                    task_obj["assignees"] = assignees

                tasks.append(task_obj)

        return tasks

    def get_task_events(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        from_timestamp: Optional[float] = None,
    ) -> List[Dict]:
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
        only_ground_truth: bool = True
            If set to True, will return events for tasks
            that have been completed in your workflow.

        concurrency: int = 10
            The number of requests that will be made in parallel.

        from_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated since the given timestamp.
            Format - output from datetime.timestamp()

        Returns
        -----------
        List[Dict]
            [{"taskId": str, "currentStageName": str, "events": List[Dict]}]
        """
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
                "END" if only_ground_truth else None,
                datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
                if from_timestamp is not None
                else None,
            ),
            concurrency,
        )

        tasks: List[Dict] = []
        with tqdm.tqdm(my_iter, unit=" datapoints") as progress:
            for task in progress:
                tasks.append(task_event_format(task, users))

        return tasks
