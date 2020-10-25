"""
Representation for the video datapoint type.
"""

from dataclasses import dataclass, field
from .base_datapoint import BaseDatapoint
from typing import List, Union
from redbrick.entity.label import VideoClassify, VideoBoundingBox


@dataclass
class Video(BaseDatapoint):
    """Video object."""

    dp_id: str
    video_name: str
    items_list: List[str]
    items_list_not_signed: List[str]
    labels: Union[VideoBoundingBox, VideoClassify] = field(init=False)

    def __post_init__(self) -> None:
        """Run after init."""
        if self.task_type == "BBOX":
            self.labels = VideoBoundingBox(labels=self.remote_labels)
        elif self.task_type == "CLASSIFY":
            self.labels = VideoClassify(remote_labels=self.remote_labels)
        else:
            raise ValueError(
                "%s task type not supported! Please reach out to contact@redbrickai.com."
                % self.task_type
            )
