"""Public API to exporting."""


from typing import List, Dict, Optional, Tuple, Any
from functools import partial
import os
import json
import copy

from shapely.geometry import Polygon  # type: ignore
import numpy as np  # type: ignore
import rasterio.features  # type: ignore
from matplotlib import cm  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import tqdm  # type: ignore

from redbrick.common.context import RBContext
from redbrick.utils.logging import print_error, print_info
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_label_utils import clean_rb_label, flat_rb_format
from redbrick.coco.coco_main import coco_converter


def _parse_entry_latest(item: Dict) -> Dict:
    history_obj = item["history"][0]
    task_id = item["taskId"]
    datapoint = history_obj["taskData"]["dataPoint"]
    items_presigned = datapoint["itemsPresigned"]
    items = datapoint["items"]
    name = datapoint["name"]
    dp_id = datapoint["dpId"]
    created_by = history_obj["taskData"]["createdByEmail"]
    labels = [clean_rb_label(label) for label in history_obj["taskData"]["labels"]]

    return flat_rb_format(
        labels, items, items_presigned, name, dp_id, created_by, task_id
    )


def parse_output_entry(item: Dict) -> Dict:
    """Parse entry for output data."""
    items_presigned = item["itemsPresigned"]
    items = item["items"]
    name = item["name"]
    dp_id = item["dpId"]
    created_by = item["labelData"]["createdByEmail"]
    labels = [clean_rb_label(label) for label in item["labelData"]["labels"]]
    task_id = item["task"]["taskId"]
    return flat_rb_format(
        labels, items, items_presigned, name, dp_id, created_by, task_id
    )


