"""
Class for controlling video exports.
"""
from .export_base import ExportBase
from dataclasses import dataclass
import os
import cv2
import numpy as np
from termcolor import colored
from tqdm import tqdm
from redbrick.entity.datapoint import Image
from redbrick.utils import url_to_image


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
        pass

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
            frame_label = labels.labels[curr_idx].category
            key_index = 0  # the current key frame index
            pbar = tqdm(total=end_idx)
            while curr_idx != end_idx:
                # check if frame is key frame, if yes get the new labels, else keep old
                if (
                    key_index < len(labels.labels)
                    and labels.labels[key_index].frameindex == curr_idx
                ):
                    frame_label = labels.labels[key_index].category
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
