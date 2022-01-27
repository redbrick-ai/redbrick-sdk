"""Public API to exporting."""
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from functools import partial
import os
import json
import copy
from datetime import datetime

from shapely.geometry import Polygon  # type: ignore
from skimage.morphology import remove_small_holes  # type: ignore
import numpy as np  # type: ignore
from matplotlib import cm  # type: ignore
import tqdm  # type: ignore
from PIL import Image  # type: ignore

from redbrick.common.context import RBContext
from redbrick.common.enums import LabelType
from redbrick.utils.files import uniquify_path, download_files
from redbrick.utils.logging import (
    print_error,
    print_info,
    print_warning,
    handle_exception,
)
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_label_utils import clean_rb_label, flat_rb_format
from redbrick.coco.coco_main import coco_converter


def _parse_entry_latest(item: Dict) -> Dict:
    try:
        task_id = item["taskId"]
        task_data = item["latestTaskData"]
        datapoint = task_data["dataPoint"]
        items_presigned = datapoint["itemsPresigned"]
        items = datapoint["items"]
        name = datapoint["name"]
        created_by = task_data["createdByEmail"]
        labels = [
            clean_rb_label(label) for label in json.loads(task_data["labelsData"])
        ]

        return flat_rb_format(
            labels,
            items,
            items_presigned,
            name,
            created_by,
            task_id,
            item["currentStageName"],
            task_data["labelsPath"],
        )
    except (AttributeError, KeyError, TypeError, json.decoder.JSONDecodeError):
        return {}


