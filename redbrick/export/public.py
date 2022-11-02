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
from shapely.geometry import Polygon  # type: ignore
from skimage.morphology import remove_small_holes  # type: ignore
import numpy as np  # type: ignore
from matplotlib import cm  # type: ignore
import tqdm  # type: ignore
from PIL import Image  # type: ignore

from redbrick.common.constants import MAX_CONCURRENCY
from redbrick.common.context import RBContext
from redbrick.common.enums import LabelType
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.files import uniquify_path, download_files
from redbrick.utils.logging import log_error, logger
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_label_utils import (
    clean_rb_label,
    dicom_rb_format,
    flat_rb_format,
)
from redbrick.coco.coco_main import coco_converter

# pylint: disable=too-many-lines


def _parse_entry_latest(item: Dict) -> Dict:
    try:
        task_id = item["taskId"]
        task_data = item["latestTaskData"]
        datapoint = task_data["dataPoint"]
        items = datapoint["items"]
        items_presigned = datapoint.get("itemsPresigned", []) or []
        name = datapoint["name"]
        created_by = (datapoint.get("createdByEntity", {}) or {}).get("email")
        created_at = datapoint["createdAt"]
        updated_by = task_data["createdByEmail"]
        updated_at = task_data["createdAt"]
        labels = [
            clean_rb_label(label) for label in json.loads(task_data["labelsData"])
        ]
        storage_id = datapoint["storageMethod"]["storageId"]
        label_storage_id = task_data["labelsStorage"]["storageId"]

        return flat_rb_format(
            labels,
            items,
            items_presigned,
            name,
            created_by,
            created_at,
            updated_by,
            updated_at,
            task_id,
            item["currentStageName"],
            task_data.get("labelsMap", []) or [],
            datapoint.get("seriesInfo"),
            json.loads(datapoint["metaData"]) if datapoint.get("metaData") else None,
            storage_id,
            label_storage_id,
            item.get("currentStageSubTask"),
        )
    except (AttributeError, KeyError, TypeError, json.decoder.JSONDecodeError):
        return {}


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
        project_type: LabelType,
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
        self.project_type = project_type
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
                task = _parse_entry_latest(val)
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
                tasks.append(_parse_entry_latest(val))
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
        # pylint: disable=no-member
        if color_hex:
            color_hex = color_hex.lstrip("#")
            return [int(color_hex[i : i + 2], 16) for i in (0, 2, 4)]
        color = (
            np.array(
                cm.tab20b(int(class_id))  # type: ignore
                if class_id > 20
                else cm.tab20c(int(class_id))  # type: ignore
            )
            * 255
        )
        return color.astype(np.uint8)[0:3].tolist()

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
    def fill_mask_holes(mask: np.ndarray, max_hole_size: int) -> np.ndarray:
        """Fill holes."""
        mask_copy = copy.deepcopy(mask)

        # find indexes where mask has labels
        mask_greater_zero = np.where(mask > 0)

        # convery copy mask to binary
        mask_copy[mask_greater_zero] = 1

        # fill holes in copy binary mask
        mask_copy = remove_small_holes(
            mask_copy.astype(bool),
            area_threshold=max_hole_size,
        )
        mask_copy = mask_copy.astype(int)

        # set original pixel values
        mask_copy[mask_greater_zero] = mask[mask_greater_zero]

        # find indexes of holes, and fill with neighbor
        mask_hole_loc = np.where((mask == 0) & (mask_copy > 0))

        for i in range(len(mask_hole_loc[0])):
            mask_copy = Export.fill_hole_with_neighbor(
                mask_copy, mask_hole_loc[0][i], mask_hole_loc[1][i]
            )

        return mask_copy

    @staticmethod
    def fill_hole_with_neighbor(mask: np.ndarray, i: Any, j: Any) -> np.ndarray:
        """Fill a pixel in the mask with it's neighbors value."""
        row, col = mask.shape
        top = 0 if j - 1 < 0 else mask[i][j - 1]
        top_right = 0 if (j - 1 < 0) or (i + 1 == row) else mask[i + 1][j - 1]
        right = 0 if i + 1 == row else mask[i + 1][j]
        bottom_right = 0 if (j + 1 == col) or (i + 1 == row) else mask[i + 1][j + 1]
        bottom = 0 if j + 1 == col else mask[i][j + 1]
        bottom_left = 0 if (i - 1 < 0) or (j + 1 == col) else mask[i - 1][j + 1]
        left = 0 if i - 1 < 0 else mask[i - 1][j]
        top_left = 0 if (i - 1 < 0) or (j - 1 == 0) else mask[i - 1][j - 1]
        mask[i][j] = max(
            top,
            top_right,
            right,
            bottom_right,
            bottom,
            bottom_left,
            left,
            top_left,
        )
        return mask

    @staticmethod
    def convert_rbai_mask(
        labels: List,
        class_id_map: Dict,
        color_map: Dict,
        fill_holes: bool = False,
        max_hole_size: int = 30,
    ) -> np.ndarray:
        """Convert rbai datapoint to a numpy mask."""
        # pylint: disable=import-error, import-outside-toplevel, disable=too-many-locals
        try:
            import rasterio.features  # type: ignore
        except Exception as error:
            log_error(
                "For windows users, please follow the rasterio "
                + "documentation to properly install the module "
                + "https://rasterio.readthedocs.io/en/latest/installation.html "
                + "Rasterio is required by RedBrick SDK to work with masks."
            )
            raise error

        imagesize = labels[0]["pixel"]["imagesize"]

        # deal with condition where imagesize is returned as float
        imagesize = np.round(imagesize).astype(int)  # type: ignore

        mask = np.zeros([imagesize[1], imagesize[0]])
        class_id_reverse = {
            class_id: category for category, class_id in class_id_map.items()
        }
        for label in labels:
            class_id = class_id_map["::".join(label["category"][0][1:])]
            regions = copy.deepcopy(label["pixel"]["regions"])
            holes = copy.deepcopy(label["pixel"]["holes"])
            imagesize = label["pixel"]["imagesize"]

            # deal with condition where imagesize is returned as float
            imagesize = np.round(imagesize).astype(int)  # type: ignore

            # iterate through regions, and create region mask
            region_mask = np.zeros([imagesize[1], imagesize[0]])
            if regions and len(regions) > 0:
                for region in regions:
                    if (
                        len(np.array(region).shape) == 1
                        or np.array(region).shape[0] < 3
                    ):
                        # Don't add empty regions to the mask
                        # Don't add regions with < 3 vertices
                        break

                    # convert polygon to mask
                    region_polygon = Polygon(region)
                    single_region_mask = (
                        rasterio.features.rasterize(
                            [region_polygon],
                            out_shape=(imagesize[1], imagesize[0]),
                        ).astype(float)
                        * class_id
                    )

                    # add single region to root region mask
                    region_mask += single_region_mask

            # iterate through holes, and create hole mask
            hole_mask = np.zeros([imagesize[1], imagesize[0]])
            if holes and len(holes) > 0:
                for hole in holes:
                    if len(np.array(hole).shape) == 1 or np.array(hole).shape[0] < 3:
                        # Don't add empty hole to negative mask
                        # Don't add holes with < 3 vertices
                        break

                    # convert polygon hole to mask
                    hole_polygon = Polygon(hole)
                    single_hole_mask = (
                        rasterio.features.rasterize(
                            [hole_polygon],
                            out_shape=(imagesize[1], imagesize[0]),
                        ).astype(float)
                        * class_id
                    )

                    # add single hole mask to total hole mask
                    hole_mask += single_hole_mask

            # subtract the hole mask from region mask
            region_mask -= hole_mask

            # cleanup:
            # - remove negative values from overlapping holes
            neg_idxs = np.where(region_mask < 0)
            region_mask[neg_idxs] = 0
            # - remove overlapping region values
            overlap_indexes = np.where(region_mask > class_id)
            region_mask[overlap_indexes] = class_id

            # merge current object to main mask
            class_idx_not_zero = np.where(region_mask != 0)
            mask[class_idx_not_zero] = region_mask[class_idx_not_zero]

            # fill all single pixel holes
            if fill_holes:
                mask = Export.fill_mask_holes(mask, max_hole_size)

            # convert 2d mask into 3d mask with colors
            color_mask = np.zeros((mask.shape[0], mask.shape[1], 3))
            class_ids = np.unique(mask)  # type: ignore
            for i in class_ids:
                if i == 0:
                    # don't add color to background
                    continue
                indexes = np.where(mask == i)
                color_mask[indexes] = color_map[class_id_reverse[i]]

        return color_mask  # type: ignore

    @staticmethod
    def _export_png_mask_data(
        datapoints: List[Dict],
        taxonomy: Dict,
        mask_dir: str,
        class_map: str,
        datapoint_map: str,
        fill_holes: bool = False,
        max_hole_size: int = 30,
    ) -> None:
        """Export png masks and map json."""
        # pylint: disable=too-many-locals
        # Create a color map from the taxonomy
        class_id_map: Dict = {}
        color_map: Dict = {}
        Export.tax_class_id_mapping(
            [taxonomy["categories"][0]["name"]],  # object
            taxonomy["categories"][0]["children"],  # categories
            class_id_map,
            color_map,
            taxonomy.get("colorMap"),
        )

        # Convert rbai to png masks and save output
        dp_map = {}
        logger.info("Converting to masks")

        for datapoint in tqdm.tqdm(datapoints):
            labels = [label for label in datapoint["labels"] if "pixel" in label]
            if not labels:
                logger.warning(
                    f"No segmentation labels in task {datapoint['taskId']}, skipping"
                )
                continue

            filename = f"{datapoint['taskId']}.png"
            dp_map[filename] = datapoint["items"][0]

            color_mask = Export.convert_rbai_mask(
                labels, class_id_map, color_map, fill_holes, max_hole_size
            )

            # save png as 3 channel np.uint8 image
            pil_color_mask = Image.fromarray(color_mask.astype(np.uint8))
            pil_color_mask.save(os.path.join(mask_dir, filename))

        with open(class_map, "w", encoding="utf-8") as file_:
            json.dump(color_map, file_, indent=2)

        with open(datapoint_map, "w", encoding="utf-8") as file_:
            json.dump(dp_map, file_, indent=2)

    def redbrick_png(  # pylint: disable=too-many-locals
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
        fill_holes: bool = False,
        max_hole_size: int = 30,
        from_timestamp: Optional[float] = None,
        to_timestamp: Optional[float] = None,
    ) -> None:
        """
        Export segmentation labels as masks.

        Masks are exported to a local directory named after project_id.
        Please visit https://docs.redbrickai.com/python-sdk/reference#png-mask-formats
        to see an overview of the format of the exported masks.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> project.export.redbrick_png()

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

        fill_holes : bool = False
            If set to True, will fill any holes in your segmentation
            masks.

        max_hole_size: int = 10
            If fill_holes = True, this parameter defines the maximum
            size hole, in pixels, to fill.

        from_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated since the given timestamp.
            Format - output from datetime.timestamp()

        to_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated till the given timestamp.
            Format - output from datetime.timestamp()

        Warnings
        ----------
        redbrick_png only works for the following types - IMAGE_SEGMENTATION, IMAGE_MULTI

        """
        if self.project_type not in (
            LabelType.IMAGE_SEGMENTATION,
            LabelType.IMAGE_MULTI,
        ):
            log_error(
                f"Project type needs to be {LabelType.IMAGE_SEGMENTATION} or "
                + f"{LabelType.IMAGE_MULTI} for redbrick_png"
            )
            return

        datapoints, taxonomy = self._get_raw_data_latest(
            concurrency,
            False if task_id else only_ground_truth,
            None if task_id else from_timestamp,
            None if task_id else to_timestamp,
        )

        if task_id:
            datapoints = [
                datapoint for datapoint in datapoints if datapoint["taskId"] == task_id
            ]

        # Create output directory
        output_dir = uniquify_path(self.project_id)
        mask_dir = os.path.join(output_dir, "masks")
        os.makedirs(mask_dir, exist_ok=True)
        logger.info(f"Saving masks to {output_dir} directory")

        Export._export_png_mask_data(
            datapoints,
            taxonomy,
            mask_dir,
            os.path.join(output_dir, "class_map.json"),
            os.path.join(output_dir, "datapoint_map.json"),
            fill_holes,
            max_hole_size,
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
        # pylint: disable=import-outside-toplevel, too-many-locals, too-many-branches
        from redbrick.utils.dicom import process_nifti_download

        task = copy.deepcopy(datapoint)
        files: List[Tuple[Optional[str], Optional[str]]] = []
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
        if sum(
            map(
                lambda val: len(val.get("itemsIndices", []) or []) if val else 0,
                task.get("seriesInfo", []) or [],
            )
        ) == len(task["items"]) and (
            len(task["seriesInfo"]) > 1 or task["seriesInfo"][0].get("name")
        ):
            for series_idx, series in enumerate(task["seriesInfo"]):
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
            files, "Downloading nifti labels", False, True, True
        )

        for label, path in zip(labels_map, paths):
            label["labelName"] = process_nifti_download(
                task.get("labels", []) or [], path, png_mask, color_map, is_tax_v2
            )

        if len(paths) > len(labels_map) and task.get("consensusTasks"):
            index = len(labels_map)
            for consensus_task in task["consensusTasks"]:
                consensus_labels = consensus_task.get("labels", []) or []
                consensus_labels_map = consensus_task.get("labelsMap", []) or []
                for consensus_label_map in consensus_labels_map:
                    consensus_label_map["labelName"] = process_nifti_download(
                        consensus_labels, paths[index], png_mask, color_map, is_tax_v2
                    )
                    index += 1

        return dicom_rb_format(task, old_format, no_consensus)

    def export_nifti_label_data(
        self,
        datapoints: List[Dict],
        taxonomy: Dict,
        nifti_dir: str,
        task_map: str,
        class_map_file: str,
        old_format: bool,
        no_consensus: bool,
        png_mask: bool,
    ) -> None:
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

        with open(task_map, "w", encoding="utf-8") as tasks_file:
            json.dump(tasks, tasks_file, indent=2)

        if png_mask:
            with open(class_map_file, "w", encoding="utf-8") as classes_file:
                json.dump(class_map, classes_file, indent=2)

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
    ) -> None:
        """
        Export dicom segmentation labels in NIfTI-1 format.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> project.export.redbrick_nifti()

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

        Warnings
        ----------
        redbrick_nifti only works for the following types - DICOM_SEGMENTATION

        """
        if self.project_type != LabelType.DICOM_SEGMENTATION:
            log_error(
                f"Project type needs to be {LabelType.DICOM_SEGMENTATION} "
                + "for redbrick_nifti"
            )
            return

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
        self.export_nifti_label_data(
            datapoints,
            taxonomy,
            nifti_dir,
            os.path.join(destination, "tasks.json"),
            os.path.join(destination, "class_map.json"),
            old_format,
            no_consensus,
            png,
        )

    def redbrick_format(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        to_timestamp: Optional[float] = None,
    ) -> List[Dict]:
        """
        Export data into redbrick format.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> result = project.export.redbrick_format()

        Parameters
        -----------------
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

        Returns:
        -----------------
        List[Dict]
            Datapoint and labels in RedBrick AI format. See
            https://docs.redbrickai.com/python-sdk/reference
        """
        datapoints, _ = self._get_raw_data_latest(
            concurrency,
            False if task_id else only_ground_truth,
            None if task_id else from_timestamp,
            None if task_id else to_timestamp,
            True,
        )

        if task_id:
            datapoints = [
                datapoint for datapoint in datapoints if datapoint["taskId"] == task_id
            ]

        return [
            {
                key: value
                for key, value in datapoint.items()
                if key not in ("labelsMap", "seriesInfo", "storageId", "labelStorageId")
            }
            for datapoint in datapoints
        ]

    def coco_format(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
        from_timestamp: Optional[float] = None,
        to_timestamp: Optional[float] = None,
    ) -> Dict:
        """
        Export project into coco format.

        >>> project = redbrick.get_project(org_id, project_id, api_key, url)
        >>> result = project.export.coco_format()

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

        to_timestamp: Optional[float] = None
            If the timestamp is mentioned, will only export tasks
            that were labeled/updated till the given timestamp.
            Format - output from datetime.timestamp()

        Returns
        -----------
        List[Dict]
            Datapoint and labels in COCO format. See
            https://cocodataset.org/#format-data

        Warnings
        ----------
        redbrick_coco only works for the following types - IMAGE_BBOX, IMAGE_POLYGON
        """
        if self.project_type not in (LabelType.IMAGE_BBOX, LabelType.IMAGE_POLYGON):
            log_error(
                f"Project type needs to be {LabelType.IMAGE_BBOX} or "
                + f"{LabelType.IMAGE_POLYGON} for redbrick_coco"
            )
            return {}

        datapoints, taxonomy = self._get_raw_data_latest(
            concurrency,
            False if task_id else only_ground_truth,
            None if task_id else from_timestamp,
            None if task_id else to_timestamp,
            True,
        )

        if task_id:
            datapoints = [
                datapoint for datapoint in datapoints if datapoint["taskId"] == task_id
            ]

        return coco_converter(datapoints, taxonomy)

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
            [{"taskId", "name", "createdAt"}]
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
