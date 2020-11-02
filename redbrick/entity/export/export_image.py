"""
Class for controlling image exports.
"""
from redbrick.entity.export.export_base import ExportBase
from dataclasses import dataclass
from termcolor import colored
import os
import cv2  # type: ignore
import json
from tqdm import tqdm  # type: ignore
import numpy as np  # type: ignore
from redbrick.entity.datapoint import Image, Video
import shutil


@dataclass
class ExportImage(ExportBase):
    """Handle image exports."""

    def export(self) -> None:
        """Export the images and labels."""
        print(colored("[INFO]:", "blue"), "Cacheing labels, and data...")
        self.cache()

        if self.labelset.task_type == "BBOX":
            print(colored("[INFO]:", "blue"), "Exporting to %s format..." % self.format)
            shutil.copytree(self.cache_dir, self.export_dir)

        elif self.labelset.task_type == "SEGMENTATION":
            pass

        shutil.rmtree(self.cache_dir)

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
            dp = self.labelset.__getitem__(i)
            if isinstance(dp, Video):
                # Ensure the data type is Image
                raise ValueError(
                    "Oops, something went wrong! Please reach out to contact@redbrickai.com."
                )
            dp_entry = {}
            dp_entry["url"] = dp.image_url_not_signed
            dp_entry["labels"] = []

            # write image data to file
            image_filepath = os.path.join(
                self.cache_dir,
                "obj_train_data",
                str(dp.image_url_not_signed).replace("/", "_"),
            )
            image_filepaths.append(
                "obj_train_data/" + str(dp.image_url_not_signed).replace("/", "_")
            )
            cv2.imwrite(  # pylint: disable=no-member
                image_filepath, np.flip(dp.image_data, axis=2)
            )

            # create the label file name
            filext_idx = image_filepath.rfind(".")
            if not filext_idx:
                filext_idx = -1
            label_filepath = image_filepath[0:filext_idx] + ".txt"

            # write labels to the txt file
            with open(label_filepath, "w+") as file:
                for label in dp.labels:
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
        # Save masks
        for i in tqdm(range(len(self.labelset.dp_ids))):
            dp = self.labelset.__getitem__(i)
            dp.labels.mask.dump(
                self.cache_dir
                + "/"
                + str(dp.image_url_not_signed).replace("/", "_")
                + ".dat"
            )

        # Save the class-mapping (taxonomy) in json format in the folder
        with open("%s/class-mapping.json" % self.cache_dir, "w+") as file:
            json.dump(dp.taxonomy, file, indent=2)

    def cache_classify(self) -> None:
        """Cache image classification."""
        pass
