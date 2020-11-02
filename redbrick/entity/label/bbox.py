"""
Representation of a bounding box labels
"""

from dataclasses import dataclass
from redbrick.entity.taxonomy import TaxonomyEntry
from redbrick.utils import compare_taxonomy
from redbrick.entity.taxonomy2 import Taxonomy2
from typing import List, Union, Dict, Any, Tuple, Optional
import numpy as np  # type: ignore
import os
import json
from tqdm import tqdm  # type: ignore
import copy
import uuid
import matplotlib.patches as patches  # type: ignore
import copy


@dataclass
class ImageBoundingBoxEntry:

    xnorm: float
    ynorm: float
    wnorm: float
    hnorm: float
    classname: List[List[str]]


@dataclass
class VideoBoundingBoxEntry:

    xnorm: float
    ynorm: float
    wnorm: float
    hnorm: float
    classname: List[List[str]]
    labelid: str
    trackid: str
    frameindex: int
    keyframe: bool
    end: bool


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


@dataclass
class BaseBoundingBox:
    labels: Union[List[ImageBoundingBoxEntry], List[VideoBoundingBoxEntry]]

    def compare_tax(self, taxonomy: Taxonomy2) -> Tuple[bool, List[List[str]]]:
        """Compare the labels category to taxonomy."""
        raise NotImplementedError()

    def __getitem__(
        self, index: int
    ) -> Union[ImageBoundingBoxEntry, VideoBoundingBoxEntry]:
        """Get item."""
        return self.labels[index]

    def __iter__(self) -> "BaseBoundingBox":
        """Label iterator."""
        self.it = 0
        return self

    def __next__(self) -> Union[ImageBoundingBoxEntry, VideoBoundingBoxEntry]:
        """Next iterator."""
        if self.it < len(self.labels):
            val = self.labels[self.it]
            self.it += 1
            return val
        else:
            raise StopIteration


class ImageBoundingBox(BaseBoundingBox):
    """Bounding box for a single image."""

    def __init__(self, labels: List[Any]) -> None:
        """Constructor."""
        self.labels: List[ImageBoundingBoxEntry]

        # Parse the remote labels, and save as entries
        entries = []
        for label in labels:

            if "bbox2d" not in label:
                raise ValueError(
                    "Incorrect format for labels entry ImageBoundingBox. bbox2d field is missing!"
                )

            label_ = label["bbox2d"]
            entry = ImageBoundingBoxEntry(
                xnorm=label_["xnorm"],
                ynorm=label_["ynorm"],
                wnorm=label_["wnorm"],
                hnorm=label_["hnorm"],
                classname=label["category"],
            )
            entries.append(entry)

        self.labels = entries

    def compare_taxonomy(self, taxonomy: Taxonomy2) -> Tuple[bool, List[List[str]]]:
        """Compare the label classes with the taxonomy."""
        # Iterate over each label
        for label in self.labels:
            check_ = compare_taxonomy(label.classname, taxonomy)
            if not check_:
                return False, label.classname

        return True, [["null", "null"]]

    def show(self, ax: Any, width: int, height: int) -> None:
        """Show the image bbox."""
        for label in self.labels:
            x = label.xnorm * width
            y = label.ynorm * height
            h = label.hnorm * height
            w = label.wnorm * width
            rect = patches.Rectangle(
                xy=(x, y),
                width=w,
                height=h,
                edgecolor=(5 / 256, 4 / 256, 170 / 256),
                facecolor=(5 / 256, 4 / 256, 170 / 256, 0.3),
            )
            ax.add_patch(rect)
            ax.text(
                x,
                y - 1,
                label.classname[0][-1],
                fontsize=10,
                color=(5 / 256, 4 / 256, 170 / 256),
            )

    def __str__(self) -> str:
        """String representation."""
        labels = []
        for label in self.labels:
            entry: Dict[Any, Any] = {}
            entry["category"] = label.classname
            entry["attributes"] = []
            entry["labelid"] = str(uuid.uuid4())
            entry["bbox2d"] = {
                "xnorm": label.xnorm,
                "ynorm": label.ynorm,
                "hnorm": label.hnorm,
                "wnorm": label.wnorm,
            }

            labels.append(entry)

        output = {"items": [{"url": "throwaway", "labels": labels}]}

        return json.dumps(output)


