"""
Representation of a bounding box labels
"""

from dataclasses import dataclass
from redbrick.entity.taxonomy import TaxonomyEntry
from typing import List, Union, Dict, Any
import numpy as np
import os
import json
from tqdm import tqdm
import copy
import uuid


@dataclass
class ImageBoundingBoxEntry:

    xnorm: float
    ynorm: float
    wnorm: float
    hnorm: float
    classname: TaxonomyEntry


@dataclass
class VideoBoundingBoxEntry:

    xnorm: float
    ynorm: float
    wnorm: float
    hnorm: float
    classname: TaxonomyEntry
    labelid: str
    trackid: str
    frameindex: int
    keyframe: bool
    end: bool


@dataclass
class BaseBoundingBox:
    labels: Union[List[ImageBoundingBoxEntry], List[VideoBoundingBoxEntry]]

    def show(self, data) -> None:
        """Show the label."""
        raise NotImplementedError()

    def __getitem__(
        self, index: int
    ) -> Union[ImageBoundingBoxEntry, VideoBoundingBoxEntry]:
        """Get item."""
        return self.labels[index]

    def __iter__(self):
        """Label iterator."""
        self.it = 0
        return self

    def __next__(self):
        """Next iterator."""
        if self.it < len(self.labels):
            val = self.labels[self.it]
            self.it += 1
            return val
        else:
            raise StopIteration


class ImageBoundingBox(BaseBoundingBox):
    """Bounding box for a single image."""

    def __init__(self, labels: dict) -> None:
        """Constructor."""
        self.labels: List[ImageBoundingBoxEntry]

        # Parse the remote labels, and save as entries
        entries = []
        for label in labels:
            label_ = label["bbox2d"]
            entry = ImageBoundingBoxEntry(
                xnorm=label_["xnorm"],
                ynorm=label_["ynorm"],
                wnorm=label_["wnorm"],
                hnorm=label_["hnorm"],
                classname=label["category"][0][-1],
            )
            entries.append(entry)

        self.labels = entries

    def show(self, data: np.ndarray) -> None:
        """Show the image bbox."""
        raise NotImplementedError()

    def __str__(self) -> str:
        """String representation."""
        labels = []
        for label in self.labels:
            entry = {}
            entry["category"] = [["object", label.classname]]
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

    def __init__(self, labels: dict) -> None:
        """Constructor."""
        self.labels: List[VideoBoundingBoxEntry]

        # parse the remote labels, and store entries
        entries = []
        for label in labels:
            entry = VideoBoundingBoxEntry(
                xnorm=label["bbox2d"]["xnorm"],
                ynorm=label["bbox2d"]["ynorm"],
                wnorm=label["bbox2d"]["wnorm"],
                hnorm=label["bbox2d"]["hnorm"],
                classname=label["category"][0][-1],
                labelid=label["labelid"],
                trackid=label["trackid"],
                frameindex=label["frameindex"],
                keyframe=label["keyframe"],
                end=label["end"],
            )
            entries.append(entry)

        self.labels = entries

    def show(self, data: List[np.ndarray]) -> None:
        """Show the video bbox."""
        raise NotImplementedError()
