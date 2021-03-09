"""Export to standard RedBrick format."""
from typing import Iterable, Dict
from redbrick.api import RedBrickApi
from redbrick.logging import print_info
from redbrick.utils import url_to_image, clear_url
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

    def _get_custom_group(self) -> None:
        return self.api.get_datapoints_paged(
            org_id=self.org_id, label_set_name=self.label_set_name
        )["customGroup"]

    def _get_batch(self) -> None:
        print(self.api.get_datapoints_paged(self.org_id, self.label_set_name))

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

    def export(
        self,
        download_data: bool = False,
        single_json: bool = False,
        use_name: bool = False,
    ) -> None:
        # Create LabelsetLabelsIterator
        labelsetIter = LabelsetLabelsIterator(
            org_id=self.org_id, label_set_name=self.label_set_name
        )

        # Create target_dir if it doesn't exist
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        # Create folder 'data' inside target_dir
        if download_data:
            target_data_dir = os.path.join(self.target_dir, "data")
            if not os.path.exists(target_data_dir):
                os.makedirs(target_data_dir)

        if download_data:
            print_info(
                "Exporting datapoints and data to dir: {}".format(self.target_dir)
            )
        else:
            print_info("Exporting datapoints to dir: {}".format(self.target_dir))

        # If single json file
        if single_json:
            dpoints_flat = []

        for dpoint in tqdm(labelsetIter, total=labelsetIter.datapointCount):
            # saving datapoint to json
            dpoint_flat = {
                "dpId": dpoint["dpId"],
                "items": dpoint["items"],
                "name": dpoint["name"],
                "createdByEmail": dpoint["labelData"]["createdByEmail"],
                "labels": dpoint["labelData"]["labels"],
            }

            # Check if current datapoint is a video
            IS_VIDEO = False
            if len(dpoint["items"]) > 1:
                # This is a video
                IS_VIDEO = True

            # If single json is required, append current datapoint to list
            if single_json:
                dpoints_flat.append(dpoint_flat)
            else:
                # Check if use_name is needed
                if use_name and dpoint["name"] is not None and dpoint["name"] is not "":
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

        # Saving all json data in a single file
        if single_json:
            jsonPath = os.path.join(
                self.target_dir,
                "{}_{}.json".format(self.org_id, self.label_set_name.replace(" ", "-")),
            )
            with open(jsonPath, mode="w", encoding="utf-8") as f:
                json.dump(dpoints_flat, f, indent=2)

        #Saving summary.json file
        org_id_summary = labelsetIter.customGroup["orgId"]
        label_set_name_summary = labelsetIter.customGroup["name"]
        taxonomy_summary = labelsetIter.customGroup["taxonomy"]
        summary_json = {
            "org_id": org_id_summary,
            "label_set_name": label_set_name_summary,
            "taxonomy": taxonomy_summary
        }
        summary_json_filepath = os.path.join(self.target_dir, "summary.json")
        with open(summary_json_filepath, mode="w", encoding="utf-8") as f:
                json.dump(summary_json, f, indent=2)
