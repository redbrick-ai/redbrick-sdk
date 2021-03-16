"""Export to standard RedBrick format."""
from typing import Iterable, Dict, Any
from redbrick.api import RedBrickApi
from redbrick.logging import print_info, print_error
from redbrick.utils import url_to_image, clear_url
from redbrick.entity.datapoint import Image
from redbrick.entity.custom_group import CustomGroup
import redbrick
from tqdm import tqdm
import os
import json
import numpy as np
import cv2


class LabelsetLabelsIterator:
    def __init__(self, org_id: str, label_set_name: str) -> None:
        """Construct LabelsetLabelsIterator."""
        self.api = RedBrickApi()
        self.label_set_name = label_set_name
        self.org_id = org_id
        self.cursor = None
        self.datapointsBatch = None
        self.datapointsBatchIndex = None
        self.customGroup = self._get_custom_group()
        self.datapointCount = self.customGroup["datapointCount"]
        self.taxonomy = self.customGroup["taxonomy"]
        self.taxonomy_segm = self._get_taxonomy_segmentation()

    def _get_custom_group(self) -> None:
        return self.api.get_datapoints_paged(
            org_id=self.org_id, label_set_name=self.label_set_name
        )["customGroup"]

    def _get_taxonomy_segmentation(self) -> Dict[Any, Any]:
        if self.customGroup["taskType"] != "SEGMENTATION":
            return None
        else:
            return self._create_taxonomy_segmentation()

    def _create_taxonomy_segmentation(self):
        tax_map: Dict[str, int] = {}
        self._trav_tax(self.taxonomy["categories"][0], tax_map)
        return self._taxonomy_update_segmentation(tax_map)

    def _trav_tax(self, taxonomy: Dict[Any, Any], tax_map: Dict[str, int]) -> None:
        """Traverse the taxonomy tree structure, and fill the taxonomy mapper object."""
        children = taxonomy["children"]
        if len(children) == 0:
            return

        for child in children:
            tax_map[child["name"]] = child["classId"]
            self._trav_tax(child, tax_map)

    def _taxonomy_update_segmentation(self, tax_map: Dict[str, int]) -> Dict[str, int]:
        """
        Fix the taxonomy mapper object to be 1-indexed for
        segmentation projects.
        """
        for key in tax_map.keys():
            tax_map[key] += 1
            if tax_map[key] == 0:
                print_error(
                    "Taxonomy class id's must be 0 indexed. \
                        Please contact contact@redbrickai.com for help."
                )
                exit(1)

        # Add a background class for segmentation
        tax_map["background"] = 0
        return tax_map

    def _trim_labels(self, entry) -> Dict:
        """Trims None values from labels"""
        for label in entry["labelData"]["labels"]:
            for k, v in label.copy().items():
                if v is None:
                    del label[k]
        return entry

    def __iter__(self) -> Iterable[Dict]:
        return self

    def __next__(self) -> dict:
        """Get next labels / datapoint."""

        # If cursor is None and current datapointsBatch has been processed
        if (
            self.datapointsBatchIndex is not None
            and self.cursor is None
            and len(self.datapointsBatch) == self.datapointsBatchIndex
        ):
            raise StopIteration

        # If current datapointsBatch is None or we have finished processing current datapointsBatch
        if (
            self.datapointsBatch is None
            or len(self.datapointsBatch) == self.datapointsBatchIndex
        ):
            if self.cursor is None:
                customGroup = self.api.get_datapoints_paged(
                    org_id=self.org_id, label_set_name=self.label_set_name
                )
            else:
                customGroup = self.api.get_datapoints_paged(
                    org_id=self.org_id,
                    label_set_name=self.label_set_name,
                    cursor=self.cursor,
                )
            self.cursor = customGroup["customGroup"]["datapointsPaged"]["cursor"]
            self.datapointsBatch = customGroup["customGroup"]["datapointsPaged"][
                "entries"
            ]
            self.datapointsBatchIndex = 0

        # Current entry to return
        entry = self.datapointsBatch[self.datapointsBatchIndex]

        self.datapointsBatchIndex += 1

        return self._trim_labels(entry)


