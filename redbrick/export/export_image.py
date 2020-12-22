"""
Class for controlling image exports.
"""
from dataclasses import dataclass
from typing import Any, Dict, List
import os
import json
from termcolor import colored
import cv2  # type: ignore
from tqdm import tqdm  # type: ignore
import numpy as np  # type: ignore

from .export_base import ExportBase
from redbrick.logging import print_info


@dataclass
class ExportImage(ExportBase):
    """Handle image exports."""

    def export(self) -> None:
        """Export the images and labels."""
        print_info("Cacheing labels, and data...")
        self.cache()
        print_info("Exported complete in %s" % self.cache_dir)

    def cache(self) -> None:
        """Cache the images and labels."""
        ExportBase.cache(self)

    def cache_bbox(self) -> None:
        """Cache image bounding boxes."""
        # Create YOLO style meta data files
        num_classes = len(list(self.labelset.taxonomy.keys()))
        train_file = "train.txt"
        names_file = "names.txt"
        data_file = "obj.data"
        backup_dir = "backup/"

        # obj.data
        with open(self.cache_dir + "/" + data_file, "w+") as file:
            file.write("classes = %s" % num_classes)
            file.write("\n")
            file.write("train = %s" % ("data" + "/" + train_file))
            file.write("\n")
            file.write("names = %s" % ("data" + "/" + names_file))
            file.write("\n")
            file.write("backup = %s" % backup_dir)

        # names.txt
        with open(self.cache_dir + "/" + names_file, "w+") as file:
            class_names = list(self.labelset.taxonomy.keys())
            for name in class_names:
                file.write(name + "\n")

        # obj_train_data/
        os.mkdir(os.path.join(self.cache_dir, "obj_train_data"))
        taxonomy_mapper = {
            name: idx for idx, name in enumerate(list(self.labelset.taxonomy.keys()))
        }
        image_filepaths = []

        # IMAGE DATA
        for i in tqdm(range(len(self.labelset.dp_ids))):
            dp_ = self.labelset.__getitem__(i)
            dp_entry = {}
            dp_entry["url"] = dp_.image_url_not_signed
            dp_entry["labels"] = []

            # write image data to file
            image_filepath = os.path.join(
                self.cache_dir,
                "obj_train_data",
                str(dp_.image_url_not_signed).replace("/", "_"),
            )
            image_filepaths.append(
                "obj_train_data/" + str(dp_.image_url_not_signed).replace("/", "_")
            )
            cv2.imwrite(  # pylint: disable=no-member
                image_filepath, np.flip(dp_.image_data, axis=2)
            )

            # create the label file name
            filext_idx = image_filepath.rfind(".")
            if not filext_idx:
                filext_idx = -1
            label_filepath = image_filepath[0:filext_idx] + ".txt"

            # write labels to the txt file
            with open(label_filepath, "w+") as file:
                for label in dp_.labels:
                    class_idx = taxonomy_mapper[label.classname[0][-1]]
                    file.write(
                        "%d %.6f %.6f %.6f %.6f \n"
                        % (
                            class_idx,
                            label.xnorm,
                            label.ynorm,
                            label.wnorm,
                            label.hnorm,
                        )
                    )

        # create train.txt file
        with open(os.path.join(self.cache_dir, train_file), "w+") as file:
            for filename in image_filepaths:
                file.write(filename + "\n")

    def cache_segmentation(self) -> None:
        """Cache image segmentation."""
        if self.format == "redbrick":
            # Save masks
            for i in tqdm(range(len(self.labelset.dp_ids))):
                dp_ = self.labelset.__getitem__(i)
                dp_.labels.mask.dump(
                    self.cache_dir
                    + "/"
                    + str(dp_.image_url_not_signed).replace("/", "_")
                    + "__export.dat"
                )

            # Save the class-mapping (taxonomy) in json format in the folder
            with open("%s/class-mapping.json" % self.cache_dir, "w+") as file:
                json.dump(dp_.taxonomy, file, indent=2)

        elif self.format == "redbrick-png":
            # iterate through all labels
            if len(self.labelset.dp_ids) == 0:
                return

            label_info: Dict[Any, Any] = {}
            label_info["labels"] = []
            color_map: Any = None
            for i in tqdm(range(len(self.labelset.dp_ids))):
                dp_ = self.labelset.__getitem__(i)
                colored_mask = dp_.labels.color_mask()
                color_map = dp_.labels.color_map
                # cv2 expected BGR
                # pylint: disable=no-member
                export_url = str(dp_.image_url_not_signed).replace("/", "_")
                cv2.imwrite(
                    os.path.join(self.cache_dir, export_url + "__export.png"),
                    np.flip(colored_mask, axis=2) * 256,
                )
                label_info_entry = {}
                label_info_entry["url"] = dp_.image_url_not_signed
                label_info_entry["createdBy"] = self.labelset.users[dp_.created_by]
                label_info_entry["exportUrl"] = export_url + "__export.png"
                label_info["labels"] += [label_info_entry]

            # Meta-data
            label_info["taxonomy"] = dp_.taxonomy
            label_info["color_map"] = {}
            for key in dp_.taxonomy:
                color_map_ = color_map(dp_.taxonomy[key]).tolist()
                label_info["color_map"][dp_.taxonomy[key]] = color_map_

            # Save the class-mapping (taxonomy) in json format in the folder
            with open("%s/class-mapping.json" % self.cache_dir, "w+") as file:
                json.dump(label_info, file, indent=2)

    def cache_classify(self) -> None:
        """Cache image classification."""
        label_file: List[Any] = []
        for i in tqdm(range(len(self.labelset.dp_ids))):
            dp = self.labelset.__getitem__(i)
            entry = {}
            entry["url"] = dp.image_url_not_signed
            entry["createdBy"] = self.labelset.users[dp.created_by]
            entry["class"] = dp.labels.labels.category
            label_file += [entry]

        with open("%s/export.json" % self.cache_dir, "w+") as file:
            json.dump(label_file, file, indent=2)