class VideoBoundingBox(BaseBoundingBox):
    """Bounding box for a single video."""

    def __init__(self, labels: List[Any]) -> None:
        """Constructor."""
        self.labels: List[VideoBoundingBoxEntry]
        self.interpolated_labels: Optional[List[List[VideoBBoxLabel]]] = None

        # parse the remote labels, and store entries
        entries = []
        for label in labels:

            # Fill out values if not provided
            if not "trackid" in label:
                label["trackid"] = str(uuid.uuid4())
            if not "end" in label:
                label["end"] = True
            if not "keyframe" in label:
                label["keyframe"] = True
            if not "labelid" in label:
                label["labelid"] = str(uuid.uuid4())

            entry = VideoBoundingBoxEntry(
                xnorm=label["bbox2d"]["xnorm"],
                ynorm=label["bbox2d"]["ynorm"],
                wnorm=label["bbox2d"]["wnorm"],
                hnorm=label["bbox2d"]["hnorm"],
                classname=label["category"],
                labelid=label["labelid"],
                trackid=label["trackid"],
                frameindex=label["frameindex"],
                keyframe=label["keyframe"],
                end=label["end"],
            )
            entries.append(entry)

        self.labels = entries

    def show(
        self, ax: Any, width: int, height: int, frameindex: int, num_frames: int
    ) -> List[Any]:
        """Show the video bbox."""
        # interpolate labels if not already done
        if not self.interpolated_labels:
            frame_labels = self.interpolate_labels(num_frames=num_frames)
            self.interpolated_labels = frame_labels

        ims = []
        for label in self.interpolated_labels[frameindex]:
            x = label.xnorm * width
            y = label.ynorm * height
            h = label.hnorm * height
            w = label.wnorm * width
            rect = patches.Rectangle(
                xy=(x, y),
                width=w,
                height=h,
                edgecolor=(5 / 256, 4 / 256, 170 / 256),
                facecolor=(5 / 256, 4 / 256, 170 / 256, 0.3),
                animated=True,
            )
            im1 = ax.add_patch(rect)
            im2 = ax.text(
                x,
                y - 1,
                label.category[0][-1],
                fontsize=10,
                color=(5 / 256, 4 / 256, 170 / 256),
                animated=True,
            )
            ims += [im1, im2]

        return ims

    def compare_taxonomy(self, taxonomy: Taxonomy2) -> Tuple[bool, List[List[str]]]:
        """Ensure labels abide by taxonomy."""
        # Iterate over each frame
        for label in self.labels:
            check = compare_taxonomy(category_path=label.classname, taxonomy=taxonomy)

            if not check:
                return check, label.classname

        return True, [["null", "null"]]

    def __str__(self) -> str:
        """String representation of self."""
        labels = []

        for label in self.labels:
            entry: Dict[Any, Any] = {}
            entry["category"] = label.classname
            entry["attributes"] = []
            entry["labelid"] = label.labelid
            entry["bbox2d"] = {
                "xnorm": label.xnorm,
                "ynorm": label.ynorm,
                "hnorm": label.hnorm,
                "wnorm": label.wnorm,
            }
            entry["frameindex"] = label.frameindex
            entry["keyframe"] = label.keyframe
            entry["trackid"] = label.trackid
            entry["end"] = label.end
            labels.append(entry)

        output = {"labels": labels}
        return json.dumps(output)

    def interpolate_labels(self, num_frames: int) -> List[List[VideoBBoxLabel]]:
        """Interpolate the frames and return interpolated object."""
        # Write labels for each frame here
        # Write labels for each frame here
        temp: Dict[Any, Any] = {}
        for label in self.labels:
            if label.trackid in temp:
                temp[label.trackid].append(label)
            else:
                temp[label.trackid] = [label]

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
            temp = keyframes[frameindex]
            if temp and temp.keyframe:
                return keyframes[frameindex]
            start: Optional[VideoBBoxLabel] = None

            for ii in reversed(range(0, frameindex)):
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
            mylist: List[Optional[VideoBBoxLabel]] = [None] * num_frames
            for label in keyframes:
                mylist[label.frameindex] = label

            return mylist

        temp2 = {}  # trackid -> full list of labels and keyframes (and None)
        for trackid, labellist in temp.items():
            temp45 = [VideoBBoxLabel.from_dict(label) for label in labellist]
            temp46 = expand_list_of_keyframes(temp45, num_frames)
            output: List[Optional[VideoBBoxLabel]] = [None] * num_frames

            for index, _ in enumerate(output):
                output[index] = interpolate2(temp46, index)

            temp2[trackid] = output

        framelabels: List[List[VideoBBoxLabel]] = []
        for index in range(num_frames):
            current_frame_labels = []
            for labellist in temp2.values():
                templable = labellist[index]
                if templable:
                    current_frame_labels.append(templable)
            framelabels.append(current_frame_labels)

        return framelabels
