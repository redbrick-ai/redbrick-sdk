"""
Representation of classification labels.
"""

from dataclasses import dataclass, field
from redbrick.entity.taxonomy2 import Taxonomy2
from redbrick.utils import compare_taxonomy
from typing import List, Union, Tuple, Dict, Any
import json
import uuid


@dataclass
class VideoClassifyEntry:
    category: List[List[str]]
    labelid: str
    frameclassify: bool
    trackid: str
    keyframe: bool
    end: bool
    frameindex: int


@dataclass
class ImageClassifyEntry:
    category: List[List[str]]


@dataclass
class ImageClassify:
    remote_labels: List[Any]
    labels: ImageClassifyEntry = field(init=False)

    def __post_init__(self) -> None:
        """Run after init."""
        self.labels = ImageClassifyEntry(self.remote_labels[0]["category"])

    def compare_taxonomy(self, taxonomy: Taxonomy2) -> Tuple[bool, List[List[str]]]:
        """Ensure self labels match taxonomy."""
        check = compare_taxonomy(category_path=self.labels.category, taxonomy=taxonomy)

        if check:
            return check, [["null", "null"]]
        else:
            return check, self.labels.category

    def show(self, ax: Any, width: int, height: int) -> None:
        """Show the image classify labels."""
        raise NotImplementedError()


@dataclass
class VideoClassify:
    remote_labels: List[Any]
    labels: List[VideoClassifyEntry] = field(init=False)

    def __post_init__(self) -> None:
        """After init."""
        entries = []
        trackid = str(uuid.uuid4())
        for label in self.remote_labels:

            # Fill out values if not provided
            if not "trackid" in label:
                label["trackid"] = trackid
            if not "end" in label:
                label["end"] = True
            if not "keyframe" in label:
                label["keyframe"] = True
            if not "labelid" in label:
                label["labelid"] = str(uuid.uuid4())

            entry = VideoClassifyEntry(
                category=label["category"],
                labelid=label["labelid"],
                frameclassify=label["frameclassify"],
                trackid=label["trackid"],
                keyframe=label["keyframe"],
                end=label["end"],
                frameindex=label["frameindex"],
            )
            entries.append(entry)

        self.labels = entries

    def compare_taxonomy(self, taxonomy: Taxonomy2) -> Tuple[bool, List[List[str]]]:
        """Ensure self labels match taxonomy."""

        for label in self.labels:
            check = compare_taxonomy(category_path=label.category, taxonomy=taxonomy)
            if not check:
                return check, label.category

        return True, [["null", "null"]]

    def __str__(self) -> str:
        """String representation of video classification."""
        labels = []
        for label in self.labels:
            entry: Dict[Any, Any] = {}
            entry["category"] = label.category
            entry["keyframe"] = label.keyframe
            entry["frameclassify"] = label.frameclassify
            entry["end"] = label.end
            entry["labelid"] = label.labelid
            entry["frameindex"] = label.frameindex
            entry["trackid"] = label.trackid
            entry["attributes"] = []

            labels.append(entry)

        output = {"labels": labels}
        return json.dumps(output)

    def show(
        self, ax: Any, width: int, height: int, frameindex: int, num_frames: int
    ) -> List[Any]:
        """show the labels."""
        raise NotImplementedError()
