"""
Class for controlling video exports.
"""
from .export_base import ExportBase
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import os
import cv2  # type: ignore
import shutil
import numpy as np  # type: ignore
from termcolor import colored
from tqdm import tqdm  # type: ignore
from redbrick.entity.datapoint import Image
from redbrick.utils import url_to_image

from datumaro.components.project import Project, Dataset, Environment  # type: ignore
from datumaro.plugins.cvat_format.converter import CvatConverter  # type: ignore
from datumaro.plugins.yolo_format.converter import YoloConverter  # type: ignore
from datumaro.plugins.coco_format.converter import CocoConverter  # type: ignore
from datumaro.plugins.voc_format.converter import VocConverter  # type: ignore


@dataclass
class ExportVideo(ExportBase):
    """Handle video exports."""

    def export(self) -> None:
        """Export the video and labels."""
        print(colored("[INFO]:", "blue"), "Cacheing labels, and data...")
        self.cache()

        if self.labelset.task_type == "BBOX":
            self.convert_bbox()
        elif self.labelset.task_type == "CLASSIFY":
            shutil.copytree(self.cache_dir, self.export_dir)

        shutil.rmtree(self.cache_dir)

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

            dp = self.labelset.__getitem__(i)
            pbar = tqdm(total=len(dp.items_list))

            # Write labels for each frame here
            temp: Dict[Any, Any] = {}
            for label in dp.labels:
                if label.trackid in temp:
                    temp[label.trackid].append(label)
                else:
                    temp[label.trackid] = [label]

            class VideoBBoxLabel:
                def __init__(
                    self,
                    labelid: str,
                    trackid: str,
                    xnorm: float,
                    ynorm: float,
                    hnorm: float,
                    wnorm: float,
                    frameindex: int,
                    keyframe: bool,
                    end: bool,
                    category: List[List[str]],
                ) -> None:
                    self.labelid = labelid
                    self.trackid = trackid
                    self.xnorm = xnorm
                    self.ynorm = ynorm
                    self.hnorm = hnorm
                    self.wnorm = wnorm
                    self.frameindex = frameindex
                    self.keyframe = keyframe
                    self.end = end
                    self.category = category

                def copy(self) -> "VideoBBoxLabel":
                    return VideoBBoxLabel(
                        self.labelid,
                        self.trackid,
                        self.xnorm,
                        self.ynorm,
                        self.hnorm,
                        self.wnorm,
                        self.frameindex,
                        self.keyframe,
                        self.end,
                        self.category,
                    )

                @classmethod
                def from_dict(cls, val: Any) -> "VideoBBoxLabel":
                    return cls(
                        labelid=val.labelid,
                        trackid=val.trackid,
                        xnorm=val.xnorm,
                        ynorm=val.ynorm,
                        wnorm=val.wnorm,
                        hnorm=val.hnorm,
                        frameindex=val.frameindex,
                        end=val.end,
                        category=val.classname[0][-1],
                        keyframe=val.keyframe,
                    )

            def interpolate(
                start: VideoBBoxLabel, frameindex: int, end: Optional[VideoBBoxLabel],
            ) -> "VideoBBoxLabel":
                if not end:
                    result = start.copy()
                    result.keyframe = False
                    return result
                assert frameindex > start.frameindex
                assert frameindex < end.frameindex
                before = frameindex - start.frameindex
                after = end.frameindex - frameindex
                total = end.frameindex - start.frameindex
                temp_ = start.copy()
                assert before > 0
                assert after > 0
                assert total > 0
                temp_.xnorm = after / total * start.xnorm + before / total * end.xnorm
                temp_.ynorm = after / total * start.ynorm + before / total * end.ynorm
                temp_.hnorm = after / total * start.hnorm + before / total * end.hnorm
                temp_.wnorm = after / total * start.wnorm + before / total * end.wnorm
                temp_.keyframe = False
                return temp_

            def interpolate2(
                keyframes: List[Optional[VideoBBoxLabel]], frameindex: int
            ) -> "Optional[VideoBBoxLabel]":
                # keyframes is a list where length = numFrames, keyframes[label.frameindex]=label
                # [ None, label, None, None, label]
                if keyframes[frameindex] and keyframes[frameindex].keyframe:
                    return keyframes[frameindex]
                start: VideoBBoxLabel = None

                for ii in range(frameindex, 0, -1):
                    label = keyframes[ii]
                    if label and label.keyframe:
                        if label.end:
                            return None
                        start = label
                        break

                if not start:
                    return None

                end: Optional[VideoBBoxLabel] = None
                for ii in range(frameindex, len(keyframes), 1):
                    label = keyframes[ii]
                    if label and label.keyframe:
                        end = label
                        break

                return interpolate(start, frameindex, end)

            def expand_list_of_keyframes(
                keyframes: List[VideoBBoxLabel], num_frames: int
            ) -> List[Optional[VideoBBoxLabel]]:
                # create a sparse list of keyframe labels of same length as num_frames
                mylist = [None] * num_frames
                for label in keyframes:
                    mylist[label.frameindex] = label

                return mylist

            temp2 = {}  # trackid -> full list of labels and keyframes (and None)
            for trackid, labellist in temp.items():
                temp45 = [VideoBBoxLabel.from_dict(label) for label in labellist]
                temp46 = expand_list_of_keyframes(temp45, len(dp.items_list))
                output = [None] * len(dp.items_list)
                for index, item in enumerate(output):
                    output[index] = interpolate2(temp46, index)

                temp2[trackid] = output

            framelabels: List[List[VideoBBoxLabel]] = []
            for index in range(len(dp.items_list)):
                current_frame_labels = []
                for labellist in temp2.values():
                    templable = labellist[index]
                    if templable:
                        current_frame_labels.append(templable)
                framelabels.append(current_frame_labels)

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
                    str(dp.items_list_not_signed[idx].replace("/", "_")),
                )
                image_filepaths.append(
                    os.path.join(
                        "obj_train_data",
                        str(dp.items_list_not_signed[idx].replace("/", "_")),
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

                # export the frame to the relvant folder
                if not os.path.isdir(
                    os.path.join(self.cache_dir, video_name, frame_label)
                ):
                    os.makedirs(os.path.join(self.cache_dir, video_name, frame_label))

                frame_data = np.flip(url_to_image(dp.items_list[curr_idx]), axis=2)
                frame_filename = dp.items_list_not_signed[curr_idx].replace("/", "_")
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

    def convert_bbox(self) -> None:
        """Convert cached bbox labels to proper format."""
        env = Environment()
        dataset = env.make_importer("yolo")(self.cache_dir).make_dataset()

        if self.format == "coco":
            CocoConverter.convert(dataset, save_dir=self.export_dir, save_images=True)

        elif self.format == "yolo" or self.format == "redbrick":
            YoloConverter.convert(dataset, save_dir=self.export_dir, save_images=True)

        elif self.format == "cvat":
            CvatConverter.convert(dataset, save_dir=self.export_dir, save_images=True)
        else:
            print(
                colored(
                    "[WARNING]: Invalid format type '%s'. Exporting with YOLO format."
                    % self.format
                )
            )
            YoloConverter.convert(dataset, save_dir=self.export_dir, save_images=True)
