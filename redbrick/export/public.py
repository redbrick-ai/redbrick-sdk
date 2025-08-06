"""Public API to exporting."""

import asyncio
import re
import shutil
from typing import Iterator, List, Dict, Optional, Sequence, Set, Tuple
from functools import partial
import os
import json
import copy
from datetime import datetime, timezone
from uuid import uuid4

import tqdm  # type: ignore

from redbrick.config import config
from redbrick.common.entities import RBProject
from redbrick.common.enums import ReviewStates, TaskFilters, TaskStates
from redbrick.common.export import Export, TaskFilterParams
from redbrick.stage import LabelStage, ReviewStage
from redbrick.types.taxonomy import Taxonomy
from redbrick.utils.common_utils import config_path, get_color
from redbrick.utils.files import (
    DICOM_FILE_TYPES,
    IMAGE_FILE_TYPES,
    NIFTI_FILE_TYPES,
    VIDEO_FILE_TYPES,
    contains_altadb_item,
    download_files,
    download_files_altadb,
    is_altadb_item,
    uniquify_path,
)
from redbrick.utils.labels import process_labels
from redbrick.utils.logging import log_error, logger
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_label_utils import (
    dicom_rb_format,
    parse_entry_latest,
    user_format,
    assignee_format,
)
from redbrick.utils.rb_event_utils import task_event_format
from redbrick.types.task import OutputTask, Series


# pylint: disable=too-many-lines