def parse_output_entry(item: Dict) -> Dict:
    """Parse entry for output data."""
    try:
        items_presigned = item["itemsPresigned"]
        items = item["items"]
        name = item["name"]
        label_data = item["labelData"]
        created_by = label_data["createdByEmail"]
        labels = [
            clean_rb_label(label) for label in json.loads(label_data["labelsData"])
        ]
        task = item["task"]
        return flat_rb_format(
            labels,
            items,
            items_presigned,
            name,
            created_by,
            task["taskId"],
            "END",
            label_data["labelsPath"],
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
        self, context: RBContext, org_id: str, project_id: str, project_type: LabelType
    ) -> None:
        """Construct Export object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.project_type = project_type

    def _get_raw_data_ground_truth(self, concurrency: int) -> Tuple[List[Dict], Dict]:
        temp = self.context.export.get_datapoints_output

        my_iter = PaginationIterator(
            partial(temp, self.org_id, self.project_id, concurrency)
        )

        general_info = self.context.export.get_output_info(self.org_id, self.project_id)

        print_info("Downloading tasks")
        with tqdm.tqdm(
            my_iter, unit=" datapoints", total=general_info["datapointCount"]
        ) as progress:
            datapoints = []
            for val in progress:
                task = parse_output_entry(val)
                if task:
                    datapoints.append(task)
            disable = progress.disable
            progress.disable = False
            progress.update(general_info["datapointCount"] - progress.n)
            progress.disable = disable

        return datapoints, general_info["taxonomy"]

    def _get_raw_data_latest(
        self, concurrency: int, cache_time: Optional[datetime] = None
    ) -> Tuple[List[Dict], Dict]:
        temp = self.context.export.get_datapoints_latest

        my_iter = PaginationIterator(
            partial(temp, self.org_id, self.project_id, cache_time, concurrency)
        )

        general_info = self.context.export.get_output_info(self.org_id, self.project_id)
        datapoint_count = self.context.export.datapoints_in_project(
            self.org_id, self.project_id
        )

        print_info("Downloading tasks")

        with tqdm.tqdm(my_iter, unit=" datapoints", total=datapoint_count) as progress:
            datapoints = []
            for val in progress:
                task = _parse_entry_latest(val)
                if task:
                    datapoints.append(task)
            disable = progress.disable
            progress.disable = False
            progress.update(datapoint_count - progress.n)
            progress.disable = disable

        return datapoints, general_info["taxonomy"]

    def _get_raw_data_single(self, task_id: str) -> Tuple[List[Dict], Dict]:
        general_info = self.context.export.get_output_info(self.org_id, self.project_id)
        datapoint = self.context.export.get_datapoint_latest(
            self.org_id, self.project_id, task_id
        )
        datapoints = []
        task = _parse_entry_latest(datapoint)
        if task:
            datapoints.append(task)
        return datapoints, general_info["taxonomy"]

    @staticmethod
    def _get_color(class_id: int) -> Any:
        """Get a color from class id."""
        if class_id > 20:
            color = (
                np.array(cm.tab20b(int(class_id))) * 255  # pylint: disable=no-member
            )
            return color.astype(np.uint8)

        color = np.array(cm.tab20c(int(class_id))) * 255  # pylint: disable=no-member
        return color.astype(np.uint8)

    @staticmethod
    def tax_class_id_mapping(
        taxonomy: Dict, class_id: Dict, color_map: Optional[Dict] = None
    ) -> None:
        """Create a class mapping from taxonomy categories to class_id."""
        for category in taxonomy:
            class_id[category["name"]] = category["classId"] + 1

            # Create a color map
            if color_map is not None:
                color_map[category["name"]] = Export._get_color(category["classId"])[
                    0:3
                ].tolist()  # not doing +1 here.

            Export.tax_class_id_mapping(category["children"], class_id, color_map)

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
    def convert_rbai_mask(  # pylint: disable=too-many-locals
        labels: List,
        class_id_map: Dict,
        fill_holes: bool = False,
        max_hole_size: int = 30,
    ) -> np.ndarray:
        """Convert rbai datapoint to a numpy mask."""
        try:
            import rasterio.features  # pylint: disable=import-error, import-outside-toplevel
        except Exception as error:
            print_error(
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

        for label in labels:
            class_id = class_id_map[label["category"][0][-1]]
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
            # - remove overlapping region values
            neg_idxs = np.where(region_mask < 0)
            region_mask[neg_idxs] = 100
            # - remove negative values from overlapping holes
            overlap_indexes = np.where(region_mask > class_id)
            region_mask[overlap_indexes] = 100

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
                color_mask[indexes] = Export._get_color(i - 1)[0:3]

        return color_mask

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
            taxonomy["categories"][0]["children"], class_id_map, color_map
        )

        # Convert rbai to png masks and save output
        dp_map = {}
        print_info("Converting to masks")

        for datapoint in tqdm.tqdm(datapoints):
            labels = [label for label in datapoint["labels"] if "pixel" in label]
            if not labels:
                print_warning(
                    f"No segmentation labels in task {datapoint['taskId']}, skipping"
                )
                continue

            filename = f"{datapoint['taskId']}.png"
            dp_map[filename] = datapoint["items"][0]

            color_mask = Export.convert_rbai_mask(
                labels, class_id_map, fill_holes, max_hole_size
            )

            # save png as 3 channel np.uint8 image
            pil_color_mask = Image.fromarray(color_mask.astype(np.uint8))
            pil_color_mask.save(os.path.join(mask_dir, filename))

        with open(class_map, "w", encoding="utf-8") as file_:
            json.dump(color_map, file_, indent=2)

        with open(datapoint_map, "w", encoding="utf-8") as file_:
            json.dump(dp_map, file_, indent=2)

    @handle_exception
    def redbrick_png(  # pylint: disable=too-many-locals
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
        fill_holes: bool = False,
        max_hole_size: int = 30,
    ) -> None:
        """
        Export segmentation labels as masks.

        Masks are exported to a local directory named after project_id.
        Please visit https://docs.redbrickai.com/python-sdk/reference#png-mask-formats
        to see an overview of the format of the exported masks.

        >>> project = redbrick.get_project(api_key, url, org_id, project_id)
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

        Warnings
        ----------
        redbrick_png only works for the following types - IMAGE_SEGMENTATION, IMAGE_MULTI

        """
        if self.project_type not in (
            LabelType.IMAGE_SEGMENTATION,
            LabelType.IMAGE_MULTI,
        ):
            print_error(
                f"Project type needs to be {LabelType.IMAGE_SEGMENTATION} or "
                + f"{LabelType.IMAGE_MULTI} for redbrick_png"
            )
            return

        if task_id:
            datapoints, taxonomy = self._get_raw_data_single(task_id)
        elif only_ground_truth:
            datapoints, taxonomy = self._get_raw_data_ground_truth(concurrency)
        else:
            datapoints, taxonomy = self._get_raw_data_latest(concurrency)

        # Create output directory
        output_dir = uniquify_path(self.project_id)
        mask_dir = os.path.join(output_dir, "masks")
        os.makedirs(mask_dir, exist_ok=True)
        print_info(f"Saving masks to {output_dir} directory")

        Export._export_png_mask_data(
            datapoints,
            taxonomy,
            mask_dir,
            os.path.join(output_dir, "class_map.json"),
            os.path.join(output_dir, "datapoint_map.json"),
            fill_holes,
            max_hole_size,
        )

    @staticmethod
    def _export_nifti_label_data(
        datapoints: List[Dict], nifti_dir: str, task_map: str
    ) -> None:
        files = []
        for datapoint in datapoints:
            files.append(
                (
                    datapoint["labelsPath"],
                    os.path.join(nifti_dir, f"{datapoint['taskId']}.nii"),
                )
            )
        loop = asyncio.get_event_loop()
        paths: List[Optional[str]] = loop.run_until_complete(download_files(files))

        tasks = [
            {
                "filePath": path,
                **{
                    key: value
                    for key, value in datapoint.items()
                    if key not in ("currentStageName", "labelsPath")
                },
            }
            for datapoint, path in zip(datapoints, paths)
        ]

        with open(task_map, "w", encoding="utf-8") as tasks_file:
            json.dump(tasks, tasks_file, indent=2)

    @handle_exception
    def redbrick_nifti(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
    ) -> None:
        """
        Export dicom segmentation labels in NIfTI-1 format.

        >>> project = redbrick.get_project(api_key, url, org_id, project_id)
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

        Warnings
        ----------
        redbrick_nifti only works for the following types - DICOM_SEGMENTATION

        """
        if self.project_type != LabelType.DICOM_SEGMENTATION:
            print_error(
                f"Project type needs to be {LabelType.DICOM_SEGMENTATION} "
                + "for redbrick_nifi"
            )
            return

        if task_id:
            datapoints, _ = self._get_raw_data_single(task_id)
        elif only_ground_truth:
            datapoints, _ = self._get_raw_data_ground_truth(concurrency)
        else:
            datapoints, _ = self._get_raw_data_latest(concurrency)

        # Create output directory
        destination = uniquify_path(self.project_id)
        nifti_dir = os.path.join(destination, "nifti")
        os.makedirs(nifti_dir, exist_ok=True)
        print_info(f"Saving NIfTI files to {destination} directory")
        Export._export_nifti_label_data(
            datapoints, nifti_dir, os.path.join(destination, "tasks.json")
        )

    @handle_exception
    def redbrick_format(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Export data into redbrick format.

        >>> project = redbrick.get_project(api_key, url, org_id, project_id)
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

        Returns:
        -----------------
        List[Dict]
            Datapoint and labels in RedBrick AI format. See
            https://docs.redbrickai.com/python-sdk/reference
        """
        if task_id:
            datapoints, _ = self._get_raw_data_single(task_id)

        elif only_ground_truth:
            datapoints, _ = self._get_raw_data_ground_truth(concurrency)
        else:
            datapoints, _ = self._get_raw_data_latest(concurrency)

        return [
            {
                key: value
                for key, value in datapoint.items()
                if key not in ("currentStageName", "labelsPath")
            }
            for datapoint in datapoints
        ]

    @handle_exception
    def coco_format(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
    ) -> Dict:
        """
        Export project into coco format.

        >>> project = redbrick.get_project(api_key, url, org_id, project_id)
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
            print_error(
                f"Project type needs to be {LabelType.IMAGE_BBOX} or "
                + f"{LabelType.IMAGE_POLYGON} for redbrick_coco"
            )
            return {}

        if task_id:
            datapoints, taxonomy = self._get_raw_data_single(task_id)
        elif only_ground_truth:
            datapoints, taxonomy = self._get_raw_data_ground_truth(concurrency)
        else:
            datapoints, taxonomy = self._get_raw_data_latest(concurrency)

        return coco_converter(datapoints, taxonomy)
