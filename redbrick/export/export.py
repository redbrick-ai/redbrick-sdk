"""Export to standard RedBrick format."""

import os
import cv2
import json
import numpy as np

from typing import Dict, Any, List

from tqdm import tqdm

from redbrick.logging import print_info, print_error
from redbrick.utils import url_to_image, clear_url
from redbrick.entity.datapoint import Image
from .labelset_iter import LabelsetIterator
from .coco_utils import coco_categories_format, coco_image_format, coco_labels_format


class Export:
    """Construct Export."""

    def __init__(self, org_id: str, label_set_name: str, target_dir: str):
        self.org_id = org_id
        self.target_dir = target_dir
        self.label_set_name = label_set_name

    def _save_all_datapoints(self, dpoints: List, lset_name: str) -> None:
        """Save all export data in single JSON file."""
        filepath = os.path.join(
            self.target_dir, "{}_{}.json".format(self.org_id, lset_name)
        )
        with open(filepath, mode="w", encoding="utf-8") as f:
            json.dump(dpoints, f, indent=2)

    def _save_datapoint(self, dpoint: dict, filepath: str) -> None:
        """Save single datapoint in a file"""
        with open(filepath, mode="w", encoding="utf-8") as f:
            json.dump(dpoint, f, indent=2)

    def _save_image(self, dpoint: str, img_filepath: str) -> None:
        """Save image to filesystem."""
        if not os.path.exists(img_filepath):
            # Downloading image from url as numpy array
            image_np = url_to_image(dpoint)
            cv2.imwrite(  # pylint: disable=no-member
                img_filepath, np.flip(image_np, axis=2)
            )

    def _get_non_existent_filename(self, filepath: str) -> str:
        """Return a new filepath if the file with same name exists."""
        if not os.path.exists(filepath):
            return filepath
        idx = 1
        while True:
            path = f"({idx})".join(os.path.splitext(filepath))
            if not os.path.exists(path):
                return path
            idx += 1

    def _write_mask(
        self, dpoint_name: str, target_masks_dir: str, color_mask: np.ndarray
    ) -> str:
        """Write mask image to filesystem."""
        basename = os.path.basename(dpoint_name)
        mask_name, ext = os.path.splitext(clear_url(basename))
        if not ext:
            ext = ".png"  # default extension
        mask_filepath = os.path.join(target_masks_dir, mask_name + ext)
        cv2.imwrite(
            mask_filepath, np.flip(color_mask, axis=2) * 255,
        )
        return mask_filepath

    def _get_image(self, dpoint: dict, labelsetIter: LabelsetIterator) -> Image:
        """Return Image object."""
        return Image(
            created_by=dpoint["labelData"]["createdByEmail"],
            org_id=labelsetIter.customGroup["orgId"],
            label_set_name=labelsetIter.customGroup["name"],
            taxonomy=labelsetIter.taxonomy_segm,
            remote_labels=dpoint["labelData"]["labels"],
            dp_id=dpoint["dpId"],
            image_url=dpoint["items"][0],
            image_url_not_signed=dpoint["itemsPresigned"][0],
            image_data=None,
            task_type=labelsetIter.customGroup["taskType"],
        )

    def _download_image_data(self, dpoint: dict, use_name, dir: str) -> None:
        """Download Image data."""

        # Handling of image filepath
        dpoint_item = dpoint["itemsPresigned"][0]
        dpoint_name = dpoint["dpId"]
        if use_name:
            dpoint_name = dpoint["name"]
        basename = os.path.basename(dpoint_name)
        img_name, ext = os.path.splitext(clear_url(basename))
        if not ext:
            ext = ".jpg"
        image_filepath = os.path.join(dir, img_name + ext)

        # Check for collisions
        if use_name:
            image_filepath = self._get_non_existent_filename(image_filepath)

        # Saving image to specified path if it doesn't exists
        self._save_image(dpoint_item, image_filepath)

    def _download_video_data(self, dpoint: dict, dir: str) -> None:
        """Download Video dataset."""
        # Video name
        video_name = dpoint["name"]
        # Create folder to store frames
        target_data_video_dir = os.path.join(dir, video_name)
        if not os.path.exists(target_data_video_dir):
            os.makedirs(target_data_video_dir)
        # Store frames
        for idx in range(len(dpoint["items"])):
            dpoint_item = dpoint["items"][idx]
            basename = os.path.basename(dpoint_item)
            _, ext = os.path.splitext(basename)
            if not ext:
                ext = ".jpg"

            image_name = str(idx + 1).zfill(6) + ext
            image_filepath = os.path.join(target_data_video_dir, image_name)

            # Saving image to specified path if it doesn't exists
            self._save_image(dpoint_item, image_filepath)

    def _save_class_mappings(
        self,
        label_info_segm: dict,
        dir: str,
        color_map: Any,
        labelsetIter: LabelsetIterator,
    ) -> None:
        """Save class mappings to filesystem."""

        label_info_segm["color_map"] = {}
        label_info_segm["taxonomy"] = labelsetIter.taxonomy_segm

        for key in labelsetIter.taxonomy_segm.keys():
            color_map_ = [0, 0, 0]
            if key != "background":
                color_map_ = list(
                    color_map(
                        labelsetIter.taxonomy_segm[key] - 1,
                        max(labelsetIter.taxonomy_segm.values()),
                    )
                )
                color_map_ = [int(c) for c in color_map_]
            label_info_segm["color_map"][labelsetIter.taxonomy_segm[key]] = color_map_

        # Save the class-mapping (taxonomy) in json format in the folder
        segm_json = os.path.join(dir, "class-mapping.json",)
        with open(segm_json, "w+") as file:
            json.dump(label_info_segm, file, indent=2)

    def _flatten_datapoint(self, dpoint: dict) -> dict:
        """Return dict simplifying the datapoint."""
        return {
            "dpId": dpoint["dpId"],
            "items": dpoint["items"],
            "name": dpoint["name"],
            "createdByEmail": dpoint["labelData"]["createdByEmail"],
            "labels": dpoint["labelData"]["labels"],
        }

    def _get_datapoint_filepath(self, dpoint: dict, use_name: bool) -> str:
        """Return filepath for saving label data."""
        fname = dpoint["dpId"]
        if use_name and dpoint["name"]:
            basename = os.path.basename(dpoint["name"])
            fname, ext = os.path.splitext(clear_url(basename))

        filepath = os.path.join(self.target_dir, "{}.json".format(fname))

        if use_name:
            filepath = self._get_non_existent_filename(filepath)

        return filepath

    def _export_video(
        self,
        labelsetIter: LabelsetIterator,
        download_data: bool,
        single_json: bool,
        use_name: bool,
        export_format: str,
    ):
        dpoints_flat = []
        target_data_dir = os.path.join(self.target_dir, "data")

        for dpoint in tqdm(labelsetIter, total=labelsetIter.datapointCount):
            dpoint_flat = self._flatten_datapoint(dpoint)
            dpoints_flat.append(dpoint_flat)

            jsonPath = self._get_datapoint_filepath(dpoint, use_name)

            if not single_json:
                self._save_datapoint(dpoint_flat, jsonPath)

            # Saving datapoint image/video data
            if download_data:
                self._download_video_data(dpoint, target_data_dir)

        if single_json:
            self._save_all_datapoints(
                dpoints_flat, self.label_set_name.replace(" ", "-")
            )

    def _export_image(
        self,
        labelsetIter: LabelsetIterator,
        download_data: bool,
        single_json: bool,
        use_name: bool,
        export_format: str,
    ):
        dpoints_flat = []
        target_data_dir = os.path.join(self.target_dir, "data")

        for dpoint in tqdm(labelsetIter, total=labelsetIter.datapointCount):
            dpoint_flat = self._flatten_datapoint(dpoint)
            dpoints_flat.append(dpoint_flat)

            jsonPath = self._get_datapoint_filepath(dpoint, use_name)

            if not single_json:
                # Save current datapoint to json file
                self._save_datapoint(dpoint_flat, jsonPath)

            # Saving datapoint image/video data
            if download_data:
                self._download_image_data(dpoint, use_name, target_data_dir)

        # Saving all json data in a single file
        if single_json:
            self._save_all_datapoints(
                dpoints_flat, self.label_set_name.replace(" ", "-")
            )

    def _export_image_segmentation(
        self,
        labelsetIter: LabelsetIterator,
        download_data: bool,
        single_json: bool,
        use_name: bool,
        export_format: str,
    ):
        color_map: Any = None
        label_info_segm: Dict[Any, Any] = {"labels": []}
        target_data_dir = os.path.join(self.target_dir, "data")
        target_masks_dir = os.path.join(self.target_dir, "masks")

        dpoints_flat = []
        for dpoint in tqdm(labelsetIter, total=labelsetIter.datapointCount):
            dpoint_flat = self._flatten_datapoint(dpoint)
            dpoints_flat.append(dpoint_flat)

            # Save segmentation PNG masks if required
            if dpoint["labelData"]["labels"]:
                dpoint_segm = self._get_image(dpoint, labelsetIter)

                colored_mask = dpoint_segm.labels.color_mask()
                color_map = dpoint_segm.labels.color_map2

                dpoint_name = dpoint["dpId"]
                if use_name:
                    dpoint_name = dpoint["name"]

                mask_filepath = self._write_mask(
                    dpoint_name, target_masks_dir, colored_mask
                )

                width, height = dpoint_segm._get_image_size()
                label_info_entry = {
                    "url": dpoint_segm.image_url_not_signed,
                    "createdBy": dpoint_segm.created_by,
                    "exportUrl": mask_filepath,
                    "img_size": [width, height],
                }

                label_info_segm["labels"] += [label_info_entry]

                jsonPath = self._get_datapoint_filepath(dpoint, use_name)
                if not single_json:
                    # Save current datapoint to json file
                    with open(jsonPath, mode="w", encoding="utf-8") as f:
                        json.dump(dpoint_flat, f, indent=2)

            # Saving datapoint image/video data
            if download_data:
                self._download_image_data(dpoint, use_name, target_data_dir)

        # Finishing png masks export
        self._save_class_mappings(
            label_info_segm, target_masks_dir, color_map, labelsetIter
        )

        # Saving all json data in a single file
        if single_json:
            self._save_all_datapoints(
                dpoints_flat, self.label_set_name.replace(" ", "-")
            )

        if export_format == "coco":
            self._export_to_coco_format(dpoints_flat, labelsetIter, label_info_segm)

    def _export_to_coco_format(
        self, dpoints: List, labelsetIter: LabelsetIterator, labels_info: List
    ):
        """Export the Polygon/Segmentation labels to COCO format."""
        taxonomy: dict = labelsetIter.customGroup["taxonomy"]
        coco_format = {
            "categories": coco_categories_format(taxonomy),
        }
        images: List = []
        annotations: List = []

        labels = [dp for dp in dpoints if dp.get("labels")]
        for idx, dp in enumerate(labels):
            # Continue when the datapoints has no labels
            if not dp.get("labels"):
                continue

            img_width, img_height = labels_info["labels"][idx]["img_size"]
            file_name = dp.get("items")[0]
            image = coco_image_format(img_width, img_height, file_name, dp.get("dpId"))

            # Generate annotation for each label
            for label in dp.get("labels"):
                annotation = coco_labels_format(
                    label, img_width, img_height, taxonomy, dp.get("dpId")
                )
                annotations.append(annotation)

            images.append(image)

        coco_format["images"] = images
        coco_format["annotations"] = annotations

        # Write the COCO Label format to file
        with open(f"{self.target_dir}/coco.json", "w") as f:
            f.write(json.dumps(coco_format))

    def _save_summary_json(self, labelsetIter: LabelsetIterator) -> None:
        """Saves summary json file of current labelset export"""
        org_id_summary = labelsetIter.customGroup["orgId"]
        label_set_name_summary = labelsetIter.customGroup["name"]
        taxonomy_summary = labelsetIter.customGroup["taxonomy"]
        summary_json = {
            "org_id": org_id_summary,
            "label_set_name": label_set_name_summary,
            "taxonomy": taxonomy_summary,
        }
        summary_json_filepath = os.path.join(self.target_dir, "summary.json")
        with open(summary_json_filepath, mode="w", encoding="utf-8") as f:
            json.dump(summary_json, f, indent=2)

    def _export_multi(
        self,
        labelsetIter: LabelsetIterator,
        download_data: bool,
        single_json: bool,
        use_name: bool,
        export_format: str,
    ):
        """Export MULTI type labels. Supporting only Polygon and Bbox now."""
        color_map: Any = None
        dpoints_flat: List = []
        label_info_segm: Dict[Any, Any] = {"labels": []}
        target_data_dir = os.path.join(self.target_dir, "data")
        target_masks_dir = os.path.join(self.target_dir, "masks")

        for dpoint in tqdm(labelsetIter, total=labelsetIter.datapointCount):
            dpoint_flat = self._flatten_datapoint(dpoint)
            dpoints_flat.append(dpoint_flat)

            # Save segmentation PNG masks if required
            if dpoint["labelData"]["labels"]:
                dpoint_segm = self._get_image(dpoint, labelsetIter)

                colored_mask = dpoint_segm.labels.color_mask()
                color_map = dpoint_segm.labels.color_map2

                dpoint_name = dpoint["dpId"]
                if use_name:
                    dpoint_name = dpoint["name"]

                mask_filepath = self._write_mask(
                    dpoint_name, target_masks_dir, colored_mask
                )

                width, height = dpoint_segm._get_image_size()
                label_info_entry = {
                    "url": dpoint_segm.image_url_not_signed,
                    "createdBy": dpoint_segm.created_by,
                    "exportUrl": mask_filepath,
                    "img_size": [width, height],
                }

                label_info_segm["labels"] += [label_info_entry]

            jsonPath = self._get_datapoint_filepath(dpoint, use_name)

            if not single_json:
                # Save current datapoint to json file
                self._save_datapoint(dpoint_flat, jsonPath)

            # Saving datapoint image/video data
            if download_data:
                self._download_image_data(dpoint, use_name, target_data_dir)

        # Finishing png masks export
        self._save_class_mappings(
            label_info_segm, target_masks_dir, color_map, labelsetIter
        )

        # Saving all json data in a single file
        if single_json:
            self._save_all_datapoints(
                dpoints_flat, self.label_set_name.replace(" ", "-")
            )

        if export_format == "coco":
            self._export_to_coco_format(dpoints_flat, labelsetIter, label_info_segm)

    def export(
        self,
        download_data: bool = False,
        single_json: bool = False,
        use_name: bool = False,
        export_format: str = "redbrick",
    ) -> None:
        # Create LabelsetIterator
        labelsetIter = LabelsetIterator(
            org_id=self.org_id, label_set_name=self.label_set_name
        )

        # Validation of optional parameters
        task_type = labelsetIter.customGroup["taskType"]
        if export_format not in ["redbrick", "png", "coco"]:
            print_error(
                f'Export format "{export_format}" not valid, please use '
                f'"redbrick", "coco" or "png"'
            )
            return

        if export_format in ["png", "coco"] and task_type not in [
            "SEGMENTATION",
            "MULTI",
            "POLYGON",
        ]:
            print_error(
                'Export format "png" and "coco" is only valid for segmentation '
                'and polygon tasks. Please use "redbrick"'
            )
            return

        # Create target_dir if it doesn't exists
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        # Create folder 'data' inside target_dir
        if download_data:
            target_data_dir = os.path.join(self.target_dir, "data")
            if not os.path.exists(target_data_dir):
                os.makedirs(target_data_dir)

        # Create masks folder
        if export_format in ["png", "coco"] and task_type in [
            "SEGMENTATION",
            "MULTI",
            "POLYGON",
        ]:
            target_masks_dir = os.path.join(self.target_dir, "masks")
            if not os.path.exists(target_masks_dir):
                os.makedirs(target_masks_dir)

        # Saving summary.json file
        self._save_summary_json(labelsetIter)

        if download_data:
            print_info(
                "Exporting datapoints and data to dir: {}".format(self.target_dir)
            )
        else:
            print_info("Exporting datapoints to dir: {}".format(self.target_dir))

        # If we are exporting image segmentation
        if export_format in ["png", "coco"]:
            if task_type in ["SEGMENTATION", "POLYGON"]:
                self._export_image_segmentation(
                    labelsetIter, download_data, single_json, use_name, export_format
                )
            else:
                self._export_multi(
                    labelsetIter, download_data, single_json, use_name, export_format
                )
        elif labelsetIter.customGroup["dataType"] == "VIDEO":
            self._export_video(
                labelsetIter, download_data, single_json, use_name, export_format
            )
        else:
            self._export_image(
                labelsetIter, download_data, single_json, use_name, export_format
            )
