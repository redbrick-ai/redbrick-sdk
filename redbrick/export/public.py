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

from redbrick.common.constants import MAX_CONCURRENCY
from redbrick.common.context import RBContext
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.files import uniquify_path, download_files
from redbrick.utils.logging import logger
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_label_utils import (
    clean_rb_label,
    dicom_rb_format,
    parse_entry_latest,
)
from redbrick.utils.rb_event_utils import task_event_format


class Export:
    """
    Primary interface to handling export from a project.

    This class has methods to export to various formats depending on
    your project type.
    """

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
        self.has_label_stage_only = bool(label_stages) and not bool(review_stages)
        self.taxonomy_name = taxonomy_name

    def _get_raw_data_latest(
        self,
        concurrency: int,
        only_ground_truth: bool = False,
        from_timestamp: Optional[float] = None,
        to_timestamp: Optional[float] = None,
        presign_items: bool = False,
        with_consensus: bool = False,
    ) -> Tuple[List[Dict], Dict]:
        # pylint: disable=too-many-locals
        temp = self.context.export.get_datapoints_latest
        stage_name = "END" if only_ground_truth else None
        my_iter = PaginationIterator(
            partial(
                temp,
                self.org_id,
                self.project_id,
                stage_name,
                datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
                if from_timestamp is not None
                else None,
                datetime.fromtimestamp(to_timestamp, tz=timezone.utc)
                if to_timestamp is not None
                else None,
                presign_items,
                with_consensus,
                concurrency,
            )
        )

        taxonomy = self.context.project.get_taxonomy(
            self.org_id, tax_id=None, name=self.taxonomy_name
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
        conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
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
            {**data, "inputLabels": label} for data, label in zip(input_data, labels)
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
                None,
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

    async def download_and_process_nifti(
        self,
        datapoint: Dict,
        nifti_dir: str,
        color_map: Dict,
        old_format: bool,
        no_consensus: bool,
        png_mask: bool,
        is_tax_v2: bool,
    ) -> Dict:
        """Download and process label maps."""
        # pylint: disable=import-outside-toplevel, too-many-locals
        # pylint: disable=too-many-branches, too-many-statements
        from redbrick.utils.dicom import process_nifti_download

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

        image_index_map = {}
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

        for label, path in zip(labels_map, paths):
            if label and label.get("labelName"):
                label["labelName"] = process_nifti_download(
                    task.get("labels", []) or [],
                    path,
                    png_mask,
                    color_map,
                    is_tax_v2,
                    image_index_map.get(label.get("imageIndex")),
                )

        if len(paths) > len(labels_map) and task.get("consensusTasks"):
            index = len(labels_map)
            for consensus_task in task["consensusTasks"]:
                consensus_labels = consensus_task.get("labels", []) or []
                consensus_labels_map = consensus_task.get("labelsMap", []) or []
                for consensus_label_map in consensus_labels_map:
                    consensus_label_map["labelName"] = process_nifti_download(
                        consensus_labels,
                        paths[index],
                        png_mask,
                        color_map,
                        is_tax_v2,
                        image_index_map.get(consensus_label_map.get("imageIndex")),
                    )
                    index += 1

        return dicom_rb_format(task, old_format, no_consensus)

    def export_nifti_label_data(
        self,
        datapoints: List[Dict],
        taxonomy: Dict,
        nifti_dir: str,
        old_format: bool,
        no_consensus: bool,
        png_mask: bool,
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
                MAX_CONCURRENCY,
                [
                    self.download_and_process_nifti(
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
                "Processing nifti labels",
            )
        )

        return tasks, class_map

    def export_tasks(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        to_timestamp: Optional[float] = None,
        old_format: bool = False,
        no_consensus: Optional[bool] = None,
        png: bool = False,
    ) -> List[Dict]:
        """
        Export labels for 'Medical' project type. Segmentations are exported in NIfTI-1 format.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> project.export.export_tasks()

        Parameters
        --------------
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

        to_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated till the given timestamp.
            Format - output from datetime.timestamp()

        old_format: bool = False
            Whether to export tasks in old format.

        no_consensus: Optional[bool] = None
            Whether to export tasks without consensus info.
            If None, will default to export with consensus info,
            if it is enabled for the given project.
            (Applicable only for new format export)

        png: bool = False
            Export nifti labels as png masks.

        Returns:
        -----------------
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
            None if task_id else to_timestamp,
            True,
            self.has_label_stage_only and not no_consensus,
        )

        if task_id:
            datapoints = [
                datapoint for datapoint in datapoints if datapoint["taskId"] == task_id
            ]

        # Create output directory
        destination = uniquify_path(self.project_id)
        nifti_dir = os.path.join(destination, "nifti")
        os.makedirs(nifti_dir, exist_ok=True)
        logger.info(f"Saving NIfTI files to {destination} directory")
        tasks, class_map = self.export_nifti_label_data(
            datapoints,
            taxonomy,
            nifti_dir,
            old_format,
            no_consensus,
            png,
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
        to_timestamp: Optional[float] = None,
        old_format: bool = False,
        no_consensus: Optional[bool] = None,
        png: bool = False,
    ) -> List[Dict]:
        """Alias to export_tasks method (Will be deprecated)."""
        return self.export_tasks(
            only_ground_truth,
            concurrency,
            task_id,
            from_timestamp,
            to_timestamp,
            old_format,
            no_consensus,
            png,
        )

    def search_tasks(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        name: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search tasks by task_id/name in groundtruth or entire project.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> result = project.export.search_tasks()

        Parameters
        -----------
        only_ground_truth: bool = True
            If set to True, will return all tasks
            that have been completed in your workflow.

        concurrency: int = 10

        name: Optional[str] = None
            If present, will return the task with task_id == name.
            If no match found, will return the task with task name == name

        Returns
        -----------
        List[Dict]
            [{"taskId": str, "name": str, "createdAt": str}]
        """
        my_iter = PaginationIterator(
            partial(
                self.context.export.task_search,
                self.org_id,
                self.project_id,
                self.output_stage_name if only_ground_truth else None,
                name,
                None,
                concurrency,
            )
        )

        with tqdm.tqdm(my_iter, unit=" datapoints") as progress:
            datapoints = [
                {
                    "taskId": task["taskId"],
                    "name": task["datapoint"]["name"],
                    "createdAt": task["createdAt"],
                }
                for task in progress
                if (task.get("datapoint", {}) or {}).get("name")
                and (not only_ground_truth or task["currentStageName"] == "END")
            ]

        return datapoints

    def get_task_events(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
    ) -> List[Dict]:
        """Get task history events log.

        Parameters
        -----------
        only_ground_truth: bool = True
            If set to True, will return events for tasks
            that have been completed in your workflow.

        concurrency: int = 10

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
            partial(
                self.context.export.task_events,
                self.org_id,
                self.project_id,
                self.output_stage_name if only_ground_truth else None,
                concurrency,
            )
        )

        with tqdm.tqdm(my_iter, unit=" datapoints") as progress:
            tasks = [
                task
                for task in progress
                if (not only_ground_truth or task["currentStageName"] == "END")
            ]

        return [task_event_format(task, users) for task in tasks]
