"""
Representation of a bounding box labels
"""

from dataclasses import dataclass
from redbrick.entity.taxonomy import TaxonomyEntry
from redbrick.utils import compare_taxonomy
from redbrick.entity.taxonomy2 import Taxonomy2
from typing import List, Union, Dict, Any, Tuple
import numpy as np  # type: ignore
import os
import json
from tqdm import tqdm  # type: ignore
import copy
import uuid
import matplotlib.patches as patches  # type: ignore
from redbrick.sort import *  # type: ignore


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


@dataclass
class BaseBoundingBox:
    labels: Union[List[ImageBoundingBoxEntry], List[VideoBoundingBoxEntry]]

    def show(self, data: Any, width: int, height: int) -> None:
        """Show the label."""
        raise NotImplementedError()

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

    def show(self, ax: Any, width: int, height: int) -> None:
        """Show the video bbox."""
        raise NotImplementedError()

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

    def __track(self, num_frames: int) -> None:
        """Generate track id's for the video. INCOMPLETE."""
        new_labels = []

        # Iterate through labels and store map of labels
        sorted_labels = {}
        for label in self.labels:
            if not label.frameindex in sorted_labels:
                sorted_labels[label.frameindex] = [label]
            else:
                sorted_labels[label.frameindex] += [label]

        # Iterate through frames and update tracks
        tracker = Sort()  # type: ignore
        label_tracks: Dict[Any, Any] = {}
        for frame in range(num_frames):
            detections = []
            # Detections exist for this frame
            if frame in sorted_labels:

                # Iterate through each label for this frame
                for label in sorted_labels[frame]:
                    detections.append(
                        [
                            label.xnorm,
                            label.ynorm,
                            label.xnorm + label.wnorm,
                            label.ynorm + label.hnorm,
                            0.9,
                        ]
                    )
                detections = np.array(detections)  # convert to numpy array

            else:
                detections = np.empty((0, 5))

            tracks = tracker.update(dets=detections)

            # Iterate through the tracks
            for idx, track in enumerate(tracks):
                x1, y1, x2, y2, track_id = track
                track_id = str(int(track_id))
                labelid = str(uuid.uuid4())

                track_uuid = None
                keyframe = False
                if track_id in label_tracks:
                    track_uuid = label_tracks[track_id]["uuid"]
                    keyframe = True
                else:
                    label_tracks[track_id] = {}
                    label_tracks[track_id]["uuid"] = str(uuid.uuid4())
                    label_tracks[track_id]["labels"] = []
                    track_uuid = label_tracks[track_id]["uuid"]
                    keyframe = True

                entry = VideoBoundingBoxEntry(
                    xnorm=sorted_labels[frame][idx].xnorm,
                    ynorm=sorted_labels[frame][idx].ynorm,
                    wnorm=sorted_labels[frame][idx].wnorm,
                    hnorm=sorted_labels[frame][idx].hnorm,
                    classname=sorted_labels[frame][idx].classname,
                    labelid=labelid,
                    trackid=track_uuid,
                    frameindex=frame,
                    keyframe=keyframe,
                    end=False,
                )
                label_tracks[track_id]["labels"].append(entry)
                new_labels.append(entry)

        # Add end frame tags
        for track in label_tracks:
            label_tracks[track]["labels"][-1].end = True

        self.labels = new_labels
