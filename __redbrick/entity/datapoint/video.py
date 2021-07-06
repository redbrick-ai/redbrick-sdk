"""
Representation for the video datapoint type.
"""

from dataclasses import dataclass, field
from .base_datapoint import BaseDatapoint
from typing import List, Union, Any, Optional
from redbrick.entity.label import VideoClassify, VideoBoundingBox
from redbrick.utils import url_to_image
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.animation as animation  # type: ignore
from tqdm import tqdm  # type: ignore


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

    def show_data(self, start: int = 0, end: int = 20) -> None:
        """Show the video data."""
        ims = []

        fig, ax = plt.subplots()

        num_frames = len(self.items_list)
        for i in tqdm(range(start, min(end, num_frames))):
            frame = url_to_image(url=self.items_list[i])
            height, width, _ = frame.shape
            im = plt.imshow(frame, animated=True)

            ims_ = self.labels.show(
                ax=ax,
                width=width,
                height=height,
                frameindex=i,
                num_frames=len(self.items_list),
            )

            ims_ = [im] + ims_  # the frame data im needs to be first
            ims.append(ims_)

        animation.ArtistAnimation(
            fig, ims, interval=50, blit=True, repeat_delay=1000,
        )
        plt.show()