class ExportRedbrick:
    def __init__(self, org_id: str, label_set_name: str, target_dir: str) -> None:
        """Construct ExportRedbrick."""
        self.org_id = org_id
        self.label_set_name = label_set_name
        self.target_dir = target_dir

    def _export_image(self,):
        pass

    def export(
        self,
        download_data: bool = False,
        single_json: bool = False,
        use_name: bool = False,
        export_format: str = "redbrick",
    ) -> None:
        # Create LabelsetLabelsIterator
        labelsetIter = LabelsetLabelsIterator(
            org_id=self.org_id, label_set_name=self.label_set_name
        )

        # Validation of optional parameters
        task_type = labelsetIter.customGroup["taskType"]
        if export_format not in ["redbrick", "png"]:
            print_error(
                'Export format "{}" not valid, please use "redbrick" or "png"'.format(
                    export_format
                )
            )
            return
        if export_format == "png" and task_type != "SEGMENTATION":
            print_error(
                'Export format "png" is only valid for segmentation tasks. Please use "redbrick"'
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
        if export_format == "png" and task_type == "SEGMENTATION":
            target_masks_dir = os.path.join(self.target_dir, "masks")
            if not os.path.exists(target_masks_dir):
                os.makedirs(target_masks_dir)

        # Saving summary.json file
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

        if download_data:
            print_info(
                "Exporting datapoints and data to dir: {}".format(self.target_dir)
            )
        else:
            print_info("Exporting datapoints to dir: {}".format(self.target_dir))

        # If single json file
        if single_json:
            dpoints_flat = []

        # Check if current labelset is of video type
        IS_VIDEO = False
        if labelsetIter.customGroup["dataType"] == "VIDEO":
            # This is a video
            IS_VIDEO = True

        # Variables required to save png masks
        if export_format == "png" and task_type == "SEGMENTATION":
            label_info_segm: Dict[Any, Any] = {}
            label_info_segm["labels"] = []
            color_map: Any = None

        for dpoint in tqdm(labelsetIter, total=labelsetIter.datapointCount):
            # saving datapoint to json
            dpoint_flat = {
                "dpId": dpoint["dpId"],
                "items": dpoint["items"],
                "name": dpoint["name"],
                "createdByEmail": dpoint["labelData"]["createdByEmail"],
                "labels": dpoint["labelData"]["labels"],
            }

            # Save segmentation PNG masks if required
            if (
                export_format == "png"
                and task_type == "SEGMENTATION"
                and len(dpoint["labelData"]["labels"]) > 0
            ):
                dpoint_segm = Image(
                    created_by=dpoint["labelData"]["createdByEmail"],
                    org_id=labelsetIter.customGroup["orgId"],
                    label_set_name=labelsetIter.customGroup["name"],
                    taxonomy=labelsetIter.taxonomy_segm,
                    remote_labels=dpoint["labelData"]["labels"],
                    dp_id=dpoint["dpId"],
                    image_url=dpoint["items"][0],
                    image_url_not_signed=dpoint["itemsPresigned"][0],
                    image_data=None,
                    task_type=task_type,
                )

                colored_mask = dpoint_segm.labels.color_mask()
                color_map = dpoint_segm.labels.color_map2

                # cv2 expected BGR
                # pylint: disable=no-member
                # Handling of image filepath
                mask_name = dpoint["itemsPresigned"][0]
                if use_name:
                    dpoint_name = dpoint["name"]
                else:
                    dpoint_name = dpoint["dpId"]
                last_slash = dpoint_name.rfind("/")
                # Replacing special characters on file path
                mask_name = clear_url(dpoint_name[last_slash + 1 :])
                file_ext = mask_name[-4:]
                if file_ext.lower() in [".jpg", ".png", ".bmp"]:
                    # If image name already has an image extension
                    mask_filepath = os.path.join(
                        target_masks_dir, mask_name.replace(file_ext.lower() + ".png")
                    )
                else:
                    mask_filepath = os.path.join(target_masks_dir, mask_name + ".png")
                cv2.imwrite(
                    mask_filepath, np.flip(colored_mask, axis=2) * 255,
                )
                label_info_entry = {}
                label_info_entry["url"] = dpoint_segm.image_url_not_signed
                label_info_entry["createdBy"] = dpoint_segm.created_by
                label_info_entry["exportUrl"] = mask_filepath
                label_info_segm["labels"] += [label_info_entry]

            # If single json is required, append current datapoint to list
            if single_json:
                dpoints_flat.append(dpoint_flat)
            else:
                # Check if use_name is needed
                if use_name and dpoint["name"] is not None and dpoint["name"] != "":
                    fname = dpoint["name"]
                    last_slash = fname.rfind("/")
                    fname = clear_url(fname[last_slash + 1 :])
                    file_ext = fname[-4:]
                    if file_ext.lower() in [".jpg", ".png", ".bmp"]:
                        # If image name already has an image extension
                        fname = fname.replace(file_ext.lower(), "")
                else:
                    fname = dpoint["dpId"]
                # Json path to store current datapoint
                jsonPath = os.path.join(self.target_dir, "{}.json".format(fname))
                # Check for collisions
                idx = 1
                while True:
                    if not os.path.exists(jsonPath):
                        break
                    jsonPath = os.path.join(
                        self.target_dir, "{}({}).json".format(fname, idx)
                    )
                    idx += 1

                # Save current datapoint to json file
                with open(jsonPath, mode="w", encoding="utf-8") as f:
                    json.dump(dpoint_flat, f, indent=2)

            # Saving datapoint image/video data
            if download_data:
                if not IS_VIDEO:
                    # Handling of image filepath
                    dpoint_item = dpoint["itemsPresigned"][0]
                    if use_name:
                        dpoint_name = dpoint["name"]
                    else:
                        dpoint_name = dpoint["dpId"]
                    last_slash = dpoint_name.rfind("/")
                    # Replacing special characters on file path
                    image_name = clear_url(dpoint_name[last_slash + 1 :])
                    file_ext = image_name[-4:]
                    if file_ext.lower() in [".jpg", ".png", ".bmp"]:
                        # If image name already has an image extension
                        image_filepath = os.path.join(target_data_dir, image_name)
                    else:
                        image_filepath = os.path.join(
                            target_data_dir, image_name + ".jpg"
                        )
                    # Downloading image from url as numpy array
                    image_np = url_to_image(dpoint_item)
                    # Check for collisions
                    idx = 1
                    while True:
                        if not os.path.exists(image_filepath):
                            break
                        if file_ext.lower() in [".jpg", ".png", ".bmp"]:
                            # If image name already has an image extension
                            image_filepath = os.path.join(
                                target_data_dir,
                                image_name[:-4] + "({})".format(idx) + image_name[-4:],
                            )
                        else:
                            image_filepath = os.path.join(
                                target_data_dir, image_name + "({}).jpg".format(idx)
                            )
                        idx += 1
                    # Saving image to specified path
                    cv2.imwrite(  # pylint: disable=no-member
                        image_filepath, np.flip(image_np, axis=2)
                    )
                else:
                    # Video name
                    video_name = dpoint["name"]
                    # Create folder to store frames
                    target_data_video_dir = os.path.join(target_data_dir, video_name)
                    if not os.path.exists(target_data_video_dir):
                        os.makedirs(target_data_video_dir)
                    # Store frames
                    idx = 1
                    for i in range(len(dpoint["items"])):
                        dpoint_item = dpoint["items"][i]
                        file_ext = dpoint_item[-4:]
                        if file_ext.lower() in [".jpg", ".png", ".bmp"]:
                            # If image name already has an image extension
                            image_name = str(idx).zfill(6) + file_ext.lower()
                        else:
                            image_name = str(idx).zfill(6) + ".jpg"
                        idx += 1
                        image_filepath = os.path.join(target_data_video_dir, image_name)
                        # Downloading image from url as numpy array
                        image_np = url_to_image(dpoint_item)
                        # Saving image to specified path
                        cv2.imwrite(  # pylint: disable=no-member
                            image_filepath, np.flip(image_np, axis=2)
                        )

        # Finishing png masks export
        if export_format == "png" and task_type == "SEGMENTATION":
            # Meta-data
            label_info_segm["taxonomy"] = labelsetIter.taxonomy_segm
            label_info_segm["color_map"] = {}
            for key in labelsetIter.taxonomy_segm.keys():
                if key == "background":
                    color_map_ = [0, 0, 0]
                else:
                    color_map_ = list(
                        color_map(
                            labelsetIter.taxonomy_segm[key] - 1,
                            max(labelsetIter.taxonomy_segm.values()),
                        )
                    )
                    color_map_ = [int(c) for c in color_map_]
                label_info_segm["color_map"][
                    labelsetIter.taxonomy_segm[key]
                ] = color_map_

            # Save the class-mapping (taxonomy) in json format in the folder
            segm_json = os.path.join(target_masks_dir, "class-mapping.json",)
            with open(segm_json, "w+") as file:
                json.dump(label_info_segm, file, indent=2)

        # Saving all json data in a single file
        if single_json:
            jsonPath = os.path.join(
                self.target_dir,
                "{}_{}.json".format(self.org_id, self.label_set_name.replace(" ", "-")),
            )
            with open(jsonPath, mode="w", encoding="utf-8") as f:
                json.dump(dpoints_flat, f, indent=2)