class ExportImpl(Export):
    """
    Primary interface for various export methods.

    The export module has many functions for exporting annotations and meta-data from projects. The export module is available from the :attr:`redbrick.RBProject` module.

    .. code:: python

        >>> project = redbrick.get_project(api_key="", org_id="", project_id="")
        >>> project.export # Export
    """

    def __init__(self, project: RBProject) -> None:
        """Construct Export object."""
        self.project = project
        self.context = self.project.context

    def get_raw_data_latest(
        self,
        concurrency: int,
        stage_name: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        presign_items: bool = False,
        with_consensus: bool = False,
        task_id: Optional[str] = None,
    ) -> Iterator[Dict]:
        """Get raw task data."""
        # pylint: disable=too-many-locals
        if task_id:
            logger.info(f"Fetching task: {task_id}")
            val = self.context.export.get_datapoint_latest(
                self.project.org_id,
                self.project.project_id,
                task_id,
                presign_items,
                with_consensus,
            )
            task = parse_entry_latest(val)
            yield task
            return

        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.get_datapoints_latest,
                self.project.org_id,
                self.project.project_id,
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
            color_map[key] = get_color(
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
                category["classId"],
            )
            ExportImpl.tax_class_id_mapping(
                trail, category["children"], class_id, color_map, taxonomy_color
            )

    @staticmethod
    def _get_task_series(task: OutputTask) -> List[Series]:
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
        original_task: OutputTask,
        storage_id: str,
        taxonomy: Taxonomy,
        image_dir: str,
        dcm_to_nii: bool,
        rt_struct: bool,
        dicom_seg: bool,
        semantic_mask: bool,
    ) -> OutputTask:
        # pylint: disable=too-many-locals, import-outside-toplevel, too-many-nested-blocks
        task, series_dirs = await self._download_task_items(
            original_task,
            storage_id,
            image_dir,
            taxonomy,
            rt_struct,
            dicom_seg,
            semantic_mask,
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

        task_series = ExportImpl._get_task_series(task)
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
                                (
                                    series["segmentations"]
                                    if isinstance(series["segmentations"], str)
                                    else series["segmentations"][0]
                                )
                                if "segmentations" in series
                                else ""
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
        task: OutputTask,
        storage_id: str,
        parent_dir: str,
        taxonomy: Taxonomy,
        rt_struct: bool,
        dicom_seg: bool,
        semantic_mask: bool,
    ) -> Tuple[OutputTask, List[str]]:
        # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        # pylint: disable=import-outside-toplevel
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
            task_series = ExportImpl._get_task_series(task)
            if task_series:
                for series_idx, series in enumerate(task_series):
                    series_dir = os.path.join(
                        task_dir,
                        re.sub(path_pattern, "-", series.get("name", "") or "")
                        or chr(series_idx + ord("A")),
                    )

                    if os.path.exists(series_dir) and not os.path.isdir(series_dir):
                        os.remove(series_dir)

                    os.makedirs(series_dir, exist_ok=True)
                    series_dirs.append(series_dir)
                    items_lists.append(
                        (
                            [series["items"]]
                            if isinstance(series["items"], str)
                            else series["items"]
                        )
                        if "items" in series
                        else []
                    )
            else:
                series_dir = os.path.join(task_dir, "A")
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
                self.project.org_id, storage_id, to_presign
            )

            if any(not presigned_path for presigned_path in presigned):
                raise Exception("Failed to presign some files")

            presigned_altadb: List[str] = []
            local_files_altadb: List[str] = []
            pos = len(presigned) - 1
            while pos >= 0:
                if presigned[pos] and is_altadb_item(presigned[pos] or ""):
                    presigned_altadb.append(presigned[pos] or "")
                    local_files_altadb.append(local_files[pos])
                    del presigned[pos]
                    del local_files[pos]
                pos -= 1

            downloaded = await download_files(
                list(zip(presigned, local_files)), "Downloading files", False
            )

            if any(not downloaded_file for downloaded_file in downloaded):
                raise Exception("Failed to download some files")

            downloaded_altadb = await download_files_altadb(
                list(zip(presigned_altadb, local_files_altadb)),
                "Downloading files",
                False,
            )

            if any(not downloaded_files for downloaded_files in downloaded_altadb):
                raise Exception("Failed to download some files")

            if task_series:
                series_items: List[List[Optional[str]]] = []
                prev_count = 0
                for series_dir, series in zip(series_dirs, task_series):
                    prev_series_items: List[str] = (
                        [series["items"]]  # type: ignore
                        if isinstance(series.get("items"), str)
                        else series["items"]  # type: ignore
                    )
                    count = 0
                    if contains_altadb_item(prev_series_items):
                        series_items.append(downloaded_altadb.pop(0))  # type: ignore
                    else:
                        count = len(prev_series_items) if "items" in series else 0
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

                if taxonomy.get("isNew") and (rt_struct or dicom_seg):
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

                        if dicom_seg:
                            from redbrick.utils.dicom_seg import (
                                convert_nii_to_dicom_seg,
                            )

                            for idx, segmentation in enumerate(segmentations):
                                seg = convert_nii_to_dicom_seg(
                                    segmentation,
                                    series_dir,
                                    taxonomy.get("objectTypes", []) or [],
                                    series.get("segmentMap", {}) or {},
                                    series.get("binaryMask", False),
                                )
                                for inst in (series.get("segmentMap") or {}).keys():
                                    if isinstance(
                                        series["segmentMap"][inst], dict  # type: ignore
                                    ) and (
                                        series["segmentMap"][inst].get("mask")  # type: ignore
                                        == segmentation
                                    ):
                                        if seg:
                                            series["segmentMap"][inst]["mask"] = seg  # type: ignore
                                        else:
                                            del series["segmentMap"][inst]["mask"]  # type: ignore

                                if idx == 0 and isinstance(
                                    series.get("segmentations"), str
                                ):
                                    if seg:
                                        series["segmentations"] = seg
                                    else:
                                        del series["segmentations"]
                                else:
                                    series["segmentations"][idx] = seg  # type: ignore

                            if isinstance(series.get("segmentations"), list):
                                series["segmentations"] = [
                                    seg for seg in series["segmentations"] if seg  # type: ignore
                                ]
                                if not series["segmentations"]:
                                    del series["segmentations"]
                        else:
                            from redbrick.utils.rt_struct import (
                                convert_nii_to_rt_struct,
                            )

                            rtstruct, new_segment_map = await convert_nii_to_rt_struct(
                                segmentations,
                                series_dir,
                                taxonomy.get("objectTypes", []) or [],
                                series.get("segmentMap", {}) or {},
                                series.get("semanticMask", semantic_mask),
                                series.get("binaryMask", False),
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
                task["items"] = [  # type: ignore
                    altadb_file
                    for altadb_files in downloaded_altadb
                    for altadb_file in altadb_files or []
                ] + downloaded

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
        mhd_mask: bool,
        taxonomy: Taxonomy,
    ) -> OutputTask:
        """Process labels."""
        # pylint: disable=too-many-locals
        task = copy.deepcopy(datapoint)
        files: List[Tuple[Optional[str], Optional[str]]] = []
        labels_map: Sequence[Optional[Dict]] = []

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
                if label_map and label_map.get("seriesIndex") is not None:
                    index = label_map["seriesIndex"]
                elif label_map and label_map.get("imageIndex") is not None:
                    index = image_index_map[label_map["imageIndex"]]
                else:
                    index = idx
                labels_map[index] = label_map

        else:
            labels_map = task.get("labelsMap", []) or []

        presign_label_paths: List[Optional[str]] = [
            task["labelsDataPath"] if task.get("labelsDataPath") else None
        ]

        presign_paths: List[Optional[str]] = [
            label_map.get("labelName") if label_map else None
            for label_map in labels_map
        ]
        len_map = len(presign_paths)

        if task.get("consensusTasks"):
            for consensus_task in task["consensusTasks"]:
                presign_label_paths.append(
                    consensus_task["labelsDataPath"]
                    if consensus_task.get("labelsDataPath")
                    else None
                )
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
                            consensus_task.get("labelsMap") or ([None] * len_map)
                        )
                    ]
                )

        if any(presign_label_path for presign_label_path in presign_label_paths):
            await self.download_labels(task, taxonomy, presign_label_paths)

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
                mhd_mask,
                bool(taxonomy.get("isNew")),
            )

        return dicom_rb_format(
            task,
            taxonomy,
            old_format,
            no_consensus,
            [stage for stage in self.project.stages if isinstance(stage, ReviewStage)],
            segmentation_dir is None,
        )

    async def download_labels(
        self, task: Dict, taxonomy: Taxonomy, presign_paths: List[Optional[str]]
    ) -> None:
        """Download labels."""
        if not presign_paths:
            return

        presigned_urls = self.context.export.presign_items(
            self.project.org_id, task["labelStorageId"], presign_paths
        )

        dirname = os.path.join(config_path(), "temp", str(uuid4()))
        os.makedirs(dirname, exist_ok=True)

        to_download: List[Tuple[Optional[str], Optional[str]]] = [
            (presign_path, uniquify_path(os.path.join(dirname, f"label-{idx}.nii.gz")))
            for idx, presign_path in enumerate(presigned_urls)
            if presign_path
        ]
        downloaded = await download_files(to_download, "Downloading labels", False)

        if presigned_urls[0] and downloaded[0]:
            with open(downloaded[0], "r", encoding="utf-8") as f_:
                task["labels"] = process_labels(json.load(f_), taxonomy)

        if len(presigned_urls) > 1:
            for idx in range(1, len(presigned_urls)):
                fpath = downloaded[idx]
                if presigned_urls[idx] and fpath:
                    with open(fpath, "r", encoding="utf-8") as f_:
                        task["consensusTasks"][idx]["labels"] = process_labels(
                            json.load(f_), taxonomy
                        )

        shutil.rmtree(dirname, ignore_errors=True)

    async def download_and_process_segmentations(
        self,
        task: Dict,
        presign_paths: List[Optional[str]],
        files: List[Tuple[Optional[str], Optional[str]]],
        segmentation_dir: Optional[str],
        has_series_info: bool,
        series_info: List[Dict],
        labels_map: Sequence[Optional[Dict]],
        image_index_map: Dict[int, int],
        color_map: Dict,
        semantic_mask: bool,
        binary_mask: Optional[bool],
        png_mask: bool,
        mhd_mask: bool,
        is_tax_v2: bool = True,
    ) -> None:
        """Download and process segmentations."""
        # pylint: disable=import-outside-toplevel, too-many-locals
        # pylint: disable=too-many-branches, too-many-statements
        from redbrick.utils.nifti import process_download

        presigned = self.context.export.presign_items(
            self.project.org_id, task["labelStorageId"], presign_paths
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
                series_names.append(
                    os.path.join(
                        task_dir,
                        re.sub(path_pattern, "-", series.get("name", "") or "")
                        or chr(series_idx + ord("A")),
                    )
                )
        else:
            series_names = [
                os.path.join(task_dir, chr(series_idx + ord("A")))
                for series_idx in range(len(labels_map) or 1)
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
                files, "Downloading segmentations", False, True, True
            )
        else:
            paths = list(list(zip(*files))[0])

        for label, path in zip(labels_map, paths):  # type: ignore
            if label and label.get("labelName"):
                label_map_data = await process_download(
                    task.get("labels", []) or [],
                    path,
                    png_mask,
                    color_map,
                    semantic_mask,
                    binary_mask,
                    mhd_mask,
                    (
                        image_index_map.get(label.get("imageIndex", -1))
                        if label.get("seriesIndex") is None
                        else label["seriesIndex"]
                    ),
                    is_tax_v2,
                )
                label["labelName"] = label_map_data["masks"]
                label["binaryMask"] = label_map_data["binary_mask"]
                label["semanticMask"] = label_map_data["semantic_mask"]
                label["pngMask"] = label_map_data["png_mask"]

        len_map = len(labels_map)
        if len(paths) > len_map and task.get("consensusTasks"):
            index = len_map
            for consensus_task in task["consensusTasks"]:
                consensus_labels = consensus_task.get("labels", []) or []
                consensus_labels_map = consensus_task.get("labelsMap") or (
                    [None] * len_map
                )
                for consensus_label_map in consensus_labels_map:
                    if not consensus_label_map:
                        index += 1
                        continue
                    label_map_data = await process_download(
                        consensus_labels,
                        paths[index],
                        png_mask,
                        color_map,
                        semantic_mask,
                        binary_mask,
                        mhd_mask,
                        (
                            image_index_map.get(consensus_label_map.get("imageIndex"))
                            if consensus_label_map.get("seriesIndex") is None
                            else consensus_label_map["seriesIndex"]
                        ),
                        is_tax_v2,
                    )
                    consensus_label_map["labelName"] = label_map_data["masks"]
                    consensus_label_map["binaryMask"] = label_map_data["binary_mask"]
                    consensus_label_map["semanticMask"] = label_map_data[
                        "semantic_mask"
                    ]
                    consensus_label_map["pngMask"] = label_map_data["png_mask"]
                    index += 1

    def preprocess_export(
        self, taxonomy: Taxonomy, get_color_map: bool
    ) -> Tuple[Dict, Dict]:
        """Get classMap and colorMap."""
        class_map: Dict = {}
        color_map: Dict = {}
        if get_color_map:
            if bool(taxonomy.get("isNew")):
                object_types = taxonomy.get("objectTypes", []) or []
                for object_type in object_types:
                    if object_type["labelType"] == "SEGMENTATION":
                        color = get_color(object_type["color"])  # type: ignore
                        color_map[object_type["classId"]] = color

                        category: str = object_type["category"]
                        if category in class_map:  # rare case
                            category += f' ({object_type["classId"]})'
                        class_map[category] = color
            else:
                ExportImpl.tax_class_id_mapping(
                    [taxonomy["categories"][0]["name"]],  # type: ignore
                    taxonomy["categories"][0]["children"],  # type: ignore
                    {},
                    color_map,
                    taxonomy.get("colorMap"),  # type: ignore
                )
                class_map = color_map

        return class_map, color_map

    async def export_nifti_label_data(
        self,
        datapoint: Dict,
        taxonomy: Taxonomy,
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
        dicom_seg: bool,
        mhd_mask: bool,
        get_task: bool,
    ) -> Optional[OutputTask]:
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
            mhd_mask,
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
                    dicom_seg,
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
        dicom_seg: bool = False,
        mhd: bool = False,
        destination: Optional[str] = None,
    ) -> Iterator[OutputTask]:
        """Export annotation data.

        Meta-data and category information returned as an Object. Segmentations are written to
        your disk in NIfTI-1 format. Please `visit our
        documentation <https://sdk.redbrickai.com/formats/index.html#export>`_
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

        dicom_seg: bool = False
            Export labels as DICOM Segmentation. (Only for DICOM images)

        mhd: bool = False
            Export segmentation masks in MHD format.

        destination: Optional[str] = None
            Destination directory (Default: current directory)

        Returns
        -----------
        Iterator[:obj:`~redbrick.types.task.OutputTask`]
            Datapoint and labels in RedBrick AI format. See
            https://sdk.redbrickai.com/formats/index.html#export


        .. note:: If both `semantic_mask` and `binary_mask` options are True,
            then one binary mask will be generated per class.
        """
        # pylint: disable=too-many-locals

        no_consensus = (
            no_consensus
            if no_consensus is not None
            else not self.project.is_consensus_enabled
        )

        # Create output directory
        destination = destination or self.project.project_id

        image_dir: Optional[str] = None
        if with_files or rt_struct or dicom_seg:
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

        coloured_png = png and not binary_mask
        class_map, color_map = self.preprocess_export(
            self.project.taxonomy, coloured_png
        )

        if coloured_png:
            with open(
                os.path.join(destination, "class_map.json"), "w", encoding="utf-8"
            ) as classes_file:
                json.dump(class_map, classes_file, indent=2)

        datapoints = self.get_raw_data_latest(
            concurrency,
            "END" if only_ground_truth else stage_name,
            None if task_id else from_timestamp,
            True,
            not no_consensus,
            task_id,
        )

        if task_file and os.path.isfile(task_file):
            os.remove(task_file)

        for datapoint in datapoints:
            task: OutputTask = asyncio.run(
                self.export_nifti_label_data(  # type: ignore
                    datapoint,
                    self.project.taxonomy,
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
                    dicom_seg,
                    mhd,
                    True,
                )
            )
            yield task

        if task_file and not os.path.isfile(task_file):
            with open(task_file, "w", encoding="utf-8") as task_file_:
                task_file_.write("[]")

    def list_tasks(
        self,
        *,
        concurrency: int = 10,
        limit: Optional[int] = 50,
        search: Optional[TaskFilters] = None,
        stage_name: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        exact_match: bool = False,
        completed_at: Optional[Tuple[Optional[float], Optional[float]]] = None,
    ) -> Iterator[Dict]:
        """
        Search tasks based on multiple queries for a project.
        This function returns minimal meta-data about the queried tasks.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> result = project.export.list_tasks()

        Parameters
        -----------
        concurrency: int = 10
            The number of requests that will be made in parallel.

        limit: Optional[int] = 50
            The number of tasks to return.
            Use None to return all tasks matching the search query.

        search: Optional[:obj:`~redbrick.common.enums.TaskFilters`] = None
            Task filter type. (Default: TaskFilters.ALL)

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

        exact_match: bool = False
            Applicable when searching for tasks by task_name.
            If True, will do a full match instead of partial match.

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
                "storageId": str,
                "updatedAt": str,
                "currentStageName": str,
                "createdBy"?: {"userId": str, "email": str},
                "priority"?: float([0, 1]),
                "metaData"?: dict,
                "series"?: [{"name"?: str, "metaData"?: dict}],
                "assignees"?: [{
                    "user": str,
                    "status": TaskStates,
                    "assignedAt": datetime,
                    "lastSavedAt"?: datetime,
                    "completedAt"?: datetime,
                    "timeSpentMs"?: float,
                }]
            }]
        """
        # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        search = search or (
            TaskFilters.ALL
            if stage_name is None
            else (TaskFilters.QUEUED if completed_at is None else TaskFilters.COMPLETED)
        )

        stages = self.project.stages
        label_stages: List[str] = [
            stage.stage_name for stage in stages if isinstance(stage, LabelStage)
        ]
        review_stages: List[str] = [
            stage.stage_name for stage in stages if isinstance(stage, ReviewStage)
        ]
        all_stages: List[str] = (
            label_stages + review_stages + [self.project.output_stage_name]
        )

        filters: TaskFilterParams = TaskFilterParams()

        if user_id:
            filters["userId"] = user_id

        if task_id:
            filters["taskId"] = task_id
            task_name = task_id
        elif task_name:
            if exact_match:
                task_name = '"' + task_name.strip('"') + '"'

        if search == TaskFilters.ALL:
            stage_name = None
            filters.pop("userId", None)
        elif search == TaskFilters.GROUNDTRUTH:
            stage_name = self.project.output_stage_name
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
        else:
            raise ValueError(f"Invalid task filter: {search}")

        members = self.context.member.list_org_members(self.project.org_id, False)

        users = {}
        for member in members:
            user = member.get("user", {})
            if user.get("userId") and user.get("email"):
                users[user["userId"]] = user["email"]

        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.task_search,
                self.project.org_id,
                self.project.project_id,
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

            if datapoint.get("storageMethod"):
                task_obj["storageId"] = datapoint["storageMethod"].get("storageId")

            if task["updatedAt"]:
                task_obj["updatedAt"] = task["updatedAt"]

            if datapoint.get("createdByEntity"):
                task_obj["createdBy"] = user_format(datapoint["createdByEntity"], users)
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
                "taskId": str,
                "currentStageName": str,
                "events": List[Dict]
            }]
        """
        # pylint: disable=too-many-locals
        members = self.context.member.list_org_members(self.project.org_id, False)

        users = {}
        for member in members:
            user = member.get("user", {})
            if user.get("userId") and user.get("email"):
                users[user["userId"]] = user["email"]

        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.task_events,
                self.project.org_id,
                self.project.project_id,
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

        with tqdm.tqdm(my_iter, unit=" datapoints", leave=config.log_info) as progress:
            for task in progress:
                task = task_event_format(task, users, with_labels)
                for event in task["events"]:
                    if "labels" not in event:
                        continue
                    labels = dicom_rb_format(
                        event["labels"],
                        self.project.taxonomy,
                        False,
                        True,
                        [
                            stage
                            for stage in self.project.stages
                            if isinstance(stage, ReviewStage)
                        ],
                        True,
                    )
                    event["labels"] = {"series": labels.get("series") or []}
                    if (
                        "classification" in labels
                        and labels.get("classification") is not None
                    ):
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
        members = self.context.member.list_org_members(self.project.org_id, False)

        users = {}
        for member in members:
            user = member.get("user", {})
            if user.get("userId") and user.get("email"):
                users[user["userId"]] = user["email"]

        my_iter = PaginationIterator(
            partial(  # type: ignore
                self.context.export.active_time,
                self.project.org_id,
                self.project.project_id,
                stage_name,
                task_id,
            ),
            concurrency,
        )

        with tqdm.tqdm(my_iter, unit=" datapoints", leave=config.log_info) as progress:
            for task in progress:
                yield {
                    "orgId": self.project.org_id,
                    "projectId": self.project.project_id,
                    "stageName": stage_name,
                    "taskId": task["taskId"],
                    "completedBy": user_format(task["user"], users),
                    "timeSpent": task["timeSpent"],
                    "completedAt": task["date"],
                    "cycle": task["cycle"],
                }
