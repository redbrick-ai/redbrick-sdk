"""
Class for controlling video exports.
"""
from dataclasses import dataclass
import os
import json
import cv2  # type: ignore
import numpy as np  # type: ignore
from termcolor import colored
from tqdm import tqdm  # type: ignore

from redbrick.utils import url_to_image
from .export_base import ExportBase


@dataclass
class ExportVideo(ExportBase):
    """Handle video exports."""

    def export(self) -> None:
        """Export the video and labels."""
        print(colored("[INFO]:", "blue"), "Cacheing labels, and data...")
        self.cache()

    def cache(self) -> None:
        """Cache the video and labels."""
        ExportBase.cache(self)

    def cache_bbox(self) -> None:
        """Cache video bounding boxes."""
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

        for i in range(len(self.labelset.dp_ids)):
            print(
                colored("[INFO]:", "blue"),
                "Exporting %s/%s video(s)" % (i + 1, len(self.labelset.dp_ids)),
            )

            # Create tqdm loader
            dp = self.labelset.__getitem__(i)
            pbar = tqdm(total=len(dp.items_list))

            # Interpolate the video labels, and get per frame labels
            framelabels = dp.labels.interpolate_labels(num_frames=len(dp.items_list))

            # Iterate through video frames
            for idx, item in enumerate(dp.items_list):
                pbar.update(1)
                dp_entry = {}
                dp_entry["url"] = dp.items_list_not_signed[idx]
                dp_entry["labels"] = []

                # write image data to file
                image_filepath = os.path.join(
                    self.cache_dir,
                    "obj_train_data",
                    str(
                        dp.items_list_not_signed[idx]
                        .replace("/", "_")
                        .replace(":", "_")
                    ),
                )
                image_filepaths.append(
                    os.path.join(
                        "obj_train_data",
                        str(
                            dp.items_list_not_signed[idx]
                            .replace("/", "_")
                            .replace(":", "_")
                        ),
                    )
                )

                frame_data = np.flip(url_to_image(item), axis=2)
                cv2.imwrite(image_filepath, frame_data)

                # create the label file name
                filext_idx = image_filepath.rfind(".")
                if not filext_idx:
                    filext_idx = -1
                label_filepath = image_filepath[0:filext_idx] + ".txt"

                # write labels to the txt file
                frame_labels = framelabels[idx]

                # write labels to the txt file
                with open(label_filepath, "w+") as file:
                    for label in frame_labels:
                        class_idx = taxonomy_mapper[label.category]
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
            pbar.close()

        # create train.txt file
        with open(os.path.join(self.cache_dir, train_file), "w+") as file:
            for filename in image_filepaths:
                file.write(filename + "\n")

    def cache_classify(self) -> None:
        """Cache video classification."""
        output = []
        for i in range(len(self.labelset.dp_ids)):
            print(
                colored("[INFO]:", "blue"),
                "Exporting %s/%s video(s)" % (i + 1, len(self.labelset.dp_ids)),
            )

            dp = self.labelset.__getitem__(i)
            video_name = dp.video_name
            labels = dp.labels

            # Loop through the key frame labels, and export by interpolating
            # the non key frames.
            start_idx = labels.labels[0].frameindex
            end_idx = len(dp.items_list)
            curr_idx = start_idx  # the current real frame index
            frame_label = labels.labels[curr_idx].category[0][-1]
            key_index = 0  # the current key frame index
            pbar = tqdm(total=end_idx)
            while curr_idx != end_idx:
                # check if frame is key frame, if yes get the new labels, else keep old
                if (
                    key_index < len(labels.labels)
                    and labels.labels[key_index].frameindex == curr_idx
                ):
                    frame_label = labels.labels[key_index].category[0][-1]
                    key_index += 1

                # check export format type
                if self.format == "redbrick-json":
                    output.append(
                        {
                            "url": dp.items_list_not_signed[curr_idx],
                            "class": frame_label,
                            "name": video_name,
                        }
                    )
                else:
                    # export the frame to the relvant folder
                    if not os.path.isdir(
                        os.path.join(self.cache_dir, video_name, frame_label)
                    ):
                        os.makedirs(
                            os.path.join(self.cache_dir, video_name, frame_label)
                        )

                    frame_data = np.flip(url_to_image(dp.items_list[curr_idx]), axis=2)
                    frame_filename = (
                        dp.items_list_not_signed[curr_idx]
                        .replace("/", "_")
                        .replace(":", "_")
                    )
                    cv2.imwrite(
                        os.path.join(
                            self.cache_dir, video_name, frame_label, frame_filename
                        ),
                        frame_data,
                    )

                # update the index
                curr_idx += 1
                pbar.update(1)
            pbar.close()

            if self.format == "redbrick-json":
                with open(os.path.join(self.cache_dir, "output.json"), "w+") as file:
                    json.dump(output, file, indent=2)