class Export:
    """Primary interface to handling export from a project."""

    def __init__(self, context: RBContext, org_id: str, project_id: str) -> None:
        """Construct Export object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id
        self.general_info: Dict = {}

    def _get_raw_data_ground_truth(self, concurrency: int) -> Tuple[List[Dict], Dict]:
        temp = self.context.export.get_datapoints_output

        my_iter = PaginationIterator(
            partial(temp, self.org_id, self.project_id, concurrency)
        )

        general_info = self.context.export.get_output_info(self.org_id, self.project_id)
        self.general_info = general_info

        print_info("Downloading tasks")
        return (
            [
                parse_output_entry(val)
                for val in tqdm.tqdm(
                    my_iter, unit=" datapoints", total=general_info["datapointCount"]
                )
            ],
            general_info["taxonomy"],
        )

    def _get_raw_data_latest(self, concurrency: int) -> Tuple[List[Dict], Dict]:
        temp = self.context.export.get_datapoints_latest

        my_iter = PaginationIterator(
            partial(temp, self.org_id, self.project_id, concurrency)
        )

        general_info = self.context.export.get_output_info(self.org_id, self.project_id)
        self.general_info = general_info
        datapoint_count = self.context.export.datapoints_in_project(
            self.org_id, self.project_id
        )

        print_info("Downloading tasks")
        return (
            [
                _parse_entry_latest(val)
                for val in tqdm.tqdm(my_iter, unit=" datapoints", total=datapoint_count)
            ],
            general_info["taxonomy"],
        )

    def _get_raw_data_single(self, task_id: str) -> Tuple[List[Dict], Dict]:
        general_info = self.context.export.get_output_info(self.org_id, self.project_id)
        self.general_info = general_info
        datapoint = self.context.export.get_datapoint_latest(
            self.org_id, self.project_id, task_id
        )
        return [_parse_entry_latest(datapoint)], general_info["taxonomy"]

    @staticmethod
    def get_color(class_id: int) -> Any:
        """Get a color from class id."""
        if class_id > 20:
            return cm.tab20b(int(class_id))  # pylint: disable=no-member

        return cm.tab20c(int(class_id))  # pylint: disable=no-member

    @staticmethod
    def uniquify_path(path: str) -> str:
        """Provide unique path with number index."""
        filename, extension = os.path.splitext(path)
        counter = 1

        while os.path.exists(path):
            path = filename + " (" + str(counter) + ")" + extension
            counter += 1

        return path

    @staticmethod
    def tax_class_id_mapping(
        taxonomy: Dict, class_id: Dict, color_map: Optional[Dict] = None
    ) -> None:
        """Create a class mapping from taxonomy categories to class_id."""
        for category in taxonomy:
            class_id[category["name"]] = category["classId"] + 1

            # Create a color map
            if color_map is not None:
                color_map[category["name"]] = Export.get_color(category["classId"])[
                    0:3
                ]  # not doing +1 here.

            Export.tax_class_id_mapping(category["children"], class_id, color_map)

    @staticmethod
    def convert_rbai_mask(  # pylint: disable=too-many-locals
        task: Dict, class_id_map: Dict
    ) -> np.ndarray:
        """Convert rbai datapoint to a numpy mask."""
        # 0 label task
        if len(task["labels"]) == 0:
            print_error("No labels")
            return np.array([])

        imagesize = task["labels"][0]["pixel"]["imagesize"]
        mask = np.zeros([imagesize[1], imagesize[0]])

        for label in task["labels"]:
            class_id = class_id_map[label["category"][0][-1]]
            regions = copy.deepcopy(label["pixel"]["regions"])
            holes = copy.deepcopy(label["pixel"]["holes"])
            imagesize = label["pixel"]["imagesize"]

            # iterate through regions, and create region mask
            region_mask = np.zeros([imagesize[1], imagesize[0]])
            if regions and len(regions) > 0:
                for region in regions:
                    if len(np.array(region).shape) == 1:
                        # Don't add empty regions to the mask
                        break

                    # convert polygon to mask
                    region_polygon = Polygon(region)
                    single_region_mask = (
                        rasterio.features.rasterize(
                            [region_polygon], out_shape=(imagesize[1], imagesize[0])
                        ).astype(float)
                        * class_id
                    )

                    # add single region to root region mask
                    region_mask += single_region_mask

            # iterate through holes, and create hole mask
            hole_mask = np.zeros([imagesize[1], imagesize[0]])
            if holes and len(holes) > 0:
                for hole in holes:
                    if len(np.array(hole).shape) == 1:
                        # Don't add empty hole to negative mask
                        break

                    # convert polygon hole to mask
                    hole_polygon = Polygon(hole)
                    single_hole_mask = (
                        rasterio.features.rasterize(
                            [hole_polygon], out_shape=(imagesize[1], imagesize[0])
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
            region_mask[neg_idxs] = 0
            # - remove negative values from overlapping holes
            overlap_indexes = np.where(region_mask > class_id)
            region_mask[overlap_indexes] = class_id

            # merge current object to main mask
            class_idx_not_zero = np.where(region_mask != 0)
            mask[class_idx_not_zero] = region_mask[class_idx_not_zero]

            # convert 2d mask into 3d mask with colors
            color_mask = np.zeros((mask.shape[0], mask.shape[1], 3))
            class_ids = np.unique(mask)  # type: ignore
            for i in class_ids:
                if i == 0:
                    # don't add color to background
                    continue
                indexes = np.where(mask == i)
                color_mask[indexes] = Export.get_color(i - 1)[0:3]

        return color_mask

    def redbrick_png(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
    ) -> None:
        """Export segmentation labels as masks."""
        if task_id:
            datapoints, taxonomy = self._get_raw_data_single(task_id)

        elif only_ground_truth:
            datapoints, taxonomy = self._get_raw_data_ground_truth(concurrency)
        else:
            datapoints, taxonomy = self._get_raw_data_latest(concurrency)

        if not self.general_info["taskType"] == "SEGMENTATION":
            print_error(
                "Project type needs to be SEGMENTATION, to use redbrick_png export!"
            )
            return

        # Create output directory
        output_dir = Export.uniquify_path(self.project_id)
        os.mkdir(output_dir)
        print_info(f"Saving masks to {output_dir} directory")

        # Create a color map from the taxonomy
        class_id_map: Dict = {}
        color_map: Dict = {}
        Export.tax_class_id_mapping(
            taxonomy["categories"][0]["children"], class_id_map, color_map
        )

        # Convert rbai to png masks and save output
        dp_map = {}
        for datapoint in datapoints:
            dp_map[datapoint["dpId"]] = datapoint["items"][0]
            color_mask = Export.convert_rbai_mask(datapoint, class_id_map)
            plt.imsave(os.path.join(output_dir, datapoint["dpId"] + ".png"), color_mask)

        with open(
            os.path.join(output_dir, "class_map.json"), "w+", encoding="utf-8"
        ) as file:
            json.dump(color_map, file, indent=2)

        with open(
            os.path.join(output_dir, "datapoint_map.json"), "w+", encoding="utf-8"
        ) as file:
            json.dump(dp_map, file, indent=2)

        return

    def redbrick_format(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
    ) -> List[Dict]:
        """Export data into redbrick format."""
        if task_id:
            datapoints, _ = self._get_raw_data_single(task_id)

        elif only_ground_truth:
            datapoints, _ = self._get_raw_data_ground_truth(concurrency)
        else:
            datapoints, _ = self._get_raw_data_latest(concurrency)

        return datapoints

    def coco_format(
        self,
        only_ground_truth: bool = True,
        concurrency: int = 10,
        task_id: Optional[str] = None,
    ) -> Dict:
        """Export project into coco format."""
        if task_id:
            datapoints, taxonomy = self._get_raw_data_single(task_id)
        elif only_ground_truth:
            datapoints, taxonomy = self._get_raw_data_ground_truth(concurrency)
        else:
            datapoints, taxonomy = self._get_raw_data_latest(concurrency)
        return coco_converter(datapoints, taxonomy)
