"""
Representation of classification labels.
"""

from dataclasses import dataclass, field
from typing import List, Union


@dataclass
class VideoClassifyEntry:
    category: str
    labelid: str
    frameclassify: bool
    trackid: str
    keyframe: bool
    end: bool
    frameindex: int


@dataclass
class ImageClassify:
    classname: str


@dataclass
class VideoClassify:
    remote_labels: dict
    labels: List[VideoClassifyEntry] = field(init=False)

    def __post_init__(self):
        """After init."""
        entries = []
        for label in self.remote_labels:
            entry = VideoClassifyEntry(
                category=label["category"][0][-1],
                labelid=label["labelid"],
                frameclassify=label["frameclassify"],
                trackid=label["trackid"],
                keyframe=label["keyframe"],
                end=label["end"],
                frameindex=label["frameindex"],
            )
            entries.append(entry)

        self.labels = entries
